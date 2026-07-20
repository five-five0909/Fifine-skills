// trans_code_read 的读取逻辑：路径必须落在 root_path（若给）或 allowedRoots（若配置）内，拒绝穿越/越界。
// 已知限制：MCP 工具按调用是无状态的，这里只做机械的路径边界校验，不追踪"是否来自本次 query 结果"——
// 后者是 SKILL.md 里对模型行为的软约束（不得读取搜索结果之外的任意路径），不是本函数的强制边界。
import fs from 'node:fs'
import path from 'node:path'
import { loadSharedConfig } from '../shared/config.mjs'
import { assertPathAllowed, assertNoTraversal } from './security.mjs'

export function readCodeSlice({ path: relOrAbs, root_path, start_line, end_line } = {}) {
    if (!relOrAbs) throw new Error('path 必填')
    const cfg = loadSharedConfig()
    const allowedRoots = cfg.codeSearch.security.allowedRoots

    let full
    if (root_path) {
        const root = path.resolve(root_path)
        full = assertNoTraversal(root, relOrAbs)
        assertPathAllowed(full, allowedRoots.length ? allowedRoots : [root])
    } else {
        full = assertPathAllowed(relOrAbs, allowedRoots)
    }

    if (!fs.existsSync(full) || !fs.statSync(full).isFile()) throw new Error(`文件不存在: ${full}`)
    const lines = fs.readFileSync(full, 'utf8').split('\n')
    const s = Math.max(1, start_line || 1)
    const e = Math.min(lines.length, end_line || lines.length)
    if (s > e) throw new Error(`start_line(${s}) 不能大于 end_line(${e})`)
    return { path: full, start_line: s, end_line: e, content: lines.slice(s - 1, e).join('\n') }
}
