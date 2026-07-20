// 共享配置层：合并新 config/config.json（跨客户端共享 schema）与旧 embed-config.json（向后兼容）。
// lib.mjs（转录续接）与 lib/code-search/*（代码检索）都从这里取配置，不再各自读文件。
//
// 优先级：新 config/config.json 存在 → 用它（并把 embedding.* 映射成扁平字段，保持与旧 CFG 形状兼容）；
//        否则回退旧 embed-config.json（行为与改造前逐字段一致，见 Goal.md 13.2 字段映射表）。
// 环境变量始终最高优先级（沿用旧行为，不新增环境变量语义）。
import fs from 'node:fs'
import path from 'node:path'
import { INSTALL_ROOT } from './paths.mjs'

export const LEGACY_CONFIG_PATH = path.join(INSTALL_ROOT, 'embed-config.json')
export const SHARED_CONFIG_PATH = path.join(INSTALL_ROOT, 'config', 'config.json')

function readJson(p) {
    if (!fs.existsSync(p)) return null
    try { return JSON.parse(fs.readFileSync(p, 'utf8')) } catch { return null }
}

const DEFAULT_CODE_SEARCH = {
    enabled: true,
    defaultMode: 'hybrid',
    indexPath: './data/code-index',
    maxFileSizeBytes: 2097152,
    ignore: { useGitignore: true, extra: [] },
    security: { allowedRoots: [] },
}

function fromSharedSchema(raw) {
    const embedding = raw.embedding || {}
    const transcript = raw.transcript || {}
    const codeSearch = { ...DEFAULT_CODE_SEARCH, ...(raw.codeSearch || {}) }
    codeSearch.ignore = { ...DEFAULT_CODE_SEARCH.ignore, ...(raw.codeSearch?.ignore || {}) }
    codeSearch.security = { ...DEFAULT_CODE_SEARCH.security, ...(raw.codeSearch?.security || {}) }

    const apiKeyEnv = embedding.apiKeyEnv || 'TRANS_EMBED_API_KEY'
    return {
        provider: embedding.provider || 'api',
        localEmbedder: embedding.local?.modelPath || '',
        localDtype: embedding.local?.dtype || 'fp32',
        baseUrl: embedding.baseUrl || '',
        apiKey: process.env[apiKeyEnv] || process.env.MISTRAL_API_KEY || '',
        model: embedding.model || 'BAAI/bge-m3',
        rerankModel: embedding.rerankModel || '',
        batchSize: embedding.batchSize || 32,
        maxChars: embedding.maxChars || 800,
        stride: embedding.stride || 720,
        autoRefresh: transcript.autoRefresh !== false,
        autoRefreshMaxChunks: transcript.autoRefreshMaxChunks || 300,
        codeSearch,
        _configPath: SHARED_CONFIG_PATH,
        _source: 'shared',
    }
}

function fromLegacySchema(raw) {
    const cfg = { ...(raw || {}) }
    cfg.provider = cfg.provider || 'api'
    cfg.localEmbedder = cfg.localEmbedder || ''
    cfg.localDtype = cfg.localDtype || 'fp32'
    cfg.baseUrl = cfg.baseUrl || ''
    cfg.apiKey = cfg.apiKey || ''
    cfg.model = cfg.model || 'BAAI/bge-m3'
    cfg.rerankModel = cfg.rerankModel || ''
    cfg.batchSize = cfg.batchSize || 32
    cfg.maxChars = cfg.maxChars || 800
    cfg.stride = cfg.stride || 720
    cfg.autoRefresh = cfg.autoRefresh !== false
    cfg.autoRefreshMaxChunks = cfg.autoRefreshMaxChunks || 300
    cfg.codeSearch = { ...DEFAULT_CODE_SEARCH }
    cfg._configPath = fs.existsSync(LEGACY_CONFIG_PATH) ? LEGACY_CONFIG_PATH : null
    cfg._source = fs.existsSync(LEGACY_CONFIG_PATH) ? 'legacy' : 'none'
    return cfg
}

/** 合并读取共享/旧配置，环境变量覆盖同旧版语义不变。 */
export function loadSharedConfig() {
    const sharedRaw = readJson(SHARED_CONFIG_PATH)
    const cfg = sharedRaw ? fromSharedSchema(sharedRaw) : fromLegacySchema(readJson(LEGACY_CONFIG_PATH))

    // 环境变量最高优先级（与旧 lib.mjs.loadConfig() 行为一致，未新增语义）
    cfg.provider = process.env.TRANS_EMBED_PROVIDER || cfg.provider
    cfg.localEmbedder = process.env.TRANS_LOCAL_EMBEDDER || cfg.localEmbedder
    cfg.baseUrl = process.env.TRANS_EMBED_BASE_URL || cfg.baseUrl
    cfg.apiKey = process.env.TRANS_EMBED_API_KEY || cfg.apiKey
    cfg.model = process.env.TRANS_EMBED_MODEL || cfg.model
    cfg.rerankModel = process.env.TRANS_RERANK_MODEL || cfg.rerankModel
    return cfg
}
