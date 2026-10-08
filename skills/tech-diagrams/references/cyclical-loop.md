# Cyclical / Measurement Loop Diagram Reference

> Deep reference for Cyclical and Measurement Loop diagrams (DevOps infinity loops, FinOps cycles, flywheel diagrams, PDCA). Supplements `diagram-types.md` with guidance from operational process models, FinOps/tokconomics patterns, and circular diagram design theory.
>
> **Sources**: DevOps infinity loop conventions, FinOps Foundation lifecycle, Amazon flywheel model, Deming PDCA/OODA cycles, MLOps lifecycle, Balanced Scorecard strategy maps, circular diagram best practices.

## What is a Cyclical/Loop Diagram?

A cyclical diagram shows **a repeating process that feeds back into itself** — each stage's output drives the next, creating continuous improvement or operational rhythm. It answers: "How does this process sustain and improve itself?"

- **Scope**: One complete operational cycle with its feedback mechanism
- **Primary shape**: Circle, infinity loop (figure-eight), or ring of connected nodes
- **Audience**: Operations teams, leadership, anyone who needs to understand a continuous process
- **Key insight**: The circle communicates that the process never stops — there is no "done"

## When to Use

- **Operational lifecycles**: DevOps, MLOps, FinOps, tokconomics
- **Continuous improvement**: PDCA, Kaplan-Norton strategy cycles
- **Flywheel models**: Self-reinforcing growth or efficiency loops
- **Cost/performance optimization**: Measure → analyze → optimize → measure
- **Feedback systems**: Any process where outputs become inputs

## Layout Patterns

### Pattern 1: Circular Ring
Nodes arranged in a circle with curved arrows between them. Simplest and most universal.

```
        ┌──────┐
   ┌────│Ingest │────┐
   │    └──────┘    │
┌──┴───┐         ┌──┴──┐
│Report│         │Parse │
└──┬───┘         └──┬──┘
   │    ┌──────┐    │
   └────│Enrich│────┘
        └──────┘
```

### Pattern 2: Infinity Loop (Figure-Eight)
Two linked loops (e.g., DEV/OPS, BUILD/RUN) joined at a crossover point. Shows two interdependent cycles.

### Pattern 3: Spiral
A circular path that doesn't close — each revolution advances upward or outward, showing cumulative improvement over time (Deming's "PDCA rolling uphill").

## Core Elements

| Element | Visual Treatment | Description |
|---------|-----------------|-------------|
| **Stage node** | Rounded rectangle or segment on the circle | One step in the cycle (e.g., "Inform", "Optimize", "Operate") |
| **Directional arrow** | Curved arrow following the arc | Shows flow direction (always clockwise) |
| **Center element** | Circle/icon at the center of the ring | The core purpose, primary artifact, or key metric |
| **Annotation callout** | External text box connected by leader line | Metrics, KPIs, or detail for a specific stage |
| **Feedback arrow** | Arrow cutting across the circle (dashed) | Shortcut or exception feedback (trigger-based restart) |
| **External input/output** | Arrow entering/exiting the circle | Data or events that enter or leave the cycle |

## Composition Rules

### Node Count
| Count | Character | Best For |
|-------|-----------|----------|
| 3 | Strategic, high-level | Executive summaries, flywheel models |
| 4 | Sweet spot for clarity | PDCA, FinOps Inform/Optimize/Operate + Govern |
| 5–6 | Balanced detail | DevOps lifecycle, MLOps stages |
| 7–8 | Maximum before splitting | Full DevOps (Plan/Code/Build/Test/Release/Deploy/Operate/Monitor) |
| 9+ | Avoid | Split into sub-cycles or use a different diagram type |

### Clockwise Convention
- **Always flow clockwise** — this matches reading convention and feels natural
- **Start at 12 o'clock** or slightly right of top (1 o'clock position)
- Number stages sequentially if temporal ordering matters

