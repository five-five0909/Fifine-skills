import { codeStatus } from '../../lib/code-search/indexer.mjs'
import { loadSharedConfig } from '../../lib/shared/config.mjs'
import { configSummaryForDisplay } from '../../lib/shared/diagnostics.mjs'
import { resolveProjectRoot } from '../../lib/shared/paths.mjs'

export const definition = {
    name: 'trans_code_status',
    description: 'Report code-search subsystem status for a given root_path: whether config/index exist, provider type, embedding availability, index update time/file/chunk counts, cache state. Never echoes the full API key.',
    inputSchema: {
        type: 'object',
        properties: { root_path: { type: 'string', description: 'Default: current working directory' } },
    },
}

export function call(a) {
    const root = resolveProjectRoot(a.root_path)
    const cfg = loadSharedConfig()
    return JSON.stringify({
        root_path: root,
        config: configSummaryForDisplay(cfg),
        embeddingAvailable: cfg.provider === 'local' || !!(cfg.baseUrl && cfg.apiKey),
        index: codeStatus(root),
        mcpServerVersion: '1.0.0',
    }, null, 2)
}
