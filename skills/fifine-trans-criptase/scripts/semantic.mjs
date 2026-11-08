#!/usr/bin/env node
// Local transcript and code-search CLI. Search and indexing share the same libraries.
import * as lib from './lib.mjs'
import { buildCodeIndex, codeStatus, CODE_INDEX_ROOT } from '../lib/code-search/indexer.mjs'
import { codeQuery } from '../lib/code-search/query.mjs'
import { readCodeSlice } from '../lib/code-search/reader.mjs'
import { resolveProjectRoot } from '../lib/shared/paths.mjs'
import { loadSharedConfig } from '../lib/shared/config.mjs'
import {
    checkNodeVersion, checkConfigFile, checkApiKeyPresence, checkEmbeddingConnectivity,
    checkDirWritable, checkCliPresence, summarize, configSummaryForDisplay,
} from '../lib/shared/diagnostics.mjs'
import { redactSecret } from '../lib/shared/redact.mjs'

function parseArgs(rest) {
    const o = { texts: [] }
    const values = {
        '--project': 'project', '--root': 'root', '--root-path': 'root',
        '--query': 'query', '--mode': 'mode', '--id': 'id', '--path': 'path',
        '--session-id': 'sessionId',
    }
    const numbers = {
        '--top': 'top', '--limit': 'limit', '--tail': 'tail', '--max-msgs': 'maxMsgs',
        '--detail-line': 'detailLine', '--detail': 'detailLine', '--line': 'line',
        '--before': 'before', '--after': 'after', '--start-line': 'startLine', '--end-line': 'endLine',
    }
    const flags = {
        '--all': 'all', '--dry': 'dry', '--force': 'force', '--rerank': 'rerank',
        '--exact': 'exact', '--semantic': 'semantic', '--no-embed': 'noEmbed',
    }
    for (let i = 0; i < rest.length; i++) {
        const a = rest[i]
        if (values[a] || numbers[a]) {
            const value = rest[++i]
            if (value === undefined || value.startsWith('--')) throw new Error(`${a} requires a value`)
            if (numbers[a]) {
                if (!/^\d+$/.test(value)) throw new Error(`${a} requires a non-negative integer`)
                o[numbers[a]] = Number(value)
            } else o[values[a]] = value
        } else if (flags[a]) o[flags[a]] = true
        else if (a === '--no-rerank') o.rerank = false
        else if (a.startsWith('--')) throw new Error(`unknown option: ${a}`)
        else o.texts.push(a)
    }
    return o
}

const usage = `Usage: node semantic.mjs <command> [options]
  list [--project PATH] [--limit N]
  scan [--id ID | --path PATH] [--project PATH] [--tail N] [--max-msgs N] [--detail-line N]
  projects [--query TEXT] [--limit N]
  search TEXT [--project PATH] [--all] [--top N] [--mode exact|semantic|hybrid] [--no-rerank]
  query TEXT [--project PATH] [--all] [--top N] [--exact|--semantic] [--rerank]
  expand --session-id ID --line N [--project PATH] [--before N] [--after N]
  index [--project PATH] [--all] [--dry] [--force] [--no-embed]
  status
  code-index [--root PATH] [--force] [--no-embed] [--dry]
  code-query TEXT [--root PATH] [--mode exact|semantic|hybrid] [--limit N]
  code-status [--root PATH]
  code-read PATH [--root PATH] [--start-line N] [--end-line N]
  code-config-check
  doctor`
const safeText = value => {
    const key = lib.CFG.apiKey
    let text = String(value)
    if (key) text = text.split(String(key)).join('[REDACTED]').split(redactSecret(key)).join('[REDACTED]')
    return text
}
const print = lines => console.log(safeText(lines.join('\n')))
const json = value => console.log(safeText(JSON.stringify(value, null, 2)))

try {
    const [cmd, ...rest] = process.argv.slice(2)
    const opts = parseArgs(rest)
    const text = opts.query ?? opts.texts.join(' ').trim()
    if (opts.mode && !['exact', 'semantic', 'hybrid'].includes(opts.mode)) throw new Error('mode must be exact, semantic, or hybrid')
    if (cmd === 'index') {
        print(await lib.indexCommand(opts))
    } else if (cmd === 'query' || cmd === 'search') {
        if (!text) throw new Error('query is required')
        if (cmd === 'search' && !(opts.exact || opts.mode === 'exact')) {
            const notes = []
            try {
                const idx = await lib.autoRefreshIndex(opts.project)
                if (idx.some(l => l.includes('+'))) notes.push(...idx)
                if (opts.all) {
                    const codexIdx = await lib.autoRefreshCodexIndex()
                    if (codexIdx.some(l => l.includes('+'))) notes.push(...codexIdx)
                }
            } catch (e) {
                notes.push(`(index auto-refresh failed, using existing index: ${String(e.message).slice(0, 120)})`)
            }
            if (notes.length) print(notes)
        }
        print(await lib.queryLines(text, {
            ...opts, exact: opts.exact || opts.mode === 'exact', semantic: opts.semantic || opts.mode === 'semantic',
            rerank: cmd === 'search' ? opts.rerank !== false : opts.rerank,
        }))
    } else if (cmd === 'list') {
        print(lib.listLines(opts))
    } else if (cmd === 'scan') {
        print(lib.scanLines(opts))
    } else if (cmd === 'expand') {
        print(lib.expandLines({ ...opts, sessionId: opts.sessionId || opts.id || opts.texts[0] }))
    } else if (cmd === 'status') {
        print(lib.statusLines())
    } else if (cmd === 'projects') {
        print(lib.projectsLines(opts))
    } else if (cmd === 'code-index') {
        const root = resolveProjectRoot(opts.root)
        const res = await buildCodeIndex(root, { force: opts.force, noEmbed: opts.noEmbed, dry: opts.dry })
        json({ root_path: root, ...res })
    } else if (cmd === 'code-query') {
        if (!text) throw new Error('query is required')
        const root = resolveProjectRoot(opts.root)
        json(await codeQuery({ query: text, mode: opts.mode, root_path: root, limit: opts.limit || opts.top || 10 }))
    } else if (cmd === 'code-status') {
        const root = resolveProjectRoot(opts.root)
        const cfg = loadSharedConfig()
        json({ root_path: root, config: configSummaryForDisplay(cfg), embeddingAvailable: cfg.provider === 'local' || !!(cfg.baseUrl && cfg.apiKey), index: codeStatus(root) })
    } else if (cmd === 'code-read') {
        json(readCodeSlice({ path: opts.path || opts.texts[0], root_path: opts.root, start_line: opts.startLine, end_line: opts.endLine }))
    } else if (cmd === 'code-config-check') {
        const cfg = loadSharedConfig()
        const checks = [
            checkNodeVersion(), checkConfigFile(), checkApiKeyPresence(cfg),
            await checkEmbeddingConnectivity(cfg, lib.embedBatch),
            checkDirWritable('代码索引目录', CODE_INDEX_ROOT),
            checkCliPresence('Claude CLI', 'claude'), checkCliPresence('Codex CLI', 'codex'),
        ]
        json({ config: configSummaryForDisplay(cfg), ...summarize(checks) })
    } else if (cmd === 'doctor') {
        const { run } = await import('./doctor.mjs')
        await run()
    } else if (!cmd || cmd === '--help' || cmd === 'help') {
        console.log(usage)
    } else {
        throw new Error(`unknown command: ${cmd}\n${usage}`)
    }
} catch (e) {
    console.error('出错: ' + safeText(e.message))
    process.exitCode = 1
}
