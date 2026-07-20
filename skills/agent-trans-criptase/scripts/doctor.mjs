#!/usr/bin/env node
// trans 统一诊断：Node/配置/embedding 连通性/转录索引/代码索引/Skill 链接/MCP 注册/锁文件/目录权限。
// 用法：node scripts/doctor.mjs   （或 node scripts/semantic.mjs doctor）
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { pathToFileURL } from 'node:url'
import { INSTALL_ROOT } from '../lib/shared/paths.mjs'
import { loadSharedConfig } from '../lib/shared/config.mjs'
import {
    checkNodeVersion, checkConfigFile, checkApiKeyPresence, checkEmbeddingConnectivity,
    checkDirWritable, checkCliPresence, checkLockLeftovers, summarize, configSummaryForDisplay,
} from '../lib/shared/diagnostics.mjs'
import { embedBatch, INDEX_ROOT, statusLines } from './lib.mjs'
import { CODE_INDEX_ROOT } from '../lib/code-search/indexer.mjs'

function skillLinkTarget(p) {
    try {
        const st = fs.lstatSync(p)
        if (st.isSymbolicLink() || st.isDirectory() && st.isSymbolicLink) {
            // Windows Junction 也会报 isSymbolicLink() = false，需要用 readlink 兜底
        }
        try { return fs.readlinkSync(p) } catch { return st.isDirectory() ? '(普通目录，非链接)' : null }
    } catch {
        return null
    }
}

function checkSkillLink(label, linkPath) {
    if (!fs.existsSync(linkPath)) return { name: label, status: 'WARN', detail: `未安装: ${linkPath}` }
    const target = skillLinkTarget(linkPath)
    if (!target) return { name: label, status: 'WARN', detail: `存在但无法读取链接目标: ${linkPath}` }
    if (target === '(普通目录，非链接)') return { name: label, status: 'WARN', detail: `${linkPath} 是普通目录而非共享链接（可能是旧版直接安装）` }
    return { name: label, status: 'PASS', detail: `${linkPath} → ${target}` }
}

function checkMcpRegistered(label, cmd, listArgs) {
    const attempts = process.platform === 'win32' ? [{ shell: false }, { shell: true }] : [{ shell: false }]
    for (const opt of attempts) {
        try {
            const out = execFileSync(cmd, listArgs, { stdio: 'pipe', ...opt }).toString()
            if (/\btrans\b/.test(out)) return { name: label, status: 'PASS', detail: '已注册 trans' }
            return { name: label, status: 'WARN', detail: `${cmd} 可用但未找到 trans 注册` }
        } catch { /* 尝试下一种调用方式 */ }
    }
    return { name: label, status: 'WARN', detail: `${cmd} CLI 不可用，跳过` }
}

// Codex 的 npm 全局 shim（codex.cmd/codex.ps1）在被 execFileSync 以非交互子进程方式调用时，
// 解析出的 mcp list 输出与交互式终端不一致（本机实测复现，疑似 shim 自身的环境解析差异，非本项目问题）。
// config.toml 是唯一真相源，直接读文件比解析 CLI stdout 更可靠，两条路径都试一遍，任一命中即算通过。
function checkCodexMcpRegistered() {
    const cliResult = checkMcpRegistered('Codex MCP 注册', 'codex', ['mcp', 'list'])
    if (cliResult.status === 'PASS') return cliResult
    const configPath = path.join(os.homedir(), '.codex', 'config.toml')
    if (!fs.existsSync(configPath)) return cliResult
    const toml = fs.readFileSync(configPath, 'utf8')
    if (/\[mcp_servers\.trans\]/.test(toml)) {
        return { name: 'Codex MCP 注册', status: 'PASS', detail: `已注册 trans（从 ${configPath} 直接确认，CLI 子进程调用与交互终端结果不一致，已知环境差异见 doctor.mjs 注释）` }
    }
    return cliResult
}

function checkTranscriptIndex() {
    const lines = statusLines()
    if (lines[0] === '尚无任何索引') return { name: '转录索引', status: 'WARN', detail: '尚无任何索引（首次使用前需 trans_index 或等待 SessionEnd 后台建索引）' }
    return { name: '转录索引', status: 'PASS', detail: `${lines.length / 2} 个项目已建索引` }
}

export async function run() {
    const cfg = loadSharedConfig()
    const home = os.homedir()
    const claudeSkill = path.join(home, '.claude', 'skills', 'trans')
    const codexSkill = path.join(home, '.agents', 'skills', 'trans')

    const checks = [
        checkNodeVersion(),
        checkConfigFile(),
        checkApiKeyPresence(cfg),
        await checkEmbeddingConnectivity(cfg, embedBatch),
        checkTranscriptIndex(),
        checkDirWritable('转录索引目录', INDEX_ROOT),
        checkDirWritable('代码索引目录', CODE_INDEX_ROOT),
        checkSkillLink('Claude Skill 链接', claudeSkill),
        checkSkillLink('Codex Skill 链接', codexSkill),
        checkMcpRegistered('Claude MCP 注册', 'claude', ['mcp', 'list']),
        checkCodexMcpRegistered(),
        checkCliPresence('Claude CLI', 'claude'),
        checkCliPresence('Codex CLI', 'codex'),
        checkLockLeftovers('锁文件残留', collectLockFiles()),
    ]

    const result = summarize(checks)
    printReport(cfg, result)
    return result
}

function collectLockFiles() {
    const out = []
    for (const root of [INDEX_ROOT, CODE_INDEX_ROOT]) {
        if (!fs.existsSync(root)) continue
        for (const enc of fs.readdirSync(root)) {
            const lockPath = path.join(root, enc, 'state.json.lock')
            if (fs.existsSync(lockPath)) out.push(lockPath)
        }
    }
    return out
}

function printReport(cfg, result) {
    console.log(`\ntrans doctor — 安装根目录: ${INSTALL_ROOT}\n`)
    console.log('配置摘要:', JSON.stringify(configSummaryForDisplay(cfg)))
    console.log('')
    for (const c of result.checks) {
        const icon = { PASS: '✓', WARN: '⚠', FAIL: '✗', SKIP: '○' }[c.status] || '?'
        console.log(`  ${icon} [${c.status}] ${c.name}${c.detail ? '  — ' + c.detail : ''}`)
    }
    console.log(`\n总体状态: ${result.overall}（FAIL ${result.failCount}，WARN ${result.warnCount}）`)
    if (result.overall !== 'PASS') {
        console.log('\n常见修复:')
        console.log('  未配置 embedding → node scripts/write-config.mjs  （或改用纯关键词: index --no-embed / query --exact）')
        console.log('  Skill 链接缺失   → 重跑 install.ps1 / install.sh')
        console.log('  MCP 未注册       → claude mcp add --scope user trans -- node mcp/server.mjs')
        console.log('                     codex mcp add trans -- node mcp/server.mjs')
    }
    console.log('')
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    run().then((r) => process.exit(r.overall === 'FAIL' ? 1 : 0))
}
