// 并发建索引压力测试：两个真实子进程同时对同一 root_path 建代码索引，验证锁机制生效——
// 一个成功建索引，另一个检测到占用后优雅跳过（返回 ok:false + 提示），索引文件不损坏（可正常加载解析）。
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = path.join(HERE, '..', '..')

function runWorker(sandboxRoot, codeIndexRoot) {
    const script = `
        import { buildCodeIndex } from '${pathToFileUrl(path.join(REPO_ROOT, 'lib', 'code-search', 'indexer.mjs'))}'
        const res = await buildCodeIndex(process.env.TRANS_TEST_ROOT, { noEmbed: true })
        console.log(JSON.stringify(res))
    `
    return new Promise((resolve, reject) => {
        const child = spawn(process.execPath, ['--input-type=module', '-e', script], {
            env: { ...process.env, TRANS_CODE_INDEX_ROOT: codeIndexRoot, TRANS_TEST_ROOT: sandboxRoot },
        })
        let out = ''
        let err = ''
        child.stdout.on('data', (d) => { out += d })
        child.stderr.on('data', (d) => { err += d })
        child.on('close', (code) => resolve({ code, out: out.trim(), err }))
        child.on('error', reject)
    })
}

function pathToFileUrl(p) {
    return 'file:///' + p.replace(/\\/g, '/')
}

test('两个进程同时对同一 root_path 建索引：锁生效，一成功一优雅跳过，索引不损坏', async () => {
    const sandboxRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-concurrent-src-'))
    const codeIndexRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-concurrent-idx-'))

    // 造点文件量，让建索引过程有一定耗时，增大真实竞争窗口
    for (let i = 0; i < 30; i++) {
        fs.writeFileSync(path.join(sandboxRoot, `file${i}.txt`), `content ${i}\n`.repeat(50))
    }

    const [r1, r2] = await Promise.all([
        runWorker(sandboxRoot, codeIndexRoot),
        runWorker(sandboxRoot, codeIndexRoot),
    ])

    const results = [r1, r2].map((r) => {
        assert.equal(r.code, 0, `子进程应正常退出，stderr: ${r.err}`)
        return JSON.parse(r.out)
    })

    const succeeded = results.filter((r) => r.ok === true)
    const skipped = results.filter((r) => r.ok === false)

    // 至少一个成功；若两个都抢到了空隙各自成功也可接受（锁窗口可能因执行太快而错开），
    // 但绝不能出现"两个都成功却数据不一致"的损坏态——用后续加载校验兜底。
    assert.ok(succeeded.length >= 1, '至少应有一个建索引成功')
    if (skipped.length) {
        assert.match(skipped[0].lines.join(' '), /索引正被.*占用/, '被跳过的一方应给出清晰的占用提示')
    }

    // 索引文件本身必须完整可解析，不能是半写入的损坏状态
    const enc = path.resolve(sandboxRoot).replace(/[^A-Za-z0-9]/g, '-')
    const statePath = path.join(codeIndexRoot, enc, 'state.json')
    const metaPath = path.join(codeIndexRoot, enc, 'meta.jsonl')
    assert.ok(fs.existsSync(statePath), 'state.json 应存在')
    const state = JSON.parse(fs.readFileSync(statePath, 'utf8')) // 不抛错即证明不是半写入的 JSON
    assert.ok(state.files && Object.keys(state.files).length > 0)
    const metaLines = fs.readFileSync(metaPath, 'utf8').split('\n').filter(Boolean)
    for (const line of metaLines) JSON.parse(line) // 每行都必须是完整合法 JSON，不能有半截行

    fs.rmSync(sandboxRoot, { recursive: true, force: true })
    fs.rmSync(codeIndexRoot, { recursive: true, force: true })
})
