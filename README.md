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
`fifine-media-to-txt`. `fifine-translation-multiple-kanban` handles
structured single- or multi-file translation with resumable JobID chunks and
selectable HTML/Markdown output. The imported `fifine-science-research-writing-skills`
skill provides an active STEMM paper-writing assistant for drafting, revising,
reviewing, and section-by-section guidance.

See [`skills.json`](skills.json) for the complete, machine-readable skill index.

## Prompt Templates

This repository also includes reusable prompt templates under [`prompts/`](prompts/).
They are reference prompts, separate from installable skills, and are included in
the npm package for users who want to reuse or adapt them manually.

### General prompts

- [`BASE AGENTS.md`](prompts/BASE%20AGENTS.md): general agent behavior and engineering workflow guidance.
- [`Claude Fable 5.md`](prompts/Claude%20Fable%205.md): a Claude-style system prompt reference.

### Product research and strategy

- [`competitive-analyst.md`](prompts/competitive-analyst.md)
- [`data-analyst.md`](prompts/data-analyst.md)
- [`product-director.md`](prompts/product-director.md)
- [`requirement-analyst.md`](prompts/requirement-analyst.md)
- [`roadmap-planner.md`](prompts/roadmap-planner.md)
- [`user-researcher.md`](prompts/user-researcher.md)

### Design and delivery

- [`critique-reviewer.md`](prompts/critique-reviewer.md)
- [`design-engine-team-lead.md`](prompts/design-engine-team-lead.md)
- [`design-system-expert.md`](prompts/design-system-expert.md)
- [`discovery-analyst.md`](prompts/discovery-analyst.md)
- [`export-specialist.md`](prompts/export-specialist.md)
- [`prototype-builder.md`](prompts/prototype-builder.md)

### Software engineering

- [`software-architect.md`](prompts/software-architect.md)
- [`software-engineer.md`](prompts/software-engineer.md)
- [`software-product-manager.md`](prompts/software-product-manager.md)
- [`software-qa-engineer.md`](prompts/software-qa-engineer.md)
- [`software-team-lead.md`](prompts/software-team-lead.md)

### Platform and operations

- [`database-optimization-expert.md`](prompts/database-optimization-expert.md)
- [`infrastructure-operations-expert.md`](prompts/infrastructure-operations-expert.md)
- [`security-expert.md`](prompts/security-expert.md)

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
