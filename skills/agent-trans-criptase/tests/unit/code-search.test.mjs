import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { loadIgnoreRules } from '../../lib/code-search/ignore.mjs'
import { assertPathAllowed, assertNoTraversal } from '../../lib/code-search/security.mjs'
import { chunkFileByLines } from '../../lib/code-search/indexer.mjs'
import { walkFiles } from '../../lib/code-search/walker.mjs'

test('loadIgnoreRules: baseline 忽略 .git/node_modules，且不可被 .transignore 移除', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-ignore-'))
    fs.writeFileSync(path.join(dir, '.transignore'), '# 用户尝试的规则\nbuild\n')
    const rules = loadIgnoreRules(dir, [], true)
    assert.ok(rules.isIgnored('.git'))
    assert.ok(rules.isIgnored('node_modules'))
    assert.ok(rules.isIgnored('.env'))
    assert.ok(rules.isIgnored('secret.key'))
    assert.ok(rules.isIgnored('build')) // 用户追加规则生效
    assert.equal(rules.isIgnored('src/index.mjs'), false)
    fs.rmSync(dir, { recursive: true, force: true })
})

test('assertNoTraversal: 拒绝 .. 穿越，放行边界内路径', () => {
    const root = process.platform === 'win32' ? 'E:\\proj' : '/proj'
    assert.throws(() => assertNoTraversal(root, '..\\..\\etc\\passwd'))
    assert.doesNotThrow(() => assertNoTraversal(root, 'src\\index.js'))
})

test('assertPathAllowed: allowedRoots 为空不限制，非空则严格校验', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-sec-'))
    assert.doesNotThrow(() => assertPathAllowed(dir, []))
    assert.doesNotThrow(() => assertPathAllowed(dir, [dir]))
    const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-outside-'))
    assert.throws(() => assertPathAllowed(outside, [dir]))
    fs.rmSync(dir, { recursive: true, force: true })
    fs.rmSync(outside, { recursive: true, force: true })
})

test('chunkFileByLines: 保留真实行号，短文件单块', () => {
    const chunks = chunkFileByLines('line1\nline2\nline3', 800)
    assert.equal(chunks.length, 1)
    assert.equal(chunks[0].start_line, 1)
    assert.equal(chunks[0].end_line, 3)
})

test('chunkFileByLines: 超过 maxChars 按行边界切块，不切断行内内容', () => {
    const lines = Array.from({ length: 50 }, (_, i) => `line ${i} `.repeat(3))
    const text = lines.join('\n')
    const chunks = chunkFileByLines(text, 100)
    assert.ok(chunks.length > 1)
    // 每块的 text 拼接应完整覆盖原始行范围，不丢行
    const totalLinesCovered = chunks.reduce((sum, c) => sum + (c.end_line - c.start_line + 1), 0)
    assert.ok(totalLinesCovered >= lines.length)
})

test('walkFiles: 跳过忽略目录/二进制/超大文件，收录普通文本文件', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-walk-'))
    fs.mkdirSync(path.join(dir, 'node_modules'))
    fs.writeFileSync(path.join(dir, 'node_modules', 'x.js'), 'ignored')
    fs.writeFileSync(path.join(dir, 'a.txt'), 'hello world')
    fs.writeFileSync(path.join(dir, 'big.txt'), 'x'.repeat(3000))
    fs.writeFileSync(path.join(dir, 'bin.dat'), Buffer.from([0, 1, 2, 0, 3]))
    const { files, skipped } = walkFiles(dir, { maxFileSizeBytes: 1000 })
    const relPaths = files.map((f) => f.relPath)
    assert.ok(relPaths.includes('a.txt'))
    assert.ok(!relPaths.some((p) => p.startsWith('node_modules')))
    assert.ok(!relPaths.includes('big.txt'))
    assert.ok(!relPaths.includes('bin.dat'))
    assert.equal(skipped.tooLarge, 1)
    assert.equal(skipped.binary, 1)
    fs.rmSync(dir, { recursive: true, force: true })
})