### Center Element
The center of the ring should contain one of:
- **Core purpose**: The "why" of the cycle (e.g., "Growth", "Cost Efficiency")
- **Primary artifact**: What the cycle produces/refines (e.g., "Model Registry", "Agent Performance")
- **Key metric**: The top-level KPI that the cycle drives (e.g., "Cost per Token")
- **Process name**: The cycle's title if not already in the diagram title

### Dual-Label Pattern (for Measurement Loops)
Each node carries two pieces of information:
1. **What it IS** — the activity or stage name (inside the node)
2. **How it is MEASURED** — the KPI or metric (as an annotation below or beside the node)

Example: Node says "Optimize" → Annotation says "$/1K tokens, latency P95, cache hit rate"

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Stage nodes | 4–6 | 8 |
| Annotation callouts | 3–4 | 6 |
| External inputs/outputs | 1–2 | 4 |
| Feedback arrows (cross-circle) | 0–1 | 2 |
| Items within any annotation | 3–4 | 5 |

## Layout Rules

### Spacing
- **Equal angular intervals** between nodes (e.g., 4 nodes = 90° apart, 6 nodes = 60° apart)
- Nodes should be evenly sized
- Maintain consistent gap between nodes and the connecting arrows

### Arrows
- **Curved arrows** that follow the circle's arc — never straight lines cutting across
- Arrow heads at the receiving end of each connection
- Arrow labels (if any) placed on the outside of the curve, not inside
- For feedback arrows that cross the circle, use **dashed style** to distinguish from the main flow

### Annotations and Callouts
- Place callout boxes **outside the circle**, connected by thin leader lines
- Standard position: below-right of the associated node
- Keep callout text brief (2–4 bullet points maximum)
- Use consistent callout box style throughout

### Color Conventions
Choose one approach:
- **Sequential gradient**: Colors progress around the circle (e.g., light blue → blue → dark blue → indigo)
- **Domain-based**: Each node colored by its functional area (e.g., blue for technical stages, green for business stages)
- **Emphasis**: One node in accent color to highlight the current focus or most critical stage; others in neutral tones

### Showing Leakage or Failure
- **Tangential outbound arrows** from a node: Shows where the cycle can break (data drops off, cost spike, failure)
- Use **warm colors** (amber, red) for leakage arrows
- **Dashed lines** for potential/conditional leakage vs. solid for actual flow

## Title Format

`PROJECT — [Cycle Name] Loop` or `PROJECT — [Process Name] Lifecycle`

## Specific Pattern: Tokconomics Measurement Loop

For ADF tokconomics (the primary ADF use case):
- **Recommended nodes**: 4–5 (Measure → Analyze → Optimize → Operate → Measure)
- **Center element**: "Token Cost Efficiency" or "$/1K tokens"
- **Annotations**: Map each stage to concrete metrics:
  - Measure: Token consumption, latency percentiles, cache hit/miss
  - Analyze: Cost attribution by agent/tool/model, waste identification
  - Optimize: Prompt compression, caching strategies, model routing
  - Operate: Budget alerts, auto-scaling thresholds, guardrails
- **External inputs**: Usage data from inference project, cost data from billing
- **External outputs**: Optimization recommendations, budget alerts, executive dashboards

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Straight arrows between circle nodes | Use curved arrows that follow the arc |
| Uneven node spacing | Place nodes at equal angular intervals |
| No center element | Always include a center focal point |
| Too many feedback arrows | Limit cross-circle arrows to 1–2 maximum |
| Clockwise/counter-clockwise inconsistency | Always use clockwise flow |
| Starting at arbitrary position | Start at 12 o'clock (or 1 o'clock) |
| Annotations cluttering the interior | Place all annotations outside the circle |
| Equal visual weight on all nodes | Emphasize the current focus or entry point |
| No metric annotations on a "measurement" loop | Every node should show what is measured at that stage |
| Overly complex single cycle | Split into primary cycle + sub-cycles rather than cramming 9+ stages |
