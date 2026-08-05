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

All publishable skills use the `skills-<category>-<capability>` namespace.

- `skills-research-*`: topic refinement, literature search, radar tracking, paper reading, and hook extraction.
- `skills-writing-*`: evidence-backed paper drafting, section writing, prose humanization, style, and prompt refinement.
- `skills-review-*`: research, writing, and plan pressure tests.
- `skills-library-*`: reference classification and metadata-based renaming.
- `skills-workflow-*`: development workflow and Trellis orchestration.
- `skills-session-*`: transcript continuation and session handoff.
- `skills-convert-*`: document OCR and local media transcription.
- `skills-web-search`: live web search.
- `skills-math-proof`: formal mathematics proof workflow.

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
