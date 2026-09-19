# CLAUDE.md — Fifine-skills

This is a **skills package repository** for AI coding tools (Claude Code, Codex).
It contains reusable SKILL.md files and companion scripts distributed via npm.

---

## Project Structure

```
├── {skill-name}/          ← Each skill is a self-contained directory
│   ├── SKILL.md           ← Required: AI-readable skill definition
│   └── *.py / *.json      ← Optional companion files
├── scripts/
│   └── postinstall.js     ← npm postinstall: distributes skills to AI tool dirs
├── package.json           ← @fifine/skills npm package
├── AGENTS.md              ← Cross-tool usage documentation
└── .trellis/              ← Task management
```

---

## Adding a New Skill

Every skill needs at minimum:
```
{skill-name}/
└── SKILL.md    ← YAML frontmatter (name, description) + markdown body
```

SKILL.md frontmatter format:
```yaml
---
name: skill-name
description: >
  One-line description shown in skill picker.
  Trigger words: /skill-name, keyword1, keyword2.
---
```

---

## postinstall.js Behavior

When a consumer project runs `npm install github:five-five0909/Fifine-skills`:
1. Reads `skills.json` in consumer project (optional)
2. Auto-detects `.claude/`, `.codex/`, `.agents/` directories
3. Copies matching skills into `{tool-dir}/skills/{name}/`

---

## Runtime and performance rule

For long-running commands, background jobs, remote execution, benchmark/profiling, or performance
optimization, route to `fifine-adaptive-runtime-orchestrator`. Keep the detailed rule set canonical
in `skills/fifine-adaptive-runtime-orchestrator/SKILL.md` and
`skills/fifine-adaptive-runtime-orchestrator/references/performance-diagnosis.md` rather than
duplicating it here. Short form: detect the real runtime target, baseline before tuning, optimize
effective output instead of raw utilization, benchmark one main hypothesis at a time, preserve
correctness/reproducibility, and monitor hardware safety.

## Trellis Task System

```bash
python .trellis/scripts/task.py create "title" [--slug name]
python .trellis/scripts/task.py start <name>
python .trellis/scripts/task.py current
python .trellis/scripts/task.py finish
```

Use Trellis for tracking skill additions, postinstall improvements, and package maintenance.

---

## Install Command (for consumers)

```bash
npm install github:five-five0909/Fifine-skills
```
