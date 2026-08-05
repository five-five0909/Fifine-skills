import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { acquireLock, atomicWriteSync, readLockInfo } from '../../lib/shared/locking.mjs'
import { redactSecret, redactConfigForDisplay } from '../../lib/shared/redact.mjs'
import { resolveProjectRoot } from '../../lib/shared/paths.mjs'

test('redactSecret: 短值全遮，长值只留末4位', () => {
    assert.equal(redactSecret(''), '(未设置)')
    assert.equal(redactSecret('abc'), '****')
    assert.equal(redactSecret('sk-1234567890'), '*'.repeat('sk-1234567890'.length - 4) + '7890')
})

test('redactConfigForDisplay: apiKey 脱敏，其余字段透传', () => {
    const out = redactConfigForDisplay({ apiKey: 'sk-abcdefgh', model: 'mistral-embed' })
    assert.equal(out.model, 'mistral-embed')
    assert.equal(out.apiKey, '*'.repeat('sk-abcdefgh'.length - 4) + 'efgh')
    assert.equal(out.apiKeySet, true)
})

test('resolveProjectRoot: 显式参数优先于 cwd', () => {
    assert.equal(resolveProjectRoot('E:\\explicit\\path'), path.resolve('E:\\explicit\\path'))
})

test('resolveProjectRoot: 无参数回退 cwd', () => {
    assert.equal(resolveProjectRoot(), process.cwd())
})

test('acquireLock: 独占获取，重复获取失败，release 后可再次获取', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-lock-'))
    const lockPath = path.join(dir, 'x.lock')
    const release = acquireLock(lockPath)
    assert.ok(release, '首次应获取成功')
    assert.equal(acquireLock(lockPath), null, '锁被占用时应返回 null')
    release()
    const release2 = acquireLock(lockPath)
    assert.ok(release2, 'release 后应可再次获取')
    release2()
    fs.rmSync(dir, { recursive: true, force: true })
})

test('acquireLock: 陈旧锁（staleMs=0）应被自动回收抢占', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-lock-'))
    const lockPath = path.join(dir, 'x.lock')
    acquireLock(lockPath) // 不 release，模拟异常退出遗留
    const release = acquireLock(lockPath, { staleMs: 0 })
    assert.ok(release, '陈旧锁应被抢占成功')
    release()
    fs.rmSync(dir, { recursive: true, force: true })
})

test('readLockInfo: 无锁返回 null，有锁返回 pid', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-lock-'))
    const lockPath = path.join(dir, 'x.lock')
    assert.equal(readLockInfo(lockPath), null)
    const release = acquireLock(lockPath)
    const info = readLockInfo(lockPath)
    assert.equal(info.pid, process.pid)
    release()
    fs.rmSync(dir, { recursive: true, force: true })
})

test('atomicWriteSync: 目标文件在 writerFn 完成前不可见新内容', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-atomic-'))
    const target = path.join(dir, 'out.txt')
    fs.writeFileSync(target, 'old')
    atomicWriteSync(target, (tmp) => fs.writeFileSync(tmp, 'new'))
    assert.equal(fs.readFileSync(target, 'utf8'), 'new')
    // 确认没有残留临时文件
    const leftovers = fs.readdirSync(dir).filter(f => f.includes('.tmp-'))
    assert.equal(leftovers.length, 0)
    fs.rmSync(dir, { recursive: true, force: true })
})

test('atomicWriteSync: writerFn 抛错时不污染目标文件，临时文件被清理', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-atomic-'))
    const target = path.join(dir, 'out.txt')
    fs.writeFileSync(target, 'old')
    assert.throws(() => atomicWriteSync(target, () => { throw new Error('boom') }))
    assert.equal(fs.readFileSync(target, 'utf8'), 'old')
    const leftovers = fs.readdirSync(dir).filter(f => f.includes('.tmp-'))
    assert.equal(leftovers.length, 0)
    fs.rmSync(dir, { recursive: true, force: true })
})
