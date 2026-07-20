#!/usr/bin/env node
// 旧配置迁移：embed-config.json（旧 schema）→ config/config.json（新共享 schema，见 Goal.md 13 节字段映射）。
// 不移动仓库位置——install.ps1/.sh 已改为直接对当前仓库位置创建 Skill 链接，无需强制搬迁到
// ~/.agent-tools 共享目录；本脚本只做"配置格式"迁移，且需交互确认才写入，不静默覆盖。
// 用法：node scripts/migrate-config.mjs [--dry-run] [--yes]
import fs from 'node:fs'
import path from 'node:path'
import readline from 'node:readline/promises'
import { INSTALL_ROOT } from '../lib/shared/paths.mjs'
import { LEGACY_CONFIG_PATH, SHARED_CONFIG_PATH } from '../lib/shared/config.mjs'

const argv = process.argv.slice(2)
const dryRun = argv.includes('--dry-run')
const yes = argv.includes('--yes')

function toSharedSchema(legacy) {
    return {
        version: 1,
        embedding: {
            provider: legacy.provider || 'api',
            baseUrl: legacy.baseUrl || '',
            apiKeyEnv: 'TRANS_EMBED_API_KEY',
            model: legacy.model || 'BAAI/bge-m3',
            rerankModel: legacy.rerankModel || '',
            dimensions: null,
            batchSize: legacy.batchSize || 32,
            maxChars: legacy.maxChars || 800,
            stride: legacy.stride || 720,
            local: { enabled: legacy.provider === 'local', dtype: legacy.localDtype || 'q8', modelPath: legacy.localEmbedder || 'embedder/embedder.mjs' },
        },
        transcript: { autoRefresh: legacy.autoRefresh !== false, autoRefreshMaxChunks: legacy.autoRefreshMaxChunks || 300 },
        codeSearch: {
            enabled: true, defaultMode: 'hybrid', indexPath: './data/code-index', maxFileSizeBytes: 2097152,
            ignore: { useGitignore: true, extra: [] }, security: { allowedRoots: [] },
        },
        clients: { claude: { installed: null }, codex: { installed: null } },
    }
}

async function main() {
    console.log(`安装根目录: ${INSTALL_ROOT}`)
    if (fs.existsSync(SHARED_CONFIG_PATH)) {
        console.log(`已存在新版配置 ${SHARED_CONFIG_PATH}，无需迁移。`)
        return
    }
    if (!fs.existsSync(LEGACY_CONFIG_PATH)) {
        console.log(`未找到旧配置 ${LEGACY_CONFIG_PATH}，也无新配置——首次使用请跑 node scripts/write-config.mjs`)
        return
    }

    const legacy = JSON.parse(fs.readFileSync(LEGACY_CONFIG_PATH, 'utf8'))
    const next = toSharedSchema(legacy)
    if (legacy.apiKey) {
        console.log('⚠ 检测到旧配置里有明文 apiKey：新 schema 不再把 key 写进文件，改用环境变量 TRANS_EMBED_API_KEY。')
        console.log(`  迁移后请自行设置: $env:TRANS_EMBED_API_KEY = "${legacy.apiKey.slice(0, 4)}...${legacy.apiKey.slice(-4)}"（此处仅作提示，不会自动写入任何文件）`)
    }

    console.log('\n将写入:')
    console.log(`  ${SHARED_CONFIG_PATH}`)
    console.log(JSON.stringify(next, null, 2))

    if (dryRun) { console.log('\n--dry-run：未实际写入'); return }

    if (!yes) {
        const rl = readline.createInterface({ input: process.stdin, output: process.stdout })
        const ans = (await rl.question('\n确认写入？输入 yes 继续: ')).trim()
        rl.close()
        if (ans !== 'yes') { console.log('已取消，未修改任何文件'); return }
    }

    fs.mkdirSync(path.dirname(SHARED_CONFIG_PATH), { recursive: true })
    fs.writeFileSync(SHARED_CONFIG_PATH, JSON.stringify(next, null, 4) + '\n')
    console.log(`✓ 已写入 ${SHARED_CONFIG_PATH}`)
    console.log(`  旧文件 ${LEGACY_CONFIG_PATH} 保留未删除（仍会作为回退兼容读取，可自行清理）`)
}

main().catch((e) => { console.error('迁移失败:', e.message); process.exit(1) })
