import { codeQuery } from '../../lib/code-search/query.mjs'

export const definition = {
    name: 'trans_code_query',
    description: 'Search indexed local code/documents in an arbitrary project directory using exact (keyword/substring, no API needed), semantic (vector, conceptual), or hybrid (RRF fusion, default) retrieval. Use exact for known identifiers/error strings/file names; semantic for fuzzy natural-language intent; hybrid when both are present or exact recall is too narrow. Call trans_code_index first if the root_path has never been indexed. Automatically degrades hybrid/semantic to exact when embedding is unavailable — check the `degraded` field in the response.',
    inputSchema: {
        type: 'object',
        properties: {
            query: { type: 'string', description: 'Search text (natural language or keywords)' },
            mode: { type: 'string', enum: ['exact', 'semantic', 'hybrid'], description: 'Default: hybrid' },
            root_path: { type: 'string', description: 'Target project directory (must already be indexed via trans_code_index)' },
            limit: { type: 'number', description: 'Max results, default 10' },
        },
        required: ['query', 'root_path'],
    },
}

export async function call(a) {
    const result = await codeQuery({ query: a.query, mode: a.mode, root_path: a.root_path, limit: a.limit || 10 })
    return JSON.stringify(result, null, 2)
}
