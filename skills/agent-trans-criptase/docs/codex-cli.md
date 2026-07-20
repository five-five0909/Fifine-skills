# Codex CLI setup

## Install

```powershell
.\install.ps1 -Clients codex
```
```bash
./install.sh --clients codex
```

What it does:
1. Writes/updates config via `scripts/write-config.mjs` (shared with the Claude side — one embedding provider config for both).
2. Creates a Skill Junction (Windows) or symlink (macOS/Linux) at `~/.agents/skills/trans` pointing at wherever this repo lives. This mirrors the convention Codex CLI itself uses: `~/.codex/skills/<name>` is typically a symlink into `~/.agents/skills/<name>` — confirmed by inspecting a real Codex CLI installation, not assumed.
3. Registers the MCP server: `codex mcp add trans -- node <repo>/mcp/server.mjs` (writes into `~/.codex/config.toml` under `[mcp_servers.trans]`). If the `codex` CLI isn't found, this step is skipped with the manual command printed instead.
4. Builds an initial keyword-only index unless `-SkipIndex` is passed.

Command syntax confirmed by running `codex mcp --help` / `codex mcp add --help` directly, not assumed from memory:
```
codex mcp add <NAME> [--env KEY=VALUE] -- <COMMAND>...
codex mcp list / get / remove / login / logout
```

## Skill discovery

Codex CLI looks under `~/.agents/skills/` (or wherever `~/.codex/skills/` symlinks resolve to). Once the Junction/symlink from `install.ps1 -Clients codex` is in place, `SKILL.md` and `agents/openai.yaml` are discoverable the same way as any other Codex skill on this machine.

## Known limitation: hooks don't auto-load from the skill bundle

Codex CLI's `hooks.json` schema is byte-for-byte identical to Claude Code's (`hooks.UserPromptSubmit[].hooks[].{type,command}`, confirmed by inspecting a real `.codex/hooks.json` on this machine) — but it's wired **per project** (`<project>/.codex/hooks.json` + a trust hash recorded in `~/.codex/config.toml`), not auto-loaded from a skill directory the way Claude Code's plugin mechanism does.

Practical effect: the `UserPromptSubmit` continuation-intent hint and the `SessionEnd` background incremental indexing (both in `hooks/hooks.json`) do not fire automatically on the Codex side. All 11 MCP tools work identically regardless — you (or the model) just call `trans_scan`/`trans_search`/`trans_code_query`/etc. directly instead of relying on the soft nudge. This is a documented gap, not a bug; replicating Claude's auto-load behavior would require per-project Codex hook installation, which is out of scope for this pass.

## Codex's own session transcripts

Codex CLI keeps its own session logs at `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, with a different event schema (`session_meta`, `event_msg`, `response_item.payload`) than Claude Code's `~/.claude/projects/*.jsonl` (`type: user/assistant/summary`).

`trans_scan({id})` and `trans_expand({sessionId})` support Codex rollout files directly. ID lookup checks the current Claude project, all Claude transcript dirs, and then `~/.codex/sessions` with a bounded recursive scan. It must not fall back to `find /` or broad semantic indexing just to locate a known Codex session id.

`trans_search --allProjects` also maintains a keyword index for Codex rollout files under a virtual project named `~/.codex/sessions (Codex CLI)`. This makes exact recall work for recent Codex conversations without knowing the rollout path first. `trans_scan({id})` remains the most precise way to resume or audit one Codex session when you already know its id/prefix.

## Verify

```powershell
codex mcp list
Test-Path "$env:USERPROFILE\.agents\skills\trans\SKILL.md"
node scripts\doctor.mjs
```

## If you run a third-party provider-switcher tool (e.g. cc-switch)

Some setups run a background app that manages multiple Claude Code/Codex provider profiles and periodically syncs `~/.codex/config.toml` / `~/.claude.json` (e.g. [cc-switch](https://github.com/) — a tray app that mirrors both clients' MCP server lists into its own local database). If such a tool's sync cycle races with `codex mcp add`, the `trans` entry can transiently disappear from `~/.codex/config.toml` before the tool's own scan re-imports it. This isn't something trans-criptase can prevent — it's inherent to running two independent things that both write the same config file. If `node scripts/doctor.mjs` reports the Codex MCP registration missing, just re-run `codex mcp add trans -- node <repo>/mcp/server.mjs` (or `.\install.ps1 -Clients codex`, which is idempotent) — it's a one-line fix, not data loss.

## Uninstall

```powershell
.\uninstall.ps1 -Clients codex          # keeps config/index by default
.\uninstall.ps1 -Clients codex -Purge   # also deletes config/index, asks for confirmation first
```
