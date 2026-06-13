---
name: llm-research-grill
description: >
  Rigorous self-grilling for LLM, PyTorch, datasets, papers, and experiments.
  Run interactive script to collect user's research state, generate structured grill report, then act on it.
  Use when the user wants to clarify an ML/LLM research direction, inspect dataset structure, debug PyTorch/HF training,
  read papers critically, design experiments, or prepare thesis/defense.
---

# LLM Research Grill

## Core flow

1. Run `python scripts/grill.py --mode <mode>`, script asks questions and collects answers
2. Script outputs a structured grill report (markdown)
3. Read the report, judge each answer, score, and assign next actions

## When to use which mode

| User state | Script | Description |
|---|---|---|
| "I want to do LLM research but don't know the problem" | `grill.py --mode direction` | Problem/direction triage |
| "I have a dataset but it's unclear" | `grill.py --mode dataset` | Dataset interrogation |
| "I'm using PyTorch/HF but something is wrong" | `grill.py --mode framework` | Framework/code audit |
| "I read a paper, force me to connect it" | `grill.py --mode literature` | Paper/book grilling |
| "I have an experiment plan, review it" | `grill.py --mode experiment` | Experiment design review |
| "I need to defend my proposal" | `grill.py --mode defense` | Defense prep |
| "Grill everything" | `grill.py --mode mixed` | Full research grill |

## After script output

1. Read the script-generated report
2. Judge each answer: good / weak / missing
3. For weak answers, ask follow-up questions
4. For missing answers, mark as risk
5. Score 0-5 per dimension (see rubric below)
6. Assign research sprint: today / this week / evidence to bring back

## Score rubric

| Score | Meaning |
|---:|---|
| 0 | Absent; not defined |
| 1 | Vague; keywords only |
| 2 | Partial; cannot guide implementation |
| 3 | Workable; small experiment possible with risk |
| 4 | Strong; defensible for advisor review |
| 5 | Publication/defense-ready |

## Output format

```markdown
## Research State Snapshot
| Dimension | Status | Evidence/Gap |
|---|---|---|

## Grill Results
[Per-answer judgment from report]

## Scoreboard
| Dimension | Score /5 | Reason | Next action |
|---|---:|---|---|

## 24-Hour Sprint
- Today: ...
- This week: ...
- Evidence to bring back: ...
```
