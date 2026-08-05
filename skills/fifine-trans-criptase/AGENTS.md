<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

If you're using Codex or another agent-capable tool, additional project-scoped helpers may live in:
- `.agents/skills/` — reusable Trellis skills
- `.codex/agents/` — optional custom subagents

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

<!-- TRELLIS:END -->

# trans-criptase project notes

Full plan and status: `Goal.md` (target architecture, task backlog, migration plan) and `.dev-done-flow/` (audit → requirements → architecture → implementation plan → progress).

## Architecture

Two subsystems sharing one MCP server (`mcp/server.mjs`), one config layer (`lib/shared/`), one lock/atomic-write layer:

- **Transcript resume + search** (unchanged product, cross-client-ized): `scripts/lib.mjs` (core logic) + `scripts/semantic.mjs` (CLI) + 6 MCP tools (`trans_search`/`trans_scan`/`trans_list`/`trans_projects`/`trans_expand`/`trans_index`). Indexes `~/.claude/projects/*.jsonl`.
- **Code/document search** (new): `lib/code-search/*` + `mcp/tools/*` + 5 MCP tools (`trans_code_query`/`trans_code_index`/`trans_code_status`/`trans_code_read`/`trans_code_config_check`). Indexes arbitrary `root_path` directories, separate namespace under `data/code-index/`.
- **Shared**: `lib/shared/{paths,config,locking,redact,diagnostics}.mjs` — path resolution, config merging (new `config/config.json` schema with legacy `embed-config.json` fallback), file locking + atomic writes, secret redaction, doctor-style checks.

Both Claude Code and Codex CLI point at the same install via a Skill Junction/symlink and register the same `mcp/server.mjs` independently (`claude mcp add` / `codex mcp add`).

## Test commands

```
npm test                      # unit + integration (node:test, zero deps, sandboxed — safe to run anytime)
npm run smoke                 # end-to-end transcript pipeline smoke test (also sandboxed)
node scripts/doctor.mjs       # live environment diagnostic (Node/config/embedding connectivity/links/MCP registration)
```

## Constraints (do not violate without discussion)

- **Backward compatibility is non-negotiable** for the 6 transcript MCP tools and the `scripts/semantic.mjs` CLI (`index`/`query --exact|--semantic`/`status`/`projects`) — their behavior must stay identical; `scripts/mcp-server.mjs` is kept as a forwarding shim to `mcp/server.mjs`, do not delete it without a major-version note.
- New code-search tools are namespaced `trans_code_*` — never reuse `trans_query`/`trans_index` for them (name collision with the transcript tools).
- Never write API keys into any file (config, log, test fixture, commit). Real keys only via env vars (`TRANS_EMBED_API_KEY`, or `apiKeyEnv` target in the shared config).
- `root_path`/`path` arguments in the code-search tools must go through `lib/code-search/security.mjs` (`assertPathAllowed`/`assertNoTraversal`) — no new read/write path may skip this.
- Don't relocate the user's repo automatically (no forced move to a canonical `~/.agent-tools/trans`) — installers link Skill directories to wherever the repo currently lives; `scripts/migrate-config.mjs` only migrates the *config format*, and asks for confirmation before writing.
- Installers (`install.ps1`/`.sh`, `uninstall.ps1`/`.sh`) must stay idempotent and must never abort entirely just because one client's CLI (`claude`/`codex`) is missing — skip that client, continue the other, print a manual follow-up command.
