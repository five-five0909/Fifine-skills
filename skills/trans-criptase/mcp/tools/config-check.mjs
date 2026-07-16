import { loadSharedConfig } from '../../lib/shared/config.mjs'
import { embedBatch } from '../../scripts/lib.mjs'
import { CODE_INDEX_ROOT } from '../../lib/code-search/indexer.mjs'
import {
    checkNodeVersion, checkConfigFile, checkApiKeyPresence, checkEmbeddingConnectivity,
    checkDirWritable, checkCliPresence, summarize, configSummaryForDisplay,
} from '../../lib/shared/diagnostics.mjs'

export const definition = {
    name: 'trans_code_config_check',
    description: 'Diagnose the code-search subsystem end to end: Node version, config file, Base URL, API key presence (never echoed), embedding model, live provider connectivity probe, index/cache directory write permissions, Claude CLI / Codex CLI presence. Returns PASS/WARN/FAIL per check plus an overall verdict.',
    inputSchema: { type: 'object', properties: {} },
}

export async function call() {
    const cfg = loadSharedConfig()
    const checks = [
        checkNodeVersion(),
        checkConfigFile(),
        checkApiKeyPresence(cfg),
        await checkEmbeddingConnectivity(cfg, embedBatch),
        checkDirWritable('代码索引目录', CODE_INDEX_ROOT),
        checkCliPresence('Claude CLI', 'claude'),
        checkCliPresence('Codex CLI', 'codex'),
    ]
    return JSON.stringify({ config: configSummaryForDisplay(cfg), ...summarize(checks) }, null, 2)
}
