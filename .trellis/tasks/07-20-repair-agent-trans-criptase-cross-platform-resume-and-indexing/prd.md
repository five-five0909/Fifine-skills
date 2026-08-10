# Repair agent-trans-criptase cross-platform resume and indexing

## Goal

Make the `agent-trans-criptase` skill usable from Claude Code, Codex, and generic
agent installations without platform-specific dead-end commands or stale retrieval
results.

## Confirmed Facts

- `SKILL.md` and the READMEs advertise `scan-transcript.ps1`, but that file is not
  distributed. The actual transcript implementation is in `scripts/lib.mjs` and
  `mcp/server.mjs`.
- `lib/code-search/indexer.mjs` appends chunks for changed files and never removes
  chunks for changed or deleted files. A local reproduction returned both replaced
  and deleted source content after an incremental index.
- `trans_list` and an ID-less `trans_scan` call Claude-only `sessionFiles()`.
  In a Codex-only transcript fixture both fail before considering rollout JSONL.
- Bootstrap creates a Codex link in `~/.agents/skills/trans`, while this repository
  distributes Codex skills to `.codex/skills/{name}`. Documentation also hard-codes
  `~/.claude/skills/trans` although runtime paths derive from `INSTALL_ROOT`.

## Requirements

1. Add a cross-platform Python transcript CLI with the documented scan/list,
   project, path, tail, message-limit, and detail-line inputs. It may delegate to
   the existing Node implementation so parsing stays authoritative in one place.
2. Replace all user-facing references to the missing PowerShell script with the
   Python CLI and installed-skill-relative paths.
3. Make changed/deleted code files disappear from the index immediately after an
   incremental indexing call. Prefer a complete rebuild whenever stale entries are
   detected over returning an incorrect hit.
4. Make `trans_list` and ID-less `trans_scan` fall back to Codex rollouts when no
   Claude transcript exists, and select the second newest Codex session when one is
   available.
5. Align bootstrap and docs with `.codex/skills/trans` and runtime-derived
   installation/config/index paths.
6. Add regression coverage for Python CLI delegation, stale code-index prevention,
   and Codex-only no-ID transcript discovery.

## Acceptance Criteria

- `python scripts/scan_transcript.py --help` works on Python 3 without PowerShell.
- The CLI can list and scan a fixture transcript through the existing Node logic.
- After changing or deleting an indexed source file, an exact query cannot return
  its prior content or deleted path.
- In a Codex-only fixture, `trans_list` returns a rollout and `trans_scan({})`
  returns a transcript brief.
- `npm test` and `npm run smoke` in `skills/agent-trans-criptase` pass.
- No published instructions require `scan-transcript.ps1`, `.agents` for Codex, or
  a fixed Claude install path.

## Out of Scope

- Replacing the Node MCP server or transcript parser.
- Migrating existing persisted indexes automatically; the next indexing operation
  may rebuild a stale index.
