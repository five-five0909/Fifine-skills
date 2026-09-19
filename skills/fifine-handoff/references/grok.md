# Grok overlay — fifine-handoff skill

Load when executing `fifine-handoff` on the **Grok** CLI.

This overlay is optional. The skill works on Grok with no special integration: it falls back to `references/destinations.md`, writes a disposable handoff file, and prints the canonical first message. Do not add external projectors or memory tools to the core flow.

## Install location

- `~/.grok/skills/fifine-handoff/`

Grok loads skills from its skills directory. Copying this skill folder directly is enough.

## Write destinations (policy-safe)

Some Grok setups run a write policy hook that denies private context in public workspace files. If your setup does, sanitize before any public-repo write. If it does not, use the portable default.

| Destination | When | Notes |
|-------------|------|-------|
| OS temp `agent-handoffs/` (see `references/destinations.md`) | **Default** | Disposable; preferred for cross-session transfer |
| A private scratch dir | Full detail with private path context allowed | Use only if policy allows private destinations |
| Current workspace (e.g. `.handoffs/`) | Only if sanitized | No literal private-root path strings; no pasted private text; git-ignore it |
| Chat inline only | Last-resort fallback | Tell the user no file was written |

Filename: `YYYY-MM-DD-<slug>.md` (kebab-case hint from the goal, max ~40 chars). Never overwrite an existing handoff; append a suffix if needed.

## Grok-specific context to capture

When relevant to the stated goal, include:

- Session id, if known from environment or session metadata
- Workspace root / cwd
- Open todos, if any were seeded
- Hook incidents, if a write was denied, with what was blocked and what safe alternative was used
- Whether changes are committed or still in the working tree

## Suggested skills for Grok receivers

List only skills you can confirm exist under the receiver's skills directory. Fifine skills keep their canonical `fifine-` names. Describe the action in plain language if you cannot confirm a matching skill exists.

## Optional follow-ups

Grok-specific project-progress tools are not assumed. Leave the handoff doc's "Optional follow-ups" section out unless the current project explicitly provides a safe command.

## First message

Use the canonical block in `references/destinations.md`. Paste it into a **new** Grok session.

## What not to do on Grok

- Do not use in-place compaction as a substitute when the user wants a **new** focused thread.
- Do not write private markers into public workspace paths.
- Do not duplicate content already in repo artifacts — reference paths only.
- Do not invoke external projectors, memory systems, or helper CLIs unless the current project explicitly provides and documents them.
