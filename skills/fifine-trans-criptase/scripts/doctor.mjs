#!/usr/bin/env node
// trans 统一诊断：Node/配置/embedding 连通性/转录索引/代码索引/Skill 链接/锁文件/目录权限。
// 用法：node scripts/doctor.mjs   （或 node scripts/semantic.mjs doctor）
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { INSTALL_ROOT } from '../lib/shared/paths.mjs'
import { loadSharedConfig } from '../lib/shared/config.mjs'
import {
    checkNodeVersion, checkConfigFile, checkApiKeyPresence, checkEmbeddingConnectivity,
    checkDirWritable, checkCliPresence, checkLockLeftovers, summarize,
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


function checkTranscriptIndex() {
    const lines = statusLines()
    if (lines[0] === '尚无任何索引') return { name: '转录索引', status: 'WARN', detail: '尚无任何索引（运行 node scripts/semantic.mjs index --all 或等待 SessionEnd 后台建索引）' }
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
        await checkEmbeddingConnectivity(cfg, embedBatch).then((check) => check.status === 'FAIL'
            ? { ...check, detail: '连接失败，请检查 embedding 配置及服务状态' }
            : check),
        checkTranscriptIndex(),
        checkDirWritable('转录索引目录', INDEX_ROOT),
        checkDirWritable('代码索引目录', CODE_INDEX_ROOT),
        checkSkillLink('Claude Skill 链接', claudeSkill),
        checkSkillLink('Codex Skill 链接', codexSkill),
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
    console.log('配置摘要:', JSON.stringify({ provider: cfg.provider, model: cfg.model, rerankModel: cfg.rerankModel, apiKey: cfg.apiKey ? '已设置' : '未设置' }))
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
    }
    console.log('')
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    run().then((r) => process.exit(r.overall === 'FAIL' ? 1 : 0))
}
