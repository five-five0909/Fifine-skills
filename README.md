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

Prefix names are filesystem-safe equivalents of logical namespaces such as `academic:humanizer`.

- `academic-*`: academic writing, literature search, reading, paper analysis, reference management, research review, and topic refinement.
- `document-paddleocr-vl`: parse PDFs, scans, screenshots, and images into Markdown.
- `writing-*`: writing roles and prompt refinement.
- `workflow-*`: guided development and Trellis task orchestration.
- `review-grill-me-cn`: pressure-test an idea or plan.
- `math-rethlas`: formal mathematics proof workflow.
- `media-transcript`: local audio/video transcription.
- `web-tavily-search`: live web search.
- `agent-trans-criptase`: session continuation and local code/document retrieval.

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
