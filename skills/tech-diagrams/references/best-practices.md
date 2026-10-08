# Best Practices — Shared Rules for Every Diagram

> Cross-cutting rules that apply to **all** diagram types in this skill. Every
> deep reference in `diagram-types.md` assumes these. Read this first; each
> type's reference adds only what is specific to that type.

## 1. One diagram, one question, one audience

A diagram answers a single question for a single audience. If you're tempted to
answer two questions, make two diagrams. Scope creep is the most common cause of
an unreadable result. Pick the type whose *purpose* matches the reader's
question (see `diagram-types.md`).

## 2. Scope & altitude discipline

- Show only what the chosen level requires; push detail to the next level down
  (C1 → C2 → C3), or to a sibling diagram.
- Respect each type's **density limits**. If you're over, split by concern —
  never shrink the type to cram more in.
- Collapse detail you don't need with the **Collapsed-subsystem card** primitive
  (a single card standing in for N hidden elements) rather than drawing it all.

## 3. Labeling

- **Arrows are verb-led and directional** — describe what flows / who initiates,
  never "uses" or "connects to". Unidirectional only; the label implies the
  return.
- **Real resource/service names**, not generic placeholders.
- **Roles, never named individuals** on any diagram (e.g., "Finance & Sales", not
  a person's name).

## 4. Honesty & provenance (non-negotiable — client-confidential work)

Applies to **every number, logo, quote, credential, or proof point** on any
diagram, and most sharply to selling/exec artifacts:

- **No fabricated data.** Every metric, stat, $ figure, percentage, logo,
  testimonial, or proof point is either (a) traceable to a real source, or
  (b) **visibly labeled** `illustrative` / `target` / `projected` / `TBD`.
- When a figure is aspirational, hedge it in the label ("projected", "with X in
  place") — do not present a target as an achieved result.
- Uncommitted dates, scopes, or topologies are annotated **"illustrative — TBD"**.
- An invented figure on a client artifact is an integrity and credibility risk,
  not a design shortcut. When in doubt, label it or leave it off.

## 5. Legend & title

- **Every diagram has a legend** explaining colors, shapes, badges, and line
  styles actually used — even when notation seems obvious (diagrams get printed
  in B&W, shared without context, and read by colorblind viewers).
- **Every diagram has a title** in its type's stated format.
- Never rely on color as the *only* differentiator — pair it with a label, shape,
  or icon.

## 6. Status colors — one convention, everywhere

Use the **standardized status-color set** and the **Status badge** primitive
(defined in `styles/google-cloud.md` → Shared Visual Primitives) consistently
across types. Do not invent a new green/amber/red meaning per diagram; if a type
needs a domain-specific mapping, state it in that diagram's legend and keep the
palette identical.

## 7. Prefer primitives over bespoke templates

Before adding a new visual mechanism, check the **Shared Visual Primitives** in
`styles/google-cloud.md` (stat card, status badge, milestone/current-position
markers, collapsed-subsystem card, scope/posture callout). Reuse them. A
mechanism used by only one diagram type is a smell — either generalize it into a
primitive or drop it. This keeps the skill a small set of composable parts rather
than a sprawl of one-off templates.
