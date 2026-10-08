# Roadmap / Milestone Timeline Diagram Reference

> Deep reference for Roadmap and Milestone-Timeline diagrams (delivery journeys,
> maturity paths, rollout plans, adoption programs). Supplements
> `diagram-types.md` and assumes the shared rules in `references/best-practices.md`.
>
> **Sources**: SAFe roadmaps (framework.scaledagile.com/roadmap/), Atlassian
> product-roadmap conventions, Now/Next/Later roadmaps, Mermaid `timeline` and
> `gantt` (milestone-view) syntax.

## What is a Roadmap Diagram?

A roadmap shows **a sequence of phases advancing toward a target state over
time** — each phase moves the work closer to the destination, marked by the
milestones that gate progress between them. It answers: "What is the journey from
where we are to where we're going, and in what order?"

- **Scope**: One delivery / adoption / maturity journey, start to target state
- **Primary shape**: Horizontal phase bands (left = now, right = target) with milestone markers
- **Audience**: Executives, steering committees, delivery leads, sponsors funding the work
- **Key insight**: Time runs left-to-right and one-directional — a roadmap has a
  beginning and a destination, and it never returns to start.

## When to Use

- **Delivery journeys**: Pilot → scale → productionize → replicate
- **Maturity / capability paths**: Read-only → assisted → selective automation → full automation
- **Rollout waves**: Group A → Group B → Group C, expanding reach each wave
- **Adoption programs**: Proof of value → limited GA → broad GA
- **Any plan whose value is the SEQUENCE and the GATES between stages**

**Do NOT use for** detailed task schedules or dependency-heavy Gantt charts — a
roadmap is a phase-level summary, not a work breakdown or a critical-path plan.
Related types:

- Repeating operational process → `cyclical-loop.md` (the opposite shape: a ring
  that returns to start, not a line to a destination).
- Two-state before/after → `comparison.md` (which points here when a change spans
  more than three phases).
- Question-driven selection → `decision-tree.md`.

## Core Elements

| Element | Shape | Description |
|---------|-------|-------------|
| **Phase band** | Wide rounded rectangle / horizontal zone | One stage of the journey — carries a name, one progress signal, and 2–4 key activities |
| **Milestone marker** | Small diamond or `Material: Flag` | A dated, verifiable event gating entry to the next phase — the **Milestone marker** primitive (see `styles/google-cloud.md`) |
| **Time axis** | Horizontal ruler or implicit left-to-right ordering | Left = now, right = target. Absolute dates (if committed) or relative labels (Q1/Q2, Phase 1/2/3) |
| **Swimlane** (optional) | Horizontal track spanning all phases | A workstream tracked across phases (e.g., "Compliance", "Automation") |
| **Progress signal** | Figure or badge inside a phase | One concrete indicator of advancement in that phase — a status badge, a scope figure, or a capability turned ON |
| **Current-position marker** | Vertical accent line + pin | The present point on the timeline — the **Current-position ("you are here") marker** primitive |
| **Scope callout** | Yellow annotation box | Scope, posture, or caveat — the **Scope / posture callout** primitive |

Status colors, status badges, milestone markers, and the current-position marker
are **shared primitives** — use them as defined in `styles/google-cloud.md` →
Shared Visual Primitives; do not re-specify their colors or shapes here.

## Composition Rules

### Phase Design
- **Phase name** as the band header (bold), with journey-stage semantics —
  "Pilot", "Scale", "Automate", "Replicate" (not "Phase 1/2/3" alone).
- **One concrete progress signal per phase** — a scope figure, a status badge, or
  a capability that turns ON. This is what makes a roadmap concrete rather than a
  list of labels. Keep the signal comparable across phases where it is a figure.
- **2–4 key activities** per phase, no more — the phase is a summary.
- Phases read strictly **left-to-right** and each must **advance toward the target
  state** — never a reset. Cumulative growth (Phase N contains everything from
  Phase N-1 plus more) applies **only when the journey itself is a rollout or
  maturity path**; a plain delivery sequence advances without necessarily
  accumulating volume.

### Milestones
- Place milestone markers **on the boundary between phases** (the gate), or at a
  dated point inside a phase.
- Every milestone is **verifiable and named** — "Pilot exit: validated on initial
  cohort", not "Milestone 1".
- **1 milestone per phase boundary; usually 2–6 total.** A gating milestone states
  its **exit criteria** — what "done" means to enter the next phase.

### Swimlanes (optional — use only for 2–4 genuinely parallel tracks)
- Each lane spans **all phases** left-to-right; the lane label sits on the far left.
- Use lanes when distinct workstreams advance at different rates (e.g., one lane
  ships early while another lights up only in a later phase).
