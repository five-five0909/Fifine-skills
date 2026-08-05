---
name: skills-session-handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

# Session Handoff

## Trigger check

Use this skill only when the user explicitly invokes `skills-session-handoff` (legacy alias: `handoff`) or asks for a compact continuation document for another agent. If the user wants the task implemented, summarized for a report, or copied into an existing project artifact instead, stop and handle that request directly.

## Create the handoff

Write one concise Markdown document for a fresh agent. The document must describe the current conversation and the exact point where work should continue.

1. Treat any arguments passed to the skill as the purpose of the next session. Put that focus near the top and use it to prioritize the remaining work.
2. Inspect the current repository state when it is in scope: working-tree status, relevant diffs, task files, plans, specs, ADRs, issues, and recent commits. Verify claims about completed work against the filesystem.
3. Do not duplicate material already captured elsewhere. Reference existing artifacts by relative path, absolute path, URL, commit, or diff instead of pasting their contents.
4. Redact secrets and personal data before writing. Replace API keys, access tokens, passwords, private keys, connection strings, email addresses, phone numbers, and other identifying data with labels such as `[REDACTED_API_KEY]` or `[REDACTED_PII]`.
5. Save the document outside the current workspace, in the operating system's temporary directory. Resolve that directory through the host/runtime (for example, Node's `os.tmpdir()` or the platform's standard temporary-directory environment variable); never hard-code an author's home path.
6. Use a unique filename such as `handoff-<timestamp>-<unique-id>.md` so an earlier handoff is not overwritten. Report the final path to the user.

## Required document structure

Keep the document compact and use these headings unless a section is genuinely not applicable:

```markdown
# Handoff: <short task title>

## Next-session focus
<the user-provided argument, or the most likely continuation goal>

## Original task
<what the user asked for, including constraints>

## Done (verified)
- <completed item with a path, commit, test, or other evidence>

## Breakpoint
<the exact unfinished step, open decision, failing test, or blocking condition>

## Remaining work
- <next action, ordered by priority>

## Relevant artifacts
- <path/URL/commit/diff reference and why it matters>

## Suggested skills
- `<skill-name>` — <why it may help with the next-session focus>

## Safety and constraints
<important assumptions, no-go areas, compatibility requirements, and redaction notes>
```

## Suggested skills

Suggest only skills that are relevant to the next-session focus and available in the current skill catalog. Prefer the smallest useful set, normally zero to three entries. Include the exact skill name and a one-line reason. Do not claim that a skill was used if it was only suggested. If no catalog skill is relevant, write `None identified.`

## Quality checks before saving

- A fresh agent can identify the original goal, verified progress, breakpoint, and first next action without reading the whole conversation.
- "Done" items are evidence-backed, while uncertain items are labeled as assumptions or open questions.
- Existing artifacts are linked or named rather than duplicated.
- No secret, credential, or unnecessary personal information remains.
- The output path is in the OS temporary directory and the file is uniquely named.
