// 共享文件锁 + 原子写：转录索引与代码索引共用，防止两个客户端的 MCP 进程并发建索引时互相踩写。
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'

const DEFAULT_STALE_MS = 10 * 60 * 1000 // 10 分钟无更新视为陈旧锁，允许抢占（进程异常退出后的自动恢复）

/**
 * 尝试获取文件锁。成功返回 release() 函数；锁被占用（且未陈旧）返回 null。
 * 锁文件内容记录 {pid, host, acquiredAt}，供占用提示与陈旧判定使用。
 */
export function acquireLock(lockPath, { staleMs = DEFAULT_STALE_MS } = {}) {
    fs.mkdirSync(path.dirname(lockPath), { recursive: true })
    const payload = JSON.stringify({ pid: process.pid, host: os.hostname(), acquiredAt: Date.now() })
    try {
        fs.writeFileSync(lockPath, payload, { flag: 'wx' }) // 独占创建，已存在则抛错
        return () => { try { fs.rmSync(lockPath, { force: true }) } catch { } }
    } catch (e) {
        if (e.code !== 'EEXIST') throw e
        // 已存在：判断是否陈旧
        let info = null
        try { info = JSON.parse(fs.readFileSync(lockPath, 'utf8')) } catch { }
        const age = info?.acquiredAt ? Date.now() - info.acquiredAt : Infinity
        if (age >= staleMs) {
            // 陈旧锁：视为异常退出遗留，回收后重试一次
            try { fs.rmSync(lockPath, { force: true }) } catch { }
            try {
                fs.writeFileSync(lockPath, payload, { flag: 'wx' })
                return () => { try { fs.rmSync(lockPath, { force: true }) } catch { } }
            } catch { return null }
        }
        return null
    }
}

/** 锁占用信息（供"清晰提示占用者"使用），无锁则返回 null。 */
export function readLockInfo(lockPath) {
    if (!fs.existsSync(lockPath)) return null
    try { return JSON.parse(fs.readFileSync(lockPath, 'utf8')) } catch { return null }
}

/**
 * 原子写：写临时文件后 rename 替换目标文件，避免并发读取到半写入内容。
 * writerFn(tmpPath) 负责把内容写进 tmpPath（可多次 write/append）。
 */
export function atomicWriteSync(targetPath, writerFn) {
    fs.mkdirSync(path.dirname(targetPath), { recursive: true })
    const tmpPath = `${targetPath}.tmp-${process.pid}-${Date.now()}`
    try {
        writerFn(tmpPath)
        fs.renameSync(tmpPath, targetPath)
    } catch (e) {
        try { fs.rmSync(tmpPath, { force: true }) } catch { }
        throw e
    }
}

/** 原子追加：先复制现有内容到临时文件、追加新内容，再 rename——用于 meta.jsonl/vec.bin 这类持续追加的索引文件。 */
export function atomicAppendSync(targetPath, chunkBuffers) {
    atomicWriteSync(targetPath, (tmpPath) => {
        if (fs.existsSync(targetPath)) fs.copyFileSync(targetPath, tmpPath)
        const fd = fs.openSync(tmpPath, 'a')
        try { for (const buf of chunkBuffers) fs.writeSync(fd, buf) } finally { fs.closeSync(fd) }
    })
}
