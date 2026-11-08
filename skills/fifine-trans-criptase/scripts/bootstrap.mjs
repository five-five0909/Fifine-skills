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
    } catch {
        return { status: 'FAIL', detail: 'local model probe failed; check model configuration' }
    }
}

export async function bootstrap({ project = resolveProjectRoot(), startIndex = true, clients = ['claude', 'codex', 'agents'] } = {}) {
    ensureConfigTemplate()
    const home = os.homedir()
    const checks = {}
    if (clients.includes('claude')) {
        checks.claudeSkill = ensureSkillLink(path.join(home, '.claude', 'skills', 'trans'))
    }
    if (clients.includes('codex')) {
        checks.codexSkill = ensureSkillLink(path.join(home, '.codex', 'skills', 'trans'))
    }
    if (clients.includes('agents')) {
        // 通用 agent 目录供其他客户端发现 Skill。
        checks.agentsSkill = ensureSkillLink(path.join(home, '.agents', 'skills', 'trans'))
    }
    const embeddingResult = await checkEmbedding(loadSharedConfig())
    const embedding = embeddingResult.status === 'FAIL'
        ? { ...embeddingResult, detail: 'embedding probe failed; check configuration and service status' }
        : embeddingResult
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
        process.exit(0)
    })
}
