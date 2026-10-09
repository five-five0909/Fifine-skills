---
name: fifine-visual-creation-orchestrator
description: Scientific-question-driven figure planner and orchestrator for AI, machine learning, deep learning, LLM, RAG, Agent, computer vision, and systems papers targeting NeurIPS, ICML, ICLR, ACL, CVPR, AAAI, Nature Machine Intelligence, TPAMI, JMLR, and Nature-family venues. Use to select from an 18-category, 180-type figure registry, design Nature/NMI multi-panel evidence chains, choose R/Python/Graphviz/interactive/generative backends, and delegate execution to installed visual skills without fabricating empirical evidence.
---

# AI Paper Figure Planner and Orchestrator

## Role

Turn a scientific question into a defensible publication figure plan. Select figure types from the registry, build a non-redundant multi-panel evidence chain, assign one composition owner plus any specialist panel producers, choose the rendering backend, and delegate execution. Do not replace downstream rendering workflows or invent experimental results.

## Progressive loading

- Read `references/orchestration-contracts.md` when planning a figure, selecting style/backend, or reviewing evidence integrity.
- Use `scripts/figure_registry.py` instead of loading all 180 records when searching or recommending figure types.
- Read individual downstream skills only after the plan assigns their role.

## Workflow

### 1. Establish the figure contract

Capture:

- target venue and role: main figure, supplementary figure, method overview, graphical abstract, presentation, or interactive explorer;
- core scientific question and provisional one-sentence claim;
- available data/evidence, unit of analysis, groups, pairing, seeds/folds, uncertainty, and source assets;
- whether the output is empirical, conceptual, interactive, or mixed;
- user-specified chart or backend, if any.

If the user supplies data without a scientific question, ask what the reader should learn before rendering. Explicit export-only, reproduction, or cosmetic-edit requests may bypass this question gate.

### 2. Decompose the claim into evidence roles

Choose only roles needed to defend the claim: setup/method, primary benchmark, baseline comparison, training dynamics, ablation, sensitivity, robustness, OOD, uncertainty, calibration, error analysis, interpretability, representation/mechanism, scaling/efficiency, qualitative examples, safety/alignment, retrieval/agent behavior, or systems deployment.

### 3. Query the 180-type registry

Use:

```bash
python3 "{SKILL_DIR}/scripts/figure_registry.py" search --question "<question>" --limit 10
```

For structured recommendations, create an input JSON outside the skill directory and run:

```bash
python3 "{SKILL_DIR}/scripts/figure_registry.py" recommend --input-json "<request.json>" --limit 3
```

Validate user-requested chart types too. Reject a type whose data or design assumptions are unavailable, explain why, and recommend valid alternatives.

Rank candidates by:

1. direct answer to the scientific question,
2. data/design compatibility,
3. evidence strength and integrity,
4. reviewer interpretability,
5. multi-panel complementarity,
6. Nature/NMI venue and style fit,
7. implementation cost.

### 4. Build the multi-panel argument

Each panel must answer a unique sub-question. Record registry ID, evidence role, source data, selection reason, rejected alternatives, hero/supporting/control importance, semantic owner, renderer, style, and integrity checks.

A common AI-paper narrative is method/setup → main result → mechanism/training/representation → ablation → robustness/OOD/uncertainty → efficiency/scaling/deployment. Use it only when it matches the claim. Prefer one hero panel with subordinate evidence for Nature-family main figures; use equal grids only for equal-weight evidence.

Remove a panel when it repeats another question, can be derived from another panel, merely restyles the same values, or does not weaken the claim when deleted.

### 5. Assign composition and specialist owners

- `nature-figure`: strict single-backend Nature/high-impact workflow.
- `academic-figure-skill`: multi-panel planning, production assets, statistics, composition, and formal QA.
- `scientific-figure-making`: known matplotlib publication plot and house style.
- `stem-illustration`: scientific mechanism, graphical abstract, and STEM schematic semantics.
- `tech-diagrams`: model architecture, software, systems, RAG/Agent, deployment, and tool-flow semantics.
- `generative-ui`: interactive HTML/SVG/Chart.js/UI.
- `baoyu-image-gen`: provider execution fallback, not the semantic owner of empirical results.

Use exactly one composition owner for the final deliverable. Add specialist producers only for genuinely different modalities, such as a schematic panel plus quantitative result panels.

### 6. Choose the rendering backend

Prefer R when R and Python are scientifically equivalent:

- `ggplot2` / `ggdist` for comparisons, distributions, uncertainty, calibration, regression, robustness, and scaling;
- `ComplexHeatmap` for annotated matrices;
- `patchwork` / `cowplot` for Nature/NMI panel composition.

Use Python when there is a concrete reason: PyTorch/TensorFlow tensors, pixel-level CV assets, Grad-CAM, feature maps, masks, diffusion trajectories, Python-only pipelines, custom matplotlib geometry, or a downstream matplotlib contract. Record the reason for choosing Python over an equally viable R path. Avoid unnecessary cross-language mixing in one static figure.

Use Graphviz/TikZ/SVG for exact architecture, computation, RAG/Agent, trace, and deployment diagrams. Use `generative-ui` for interactive browser output.

Use a runtime-exposed `magpie-image` tool only for genuinely generative pixels: conceptual illustrations, graphical abstracts, covers, artistic assets, and non-evidentiary schematic elements. Follow its actual exposed name and schema; never guess them. If unavailable, use the semantic owner's renderer, then `baoyu-image-gen` where appropriate.

Never use a generative engine to fabricate benchmarks, confusion matrices, statistical plots, heatmaps, microscopy evidence, blots, gels, or quantitative results.

### 7. Apply Nature/NMI style and QA

Default to `NMI_PASTEL` for ML/AI comparisons and `NATURE_CLASSIC` for broad Nature-family work. Use `CNS_RESTRAINED`, `NATURE_IMAGING`, `NATURE_MATERIAL`, `NATURE_CLINICAL`, `NATURE_GENOMICS`, or `NATURE_SYSTEMS` when the content requires it.

Load the exact palette and integrity rules from `references/orchestration-contracts.md`. Preserve semantic colors across panels, use 2–4 main colors plus one accent, avoid default/rainbow palettes, and prefer editable SVG/PDF masters plus a 300 dpi preview.

## Registry commands

```bash
python3 "{SKILL_DIR}/scripts/figure_registry.py" validate
python3 "{SKILL_DIR}/scripts/figure_registry.py" categories
python3 "{SKILL_DIR}/scripts/figure_registry.py" show fig-127
python3 "{SKILL_DIR}/scripts/figure_registry.py" search --category reliability --backend r
```

## Output contract

For a simple figure, omit empty fields. For a manuscript figure, report:

```text
SCIENTIFIC_QUESTION=
FIGURE_CLAIM=
TARGET_VENUE=
FIGURE_SELECTION=<registry IDs and names>
SELECTION_RATIONALE=
REJECTED_ALTERNATIVES=
PANEL_PLAN=
COMPOSITION_OWNER=
SPECIALIST_PRODUCERS=
STATIC_BACKEND=
GENERATIVE_ENGINE=
STYLE_PROFILE=
INTEGRITY_REQUIREMENTS=
ENGINE_FALLBACK=
DELIVERABLES=
NEXT=
```
