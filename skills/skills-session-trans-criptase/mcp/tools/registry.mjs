// 代码检索工具注册表：MCP server 只从这里取 TOOLS 定义与分发，每个工具自身是薄封装（参数校验+调用 lib/code-search）。
import * as query from './query.mjs'
import * as index from './index.mjs'
import * as status from './status.mjs'
import * as read from './read.mjs'
import * as configCheck from './config-check.mjs'

const MODULES = [query, index, status, read, configCheck]

export const TOOLS = MODULES.map((m) => m.definition)

const CALLERS = Object.fromEntries(MODULES.map((m) => [m.definition.name, m.call]))

export async function handleCodeToolCall(name, args) {
    const fn = CALLERS[name]
    if (!fn) throw new Error(`unknown tool: ${name}`)
    return fn(args)
}