- Do NOT use lanes just to fit more boxes — a single journey (one lane) is the
  common case.

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Phases | 3–5 | 6 |
| Swimlanes | 1 (single journey) or 2–3 | 4 |
| Milestones total | 2–6 | 8 |
| Key activities per phase | 2–4 | 5 |
| Progress signals per phase | 1 | 2 |
| Annotation callouts | 3–5 | 7 |
| Text per activity line | 4–10 words | 15 words |

If you exceed 6 phases, group into **epochs** (Near / Mid / Long term) as linked
sub-roadmaps, or drop to a Now/Next/Later banding.

## Layout

Left-to-right phase columns/bands, with optional horizontal swimlanes crossing
every phase. Current phase emphasized; target phase visually distinct.

```
 PROJECT — Roadmap: <Journey Name>                        [ ▲ you are here ]
 ┌──────────┬──────────────┬──────────────┬──────────────┐
 │  PILOT   │    SCALE     │   AUTOMATE   │   REPLICATE   │   ← phase bands
 │ (current)│              │              │  (target)     │
 │ signal   │ signal       │ signal       │ signal        │
 │ • act 1  │ • act 1      │ • act 1      │ • act 1       │
 │ • act 2  │ • act 2      │ • act 2      │ • act 2       │
 └────◆─────┴──────◆───────┴──────◆───────┴──────◆────────┘
      gate         gate           gate           gate       ← milestones on boundaries
 ── time ───────────────────────────────────────────────►
      (optional swimlanes span all phases below:)
 Compliance │····│··········│··············│···············│
 Automation │    │          │██████████████│███████████████│
                                                     [ Scope callout ]
```

- **Direction**: strictly left-to-right. Time never flows right-to-left and never
  loops. If the plan repeats, it is a cycle (`cyclical-loop.md`), not a roadmap.
- **Phase bands** are the dominant element — full-width horizontal, generous
  height, ≥40px whitespace between bands and around markers.
- **Time axis**: optional thin ruler along top or bottom with phase boundaries
  marked. Use absolute dates only if committed; otherwise relative labels, and
  flag uncommitted dates "illustrative — TBD" (best-practices §4).
- **Emphasis**: current phase in saturated blue (`#E8F0FE`); future phases in
  lighter tints/grey; target/end-state phase can carry a distinct green accent
  (`#E6F4EA`) to read as the destination. Never rely on color alone — pair with a
  label (best-practices §5).
- Align milestone markers to a common baseline; keep every label legible even for
  a short phase.

## Naming Conventions

- **Phase names**: short noun/verb, journey-stage semantics — pair any number with
  a name ("Phase 2 — Scale", not "Phase 2").
- **Milestones**: dated, verifiable, outcome-worded — "Scale exit: broad-GA
  readiness signed off".
- **Progress signals**: concrete and comparable — a scope figure ("initial cohort
  → all groups"), a status badge, or a capability ("selective auto-writes ON").
- **Roles, never named individuals** on any lane or callout (best-practices §3).

## Title Format

`PROJECT — Roadmap: [Journey Name]`

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Roadmap drawn as a cycle | Roadmaps are linear with a destination — left-to-right bands, not a ring (`cyclical-loop.md`) |
| Used as a task schedule / dependency Gantt | Keep it phase-level; move task/dependency detail to a real Gantt |
| Phases that don't advance | Every phase must move toward the target; show the progress signal |
| "Phase 1/2/3" with no names | Name each phase by its journey stage; numbers alone say nothing |
| No progress signal | Add one concrete signal per phase — a figure, badge, or capability |
| Milestones with no exit criteria | Each gating milestone states what "done" means to enter the next phase |
| Committed-looking dates that aren't | Mark uncommitted dates "illustrative — TBD"; never imply false precision |
| >6 phases in one view | Group into epochs (Near/Mid/Long) or split into linked sub-roadmaps |
| Swimlanes used to cram boxes | Use lanes only for genuinely parallel workstreams; default is one journey |
| Reinventing badges/markers/colors | Reuse the shared primitives from `styles/google-cloud.md`; keep the status palette |
| Missing legend | Include a legend for phase states, milestone states, and badge meanings |

## Checklist

- [ ] **Single journey** — one start, one destination, strictly left-to-right
- [ ] **3–5 phases**, each with a name (not just a number)
- [ ] **One concrete progress signal** per phase, advancing toward the target
- [ ] **2–4 key activities** per phase, no work-breakdown clutter
- [ ] **2–6 milestones**, 1 per phase boundary, each with exit criteria
- [ ] **Current position marked** ("you are here") using the shared primitive
- [ ] **Uncommitted dates/scope** flagged "illustrative — TBD"
- [ ] **Emphasis** on current phase; target phase visually distinct
- [ ] **Status colors, badges, milestone/position markers** reused from `styles/google-cloud.md`
- [ ] **Legend included** for phase/milestone/badge conventions
- [ ] **Title follows format**: `PROJECT — Roadmap: [Journey Name]`
