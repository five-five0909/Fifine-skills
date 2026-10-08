# Comparison / Split-Screen Diagram Reference

> Deep reference for Comparison diagrams (split-screen, before/after, side-by-side). Supplements `diagram-types.md` with guidance from visual comparison theory, consulting conventions, and cloud migration patterns.
>
> **Sources**: Gleicher's taxonomy of visual comparison, Tufte's small multiples, McKinsey/Deloitte presentation conventions, Google Cloud Architecture Center, cognitive load research.

## What is a Comparison Diagram?

A comparison diagram shows **two or more states side-by-side** — current vs. future, option A vs. option B, or before vs. after migration. It answers: "What changes and what stays the same?"

- **Scope**: Two (or occasionally three) states of the same system or decision
- **Primary technique**: Juxtaposition — placing states side by side with shared spatial structure
- **Audience**: Executives, steering committees, decision-makers — anyone evaluating a change
- **Key insight**: The diagram's value comes from what differs, not what's shown

## When to Use

- **Before/after migration**: Current architecture → target architecture
- **Option comparison**: Two competing approaches for a decision
- **Progress tracking**: Design-time vision vs. current implementation state
- **Gap analysis**: What exists vs. what's needed
- **Technology evaluation**: Incumbent stack vs. proposed replacement

## Core Layout Patterns

### Pattern 1: Side-by-Side Split-Screen
Two panels separated by a vertical divider. Shared elements maintain position across panels.

```
┌─────────────────────┬─────────────────────┐
│    CURRENT STATE     │    FUTURE STATE      │
│                      │                      │
│  ┌───┐    ┌───┐     │  ┌───┐    ┌───┐     │
│  │ A │───→│ B │     │  │ A │───→│ B'│     │
│  └───┘    └───┘     │  └───┘    └───┘     │
│       ↓             │       ↓              │
│  ┌───────┐          │  ┌───────┐ ┌─────┐  │
│  │   C   │          │  │  C'   │ │ NEW │  │
│  └───────┘          │  └───────┘ └─────┘  │
└─────────────────────┴─────────────────────┘
         ← shared vertical axis →
```

### Pattern 2: Stacked (Top/Bottom)
Current state on top, future state below. Better for wide architectures.

### Pattern 3: Graduated Transition
Three+ panels showing phases: Current → Phase 1 → Phase 2 → Target. Use sparingly — more than 3 panels dilutes impact.

## Composition Rules

### Shared Structure Principle
- **Identical spatial layout** for shared elements across both panels — same position, same size
- Elements that exist in both states must occupy the **same coordinates** in each panel
- This creates a visual "diff" — the eye naturally detects what moved, changed, or appeared

### Marking Changes
- **New elements**: Highlight with accent color (green border, bold outline, or colored fill)
- **Removed elements**: Show as ghosted/greyed-out in the "after" panel (don't just delete — the absence is the point)
- **Modified elements**: Use a distinct color treatment (amber/yellow border) with the change annotated
- **Unchanged elements**: Muted/grey treatment — present for context but not the focus

### Change Summary
- Include a **change callout panel** below or between the two states
- List key differences as bullet points with directional indicators (→ changed to, + added, − removed)
- Quantify where possible: "5 services → 3 services", "$65K/year → $9K/year"

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Elements per panel | 5–7 | 9 |
| Total elements (both panels) | 10–14 | 18 |
| Arrows per panel | 5–8 | 12 |
| Change annotations | 3–5 | 7 |

If either panel would exceed 9 elements, the diagram needs to be split into focused views (e.g., one comparison for compute, another for data tier).

## Layout Rules

### Panel Design
- **Equal panel width** — never make one side bigger (implies preference or importance)
- Clear **panel headers** at the top: "Current State" / "Target State" or "Option A" / "Option B"
- Vertical divider line between panels — dashed grey, not bold
- **Shared legend at bottom** (not duplicated in each panel)

### Visual Weight
- "After" or "recommended" panel can use slightly richer colors, but the structural layout must be identical
- Never use the layout itself to argue for one option — let the content speak

### Spatial Anchoring
- Choose a spatial grammar from the existing diagram types (C2-style, network-style, data-flow-style) and apply it identically to both panels
- External actors/systems at the same edges in both panels
- Data stores in the same position in both panels

## Color Conventions

| State | Color Treatment |
|-------|----------------|
| Unchanged element | Light grey fill (#F1F3F4), grey border (#9AA0A6) |
| New/added element | Green border (#34A853), white or light green fill |
| Removed element | Dashed border, greyed out (#E8EAED fill), strikethrough text |
| Modified element | Amber/yellow border (#F29900), white fill |
| Panel headers | Bold text, no background color (keep clean) |
| Divider line | Dashed grey (#DADCE0) |

## Arrow Conventions

- Use the **same arrow style** in both panels (solid for sync, dashed for async)
- New connections: accent color (matches new element color)
- Removed connections: greyed dashed line with strikethrough or omitted entirely
- Label arrows only where the interaction changes — don't re-label unchanged arrows

## Title Format

`PROJECT — Comparison: [Current/Future | Option A/Option B | Before/After]`

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Different layouts per panel | Use identical spatial structure — changes should be visible through content differences, not layout rearrangement |
| All elements highlighted | Only mark what changed — if everything is different, you're comparing two different systems, not showing a migration |
| No change summary | Always include a callout listing the key differences |
| Panels with different element counts but no ghost elements | Show removed elements as ghosts so the viewer sees what disappeared |
| More than 3 panels | Stick to 2 panels for before/after; use a roadmap diagram for multi-phase |
| Biased panel sizing | Panels must be equal width regardless of content density |
| Unlabeled divider | Always label what each panel represents |
| Too many change annotations | Focus on 3–5 key changes, not every modification |
| Color without redundant encoding | Don't rely on color alone — add labels like "NEW", "REMOVED", or border style changes |
| Forgetting the legend | Include a legend explaining the color/border conventions for change types |
