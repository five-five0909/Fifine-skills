// MCP server 集成测试：tools/list 数量、代码检索全链路（noEmbed，零 API 依赖，沙箱隔离）。
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const SERVER = path.join(HERE, '..', '..', 'mcp', 'server.mjs')

function rpc(requests, env = {}) {
    return new Promise((resolve, reject) => {
        const child = spawn(process.execPath, [SERVER], { env: { ...process.env, ...env } })
        let out = ''
        let err = ''
        child.stdout.on('data', (d) => { out += d })
        child.stderr.on('data', (d) => { err += d })
        child.on('close', () => {
            const lines = out.split('\n').filter(Boolean).map((l) => { try { return JSON.parse(l) } catch { return null } }).filter(Boolean)
            resolve({ lines, err })
        })
        child.on('error', reject)
        child.stdin.write(requests.map((r) => JSON.stringify(r)).join('\n') + '\n')
        child.stdin.end()
    })
}

test('tools/list 返回全部 11 个工具（6 转录 + 5 代码检索）', async () => {
    const { lines } = await rpc([{ jsonrpc: '2.0', id: 1, method: 'tools/list' }])
    const tools = lines[0].result.tools.map((t) => t.name)
    const expected = [
        'trans_search', 'trans_scan', 'trans_list', 'trans_projects', 'trans_expand', 'trans_index',
        'trans_code_query', 'trans_code_index', 'trans_code_status', 'trans_code_read', 'trans_code_config_check',
    ]
    for (const name of expected) assert.ok(tools.includes(name), `缺少工具 ${name}`)
    assert.equal(tools.length, 11)
})

test('代码检索全链路：index(noEmbed) → query(exact) → read，沙箱隔离不碰真实数据', async () => {
    const sandboxRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-mcp-code-'))
    const codeIndexRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-mcp-idx-'))
    const needle = 'zebrafish_gate_checkpoint'
    fs.writeFileSync(path.join(sandboxRoot, 'pipeline.py'), `def ${needle}():\n    return True\n`)

    const env = { TRANS_CODE_INDEX_ROOT: codeIndexRoot }
    const call = (name, args) => [{ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }]

    const idx = await rpc(call('trans_code_index', { root_path: sandboxRoot, noEmbed: true }), env)
    const idxBody = JSON.parse(idx.lines[0].result.content[0].text)
    assert.equal(idxBody.ok, true)
    assert.ok(idxBody.chunksAdded >= 1)

    const q = await rpc(call('trans_code_query', { root_path: sandboxRoot, query: needle, mode: 'exact' }), env)
    const qBody = JSON.parse(q.lines[0].result.content[0].text)
    assert.equal(qBody.mode, 'exact')
    assert.ok(qBody.results.length >= 1)
    assert.equal(qBody.results[0].path, 'pipeline.py')

    const r = await rpc(call('trans_code_read', { root_path: sandboxRoot, path: qBody.results[0].path }), env)
    const rBody = JSON.parse(r.lines[0].result.content[0].text)
    assert.ok(rBody.content.includes(needle))

    fs.rmSync(sandboxRoot, { recursive: true, force: true })
    fs.rmSync(codeIndexRoot, { recursive: true, force: true })
})

test('trans_code_read 拒绝越界穿越', async () => {
    const sandboxRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-mcp-code-'))
    const call = (name, args) => [{ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }]
    const r = await rpc(call('trans_code_read', { root_path: sandboxRoot, path: '..\\..\\..\\secret.txt' }))
    assert.equal(r.lines[0].result.isError, true)
    fs.rmSync(sandboxRoot, { recursive: true, force: true })
})
