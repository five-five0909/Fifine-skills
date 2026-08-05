#!/usr/bin/env node
// 兼容 shim：MCP Server 已迁移到 mcp/server.mjs（同时挂载转录续接 + 代码检索工具）。
// 保留本文件路径，防止任何硬编码了旧路径的第三方文档/脚本/MCP 注册记录瞬间失效。
// 计划在下一个大版本移除，请尽快改为直接指向 mcp/server.mjs。
import '../mcp/server.mjs'
