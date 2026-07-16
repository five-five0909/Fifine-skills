import { readCodeSlice } from '../../lib/code-search/reader.mjs'

export const definition = {
    name: 'trans_code_read',
    description: 'Read a line range from a file discovered via trans_code_query. Path is validated against root_path/allowedRoots to prevent traversal or symlink escape; reads outside the configured boundary are rejected.',
    inputSchema: {
        type: 'object',
        properties: {
            path: { type: 'string', description: 'File path (relative to root_path, or absolute if within allowedRoots)' },
            root_path: { type: 'string', description: 'Project root the path is relative to' },
            start_line: { type: 'number' },
            end_line: { type: 'number' },
        },
        required: ['path'],
    },
}

export function call(a) {
    return JSON.stringify(readCodeSlice(a), null, 2)
}
