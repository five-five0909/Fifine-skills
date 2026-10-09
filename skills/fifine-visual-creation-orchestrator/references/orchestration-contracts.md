# AI Paper Figure Orchestration Contracts

Load this reference when selecting figure types, planning multi-panel figures, choosing a backend, or checking Nature/NMI submission quality.

## Scientific-question contract

Before rendering, establish:

- target venue and manuscript role,
- scientific question and one-sentence figure claim,
- available evidence and source data,
- unit of analysis, groups, pairing, seeds/folds, and uncertainty,
- whether the deliverable is empirical, conceptual, interactive, or mixed.

If data are supplied without a question, ask what the reader should learn. Export-only and explicit cosmetic-edit requests may bypass this gate.

## Candidate ranking

Rank compatible registry entries in this order:

1. direct answer to the scientific question,
2. compatibility with available data and experimental design,
3. strength and honesty of evidence,
4. reviewer interpretability,
5. complementarity within the panel narrative,
6. Nature/NMI venue and style fit,
7. implementation cost.

Reject a requested chart when its assumptions are unsupported. Explain the incompatibility and offer the nearest valid alternatives.

## Backend policy

Prefer R when R and Python are equally faithful:

- `ggplot2` / `ggdist`: comparisons, distributions, uncertainty, calibration, regression, robustness, scaling;
- `ComplexHeatmap`: annotated heatmaps and large matrices;
- `patchwork` / `cowplot`: precise Nature/NMI multi-panel composition.

Use Python for concrete reasons:

- PyTorch/TensorFlow tensors or a Python-only analysis pipeline,
- pixel-level CV composition, Grad-CAM, feature maps, masks, diffusion trajectories,
- custom matplotlib geometry or a downstream matplotlib contract.

Use Graphviz/TikZ/SVG for exact architecture, computation, RAG/Agent, tool trace, and deployment diagrams. Use `generative-ui` for interactive browser output.

Do not mix R and Python within one static figure without a real modality or asset reason. Record why Python was selected over an equally viable R path.

## Downstream ownership

- `nature-figure`: strict single-backend Nature workflow and figure contract.
- `academic-figure-skill`: multi-panel planning, production assets, statistics, composition, and formal QA.
- `scientific-figure-making`: known matplotlib publication plot and house style.
- `stem-illustration`: scientific mechanism, graphical abstract, and STEM schematic semantics.
- `tech-diagrams`: software, cloud, systems, RAG/Agent, and deployment semantics.
- `generative-ui`: interactive HTML/SVG/Chart.js/UI.
- `baoyu-image-gen`: provider execution fallback, not the semantic owner of empirical evidence.

One composition owner controls the final figure. Specialist producers are allowed only for genuinely different panel modalities.

## Generative engine policy

Use a runtime-exposed `magpie-image` tool as the preferred engine only for genuinely generative pixels: conceptual illustrations, graphical abstracts, covers, artistic assets, and non-evidentiary schematic elements.

- Use the exact runtime-exposed tool name and schema.
- Never guess its command, arguments, model, endpoint, or MCP configuration.
- If it is not exposed, use the semantic owner's supported renderer, then `baoyu-image-gen` where appropriate.
- Never generate benchmark plots, confusion matrices, heatmaps, microscopy evidence, blots, gels, or statistical results with a generative model.

## Nature/NMI style profiles

### NMI_PASTEL

Default for ML/AI quantitative papers and method-family comparisons. Reuse `nature-figure/references/api.md` `PALETTE_NMI_PASTEL`: low-saturation blue-violet, grey-blue, and soft pink families. Related model sizes share a hue family; green/red are reserved for directional deltas.

### NATURE_CLASSIC

Neutral-dominant Nature-family editorial styling: one signal family, one restrained accent, white background, deep-grey text, small lowercase panel labels, and asymmetric hero/supporting composition when evidence weights differ.

### CNS_RESTRAINED

Reuse `academic-figure-skill/references/color-palettes.md`: semantic blue, red, green, orange, purple, and grey; 2–4 main colors plus one accent; print-safe and colorblind-redundant.

### NATURE_IMAGING

Only for real imaging plates. Use black within image regions, grayscale context, cyan/magenta/white channels, consistent crops, overlays, and scale bars. Never fabricate microscopy.

### NATURE_MATERIAL / NATURE_CLINICAL / NATURE_GENOMICS

Reuse the matching profiles from `nature-figure/references/api.md` for materials, longitudinal clinical panels, and genomics/omics displays.

### NATURE_SYSTEMS

Use restrained flat fills, minimal icons, explicit trust/module boundaries, precise labels, and semantic colors shared with quantitative panels. Avoid cloud-marketing gradients, glow, heavy shadows, and decorative 3D.

## Global visual rules

- Use 2–4 main colors plus one small-area accent.
- A semantic color keeps the same meaning across all panels.
- Red is reserved for the strongest result, risk, or directional callout.
- Red/green cannot be the only critical encoding; add shape, line style, direct labels, facets, or ordering.
- Reject final use of ggplot hue defaults, matplotlib `tab10`/`tab20`, Excel defaults, `jet`, and rainbow palettes.
- Except for real imaging profiles, default to white background, deep-grey text, generous whitespace, and no decorative glow, thick shadow, or unnecessary gradient.
- Generative prompts must contain palette hex values, background, accent proportion, typography intent, and forbidden effects; “Nature style” alone is insufficient.

## Multi-panel contract

Plan:

- `figure_claim`, `figure_archetype`, `hero_panel`, `narrative_order`,
- `shared_semantics`, `style_profile`, `composition_owner`,
- `specialist_producers`, `final_backend`, `export_contract`.

Each panel records:

- label and registry ID,
- unique sub-question and evidence role,
- source data and selection reason,
- rejected alternatives,
- hero/supporting/control importance,
- semantic owner, engine, and integrity checks.

A common AI-paper narrative is method/setup → main result → mechanism/training/representation → ablation → robustness/OOD/uncertainty → efficiency/scaling/deployment. Use it only when it supports the actual claim. Prefer a hero panel with subordinate evidence for Nature-family main figures; use equal grids only for equal-weight evidence.

Remove a panel when it repeats the same question, can be derived from another panel, merely restyles the same values, or does not weaken the claim when deleted.

## Evidence-integrity contract

For every empirical panel:

- map each mark to source data,
- preserve declared runs, seeds, folds, classes, datasets, and methods,
- define sample unit, `n`, center, interval, test, and correction where applicable,
- disclose missing/failed runs and aggregation rules,
- distinguish train/validation/test and external datasets,
- keep comparable axes and scales honest.

AI/CS-specific checks:

- benchmark plots disclose task and metric aggregation;
- training curves distinguish raw observations from smoothing;
- ablation does not claim causality beyond the intervention;
- scaling plots separate observed ranges from fitted extrapolation;
- calibration requires probabilities and labels;
- OOD plots define ID/OOD datasets and score direction;
- t-SNE/UMAP geometry is not proof of high-dimensional separation;
- attention is not automatically a causal explanation;
- LLM evaluation discloses judge/rater protocol;
- RAG/Agent figures separate system structure from measured performance;
- systems figures define hardware, batch size, concurrency, latency, throughput, energy, and cost conditions.

Conceptual/generative panels must not invent model components, biological mechanisms, retrieval stages, causal arrows, or experimental evidence. Verify all labels after rendering.

## Export contract

For Nature/NMI submission work, prefer editable SVG/PDF masters for text and line art. Add 300 dpi PNG previews; use TIFF or other raster formats only when required by image content or journal submission. Keep fonts, panel labels, line weights, color semantics, and physical dimensions consistent across the full figure.
