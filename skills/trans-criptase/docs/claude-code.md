# Claude Code setup

## Install

```powershell
.\install.ps1 -Clients claude
```
```bash
./install.sh --clients claude
```

What it does (see `install.ps1`/`install.sh` for the exact steps):
1. Writes/updates config via `scripts/write-config.mjs` (skipped fields keep prior values).
2. Creates a Skill Junction (Windows, no admin rights needed) or symlink (macOS/Linux) at `~/.claude/skills/trans` pointing at wherever this repo lives. If that path already exists as a real directory (not a link), it's left untouched — no data loss.
3. Builds an initial keyword-only index (zero API cost) unless `-SkipIndex` is passed.

**No explicit `claude mcp add` step.** Earlier versions of this installer ran `claude mcp add --scope user trans -- node mcp/server.mjs` here — but the Skill directory already ships its own `.mcp.json`, and Claude Code auto-registers that as soon as it discovers the Skill directory (shows up as `plugin:trans:trans`, auto-`Connected`, no approval prompt). Also running the explicit `--scope user` registration created a second, independent registration of the same name in a different scope, which Claude Code then flags as a conflict ("defined in multiple scopes with different endpoints"). Removing the redundant step fixes this at the root instead of asking you to clean it up after the fact. If for some reason the Skill isn't being auto-discovered (e.g. a nonstandard install layout), you can still fall back to the manual command Claude itself prints (`claude mcp add --scope user trans -- node <repo>/mcp/server.mjs`), but that's the exception, not the default path.

## Skill discovery

Claude Code auto-loads `SKILL.md`, `hooks/hooks.json`, and `.mcp.json` from any directory under `~/.claude/skills/`. Because `~/.claude/skills/trans` is a Junction/symlink to the actual repo, edits to the repo take effect on the next Claude Code session with no re-linking needed. The MCP server is part of this auto-load — no separate registration is needed once the link exists (see above).

## If you're developing trans-criptase itself (not a normal install)

If your Claude Code project directory *is* this repo (i.e. you `cd` into `trans-criptase` and open Claude Code there), you'll additionally see this repo's own root `.mcp.json` picked up as a **project-scoped** MCP declaration (`${CLAUDE_PLUGIN_ROOT}` unresolved outside real plugin-loading context, shown as "Pending approval"). That's expected and harmless — it coexists with the working `plugin:trans:trans` entry from the Skill link. It only shows up because the repo's `.mcp.json` doubles as the plugin manifest for the marketplace-install path (`/plugin install trans@trans-criptase`); normal end users installing into unrelated project directories never see this. If it bothers you while developing, `claude mcp remove trans -s project` clears just that one.

Alternative: this repo is also a Claude Code plugin marketplace — `/plugin marketplace add <this repo>` then `/plugin install trans@trans-criptase` achieves the same Skill+hook loading without running the installer (you still configure embedding separately, see the main README).

## Hooks (Claude-only feature)

`hooks/hooks.json` declares `UserPromptSubmit` (continuation-intent hint) and `SessionEnd` (background incremental transcript indexing). These load automatically with the plugin/skill directory — no `settings.json` edits. Codex CLI does not have an equivalent auto-loading mechanism for skill-bundled hooks (see `docs/codex-cli.md`), so this specific behavior is Claude-only; the MCP tools themselves work identically on both clients.

## MCP tools available

All 11: the 6 transcript tools (`trans_search`/`trans_scan`/`trans_list`/`trans_projects`/`trans_expand`/`trans_index`) plus the 5 code-search tools (`trans_code_query`/`trans_code_index`/`trans_code_status`/`trans_code_read`/`trans_code_config_check`).

## Verify

```powershell
claude mcp list
Test-Path "$env:USERPROFILE\.claude\skills\trans\SKILL.md"
node scripts\doctor.mjs
```

## Uninstall

```powershell
.\uninstall.ps1 -Clients claude          # keeps config/index by default
.\uninstall.ps1 -Clients claude -Purge   # also deletes config/index, asks for confirmation first
```
