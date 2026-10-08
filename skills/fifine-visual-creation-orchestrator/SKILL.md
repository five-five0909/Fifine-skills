---
name: fifine-visual-creation-orchestrator
description: Global visual-creation routing skill. Use for any request to draw, generate, edit, polish, audit, or export an image, chart, scientific figure, technical diagram, STEM illustration, HTML/SVG widget, UI mockup, or publication visual; classify the desired output and delegate to the correct installed visual skill without duplicating its workflow.
---

# Visual Creation Orchestrator

## Role

Act only as the routing front door. Select one downstream visual skill, explain the choice briefly, then follow that skill. Do not perform environment checks, dependency installation, provider setup, MCP detection, or generation logic here; the selected downstream skill owns those details.

## Workflow

1. Identify the requested visual deliverable and whether the user wants creation, editing, review, or export.
2. Respect an explicitly named downstream skill unless it is clearly incompatible with the requested deliverable.
3. Select exactly one primary route using the precedence below.
4. State `ROUTE=<skill>` and one sentence explaining why.
5. Load or invoke the selected skill and follow its complete workflow, including its own questions, environment requirements, generation method, QA, and export rules.
6. Use a second skill only when the task contains two genuinely separate deliverables; state the order and boundary between them.

## Route precedence

| User need | Route |
|---|---|
| Interactive controls, browser-delivered HTML, Chart.js, editable SVG widget, UI mockup, Canvas animation | `generative-ui` |
| C4, software/cloud/network/security architecture, deployment topology, system sequence, technical data flow | `tech-diagrams` |
| Scientific mechanism, pathway, experimental workflow, anatomy/cell concept, STEM teaching illustration or scientific poster | `stem-illustration` |
| Photorealistic or artistic image, reference-image editing, general text-to-image, multi-provider or batch image generation | `baoyu-image-gen` |
| Conventional data-driven matplotlib figure for a paper, report, or slide | `scientific-figure-making` |
| Full manuscript-figure workflow with panel planning, production-asset reuse, statistics reporting, and formal QA | `academic-figure-skill` |
| Explicit Nature/high-impact workflow requiring one exclusive Python or R backend, or explicit `nature-figure` request | `nature-figure` |

## Overlap rules

- Choose `generative-ui` when interaction, browser delivery, HTML, UI, or editable web SVG is part of the output.
- Choose `tech-diagrams` for software and infrastructure semantics, including C4, network boundaries, deployment, and cloud systems.
- Choose `stem-illustration` for scientific and educational concepts that are illustrated rather than plotted from measured data.
- Choose `baoyu-image-gen` for general-purpose generated imagery, reference-image transformations, and provider-based image batches.
- Choose `scientific-figure-making` for direct publication-style matplotlib plots when the user already knows the chart or data story.
- Choose `academic-figure-skill` for a complete manuscript figure composed from multiple panels, assets, statistics, or mixed plotting workflows.
- Choose `nature-figure` when the user explicitly requests it, explicitly requires a single Python/R backend, or wants its figure-contract workflow.
- When `nature-figure` is selected and the request does not already specify Python or R, preserve its blocking question: **“Python or R?”** Do not infer a default.
- If the user asks only for a prompt, brief, layout plan, or critique, still route by visual semantics; the downstream skill decides whether generation is necessary.

## Multi-deliverable requests

Use two routes only when outputs are independently useful. Examples:

- A system architecture diagram plus an interactive product mockup: `tech-diagrams` first, then `generative-ui`.
- A manuscript data figure plus a graphical abstract: `academic-figure-skill` first, then `stem-illustration`.
- A STEM mechanism illustration plus photorealistic cover art: `stem-illustration` first, then `baoyu-image-gen`.

Do not chain skills merely because their trigger words overlap.

## Output contract

Before delegation, report:

```text
ROUTE=<primary-skill>
DELIVERABLE=<short description>
WHY=<one concise routing reason>
NEXT=<invoke/follow the selected skill>
```

For a genuine multi-deliverable request, add:

```text
SECONDARY_ROUTE=<skill>
BOUNDARY=<what the secondary skill produces>
```
