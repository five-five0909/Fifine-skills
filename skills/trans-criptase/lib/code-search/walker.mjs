// 目录遍历：跳过忽略规则命中项、二进制文件、超大文件、越界符号链接。
import fs from 'node:fs'
import path from 'node:path'
import { assertPathAllowed } from './security.mjs'
import { loadIgnoreRules } from './ignore.mjs'

const BINARY_SNIFF_BYTES = 8192

function looksBinary(filePath) {
    let fd
    try {
        fd = fs.openSync(filePath, 'r')
        const buf = Buffer.alloc(BINARY_SNIFF_BYTES)
        const bytesRead = fs.readSync(fd, buf, 0, BINARY_SNIFF_BYTES, 0)
        for (let i = 0; i < bytesRead; i++) if (buf[i] === 0) return true
        return false
    } catch {
        return true
    } finally {
        if (fd !== undefined) { try { fs.closeSync(fd) } catch { } }
    }
}

/**
 * 递归遍历 rootPath，返回可索引文件列表 + 跳过统计。
 * root 本身先经 allowedRoots 校验；目录内每个符号链接条目单独校验真实落点。
 */
export function walkFiles(rootPath, { allowedRoots = [], maxFileSizeBytes = 2 * 1024 * 1024, ignoreExtra = [], useGitignore = true } = {}) {
    const resolvedRoot = assertPathAllowed(rootPath, allowedRoots)
    if (!fs.existsSync(resolvedRoot) || !fs.statSync(resolvedRoot).isDirectory()) {
        throw new Error(`root_path 不是有效目录: ${resolvedRoot}`)
    }
    const ignore = loadIgnoreRules(resolvedRoot, ignoreExtra, useGitignore)
    const out = []
    const skipped = { binary: 0, tooLarge: 0, ignored: 0, symlinkEscape: 0 }

    function walk(dir) {
        let entries
        try { entries = fs.readdirSync(dir, { withFileTypes: true }) } catch { return }
        for (const ent of entries) {
            const full = path.join(dir, ent.name)
            const rel = path.relative(resolvedRoot, full)
            if (ignore.isIgnored(rel)) { skipped.ignored++; continue }
            if (ent.isSymbolicLink()) {
                let real
                try { real = fs.realpathSync(full) } catch { continue }
                if (real !== resolvedRoot && !real.startsWith(resolvedRoot + path.sep)) { skipped.symlinkEscape++; continue }
            }
            let stat
            try { stat = fs.statSync(full) } catch { continue }
            if (stat.isDirectory()) { walk(full); continue }
            if (!stat.isFile()) continue
            if (stat.size > maxFileSizeBytes) { skipped.tooLarge++; continue }
            if (looksBinary(full)) { skipped.binary++; continue }
            out.push({ path: full, relPath: rel.replace(/\\/g, '/'), size: stat.size, mtimeMs: stat.mtimeMs })
        }
    }
    walk(resolvedRoot)
    return { root: resolvedRoot, files: out, skipped }
}
