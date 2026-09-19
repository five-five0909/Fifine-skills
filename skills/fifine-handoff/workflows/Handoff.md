# Handoff workflow

Executable steps for the `fifine-handoff` skill. Harness-agnostic; consult your overlay under `references/` only for destination and sibling-tool details.

## 1. Confirm goal

- If the user passed text after `/fifine-handoff`, that text **is** the next-session goal. (How arguments arrive differs by harness — some append them as a user message, some substitute `$ARGUMENTS`. Read the goal from the user's request, not from a specific substitution token.)
- If no goal was given, ask once: "What should the next session focus on?"
- Do not proceed without a clear goal — handoff quality depends on it.

## 2. Extract (goal-filtered)

From the current session, pull only what the next agent needs for **that goal**:

- Decisions already made
- COMPLETED / IN PROGRESS / NEXT / BLOCKERS
- Artifact paths (plans, markdown reports, open PRs) — paths only
- Files to read, in order
- Approaches that failed (with enough detail to avoid retry)
- Open todos if any were seeded

Skip tangents, tool-call noise, and content recoverable from git or named artifacts. Verify claims about completed work against the filesystem (working-tree status, commits, task files, test output) instead of restating the conversation.

## 3. Choose write destination

- If a harness overlay applies, follow its destination table (`references/claude-code.md`, `references/codex.md`, `references/pi.md`, or `references/grok.md`).
- Otherwise use the portable default in `references/destinations.md`: the OS temp directory under an `agent-handoffs/` subfolder.

Create the output directory if it is missing. Filename: `YYYY-MM-DD-<slug>.md` where slug is a kebab-case hint from the goal (max ~40 chars). Never overwrite an existing handoff; if the path already exists, append a short time or numeric suffix.

## 4. Compose document

- Apply `references/template.md`
- Redact secrets and PII: API keys, access tokens, passwords, private keys, connection strings, email addresses, phone numbers, and other identifying data become `[REDACTED_API_KEY]` / `[REDACTED_PII]` style labels
- Mandatory sections: **Suggested first message**, **Current state** (all four rows), and **Suggested skills**. The rest (Decisions, Failed approaches, Artifacts, Relevant files, Policy notes) are optional — include them when they apply, omit them when empty rather than padding with "none"
- List skills the receiver should invoke first, preferring ones you can confirm exist in the receiving harness. If no skill is relevant, write `- None identified.`

## 5. Write file

- Write the file with the current harness's normal file-write mechanism
- If a write is denied by policy (e.g. a PreToolUse hook blocks it), fall back in order: (a) sanitized content to a policy-allowed location named in your overlay, (b) a private scratch path, or (c) deliver the doc inline in chat and tell the user no file was written

## 6. Optional persistence

If — and only if — the receiving harness has a project-progress or session-note tool (named in its overlay), and the work maps to a named project, offer to append a one-line note via that tool. This step is **optional sugar**; never block a handoff on it, and never invoke a tool the current harness does not provide.

## 7. Report to user

Return:

1. Absolute path to the handoff file (or "inline only" if no file)
2. The suggested first message in a copy-paste fence
3. One line: "Start a new session and paste the first message."

Do not start the next session's work in the current turn unless the user asks to continue here instead.
