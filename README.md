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
`fifine-ref-classify`, `fifine-dev-done-flow`, and
`fifine-trellis-task-orchestrator`. The former AI research writing skill is
retired and is no longer published.

See [`skills.json`](skills.json) for the complete, machine-readable skill index.

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
```

Repository-level scripts live under `scripts/`, and `skills.json` serves as the root index for scanners.
