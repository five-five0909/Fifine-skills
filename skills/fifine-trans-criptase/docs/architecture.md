# Architecture

`SKILL.md` guides the agent; `scripts/semantic.mjs` is the local CLI. It calls transcript logic in `scripts/lib.mjs`, code search in `lib/code-search/`, and shared configuration, locking and diagnostics in `lib/shared/`. No MCP server is needed.

The target project resolves from an explicit argument, then supported project environment variables, then the current working directory. Transcript and code indexes are separate. Index writes use locks; indexes may contain plaintext and must be protected like the source data. Code reads enforce root, traversal and symlink boundaries. See `environment.md` for configuration and data paths.
