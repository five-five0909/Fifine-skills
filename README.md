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

- `dev-done-flow`: Use this skill when the user wants to start, plan, structure, diagnose, or iterate on a development task through a guided workflow.
- `grill-me-cn`: Use this skill when the user wants a rigorous idea or plan review before execution, especially for solution pressure tests, workflow audits, or identifying missing assumptions before committing to a direction.
- `idea-hook-forge`: Use this skill when the user wants to decompose a research paper PDF into structured components, extract hooks, and generate idea, experiment, and writing artifacts with an HTML report as the main output.
- `lit-speed-read`: Use this skill when the user needs a fast but structured reading workflow for a paper, URL, PDF, or HTML source, especially to summarize the core claim and generate a report for academic review.
- `llm-research-grill`: Use this skill when the user needs a rigorous audit of an LLM or PyTorch research direction, dataset, experiment, or paper understanding, especially before committing to implementation or defense.
- `media-transcript`: Use this skill when the user wants to transcribe a local video or audio file into plain text through ffmpeg and DashScope ASR. Reads `DASHSCOPE_API_KEY` from the environment by default.
- `paper-weaver`: Use this skill when the user wants a structured paper-reading pipeline driven from a PDF, especially to produce staged outputs for abstract, introduction, related work, method, formulas, and experiments.
- `paddleocr-vl`: Use this skill when the user wants to parse PDFs, screenshots, scans, images, or image-only documents into Markdown through the official PaddleOCR-VL AI Studio API.
- `parallel-executor-with-trellis`: Use this skill when the user has a large task that can be split into independent workstreams, especially for Trellis-managed planning, task decomposition, parallel execution, and final verification.
- `prompt-amplifier`: Use this skill when the user wants an instruction rewritten into a stronger execution prompt before handing it to another model or workflow, especially when adherence and precision matter.
- `ref-classify`: Use this skill when the user needs to classify research PDF references into predefined topic buckets, especially for batch organization of literature folders with fallback confirmation on uncertain matches.
- `ref-rename`: Use this skill when the user wants to batch rename research PDFs from extracted metadata, especially for incremental cleanup of literature libraries with user confirmation on naming choices.
- `tavily-search`: Use this skill when the user asks for current information, recent updates, documentation lookup, or fact verification, especially when a live web search is required instead of relying on stale model memory.
- `topic-refiner`: Use this skill when the user has a broad research direction, weak paper framing, or an unclear question, especially to turn raw ideas into a focused and defensible research problem.
- `rethlas`: Use this skill when the user wants to prove a math problem using the Rethlas AI-driven formal proof system.
- `trellis-task-orchestrator`: Use this skill when the user needs a Trellis-oriented task plan for implementation, bug fixing, refactoring, or spec work, especially to produce a PRD, execution steps, and acceptance checks.
- `humanizer`: Use this skill when the user wants to remove AI-generated writing patterns from text, making it sound more natural and human-written, based on Wikipedia's 33 AI writing pattern guide.
- `write-research-grill`: Use this skill when the user is preparing to write a paper, proposal, report, or argument and needs a structured pre-writing interrogation before drafting.
- `academic-radar`: Use this skill when the user wants to track the latest papers in a research direction (Mamba, SSM, hyperspectral, SOC, PINN, etc.) and generate an H1/H2/H3 priority HTML report via Node.js scripts calling arXiv, OpenAlex, and Semantic Scholar.
- `academic-search`: Use this skill when the user needs to search academic literature, query paper metadata (DOI, BibTeX, PDF, citations, code links), or perform discipline-aware multi-platform retrieval with deduplication and structured output.

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
