# transcriptase

**English** | [简体中文](README.zh-CN.md)

[![LINUX DO](https://img.shields.io/badge/LINUX%20DO-community-ffb003?logo=discourse&logoColor=white)](https://linux.do)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> Make Claude Code remember what it already said.

<p align="center">
  <img src="https://raw.githubusercontent.com/Scotlight/trans-criptase/main/assets/demo.svg" alt="trans resuming a dropped session inside Claude Code" width="760">
</p>

Every Claude Code session leaves a full transcript on disk (JSONL), but all you get officially is a flat `--resume` list — you can't find, search, or resume across it. transcriptase turns those dormant transcripts into two things: **a resumable scene**, and **a searchable memory**.

The name comes from reverse transcriptase: others transcribe conversations into files; we reverse-transcribe files back into live context.

**Works with both Claude Code and Codex CLI.** One repo, one MCP server (`mcp/server.mjs`), one config, one set of indexes — both clients connect to the same install via a Skill symlink/Junction, no duplicated setup. See [Quick start](#quick-start).

transcriptase also indexes **your actual project source code**, not just past conversations — exact/semantic/hybrid retrieval over any local directory via the `trans_code_*` tools, independent of the transcript search above. See [Code / document retrieval](#code--document-retrieval).

## Four capabilities

**1. Session resumption (`/trans`)**
Session dropped, context blew up, machine rebooted? One command scans an old session transcript and produces a five-part resumption brief:

```
session size → compacted summary → user-message thread (with line numbers) → tail overview → breakpoint detail (full content of every Edit/Write)
```

The breakpoint detail pins down "which step of which file you last touched, which edit never landed" — the new session picks up from there instead of re-treading the whole path.

**2. Cross-session semantic search**
"How did I do that font migration last time?" "Which session mentioned the merge collision?" — not in the current context, but it's in the transcripts. Hybrid search (vector + keyword RRF fusion, optional reranker) does fuzzy recall and returns `sessionId:line`.

**3. Line-level context expansion**
After a hit, pull the full records around `sessionId:line` (including tool calls and results) and **re-inject those old details into the current conversation** — instead of jumping off to resume a dead session whose context blew up long ago.

**4. Local code / document retrieval (arbitrary directories, separate from transcripts)**
"Where is `X` implemented", "find that error string", "what's similar to Y" — over your actual source tree, not past chat. `trans_code_index` builds a per-directory index; `trans_code_query` supports exact (keyword, no API), semantic (vector), or hybrid (RRF fusion, default) retrieval with automatic degrade-to-exact when embedding isn't configured; `trans_code_read` pulls the matched lines with a path-traversal-safe boundary. See [Code / document retrieval](#code--document-retrieval).

All four are offered simultaneously as **MCP tools (Claude Code + Codex CLI) + CLI + Skill**, with three ways to trigger the transcript side: run `/trans` explicitly, invoke the MCP tools directly, or let the `UserPromptSubmit` hook nudge the model — when your message hints at continuation ("last time…", "that session…", "接着上次…"), the hook injects a soft suggestion and the model decides whether a search/scan is actually warranted. Nothing fires behind your back; the hint is advisory, and you can always drive it by hand.

## See it in action

Real screenshots, not mockups. The point of the hook is that it *suggests* — the model still decides.

**1. Say "what did I do yesterday?" and it resumes on its own.** The `昨天` trigger fires the hint; the model calls `trans` repeatedly, walks back through your sessions (the newest one was just a `/plugin` command, so it keeps digging), and hands back a real summary of yesterday's six sessions.

<p align="center">
  <img src="https://raw.githubusercontent.com/Scotlight/trans-criptase/main/assets/showcase-1-auto-resume.png" alt="asking what did I do yesterday triggers trans to scan back through sessions and summarize" width="760">
</p>

**2. It does NOT fire on a false positive.** "Yesterday's weather" also contains `昨天`, so the hook still injects its hint — but the model reads the whole message, sees it has nothing to do with session history, and asks for your city instead of blindly calling the tool. The hint is advisory, exactly as designed.

<p align="center">
  <img src="https://raw.githubusercontent.com/Scotlight/trans-criptase/main/assets/showcase-2-no-false-trigger.png" alt="asking about yesterday's weather does not trigger a tool call — the model asks for the city instead" width="760">
</p>

**3. Ask it to work without tools and it's honest about the gap.** Tell it "don't use any tools/plugins/skills/MCP" and it admits it has no memory of yesterday and can't reach `git log` or the filesystem — then offers to look it up *with* those tools. That's the baseline transcriptase exists to fix.

<p align="center">
  <img src="https://raw.githubusercontent.com/Scotlight/trans-criptase/main/assets/showcase-3-no-tools-baseline.png" alt="told to use no tools, the model honestly says it cannot recall yesterday and suggests git log or the trans plugin" width="760">
</p>

## Quick start

### Method A: one-command install via marketplace (recommended)

This repo is also a Claude Code plugin **marketplace**. Add it once, then install:

```shell
/plugin marketplace add Scotlight/trans-criptase
/plugin install trans@trans-criptase
```

That is all for the skill + SessionEnd hook (they load with the plugin, **without touching your `settings.json`**). To unlock semantic/hybrid search you still configure embedding once (see [Configuration](#configuration)); the MCP server can be registered with `claude mcp add` (see Method B step 2) or declared via the plugin's `.mcp.json`.

### Method B: clone into the skills directory (for development / customization)

transcriptase is a **Claude Code skills-dir plugin**: clone it under `~/.claude/skills/` and it auto-loads next session (the skill + SessionEnd hook take effect with the plugin, **without touching your `settings.json`**). MCP tools are registered with one `claude mcp add`.

```powershell
# 1. Clone into the skills directory (the folder MUST be named trans)
git clone https://github.com/Scotlight/trans-criptase "$env:USERPROFILE/.claude/skills/trans"
cd "$env:USERPROFILE/.claude/skills/trans"
# macOS/Linux: git clone https://github.com/Scotlight/trans-criptase ~/.claude/skills/trans && cd ~/.claude/skills/trans

# 2. One-shot setup: generate config + register MCP for BOTH Claude Code and Codex CLI (skips whichever
#    CLI isn't installed, with no interruption to the other). Pick any of these:
./install.ps1                                                    # both clients, interactive config wizard
./install.ps1 -Clients claude                                    # Claude Code only
./install.ps1 -Clients codex                                     # Codex CLI only
./install.ps1 -BaseUrl https://api.mistral.ai/v1 -ApiKey sk-xxx -Model mistral-embed   # args, one-liner
#   macOS/Linux: ./install.sh --clients claude,codex --baseUrl ... --apiKey ...
./install.ps1 -Provider local -LocalDtype q8                     # local-model tier (see docs/local-model.md)
./install.ps1 -ExactOnly                                         # skip embedding entirely, keyword search only
#   Prints the real paths of the shared install root / config / index / MCP server at the end.
#   Verify anytime: node scripts/doctor.mjs

# 3. Build the index + verify
node scripts/semantic.mjs index --force                      # with embedding: full vector index
node scripts/semantic.mjs query "error text or a variable name" --exact   # works with zero config: pure keyword, no API
```

> **Don't want the key in a file?** Skip `-ApiKey` and set the env var `TRANS_EMBED_API_KEY` instead (`setx TRANS_EMBED_API_KEY "sk-xxx"` on Windows, or write it into your shell profile on macOS/Linux). It takes precedence over the config file, so the key never lands in a file, a conversation, or the transcript index. `TRANS_EMBED_BASE_URL` / `TRANS_EMBED_MODEL` etc. work the same way.

Next new session you'll get the `/trans:trans` skill, 11 MCP tools (6 transcript tools — `trans_search` / `trans_scan` / `trans_list` / `trans_projects` / `trans_expand` / `trans_index` — plus 5 code-search tools — `trans_code_query` / `trans_code_index` / `trans_code_status` / `trans_code_read` / `trans_code_config_check`), a `UserPromptSubmit` hook that hints at continuation intent (Claude Code only — Codex CLI wires hooks per-project, not per-skill, so this specific nudge doesn't auto-fire there yet; the MCP tools work identically on both), and background incremental indexing at the end of every session (the SessionEnd hook, same caveat).

> **Why clone into `~/.claude/skills/trans` rather than "anywhere + an install script"?** Because a skills-dir plugin auto-loads from that location. This way the hook is defined in the plugin's own `hooks/hooks.json`, physically isolated from your `settings.json` — swapping providers or rewriting `settings.json` won't clobber it. The folder must be named `trans` (scripts and index are located by it).
>
> For `--plugin-dir` temporary testing or marketplace distribution, see the [Claude Code plugin docs](https://code.claude.com/docs/en/plugins).

### Or: let the AI install it (recommended)

Copy the block below and hand it to Claude Code; it takes care of the rest:

```text
Please install and configure transcriptase (a Claude Code session-transcript search/resume tool, repo: https://github.com/Scotlight/trans-criptase). Go step by step; verify each step succeeds before the next:

1. Clone the repo into ~/.claude/skills/trans (the folder MUST be named trans — a skills-dir plugin auto-loads from that location). Then run the install script in that directory: on Windows run ./install.ps1 with pwsh, on macOS/Linux run bash install.sh. It does only two things: generate embed-config.json, and register an MCP server named trans via claude mcp add (it does NOT touch my settings.json). Confirm the clone finished and both steps succeeded. Note: the plugin's /trans:trans skill and SessionEnd hook need no extra registration — they take effect next session. Do not edit my settings.json.

2. Verify the base pipeline with zero config: in ~/.claude/skills/trans run
   node scripts/semantic.mjs index --no-embed
   then search a keyword that appeared in one of my recent sessions:
   node scripts/semantic.mjs query "<that keyword>" --exact
   It passes only if there are hits.

3. Ask me which embedding tier (ask only once):
   a) Remote API — you MAY run the install script with baseUrl/model args for me (those are not secrets), but the apiKey must never pass through you: let me choose — either I open ~/.claude/skills/trans/embed-config.json and fill apiKey myself, or I set the env var TRANS_EMBED_API_KEY in my terminal (the key never enters the conversation/file/index and takes precedence over the file). baseUrl should be an OpenAI-compatible endpoint ending in /v1; recommended model BAAI/bge-m3, optional reranker BAAI/bge-reranker-v2-m3.
   b) Local model (zero cloud) — walk me through the six steps in docs/local-model.md; I need to download the model files manually, and you validate the placement and config.
   c) Keyword only for now — skip this step and step 4.

4. After config, run node scripts/semantic.mjs index --force to build the vector index, then test query with a semantic question (not an exact keyword) and show me the hits to confirm quality.

5. To wrap up, tell me in a few sentences: when each of the 5 MCP tools (trans_search / trans_expand / trans_scan / trans_list / trans_index) gets used, how /trans:trans is triggered, and that the SessionEnd hook incrementally indexes the just-ended session after each of my sessions (only for projects already indexed, skipping the currently-active session, with a budget cap, so it never slows down searches). Remind me all of this takes effect only in a new session.

Hard constraints: never print my apiKey into the conversation, command-line args, or logs; treat transcripts under ~/.claude/projects as read-only, never modify them; stop and report on any step failure — do not push through broken.
```

## Configuration

Three tiers, pick as needed:

| Tier | Needs | Capability |
|---|---|---|
| **Zero-config** | nothing | keyword/substring search (`--exact`), works natively for CJK |
| **Remote API** | any OpenAI-compatible embedding endpoint | + semantic/hybrid search; recommend `BAAI/bge-m3` (best for Chinese), optional `bge-reranker-v2-m3` rerank |
| **Local model** | download an ONNX model once (~24–450MB) | same as above, but **fully offline** (`allowRemoteModels=false` hard-locked) → [local setup guide](docs/local-model.md) |

`embed-config.example.json`:

```jsonc
{
    "provider": "api",              // "api" or "local"
    "baseUrl": "https://your-endpoint/v1",
    "apiKey": "sk-...",
    "model": "BAAI/bge-m3",
    "rerankModel": "BAAI/bge-reranker-v2-m3",   // leave empty to skip rerank
    "localEmbedder": "embedder/embedder.mjs",   // used when provider=local
    "localDtype": "fp32"
}
```

### Three ways to write the config

**1. install-script args (personal one-liner, non-interactive)**

```powershell
./install.ps1 -BaseUrl https://your-endpoint/v1 -ApiKey sk-xxx     # remote API tier
./install.ps1 -Provider local -LocalDtype q8                       # local-model tier
```

macOS/Linux long options: `./install.sh --baseUrl ... --apiKey ...`. The script calls `scripts/write-config.mjs` to persist, and apiKey is masked in the log.

**2. Environment variables (key never lands in file/conversation/transcript — safest)**

Any config field can be overridden by an env var of the same purpose, taking precedence over the file. The most useful is keeping `apiKey` in an env var only — leave that line empty in `embed-config.json`:

| Env var | Overrides |
|---|---|
| `TRANS_EMBED_API_KEY` | apiKey |
| `TRANS_EMBED_BASE_URL` | baseUrl |
| `TRANS_EMBED_MODEL` / `TRANS_RERANK_MODEL` | model / rerankModel |
| `TRANS_EMBED_PROVIDER` / `TRANS_LOCAL_EMBEDDER` | provider / localEmbedder |

```powershell
setx TRANS_EMBED_API_KEY "sk-xxx"     # Windows, takes effect on a new terminal
export TRANS_EMBED_API_KEY=sk-xxx     # macOS/Linux, write into your shell rc
```

> **Why this matters especially for trans**: trans indexes exactly the `~/.claude/projects/*.jsonl` transcripts. Once a key enters the conversation, trans will chunk it, embed it, write it into `index/` in plaintext, and send it as text-to-embed to your endpoint. So when letting the AI install this, **never hand it the key** — use an env var, or open the file and fill it yourself.

**3. Manual edit**: `cp embed-config.example.json embed-config.json` and fill it in. The file is already blocked by `.gitignore`, so it won't be committed by accident.

## Usage

### MCP tools

The model may call these on its own when the context calls for it (the `UserPromptSubmit` hook can nudge it toward a search/scan — see below), or you can invoke them explicitly.

| Tool | Does what |
|---|---|
| `trans_search` | fuzzy-search old session details; **auto incremental-refresh before searching**, zero maintenance |
| `trans_expand` | expand context around `sessionId:line` |
| `trans_scan` | produce the session resumption brief (five-part report) |
| `trans_list` | list candidate sessions (mtime desc + first-message preview) |
| `trans_projects` | list all known projects (real cwd + recency + indexed status) for cross-project search |
| `trans_index` | build/rebuild the transcript index manually |
| `trans_code_query` | exact/semantic/hybrid search over an indexed local directory (`root_path`), returns `path`/`start_line`/`end_line`/`score`/`match_type`/`snippet` |
| `trans_code_index` | build/incrementally update the code/document index for a `root_path` |
| `trans_code_status` | index + config status for a `root_path` (never echoes the full API key) |
| `trans_code_read` | read a line range from a matched file, bounded to `root_path`/`allowedRoots` (rejects traversal/symlink escape) |
| `trans_code_config_check` | end-to-end diagnostic: Node version, config, live embedding connectivity probe, Claude/Codex CLI presence |

See [Code / document retrieval](#code--document-retrieval) below for how `trans_code_*` differs from the transcript tools above.

### CLI

```powershell
node scripts/semantic.mjs query "pinned sidebar drag width"   # hybrid (vector + keyword RRF)
node scripts/semantic.mjs query "..." --exact                # pure keyword, no API
node scripts/semantic.mjs query "..." --rerank               # add rerank
node scripts/semantic.mjs query "..." --all                  # across all projects
node scripts/semantic.mjs index                              # incremental index (seconds)
node scripts/semantic.mjs projects                           # list known projects (real cwd) for cross-project search
node scripts/semantic.mjs projects --query epub              # narrow by path/preview substring
python scripts/scan_transcript.py --id <session-prefix>      # resumption brief (--list lists candidates)
```

**Cross-project search.** By default `query` / `index` only touch the current project. To pull a detail from a *different* project, first run `projects` to get that project's real working-directory path, then pass it explicitly:

```powershell
node scripts/semantic.mjs projects --query epub              # find the target project's real path
node scripts/semantic.mjs query "font migration" --project "D:\path\to\that\project"
```

This targets one project instead of `--all` (which re-scans every index and degrades as projects accumulate).

### Auto-trigger hook

The plugin ships a `UserPromptSubmit` hook (`scripts/prompt-hint.mjs`). Every time you send a message, it scans for continuation/recall intent — `昨天` / `上次` / `之前说` / `记得…做` / `接着上次` / `恢复会话`, plus English `last time` / `pick up where` / `previous session`, and bare session-UUID fragments. On a hit it injects one advisory line into the model's context suggesting `trans_scan` / `trans_search`; the model reads your full message and decides whether it's actually needed. On a miss (or malformed input) it exits silently with zero side effects. Nothing fires automatically — the hook only *suggests*.

**Which hooks fire, and when:**

| Hook | Fires | What it does | Blocking? |
|---|---|---|---|
| `UserPromptSubmit` (`prompt-hint.mjs`) | every message you send | injects one advisory line on an intent hit; silent no-op otherwise | no — self-terminates after a 3s safety timeout, and a miss returns instantly |
| `SessionEnd` (`session-end-index.mjs`) | when a session ends | spawns a **detached** background process to incrementally index the just-ended session, then exits immediately | no — the index work runs in a child process that's `unref`'d, so it never delays session close |

**Failure / timeout behavior:** both hooks are best-effort and fail open. `prompt-hint.mjs` wraps everything in try/catch, emits nothing on error, and has a hard 3-second `setTimeout` fallback so it can never hang your prompt. `session-end-index.mjs` only spawns an indexer for projects that already have an index (never blocks, never builds on first sight), and swallows any spawn error. If either hook is missing or broken, Claude Code proceeds normally — you just lose the suggestion / the background refresh.

**Coexisting with other plugins:** these hooks are declared in the plugin's own `hooks/hooks.json` (via `${CLAUDE_PLUGIN_ROOT}`), **not** in your `settings.json`. Claude Code runs all registered `UserPromptSubmit` hooks, so ours composes additively with any you or another plugin define — it only ever *appends* `additionalContext`, never rewrites the prompt or short-circuits other hooks. Removing the plugin directory removes the hooks cleanly; nothing is left behind in `settings.json`.

## Code / document retrieval

Independent of the transcript search above: index and search **any local project directory** — source code, docs, logs. Same embedding provider config as transcript search (one key, both subsystems), separate index namespace (`data/code-index/` vs `index/`).

```powershell
node scripts/semantic.mjs code-index --root . --no-embed              # keyword-only index, zero API cost
node scripts/semantic.mjs code-query "buildIndexLines" --root . --mode exact
node scripts/semantic.mjs code-index --root . --force                 # full rebuild (after an embedding-model change)
node scripts/semantic.mjs code-query "how do we handle concurrent index writes" --root . --mode hybrid
node scripts/semantic.mjs code-status --root .
```

Mode selection: `exact` for known identifiers/error strings/file names (no API needed); `semantic` for fuzzy natural-language intent; `hybrid` (default) when both apply or exact recall is too narrow. `hybrid`/`semantic` auto-degrade to `exact` when embedding is unavailable — the response carries `degraded: true` and a `reason`.

Safety: files are filtered through a built-in ignore baseline (`.git`, `node_modules`, `dist`, `.env`, `*.key`/`*.pem`, common secret dirs, binaries, oversized files) plus `.transignore` (or `.gitignore` as fallback) for project-specific rules — the baseline cannot be removed by user rules, only extended. If `codeSearch.security.allowedRoots` is configured in `config/config.json`, every `root_path`/`path` argument is validated against it (path-traversal and symlink-escape both rejected); left empty, any local path is reachable — tighten this if you don't want that.

## Doctor

One command checks the whole pipeline end to end — Node version, config file, API key presence (never echoed), live embedding connectivity probe, transcript/code index status, Claude/Codex Skill links, Claude/Codex MCP registration, stale lock files, directory write permissions:

```powershell
node scripts/doctor.mjs
```

Outputs PASS/WARN/FAIL/SKIP per check plus an overall verdict and copy-paste fix commands.

### Search wisdom

Rerank score < 0.5 = you didn't catch the real one. **Rephrase and re-search**, using the words the person actually used at the time: what "two windows overwriting each other" won't find, "another session clobbered my refactor" nails in one shot. For variable names and error strings, use `--exact`.

### Verify install (smoke test)

A hermetic, copy-paste smoke test that exercises the full pipeline — build index → recall a known needle → list projects → wipe → confirm it's gone — **without touching your real transcripts or index** (it runs entirely in a temp sandbox via `TRANS_PROJECTS_ROOT` / `TRANS_INDEX_ROOT` overrides). Keyword-only, so **no API key required**; Node-only, so it runs identically on Windows/macOS/Linux:

```bash
node test/smoke.mjs        # or: npm run smoke
```

Expected tail:

```
  ✓ query recalls the known needle
  ✓ projects lists the real cwd
  ✓ after wipe, needle is no longer recalled

PASS — all smoke checks green
```

Unit + integration tests (pure functions + a full MCP-server round trip, also zero-dependency, sandboxed):

```bash
npm test
```

## Architecture

```
                        SKILL.md (shared trigger/mode rules for both clients)
                                       │
                    ┌──────────────────┴──────────────────┐
          Claude Code Skill                        Codex CLI Skill
      ~/.claude/skills/trans (Junction)        ~/.codex/skills/trans (Junction)
                    └──────────────────┬──────────────────┘
                            mcp/server.mjs (single stdio MCP process)
                    ┌──────────────────┴──────────────────┐
         6 transcript tools                        5 trans_code_* tools
         (scripts/lib.mjs)                     (lib/code-search/*)
                    │                                      │
        index/<project>/ (transcripts)         data/code-index/<root>/ (any directory)
                    └──────────────────┬──────────────────┘
                          lib/shared/{paths,config,locking,redact}.mjs
                       (one config, one embedding provider, one lock/atomic-write layer)
```

```
~/.claude/projects/<project>/*.jsonl     transcripts (read-only, never modified)
        │  parse: filter noise/tool output, chunk (800 chars / 720 stride)
        ▼
index/<project>/  meta.jsonl + vec.bin   plaintext chunks + normalized vectors (binary)
        │  state.json records lines processed per session → incremental index embeds only new
        ▼
query: vector dot-product top200 ─┐
       keyword substring top200 ──┴→ RRF fusion → (optional rerank) → sessionId:line
```

- Both indexes are **local files**, no database dependency; writes go through a file lock + atomic rename (`lib/shared/locking.mjs`) so two MCP processes (one per client) building the same index concurrently can't corrupt it
- Zero npm dependencies (node ≥ 18) anywhere in `mcp/`, `lib/`, `scripts/`; the MCP server is hand-written stdio JSON-RPC
- The local-model option uses transformers.js (ONNX), with dependencies isolated in `embedder/` — not installing it doesn't affect anything else

### File layout

```
<wherever you clone trans-criptase>/     ← single source of truth; both clients link here
├── SKILL.md                      shared trigger/mode-selection rules (transcript + code search)
├── agents/openai.yaml            Codex/OpenAI Skills metadata (same skill, non-Claude discovery)
├── mcp/server.mjs                single MCP process, both tool families
├── mcp/tools/                    trans_code_* tool definitions (thin wrappers over lib/code-search)
├── lib/shared/                   paths / config / locking / redact / diagnostics — shared by both subsystems
├── lib/code-search/              exact/semantic/hybrid retrieval over arbitrary directories
├── scripts/lib.mjs               transcript parsing/index/search core (unchanged behavior, now built on lib/shared)
├── scripts/mcp-server.mjs        compat shim → mcp/server.mjs (old hardcoded paths keep working)
├── scripts/doctor.mjs            end-to-end diagnostic (see Doctor section)
├── config/config.example.json    new shared config schema (embedding + transcript + codeSearch + clients)
├── embed-config.json             legacy config format, still read as a fallback (blocked by .gitignore)
├── index/                        transcript vector index (blocked by .gitignore)
├── data/code-index/              code/document index, one namespace per indexed root_path (blocked by .gitignore)
├── scripts/bootstrap.mjs         dual-client bootstrap (skips a missing CLI, doesn't abort)
├── uninstall.sh                  cleanup helper
└── embedder/                     local-model option (transformers.js + your own model files)
```

Claude Code and Codex CLI each get a Skill directory (`~/.claude/skills/trans`, `~/.codex/skills/trans`) created as a Junction (Windows, no admin rights needed) or symlink (macOS/Linux) pointing at wherever you cloned this repo — **one codebase, one config, one set of indexes**, two independent client registrations. Each client's MCP registration is separate (`claude mcp add` / `codex mcp add`) but both point at the same `mcp/server.mjs`. Scripts derive their own location via `import.meta.url` (`lib/shared/paths.mjs`), so nothing is hardcoded to a specific install path.

## FAQ

**Q: HuggingFace model download returns 403?**
HF's Xet CDN (`cas-bridge.xethub.hf.co`) denies access from some network egresses, and hf-mirror doesn't proxy it. Download the model files manually from a mirror like ModelScope and drop them into `embedder/models/<model-id>/` — the local option is designed for exactly this "bring your own files, load fully offline." See the [local setup guide](docs/local-model.md).

**Q: Is the index safe?**
`index/` holds **plaintext chunks of all your conversations**. It only lives locally, but if you use remote embedding, the chunk text is sent to your configured API endpoint — if that bothers you, use a local model or the keyword-only tier. `.gitignore` already blocks index, models, and the real config; don't force-add them.

**Q: Cost?**
bge-m3-class embedding is dirt cheap: a full index of 700+ chunks is ~500K input tokens once, then incremental is nearly free; each query is ~50–200 tokens.

**Q: Cross-platform?**
The core is Node with a stdlib-only Python scan/list adapter, so the CLI and MCP paths work on Windows, macOS, and Linux without PowerShell.

## License

MIT
