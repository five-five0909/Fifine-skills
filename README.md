# Fifine Skills

A collection of reusable AI agent skills.

## Install

Depending on your `ccswitch` version, install from GitHub with either:

```bash
ccswitch add five-five0909/Fifine-skills
```

or:

```bash
ccswitch add https://github.com/five-five0909/Fifine-skills.git
```

If you use the `skills` CLI:

```bash
npx skills add five-five0909/Fifine-skills
```

This repository can also still be installed through npm:

```bash
npm install github:five-five0909/Fifine-skills
```

## Skills

All publishable skills use the `fifine-<original-name>` namespace. The prefix is
the only namespace marker; the remainder keeps the familiar skill name.

Examples include `fifine-live-humanizer`, `fifine-paper-weaver`,
`fifine-pdf-ref-classify`, `fifine-paper-idea-hook-forge`, and
`fifine-media-to-txt`. The former AI research writing skill is retired and is
no longer published.

See [`skills.json`](skills.json) for the complete, machine-readable skill index.

## Prompt Templates

This repository also includes reusable prompt templates under [`prompts/`](prompts/).
They are reference prompts, separate from installable skills, and are included in
the npm package for users who want to reuse or adapt them manually.

- [`BASE AGENTS.md`](prompts/BASE%20AGENTS.md): a general agent behavior and engineering workflow prompt.
- [`Claude Fable 5.md`](prompts/Claude%20Fable%205.md): a Claude-style system prompt reference.

## Development

```bash
npm run validate
```

## Structure

The collection follows this structure:

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/agents/openai.yaml
skills/<skill-name>/references/
skills/<skill-name>/scripts/
skills/<skill-name>/assets/
prompts/<prompt-name>.md
```

Repository-level scripts live under `scripts/`, prompt templates live under
`prompts/`, and `skills.json` serves as the root index for scanners.
