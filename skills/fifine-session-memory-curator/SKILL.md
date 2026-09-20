---
name: fifine-session-memory-curator
description: Curate durable preferences, corrections, pitfalls, and lessons from the current conversation into auditable agent memory without blindly treating every statement as truth. Use when the user asks for /fifine-session-memory-curator, user scoop, session memory, 用户偏好归纳, 踩坑经验总结, or 写入全局 agent 配置.
---

# Fifine Session Memory Curator

Turn the current conversation into **small, durable, correctable agent memory**. Preserve what is valuable, but do not convert every sentence, temporary frustration, assistant guess, or project-local detail into a permanent global rule.

The memory must remain subordinate to current explicit instructions and live evidence. Its job is continuity, not unquestioning compliance.

## Core model

Use two layers:

1. **Ledger** — preserves curated entries, scope, grounding, confidence, status, and revision history in a JSON sidecar.
2. **Active block** — contains only concise, currently active global instructions in the agent's global configuration.

This separation gives the user retention and auditability while allowing the AI to correct, supersede, narrow, or reject bad memories later.

## Workflow

### 1. Extract evidence before writing rules

Review the current conversation and collect only potentially reusable items:

- explicit user preferences;
- user corrections to the assistant;
- repeated workflow choices;
- pitfalls with a demonstrated fix or safe alternative;
- stable constraints that future agents cannot cheaply infer again.

Keep the source meaning intact. Do not strengthen “this time” into “always,” or turn an assistant proposal into a user preference.

### 2. Run an AI correction pass

Before promoting an item, challenge it:

- **Grounding:** Was it actually stated or demonstrated, or merely inferred by the assistant?
- **Scope:** Is it global, project-specific, task-specific, or temporary?
- **Stability:** Is it likely to remain useful across future sessions?
- **Conflict:** Does it contradict a newer correction, an existing memory, current instructions, or verified external facts?
- **Safety:** Does it expose a secret, personal identifier, credential, or sensitive raw transcript?
- **Actionability:** Can a future agent act on it without the missing conversation?

When a factual or tool-behavior claim is current and consequential, verify it against an authoritative source before promoting it. Provenance proves what was said; it does not prove that the statement is objectively true.

### 3. Classify every candidate

Create a proposal JSON following [references/memory-curation-policy.md](references/memory-curation-policy.md). Every entry needs a stable `key`, one actionable `instruction`, and these decisions:

- `category`: `preference`, `correction`, `pitfall`, `workflow`, or `constraint`;
- `scope`: `global`, `project`, or `session`;
- `grounding`: `explicit_user`, `user_correction`, `repeated_observation`, `verified_external`, or `assistant_inference`;
- `confidence`: `high`, `medium`, or `low`;
- `status`: `active`, `candidate`, `rejected`, `superseded`, or `deleted`;
- `evidence`: a short source summary, not a transcript dump.

Promotion rule:

- Write to global config only when `scope=global`, `status=active`, and grounding is strong.
- An inferred or merely observed preference stays `candidate` unless the user explicitly confirms it.
- Project-local knowledge belongs in project instructions or project memory, not the global block.
- A newer correction supersedes the older entry; never leave contradictory instructions simultaneously active.

### 4. Preview versus write

- If the user asks only to summarize or inspect, produce the proposal and do not mutate configuration.
- If the invocation explicitly asks to save, remember, update, or write global agent configuration, that authorizes this curation write only.
- Preview the promoted instructions before writing when any entry is ambiguous, inferred, sensitive, or conflicts with existing memory.

### 5. Select the target deliberately

Prefer the active agent's own global configuration:

- Codex: an existing non-empty `${CODEX_HOME:-~/.codex}/AGENTS.override.md`, otherwise `${CODEX_HOME:-~/.codex}/AGENTS.md`
- Claude Code: `${CLAUDE_CONFIG_DIR:-~/.claude}/CLAUDE.md`
- Generic agents: `${AGENTS_HOME:-~/.agents}/AGENTS.md`
- Otherwise use a user-specified absolute path.

Pass the target explicitly when possible. Do not write to every ecosystem unless the user requests synchronization.

### 6. Merge deterministically

Use the helper rather than hand-editing the managed block:

```bash
python skills/fifine-session-memory-curator/scripts/update_session_memory.py \
  --target codex \
  --proposal-file /path/to/session-memory-proposal.json
```

Useful options:

- `--target codex|claude|agents|auto|/absolute/path`
- `--ledger /absolute/path/to/ledger.json`
- `--dry-run`
- `--no-backup`

The helper validates the proposal, retains candidates and superseded entries in the ledger, rejects weakly grounded automatic promotion, atomically updates the managed block, and preserves content outside it.

## Active block behavior

The generated block is the **runtime bridge** that future agents actually receive. It explicitly tells them that:

- memories are defaults, not unquestionable facts;
- current user instructions and verified live evidence take precedence;
- an apparent contradiction should trigger clarification or a memory update;
- rules apply only within their recorded meaning and scope;
- detailed provenance lives in the ledger path printed inside the block;
- `fifine-session-memory-curator` is the maintenance workflow for inspecting or revising that ledger.

The ledger itself is deliberately not injected into every prompt. Only the compact active block is loaded routinely; the agent reads the ledger on demand when it needs provenance, conflict resolution, correction, or deletion.

Codex and Claude Code normally discover global instruction files at session startup. After writing the block, explain that it is guaranteed to affect the next agent session. In the current session, continue using the newly curated rules from the conversation context; if the host does not hot-reload instructions, explicitly read the updated target or start a new session rather than claiming automatic reload.

Keep no more than 12 active global instructions. If there are more, curate and consolidate rather than truncating silently.

## Final response

Report:

- which target and ledger were updated, or that the result is draft-only;
- active instructions added, changed, or superseded;
- candidates deliberately retained without promotion;
- rejected items and the short reason, especially wrong scope, weak grounding, conflict, or sensitive content;
- when the rules become active: immediately in the current conversation context, and reliably from the next session through the global instruction file.
