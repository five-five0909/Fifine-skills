// 共享诊断检查函数：scripts/doctor.mjs（CLI）与 trans_code_config_check（MCP 工具）共用同一批实现，
// 避免两处分别写一遍连通性探测/权限检查逻辑而彼此漂移。输出统一 PASS/WARN/FAIL/SKIP。
import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { redactConfigForDisplay } from './redact.mjs'
import { SHARED_CONFIG_PATH, LEGACY_CONFIG_PATH } from './config.mjs'

export const mkCheck = (name, status, detail = '') => ({ name, status, detail })

export function checkNodeVersion() {
    const [major] = process.versions.node.split('.').map(Number)
    if (major >= 18) return mkCheck('Node 版本', 'PASS', `v${process.versions.node}`)
    return mkCheck('Node 版本', 'FAIL', `v${process.versions.node}（需要 >=18）`)
}

export function checkConfigFile() {
    if (fs.existsSync(SHARED_CONFIG_PATH)) return mkCheck('配置文件', 'PASS', `共享配置: ${SHARED_CONFIG_PATH}`)
    if (fs.existsSync(LEGACY_CONFIG_PATH)) return mkCheck('配置文件', 'WARN', `旧版配置: ${LEGACY_CONFIG_PATH}（建议 node scripts/migrate-config.mjs 迁移）`)
    return mkCheck('配置文件', 'WARN', '未找到配置文件，将使用默认值（仅 exact 检索可用）')
}

export function checkApiKeyPresence(cfg) {
    if (cfg.provider === 'local') return mkCheck('API Key', 'SKIP', 'provider=local，无需 API Key')
    if (cfg.apiKey) return mkCheck('API Key', 'PASS', '已设置（不回显）')
    return mkCheck('API Key', 'WARN', '未设置：semantic/hybrid 检索不可用，exact 仍可用')
}

export async function checkEmbeddingConnectivity(cfg, embedBatchFn) {
    if (cfg.provider === 'local') {
        return mkCheck('Embedding 连通性', 'SKIP', 'provider=local，跳过远程探测')
    }
    if (!cfg.baseUrl || !cfg.apiKey) {
        return mkCheck('Embedding 连通性', 'SKIP', '未配置 baseUrl/apiKey，跳过探测')
    }
    try {
        const vecs = await embedBatchFn(['trans 连通性自检'], true)
        const dims = vecs?.[0]?.length
        if (!dims) return mkCheck('Embedding 连通性', 'FAIL', '响应无有效向量')
        return mkCheck('Embedding 连通性', 'PASS', `可用（${dims} 维，model=${cfg.model}）`)
    } catch (e) {
        return mkCheck('Embedding 连通性', 'FAIL', String(e.message).slice(0, 200))
    }
}

export function checkDirWritable(label, dir) {
    try {
        fs.mkdirSync(dir, { recursive: true })
        const probe = path.join(dir, `.write-test-${process.pid}`)
        fs.writeFileSync(probe, 'x')
        fs.rmSync(probe, { force: true })
        return mkCheck(label, 'PASS', dir)
    } catch (e) {
        return mkCheck(label, 'FAIL', `${dir}: ${e.message}`)
    }
}

export function checkCliPresence(label, cmd) {
    // Windows 上很多 CLI 是 .cmd shim，execFileSync 直接调用可能找不到；shell 只在直接调用失败时才启用，
    // 且 cmd/参数均为硬编码字面量（不含用户输入），不构成命令注入面。
    try {
        const out = execFileSync(cmd, ['--version'], { stdio: 'pipe' }).toString().trim()
        return mkCheck(label, 'PASS', out.split('\n')[0])
    } catch (e1) {
        if (process.platform !== 'win32') return mkCheck(label, 'WARN', `未找到 ${cmd} CLI（跳过该客户端的相关检查）`)
        try {
            const out = execFileSync(cmd, ['--version'], { stdio: 'pipe', shell: true }).toString().trim()
            return mkCheck(label, 'PASS', out.split('\n')[0])
        } catch {
            return mkCheck(label, 'WARN', `未找到 ${cmd} CLI（跳过该客户端的相关检查）`)
        }
    }
}

export function checkLockLeftovers(label, lockPaths) {
    const stale = lockPaths.filter((p) => fs.existsSync(p))
    if (!stale.length) return mkCheck(label, 'PASS', '无残留锁文件')
    return mkCheck(label, 'WARN', `发现 ${stale.length} 个锁文件（若确认无进程占用可手动删除）: ${stale.slice(0, 5).join(', ')}`)
}

export function summarize(checks) {
    const fail = checks.filter((c) => c.status === 'FAIL').length
    const warn = checks.filter((c) => c.status === 'WARN').length
    return { overall: fail ? 'FAIL' : warn ? 'WARN' : 'PASS', failCount: fail, warnCount: warn, checks }
}

export function configSummaryForDisplay(cfg) {
    return redactConfigForDisplay({ provider: cfg.provider, baseUrl: cfg.baseUrl, model: cfg.model, rerankModel: cfg.rerankModel, apiKey: cfg.apiKey })
}
