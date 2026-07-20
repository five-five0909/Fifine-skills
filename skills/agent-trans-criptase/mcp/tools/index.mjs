import { buildCodeIndex } from '../../lib/code-search/indexer.mjs'
import { resolveProjectRoot } from '../../lib/shared/paths.mjs'

export const definition = {
    name: 'trans_code_index',
    description: 'Build or incrementally update the code/document search index for an arbitrary local project directory. Incremental by default (only changed files re-embedded, tracked by mtime); force=full rebuild (after changing embedding model or index corruption); noEmbed=keyword-only index (zero API cost, exact queries only); dry=estimate new chunk count without calling the embedding API. Respects .transignore/.gitignore and a built-in baseline ignore list (.git, node_modules, secrets, binaries, oversized files).',
    inputSchema: {
        type: 'object',
        properties: {
            root_path: { type: 'string', description: 'Directory to index; default: current working directory' },
            force: { type: 'boolean' },
            noEmbed: { type: 'boolean' },
            dry: { type: 'boolean' },
        },
    },
}

export async function call(a) {
    const root = resolveProjectRoot(a.root_path)
    const res = await buildCodeIndex(root, { force: a.force, noEmbed: a.noEmbed, dry: a.dry })
    return JSON.stringify({ root_path: root, ...res }, null, 2)
}
