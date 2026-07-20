// 代码/文档索引构建：与转录索引同款三件套（state.json + meta.jsonl + vec.bin），独立命名空间 data/code-index/。
// 复用 scripts/lib.mjs 的 embedBatch/normalize（同一 embedding provider 配置，两条主线共用一份 key）。
// 与转录索引不同：按真实行号切块（不拉平换行），保证 start_line/end_line 对源代码有意义。
import fs from 'node:fs'
import path from 'node:path'
import { INSTALL_ROOT } from '../shared/paths.mjs'
import { loadSharedConfig } from '../shared/config.mjs'
import { acquireLock, atomicWriteSync, readLockInfo } from '../shared/locking.mjs'
import { embedBatch, normalize } from '../../scripts/lib.mjs'
import { walkFiles } from './walker.mjs'

export const CODE_INDEX_ROOT = process.env.TRANS_CODE_INDEX_ROOT || path.join(INSTALL_ROOT, 'data', 'code-index')

export const encodeRoot = (p) => path.resolve(p).replace(/[^A-Za-z0-9]/g, '-')

export function codeIndexPaths(rootPath) {
    const enc = encodeRoot(rootPath)
    const iDir = path.join(CODE_INDEX_ROOT, enc)
    return {
        enc, iDir,
        state: path.join(iDir, 'state.json'),
        meta: path.join(iDir, 'meta.jsonl'),
        vec: path.join(iDir, 'vec.bin'),
        lock: path.join(iDir, 'state.json.lock'),
    }
}

function writeStateSync(P, state) {
    atomicWriteSync(P.state, (tmp) => fs.writeFileSync(tmp, JSON.stringify(state)))
}

/** 按行切块，保留真实行号（不同于转录索引的 chunkText，那个会拉平换行——源码需要保留行结构）。 */
export function chunkFileByLines(text, maxChars) {
    const lines = text.split('\n')
    const chunks = []
    let buf = []
    let bufLen = 0
    let startLine = 1
    for (let i = 0; i < lines.length; i++) {
        buf.push(lines[i])
        bufLen += lines[i].length + 1
        if (bufLen >= maxChars) {
            chunks.push({ start_line: startLine, end_line: i + 1, text: buf.join('\n') })
            buf = []; bufLen = 0; startLine = i + 2
        }
    }
    if (buf.length) chunks.push({ start_line: startLine, end_line: lines.length, text: buf.join('\n') })
    if (!chunks.length) chunks.push({ start_line: 1, end_line: lines.length || 1, text })
    return chunks
}

export function loadCodeIndex(rootPath) {
    const P = codeIndexPaths(rootPath)
    if (!fs.existsSync(P.state) || !fs.existsSync(P.meta)) return null
    const state = JSON.parse(fs.readFileSync(P.state, 'utf8'))
    const metas = fs.readFileSync(P.meta, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l))
    let fa = null
    let n = metas.length
    if (state.dims && fs.existsSync(P.vec)) {
        const raw = fs.readFileSync(P.vec)
        const ab = new ArrayBuffer(raw.length)
        Buffer.from(ab).set(raw)
        fa = new Float32Array(ab)
        n = Math.min(Math.floor(fa.length / state.dims), metas.length)
    }
    return { enc: P.enc, root: state.root || rootPath, state, fa, metas, n }
}

/**
 * 建/增量更新代码索引。force=全量重建；incremental（默认 true 语义，通过 mtime 比对实现）；
 * noEmbed=仅关键词；dry=只统计不写盘。返回 {ok, lines, filesIndexed, chunksAdded}。
 */
