# Migration

## From the old single-client layout

Older installs of this repo were Claude-Code-only: cloned directly into `~/.claude/skills/trans`, config at `<that dir>/embed-config.json`, MCP server at `scripts/mcp-server.mjs`. None of that stops working — this migration is opt-in, not required.

### What actually changed vs. what's still there

| | Before | Now |
|---|---|---|
| MCP server entry point | `scripts/mcp-server.mjs` | `mcp/server.mjs` (the old path still works — it's now a one-line forwarding shim, kept so nothing with the old path hardcoded breaks) |
| Config file | `embed-config.json` only | `config/config.json` (new schema) preferred, `embed-config.json` still read as a fallback — no forced conversion |
| MCP tools | 6 (transcript only) | 11 (6 transcript, unchanged behavior + 5 new `trans_code_*`) |
| Install target | assumed `~/.claude/skills/trans` | works from wherever you cloned the repo; Claude/Codex Skill directories are Junctions/symlinks pointing at that location |
| Codex CLI | not supported | supported via the same `mcp/server.mjs`, same config, same indexes |

### Should I do anything?

**No forced relocation.** Unlike an earlier draft of this plan, the installer does **not** automatically move your repository to a canonical shared location (e.g. `~/.agent-tools/trans`) — that would be a hard-to-reverse operation on your git working tree performed without asking, which this project's own operating principles rule out. `install.ps1`/`.sh` link the Claude/Codex Skill directories to **wherever your repo currently is**.

If you want the new shared config format (mainly useful if you're about to add Codex CLI support and want one config for both):

```powershell
node scripts/migrate-config.mjs --dry-run    # preview what would be written, changes nothing
node scripts/migrate-config.mjs              # writes config/config.json, asks for confirmation, does NOT delete embed-config.json
```

If you skip this, everything keeps working off `embed-config.json` — `lib/shared/config.mjs` reads it as a fallback whenever `config/config.json` doesn't exist.

### Adding Codex CLI to an existing Claude-only install

```powershell
.\install.ps1 -Clients codex
```
This only touches the Codex side (new `~/.agents/skills/trans` link + `codex mcp add`); your existing Claude Code setup is untouched.

### Verify after migrating

```powershell
node scripts/doctor.mjs
```

### Rolling back

Nothing destructive happens by default. If you ran `migrate-config.mjs` and want to go back to the old config exclusively, just delete `config/config.json` — `embed-config.json` is untouched and becomes authoritative again.
