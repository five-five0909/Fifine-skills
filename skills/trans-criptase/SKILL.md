---
name: trans-criptase
description: 转录续接（DNA 式 transcription）：把中断/旧会话的 JSONL 转录读出来，提取「原任务 → 已完成 → 断点 → 剩余」，报告后接着干；同时提供对任意本地项目目录的 exact/semantic/hybrid 代码与文档检索（trans_code_*）。当用户说「/trans / 恢复会话 / 接着上次 / 续接 xxx 会话 / resume session / 上次聊到哪了」，或要求在本地代码/文档中定位符号、报错、相关实现时使用。
argument-hint: "[会话ID或前缀] [尾部记录数，默认60]"
---

# /trans — Session transcript resume

DNA central dogma approach: **transcribe** (read the dead session's JSONL into intelligence) → **translate** (produce a resumption report) → **express** (continue the work). Read-only on transcript files, never modifies them.

> **MCP first**: if this session has the `trans` MCP server connected (transcript tools `trans_scan` / `trans_list` / `trans_search` / `trans_expand` / `trans_index` / `trans_projects`, plus code-search tools `trans_code_query` / `trans_code_index` / `trans_code_status` / `trans_code_read` / `trans_code_config_check` — see section 7), call the tools directly and skip the script commands below; they are semantically equivalent, and the transcript tools auto-refresh the index. The scripts below are a fallback when MCP is unavailable (code search has no script fallback yet; use `node scripts/semantic.mjs code-query/code-index` if available, otherwise fall back to normal Grep/Read).

> **Codex fast path**: `trans_scan({id})` / `trans_expand({sessionId})` supports Codex CLI rollout JSONL files under `~/.codex/sessions/YYYY/MM/DD/rollout-...-<session-id>.jsonl`. ID lookup is bounded to `~/.claude/projects` and `~/.codex/sessions` and must not fall back to `find /` or broad semantic indexing just to locate a known session id. Use `path` only when the user gives an exact file path.

## 1. Transcribe: run the scan script (one call, full intelligence)

> When MCP is available: `trans_scan({id})` is equivalent; if unsure which session to resume, call `trans_list()` first.

```powershell
& "$env:USERPROFILE\.claude\skills\trans\scripts\scan-transcript.ps1" -Id <ID-prefix>
```

| Param | Purpose |
|---|---|
| `-Id <prefix>` | Session UUID or prefix; searches current Claude project, all Claude transcript dirs, then bounded Codex sessions (`~/.codex/sessions`) |
| (no args) | Auto-picks the **second-newest** transcript in current project (newest = this session, auto-skipped) |
| `-List` | List candidate sessions (mtime desc + first user message preview); use when user didn't provide an ID |
| `-Tail <n>` | Tail overview record count, default 60 |
| `-MaxMsgs <n>` | User message thread count, default 60; `0` = all |
| `-Detail <line>` | Override breakpoint detail anchor (default: auto-picks last task-bearing user message, filtering out "Continue from where you left off" / [Request interrupted] / image-only / bare #tags) |
| `-Path <path>` | Specify transcript file directly, skip discovery |
| `-Project <path>` | Resolve for a different project directory (default: cwd) |

Output has five sections: **session file** (size) → **compacted summary** (if present) → **user message thread** (with line numbers + timestamps, reconstructing the task trajectory) → **tail overview** (where it broke) → **breakpoint detail** (all assistant actions after the anchor, including full Edit/Write input — the precise boundary of the half-finished work).

If output is truncated on long sessions: reduce `-MaxMsgs`/`-Tail` for partial runs, or use `-Detail` to zoom into just the breakpoint section.

## 2. Manual fallback (if scripts are missing/broken)

Claude transcripts live at `~/.claude/projects/<encoded>/*.jsonl`, where encoded = project cwd with **all non-alphanumeric chars replaced by `-`**. Codex CLI transcripts live at `~/.codex/sessions/YYYY/MM/DD/rollout-...-<session-id>.jsonl`. Claude records use `type` ∈ `user`/`assistant`/`summary` with `message.content`; Codex records use `session_meta`, `event_msg`, and `response_item.payload` (`message`, `function_call`, `function_call_output`). Extract with bounded tail/context reads first, then full real user messages, then assistant/tool actions from the last task message onward. **Never read a large file whole into context and never run a full-disk search to locate a known session id.**

## 3. Verify: reconcile with disk (mandatory)

**Transcript ≠ disk truth.** Every "completed" edit in the transcript must be verified against what actually landed on disk — another session may have overwritten it:

1. `git status --short` + `git diff --stat` — does the working tree match what the breakpoint detail claims?
2. For each Edit/Write in the breakpoint detail, verify current state with Read / `git diff <file>`
3. Working tree has changes the transcript can't explain → **stop and report**, handle as multi-session conflict, don't overwrite

## 4. Translate and express: produce the resumption report, then continue

Report in four sections: **ORIGINAL TASK → DONE (verified) → BREAKPOINT (which file, which step) → REMAINING steps**.

Then resume per the target project's rules: if the project has a write gate / approval requirement (typically in its CLAUDE.md), present a plan and wait for confirmation before writing; otherwise continue directly. Reuse the original session's approach and naming — don't start from scratch.

## 5. Semantic search: fuzzy-recall old details across sessions (optional enhancement)

Scenario: user mentions an old detail not in the current context — "how did we do the font migration last time", "that WebDAV CORS issue we discussed before" — but can't remember which session. Use vector search for fuzzy recall, get `sessionId:line`, then expand.

> When MCP is available: `trans_search({query})` → on hit `trans_expand({sessionId, line})`; the index auto-refreshes before search, zero maintenance. CLI commands below are fallback.

**One-time setup**: edit `~/.claude/skills/trans/embed-config.json` with `baseUrl` (OpenAI-compatible, ending in `/v1`) and `apiKey`; or set env vars `TRANS_EMBED_BASE_URL` / `TRANS_EMBED_API_KEY` (recommended — keeps the key out of files). Default model: `BAAI/bge-m3` (best for Chinese retrieval); reranker default: `BAAI/bge-reranker-v2-m3`.

```powershell
# Build/update index for current project (incremental: only new lines, unchanged sessions skipped)
node "$env:USERPROFILE\.claude\skills\trans\scripts\semantic.mjs" index
node ...\semantic.mjs index --no-embed # keyword-only index, zero API cost (queries must use --exact)
node ...\semantic.mjs index --dry      # estimate new chunk count without calling API
node ...\semantic.mjs index --all      # index all projects
node ...\semantic.mjs index --force    # full rebuild (after model change or index corruption)

# Query: outputs score / sessionId:line / role+time / preview. Default: hybrid (vector + keyword RRF fusion)
node ...\semantic.mjs query "font migration to dedicated table" --top 8
node ...\semantic.mjs query "..." --exact       # keyword/substring only (variable names, error strings; no API)
node ...\semantic.mjs query "..." --semantic    # vector only (conceptual fuzzy query)
node ...\semantic.mjs query "..." --rerank      # rerank after recall for highest quality
node ...\semantic.mjs query "..." --all         # search across all projects

node ...\semantic.mjs status           # index stats per project: model/dims/chunks/size
```

After a hit: `scan-transcript.ps1 -Id <session-prefix> -Detail <line>` to expand that section's full context.

## 6. Cross-project recall: find work done in a DIFFERENT project

Scenario: the user is in project B but references work done in project A — "that thing I did in the epub reader project", "上次在 xxx 仓库改的配置". The prior work lives in **A's** transcripts, which are stored under A's own encoded directory — so a default `trans_search` (current project only) will miss it, and blindly using `allProjects` re-scans every index and degrades as projects accumulate.

Correct workflow — **locate first, then target one project**:

1. `trans_projects()` — lists every known project by real working-directory path (read back from each transcript's `cwd` field, since the encoded directory name is lossy), newest-active first, with session count / indexed status / newest first-message preview. Pass `query` to narrow by path or preview substring.
2. Take the target project's **exact real path** from that list and pass it to `trans_search({query, project: "<that path>"})` (or `trans_scan({project})`). This searches just that one project — no blind polling.

> When MCP is available: `trans_projects({query})`. CLI fallback: `node ...\semantic.mjs projects [--query <kw>] [--limit 40]`.

Key facts: vector binary is stored at `~/.claude/skills/trans/index/<project-encoded>/`, no database dependency; incremental indexing tracks per-session processed lines via `state.json`; switching embedding models triggers auto-rebuild (dimension-mismatched queries are skipped with a warning).

## 7. Code / document retrieval (arbitrary local directories, separate from session transcripts)

Scenario: the user asks to locate code, trace a symbol, find an error string, or recall "how did we implement X" **in the current project's source tree** — this is a different retrieval target from sections 1-6 above (which search *past conversations*). Use the `trans_code_*` tools:

`trans_code_query` / `trans_code_index` / `trans_code_status` / `trans_code_read` / `trans_code_config_check`. Deliberately not `trans_query`/`trans_index` — those names are taken by the transcript tools in section 1-6; do not confuse the two families.

**Mode selection** (pass as `mode` to `trans_code_query`):
- **exact** — complete error text, variable/function/class names, file names, paths, commands, config keys, exact strings. No API required.
- **semantic** — natural-language description, fuzzy intent, conceptual search, "find something similar to X", user doesn't know the exact keyword.
- **hybrid** (default) — exact recall too narrow, semantic recall too broad, or the query mixes identifiers with natural-language intent. Prefer this when unsure.

**Degradation chain**: `hybrid`/`semantic` unavailable (no embedding configured, network failure, dimension mismatch after a model change) → automatically falls back to `exact`, response carries `degraded: true` + `reason`. Report the degradation to the user rather than silently presenting exact-only results as if they were the requested mode. Without any embedding configuration, `exact` still works.

**Workflow**:
1. If the target directory has never been indexed, call `trans_code_index({root_path})` first (incremental by default; `force` to rebuild after an embedding-model change or suspected corruption).
2. `trans_code_query({query, mode, root_path, limit})` → results carry `path` / `start_line` / `end_line` / `score` / `match_type` / `snippet`.
3. Need more context than the snippet? `trans_code_read({path, root_path, start_line, end_line})` — reads are bounded to `root_path`/`allowedRoots`; traversal or symlink escape is rejected.
4. Unsure why results look off (no embedding, wrong model, permission issue)? `trans_code_config_check()` or `trans_code_status({root_path})`.

**Ground rules** (apply to both the transcript tools and the code-search tools): never fabricate a result; always give a real path and line number when available; clearly distinguish keyword matches (`match_type: exact`) from semantic matches (`match_type: semantic`/`hybrid`); rank higher-relevance results first; if results are insufficient, say so explicitly rather than padding the answer.
