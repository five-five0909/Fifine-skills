// 代码检索编排：模式选择 + 降级链 + 输出格式化。MCP 工具层（mcp/tools/query.mjs）与 CLI（scripts/semantic.mjs code-query）共用。
import { loadSharedConfig } from '../shared/config.mjs'
import { loadCodeIndex } from './indexer.mjs'
import { exactSearch } from './exact-search.mjs'
import { semanticSearch } from './semantic-search.mjs'
import { hybridSearch } from './hybrid-search.mjs'

function toResult(h, matchType) {
    const m = h.ix.metas[h.i]
    const snippet = m.text.length > 400 ? m.text.slice(0, 400) + '…' : m.text
    return { path: m.path, start_line: m.start_line, end_line: m.end_line, score: +h.score.toFixed(4), match_type: matchType, snippet }
}

/**
 * codeQuery({query, mode, root_path, limit}) → { mode, query, results, degraded?, notes? }
 * 降级链：hybrid/semantic 在 embedding 不可用时自动退到 exact，返回体标注 degraded:true + 原因。
 */
export async function codeQuery({ query, mode = 'hybrid', root_path, limit = 10 } = {}) {
    if (!query) throw new Error('query 必填')
    if (!root_path) throw new Error('root_path 必填')

    const idx = loadCodeIndex(root_path)
    if (!idx) {
        return { mode, query, results: [], error: `没有可用索引：先调 trans_code_index({root_path: "${root_path}"})` }
    }
    const indexes = [idx]

    if (mode === 'exact') {
        const ranked = exactSearch(indexes, query, limit)
        return { mode: 'exact', query, results: ranked.map((h) => toResult(h, 'exact')) }
    }

    if (mode === 'semantic') {
        const { hits, notes, failed } = await semanticSearch(indexes, query, limit)
        if (failed || !hits.length) {
            // semantic 显式请求但不可用：不静默换算法，如实报告并附带 exact 结果兜底（比空手而归更有用）
            const fallback = exactSearch(indexes, query, limit)
            return {
                mode: 'semantic', query, degraded: true,
                reason: notes.join('; ') || '无向量索引',
                results: fallback.map((h) => toResult(h, 'exact')),
            }
        }
        return { mode: 'semantic', query, results: hits.slice(0, limit).map((h) => toResult(h, 'semantic')), notes: notes.length ? notes : undefined }
    }

    // hybrid（默认）：降级链 hybrid → exact
    const { ranked, notes, degraded } = await hybridSearch(indexes, query, limit)
    const usedType = degraded ? 'exact' : 'hybrid'
    return {
        mode: 'hybrid', query,
        results: ranked.slice(0, limit).map((h) => toResult(h, usedType)),
        ...(degraded ? { degraded: true, reason: notes.join('; ') || '向量不可用，已降级纯关键词' } : {}),
    }
}

export function codeConfigDefaults() {
    return loadSharedConfig().codeSearch
}
