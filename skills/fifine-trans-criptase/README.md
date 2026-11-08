# fifine-trans-criptase

Resume Claude Code and Codex CLI sessions and search historical conversations, local code, and documents using the skill and its bundled Node.js CLI. No MCP server or registration is required. The host must allow local command execution; Node.js 18 or later is required.

## Usage

Install this skill into the host's skills directory, then ask the agent to resume a session or search your project. The agent follows `SKILL.md` and invokes the bundled commands. The directory need not be named `trans`.

For manual use, replace `<skill-dir>` and `<project>` with the actual paths:

```sh
node "<skill-dir>/scripts/semantic.mjs" list --project "<project>"
node "<skill-dir>/scripts/semantic.mjs" scan --id "<session-id>" --project "<project>"
node "<skill-dir>/scripts/semantic.mjs" index --project "<project>" --no-embed
node "<skill-dir>/scripts/semantic.mjs" search "keyword" --project "<project>" --exact
node "<skill-dir>/scripts/semantic.mjs" code-index --root "<project>" --no-embed
node "<skill-dir>/scripts/semantic.mjs" code-query "keyword" --root "<project>" --mode exact
```

Run `node "<skill-dir>/scripts/semantic.mjs"` for the command reference. Transcripts are read-only; reconcile the current working tree before resuming edits.

## Configuration and privacy

Exact search needs no API key. Semantic search requires a configured remote embedding service or a local model. Remote embedding sends indexed conversation or code text to that service and may incur charges. See [environment configuration](docs/environment.md) and [local models](docs/local-model.md). Never put keys in the repository, command arguments, or conversation. Indexes can contain plaintext excerpts from conversations and source files.

Existing legacy config files remain readable. This package does not automatically remove previously registered MCP entries; remove any stale registration through the relevant client if needed.
