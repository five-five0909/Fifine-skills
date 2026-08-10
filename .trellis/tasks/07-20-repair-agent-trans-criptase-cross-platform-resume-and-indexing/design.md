# Design

The Python CLI is a portability adapter. It resolves its own directory, invokes
`node semantic.mjs` for index/query commands, and invokes `mcp/server.mjs` over
stdio JSON-RPC for `scan` and `list`. This retains one authoritative transcript
parser and output format.

For code indexing, compare the persisted file manifest with the scanned files. If
any old file is removed or a file's mtime/size changes, reset the metadata/vector
files and rebuild the complete current scan. The scan is already bounded by ignore
rules and configured file limits, so this prioritizes correct results over a
partially incremental but invalid vector store.

Transcript discovery uses existing Claude project files first. When unavailable,
it selects Codex rollout files ordered by mtime, with the same second-newest
heuristic used for active Claude sessions.
