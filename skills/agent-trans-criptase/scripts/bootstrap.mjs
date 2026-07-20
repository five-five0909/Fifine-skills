#!/usr/bin/env node
// Idempotent first-use setup for the shared Claude Code and Codex installation.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawn, spawnSync } from 'node:child_process'
import { pathToFileURL } from 'node:url'
import { INSTALL_ROOT, resolveProjectRoot } from '../lib/shared/paths.mjs'
import { loadSharedConfig } from '../lib/shared/config.mjs'
import { checkEmbeddingConnectivity } from '../lib/shared/diagnostics.mjs'
import { embedBatch } from './lib.mjs'

const SERVER_PATH = path.join(INSTALL_ROOT, 'mcp', 'server.mjs')
const SEMANTIC_PATH = path.join(INSTALL_ROOT, 'scripts', 'semantic.mjs')
const CONFIG_WRITER = path.join(INSTALL_ROOT, 'scripts', 'write-config.mjs')

function run(command, args) {
    const result = spawnSync(command, args, {
        encoding: 'utf8',
        shell: process.platform === 'win32',
        timeout: 15_000,
    })
    return {
        ok: !result.error && result.status === 0,
        output: `${result.stdout || ''}\n${result.stderr || ''}`.trim(),
        error: result.error?.message || '',
    }
}

function linkedTo(target, source) {
    try {
        return fs.realpathSync(target) === fs.realpathSync(source)
    } catch {
        return false
    }
}

export function ensureSkillLink(target, source = INSTALL_ROOT) {
    if (fs.existsSync(target)) {
        if (linkedTo(target, source)) return { status: 'PASS', detail: 'already linked' }
        return { status: 'WARN', detail: 'existing non-matching path was left untouched' }
    }
    try {
        fs.mkdirSync(path.dirname(target), { recursive: true })
        fs.symlinkSync(source, target, process.platform === 'win32' ? 'junction' : 'dir')
        return { status: 'PASS', detail: 'linked' }
    } catch (error) {
        return { status: 'WARN', detail: `could not create link: ${error.message}` }
    }
}

export function hasTransRegistration(output) {
    return /(?:\bmcp_servers\.trans\b|\btrans\b)/i.test(output)
}

function ensureMcp(client) {
    const listed = run(client, ['mcp', 'list'])
    if (!listed.ok) {
        return { status: 'WARN', detail: `${client} CLI is unavailable: ${listed.error || listed.output}` }
    }
    if (hasTransRegistration(listed.output)) return { status: 'PASS', detail: 'already registered' }

    const args = client === 'claude'
        ? ['mcp', 'add', '--scope', 'user', 'trans', '--', 'node', SERVER_PATH]
        : ['mcp', 'add', 'trans', '--', 'node', SERVER_PATH]
    const added = run(client, args)
    if (!added.ok) return { status: 'WARN', detail: `registration failed: ${added.error || added.output}` }

    const verified = run(client, ['mcp', 'list'])
    return verified.ok && hasTransRegistration(verified.output)
        ? { status: 'PASS', detail: 'registered and verified' }
        : { status: 'WARN', detail: 'registration command succeeded but could not be verified' }
}

export function probeMcpServer(timeoutMs = 5_000) {
    return new Promise((resolve) => {
        const child = spawn(process.execPath, [SERVER_PATH], { stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true })
        let output = ''
        let settled = false
        const finish = (result) => {
            if (settled) return
            settled = true
            clearTimeout(timer)
            child.kill()
            resolve(result)
        }
        const timer = setTimeout(() => finish({ status: 'FAIL', detail: 'MCP handshake timed out' }), timeoutMs)
        child.on('error', (error) => finish({ status: 'FAIL', detail: error.message }))
        child.stdout.on('data', (chunk) => {
            output += chunk
            for (const line of output.split('\n')) {
                try {
                    const message = JSON.parse(line)
                    if (message.id === 1 && message.result?.serverInfo?.name === 'trans') {
                        finish({ status: 'PASS', detail: 'JSON-RPC initialize succeeded' })
                    }
                } catch { /* Wait for a complete JSON line. */ }
            }
        })
        child.stdin.end(`${JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'initialize', params: {} })}\n`)
    })
}

function startInitialIndex(project, embeddingReady) {
    const args = [SEMANTIC_PATH, 'index', '--project', project]
    if (!embeddingReady) args.push('--no-embed')
    try {
        const child = spawn(process.execPath, args, { detached: true, stdio: 'ignore', windowsHide: true })
        child.unref()
        return { status: 'PASS', detail: embeddingReady ? 'semantic index started in background' : 'keyword index started in background' }
    } catch (error) {
        return { status: 'WARN', detail: `could not start index: ${error.message}` }
    }
}

function ensureConfigTemplate() {
    const configPath = path.join(INSTALL_ROOT, 'embed-config.json')
    const sharedPath = path.join(INSTALL_ROOT, 'config', 'config.json')
    if (fs.existsSync(configPath) || fs.existsSync(sharedPath)) return
    run(process.execPath, [CONFIG_WRITER, '--template'])
}

async function checkEmbedding(cfg) {
    if (cfg.provider !== 'local') return checkEmbeddingConnectivity(cfg, embedBatch)
    try {
        const vectors = await embedBatch(['trans local embedding self-test'], true)
        const dimensions = vectors?.[0]?.length
        return dimensions
            ? { status: 'PASS', detail: `local model is usable (${dimensions} dimensions, model=${cfg.model})` }
            : { status: 'FAIL', detail: 'local model returned no vector' }
    } catch (error) {
        return { status: 'FAIL', detail: `local model probe failed: ${error.message}` }
    }
}

export async function bootstrap({ project = resolveProjectRoot(), startIndex = true, clients = ['claude', 'codex'] } = {}) {
    ensureConfigTemplate()
    const home = os.homedir()
    const checks = { mcpProbe: await probeMcpServer() }
    if (clients.includes('claude')) {
        checks.claudeSkill = ensureSkillLink(path.join(home, '.claude', 'skills', 'trans'))
        checks.claudeMcp = ensureMcp('claude')
    }
    if (clients.includes('codex')) {
        checks.codexSkill = ensureSkillLink(path.join(home, '.codex', 'skills', 'trans'))
        checks.codexMcp = ensureMcp('codex')
    }
    const embedding = await checkEmbedding(loadSharedConfig())
    checks.embedding = embedding
    if (startIndex) checks.index = startInitialIndex(project, embedding.status === 'PASS')
    return checks
}

function print(checks) {
    for (const [name, check] of Object.entries(checks)) {
        console.log(`${check.status} ${name}: ${check.detail}`)
    }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    const projectFlag = process.argv.indexOf('--project')
    const project = projectFlag >= 0 ? process.argv[projectFlag + 1] : undefined
    const clientsFlag = process.argv.indexOf('--clients')
    const clients = clientsFlag >= 0 ? process.argv[clientsFlag + 1].split(',').filter(Boolean) : undefined
    const noIndex = process.argv.includes('--no-index')
    bootstrap({ project, clients, startIndex: !noIndex }).then((checks) => {
        print(checks)
        process.exit(checks.mcpProbe.status === 'FAIL' ? 1 : 0)
    })
}
