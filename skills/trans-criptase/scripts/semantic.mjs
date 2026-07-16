#!/usr/bin/env node
// trans 语义检索 CLI（逻辑在 lib.mjs / lib/code-search，MCP 服务器共用）
// 用法：
//   node semantic.mjs index  [--project <路径>] [--all] [--dry] [--force] [--no-embed]
//   node semantic.mjs query "自然语言描述" [--top 8] [--project <路径>] [--all] [--exact|--semantic] [--rerank]
//   node semantic.mjs status
//   node semantic.mjs code-index --root <路径> [--force] [--no-embed] [--dry]
//   node semantic.mjs code-query "描述" --root <路径> [--mode exact|semantic|hybrid] [--top 10]
//   node semantic.mjs code-status [--root <路径>]
//   node semantic.mjs doctor
import * as lib from './lib.mjs'
import { buildCodeIndex, codeStatus } from '../lib/code-search/indexer.mjs'
import { codeQuery } from '../lib/code-search/query.mjs'
import { resolveProjectRoot } from '../lib/shared/paths.mjs'

function parseArgs(rest) {
    const o = { project: process.cwd(), top: 8, texts: [] }
    for (let i = 0; i < rest.length; i++) {
        const a = rest[i]
        if (a === '--project') o.project = rest[++i]
        else if (a === '--top') o.top = parseInt(rest[++i], 10) || 8
        else if (a === '--all') o.all = true
        else if (a === '--dry') o.dry = true
        else if (a === '--force') o.force = true
        else if (a === '--rerank') o.rerank = true
        else if (a === '--exact') o.exact = true
        else if (a === '--semantic') o.semantic = true
        else if (a === '--no-embed') o.noEmbed = true
        else if (a === '--limit') o.limit = parseInt(rest[++i], 10) || 40
        else if (a === '--query') o.query = rest[++i]
        else if (a === '--root') o.root = rest[++i]
        else if (a === '--mode') o.mode = rest[++i]
        else o.texts.push(a)
    }
    return o
}

const [cmd, ...rest] = process.argv.slice(2)
const opts = parseArgs(rest)
const print = (lines) => console.log(lines.join('\n'))

try {
    if (cmd === 'index') {
        print(await lib.indexCommand(opts))
    } else if (cmd === 'query') {
        const text = opts.texts.join(' ').trim()
        if (!text) { console.log('用法: node semantic.mjs query "描述" [--top 8] [--all] [--exact|--semantic] [--rerank]'); process.exit(1) }
        print(await lib.queryLines(text, opts))
    } else if (cmd === 'status') {
        print(lib.statusLines())
    } else if (cmd === 'projects') {
        print(lib.projectsLines(opts))
    } else if (cmd === 'code-index') {
        const root = resolveProjectRoot(opts.root)
        const res = await buildCodeIndex(root, { force: opts.force, noEmbed: opts.noEmbed, dry: opts.dry })
        print([`root: ${root}`, ...res.lines])
    } else if (cmd === 'code-query') {
        const text = opts.texts.join(' ').trim()
        if (!text) { console.log('用法: node semantic.mjs code-query "描述" --root <路径> [--mode exact|semantic|hybrid] [--top 10]'); process.exit(1) }
        const root = resolveProjectRoot(opts.root)
        const res = await codeQuery({ query: text, mode: opts.mode, root_path: root, limit: opts.top })
        console.log(JSON.stringify(res, null, 2))
    } else if (cmd === 'code-status') {
        const root = resolveProjectRoot(opts.root)
        console.log(JSON.stringify({ root, ...codeStatus(root) }, null, 2))
    } else if (cmd === 'doctor') {
        const { run } = await import('./doctor.mjs')
        await run()
    } else {
        console.log('用法:\n  node semantic.mjs index  [--project <路径>] [--all] [--dry] [--force] [--no-embed]\n  node semantic.mjs query "自然语言描述" [--top 8] [--project <路径>] [--all] [--exact|--semantic] [--rerank]\n  node semantic.mjs projects [--query <关键词>] [--limit 40]\n  node semantic.mjs status\n  node semantic.mjs code-index --root <路径> [--force] [--no-embed] [--dry]\n  node semantic.mjs code-query "描述" --root <路径> [--mode exact|semantic|hybrid] [--top 10]\n  node semantic.mjs code-status [--root <路径>]\n  node semantic.mjs doctor\n默认混合检索（向量+关键词 RRF 融合）；--exact 纯关键词（无需 API）；--semantic 纯向量')
    }
} catch (e) {
    console.error('出错: ' + e.message)
    process.exit(1)
}