export async function buildCodeIndex(rootPath, opts = {}) {
    const cfg = loadSharedConfig()
    const cs = cfg.codeSearch
    const P = codeIndexPaths(rootPath)
    fs.mkdirSync(P.iDir, { recursive: true })

    const release = acquireLock(P.lock)
    if (!release) {
        const info = readLockInfo(P.lock)
        const who = info ? `pid ${info.pid}@${info.host}（${new Date(info.acquiredAt).toISOString()} 起）` : '未知进程'
        return { ok: false, lines: [`代码索引正被 ${who} 建索引占用，本次跳过（陈旧锁 10 分钟后自动回收）`] }
    }
    try {
        return await build()
    } finally {
        release()
    }

    async function build() {
        const out = []
        const mode = opts.noEmbed ? 'kw' : 'vec'
        let state = fs.existsSync(P.state)
            ? JSON.parse(fs.readFileSync(P.state, 'utf8'))
            : { model: cfg.model, dims: 0, mode, root: path.resolve(rootPath), files: {} }
        if (opts.force || (state.model && state.model !== cfg.model) || (state.mode && state.mode !== mode)) {
            if (state.model && state.model !== cfg.model) out.push(`模型从 ${state.model} 换成 ${cfg.model}，全量重建`)
            state = { model: cfg.model, dims: 0, mode, root: path.resolve(rootPath), files: {} }
            fs.rmSync(P.meta, { force: true })
            fs.rmSync(P.vec, { force: true })
        }
        state.mode = mode

        const { files, skipped } = walkFiles(rootPath, {
            allowedRoots: cs.security.allowedRoots,
            maxFileSizeBytes: cs.maxFileSizeBytes,
            ignoreExtra: cs.ignore.extra,
            useGitignore: cs.ignore.useGitignore,
        })

        const currentFiles = Object.fromEntries(files.map((f) => [f.relPath, { mtimeMs: f.mtimeMs, size: f.size }]))
        const staleEntries = Object.entries(state.files || {}).some(([relPath, previous]) => {
            const current = currentFiles[relPath]
            return !current || current.mtimeMs !== previous.mtimeMs || current.size !== previous.size
        })
        if (staleEntries) {
            out.push('检测到已修改或删除的文件，完整重建索引以清除过期结果')
            if (!opts.dry) {
                state = { model: cfg.model, dims: 0, mode, root: path.resolve(rootPath), files: {} }
                fs.rmSync(P.meta, { force: true })
                fs.rmSync(P.vec, { force: true })
            }
        }

        let totalNew = 0
        for (const f of files) {
            const prev = state.files[f.relPath]
            if (prev && prev.mtimeMs === f.mtimeMs && !opts.force) continue
            let text
            try { text = fs.readFileSync(f.path, 'utf8') } catch { continue }
            const parts = chunkFileByLines(text, cfg.maxChars)
            const chunks = parts.map((p, k) => ({ path: f.relPath, start_line: p.start_line, end_line: p.end_line, part: k, text: p.text }))

            if (opts.dry) { totalNew += chunks.length; continue }

            if (chunks.length && opts.noEmbed) {
                const metaFd = fs.openSync(P.meta, 'a')
                try { for (const c of chunks) fs.writeSync(metaFd, JSON.stringify(c) + '\n') } finally { fs.closeSync(metaFd) }
            } else if (chunks.length) {
                const vecFd = fs.openSync(P.vec, 'a')
                const metaFd = fs.openSync(P.meta, 'a')
                try {
                    for (let i = 0; i < chunks.length; i += cfg.batchSize) {
                        const batch = chunks.slice(i, i + cfg.batchSize)
                        const vecs = await embedBatch(batch.map((c) => c.text))
                        if (!state.dims) state.dims = vecs[0].length
                        for (let k = 0; k < batch.length; k++) {
                            const v = normalize(Float32Array.from(vecs[k]))
                            fs.writeSync(vecFd, Buffer.from(v.buffer, v.byteOffset, v.byteLength))
                            fs.writeSync(metaFd, JSON.stringify(batch[k]) + '\n')
                        }
                    }
                } finally { fs.closeSync(vecFd); fs.closeSync(metaFd) }
            }
            state.files[f.relPath] = { mtimeMs: f.mtimeMs, size: f.size }
            writeStateSync(P, state)
            totalNew += chunks.length
        }

        if (!opts.dry) writeStateSync(P, state)
        const tailNote = opts.noEmbed ? '（纯关键词索引，查询走 exact；填好 key 后 force 重建升级混合）' : ''
        out.push(opts.dry
            ? `[dry] 共将新增 ${totalNew} 块（扫描 ${files.length} 文件，未调 API）`
            : `新增 ${totalNew} 块，扫描 ${files.length} 文件，索引就绪${tailNote}（忽略 ${skipped.ignored}，二进制 ${skipped.binary}，超限 ${skipped.tooLarge}，符号链接逃逸 ${skipped.symlinkEscape}）`)
        return { ok: true, lines: out, filesIndexed: files.length, chunksAdded: totalNew }
    }
}

export function codeStatus(rootPath) {
    const idx = loadCodeIndex(rootPath)
    if (!idx) return { indexed: false }
    return {
        indexed: true,
        model: idx.state.model,
        mode: idx.state.mode,
        dims: idx.state.dims,
        chunks: idx.metas.length,
        fileCount: Object.keys(idx.state.files || {}).length,
        vecSizeMB: (() => { try { return +(fs.statSync(codeIndexPaths(rootPath).vec).size / 1048576).toFixed(1) } catch { return 0 } })(),
    }
}
