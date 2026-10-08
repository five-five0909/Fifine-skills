# Sequence Diagram Reference

> Deep reference for Sequence diagrams. Supplements `diagram-types.md` with guidance from UML best practices, C4 dynamic diagrams, Google Cloud Architecture patterns, and multi-agent system conventions.
>
> **Sources**: ZenUML, c4model.com (Simon Brown), CodeAnt AI, Creately, AWS multi-agent patterns, Google Cloud Architecture Center conventions.

## What is a Sequence Diagram?

A sequence diagram shows **how elements collaborate at runtime** to implement a specific scenario, use case, or feature. Time flows top-to-bottom. Participants are arranged left-to-right across the top with vertical lifelines. Horizontal arrows between lifelines show interactions in temporal order.

- **Scope**: One scenario, one user journey, one feature flow
- **Primary elements**: Participants (components, services, agents, external systems, people)
- **Audience**: Developers, architects, technical leads
- **C4 alignment**: Equivalent to a C4 "Dynamic Diagram" in sequence style

## When to Use

Use sequence diagrams **sparingly** — only for flows that are hard to understand from static diagrams (C1/C2/C3) alone. Good candidates:
- Multi-step orchestration with non-obvious ordering
- Flows involving delegation chains (agent → sub-agent → external system)
- Scenarios where the temporal ordering matters (e.g., "data must be fetched before prediction can run")
- Request-response lifecycles that cross multiple system boundaries

## Density Limits

| Element | Limit | Notes |
|---------|-------|-------|
| Participants | **6–9 max** | 7 ± 2 sweet spot (Miller's Law). Fewer is better. |
| Messages | **15–20 max** | Beyond ~20, vertical length kills comprehension |
| Fragment nesting | **1–2 levels max** | More than 2 nested alt/loop/par → split diagrams |
| Return arrows | **Always show** | Omitting returns creates sync/async ambiguity |

If over limits, split by: sub-scenario, phase, or use `ref` fragments to point to sub-sequences.

## Participant Ordering

1. **Initiator (person/client) on the far left**
2. **Remaining participants left-to-right by first appearance** in the flow
3. **Terminal systems (databases, external APIs) on the far right**
4. This ordering minimizes arrow crossing — arrows mostly flow left-to-right

## Labeling Convention

### Participants
- **Short, role-based names**: "Root Agent", "Databricks", "Business User" — not instance names or class names
- **Must match C4 static model**: Use the exact same names from your C1/C2/C3 diagrams
- **Include technology subtitle**: Same two-line card format as static diagrams (name + technology/role)

### Messages (Arrow Labels)
- **Every arrow MUST have a label** — never leave arrows unlabeled
- **Verb-phrase format**: "Delegates prescriptive question", "Queries bot APIs", "Returns prediction"
- **Consistent abstraction level**: Don't mix HTTP-level detail (`POST /api/v2/predict`) with conceptual labels (`Send prediction request`) in the same diagram. Pick one level.
- **Short labels preferred**: 2–6 words. Put protocol details in a legend if needed.

### Numbered Steps
- **Number every interaction** — use filled blue circles (#4285F4) with white numbers (Google Cloud pattern)
- Numbers follow **temporal order** for the specific scenario
- Place numbers ON or adjacent to the arrow they describe
- Return arrows get their own number (don't skip them)

## Arrow Styles

| Arrow Style | Meaning | When to Use |
|-------------|---------|-------------|
| Solid line, filled arrowhead | Synchronous call / direct invocation | External API calls, tool invocations |
| Dashed line, open arrowhead | Return / response | Every response to a synchronous call |
| Dashed line, filled arrowhead | Asynchronous message / delegation | Agent delegation, event publishing |
| Self-arrow (loop back) | Internal processing | LLM reasoning, local computation |

## Activation Bars

- Thin rectangles on lifelines during the period when a participant is actively processing
- Show them for **synchronous blocking calls** — the caller's bar stays active while waiting
- Helps readers see which participants are "busy" at any point in time
- Optional but recommended for clarity in multi-step flows

## Fragment Usage

Use fragments sparingly:

| Fragment | Purpose | Example |
|----------|---------|---------|
| `alt` | Conditional branching | "If prescriptive question / else data query" |
| `opt` | Optional step | "If cache miss, fetch from API" |
| `loop` | Repeated interaction | "Retry up to 3 times" |
| `par` | Parallel execution | "Fetch data from Source A and Source B simultaneously" |
| `ref` | Sub-sequence reference | "See: Authentication Flow diagram" |

**Rules:**
- Max 1–2 nesting levels
- Prefer **separate diagrams per scenario** over complex alt fragments
- Use `ref` to extract reusable sub-sequences
- Label every fragment with a clear guard condition

## Agent-Specific Conventions

When diagramming multi-agent AI systems:

### Participant Types
| Participant | Visual Treatment | Position |
|-------------|-----------------|----------|
| User / Client | Person card (tinted background) | Far left |
| Orchestrator Agent | Agent card (head-cogwheel icon) | Left-center |
| Sub-Agent | Agent card (same icon, different name) | Center |
| External System | System card (provider icon) | Right |
| LLM Endpoint | System card | Far right (or shown as infrastructure) |
| Shared Infrastructure | Horizontal band or note | Bottom |

### Delegation Patterns

**Hierarchical delegation** (most common):
```
User → Orchestrator → Sub-Agent → External System
                   ← results ←
         ← response ←
```
- Dashed arrows for internal delegation (orchestrator → sub-agent)
- Solid arrows for external calls (agent → API)
- Return arrows trace back through the chain

**Two-step orchestration** (agent coordinates multiple calls):
```
User → Orchestrator → Sub-Agent A → External A (Step 1: get data)
                    → External B (Step 2: process data)
       ← response ←
```
- Label steps explicitly: "Step 1: Data request", "Step 2: Predict"
- Show the temporal dependency clearly (Step 2 depends on Step 1's result)

### LLM Inference
- If LLM calls are the **focus** of the diagram → show LLM as a participant with explicit prompt/completion arrows
- If LLM calls are **infrastructure** (every agent uses it) → show as a note or unnumbered infrastructure band at the bottom
- Don't show every internal LLM reasoning step unless that's the diagram's purpose

### Self-Messages
Use self-arrows (arrow from participant back to itself) for:
- Internal LLM reasoning / prompt composition
- Result assembly / formatting
- Decision logic ("classify intent")
Keep these to 1–2 per diagram — too many clutters the flow.

## Layout Rules

### Spatial Arrangement
- **Participants across the top** as cards with lifelines dropping down
- **Messages horizontal** between lifelines, flowing left-to-right for requests
- **Return arrows below** their corresponding request (parallel, slight vertical gap)
- **Time flows top-to-bottom** — later interactions are lower on the diagram
- **Consistent vertical spacing** between messages (compressed areas imply "unimportant")

### Whitespace and Grouping
- **Group related interactions visually** — leave vertical gaps between logically distinct phases
- Phase labels as notes on the left margin (e.g., "Phase 1: Data Retrieval", "Phase 2: Analysis")
- Minimum 40px between elements for readability

### Infrastructure
- **Shared infrastructure** (LLM proxy, auth middleware) can be shown as:
  - A participant (if interactions with it are important)
  - A horizontal band at the bottom (if it's background context)
  - A note annotation (if it's purely informational)
- **Unnumbered** if it's not part of the primary flow

## Common Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|---|---|---|
| **"God diagram"** — entire system in one sequence | Unreadable, unmaintainable | One diagram per scenario/use case |
| **Unlabeled messages** | Readers guess at meaning | Always label with verb phrase |
| **Missing return arrows** | Ambiguous: sync vs async? fire-and-forget? | Always show returns (dashed) |
| **Too many nested fragments** | Cognitive overload | Split into separate diagrams |
| **Inconsistent abstraction** | Mixing HTTP verbs with business concepts | Pick one level per diagram |
| **Participant ordering by alphabet** | Creates unnecessary arrow crossing | Order by flow sequence |
| **Showing every error path inline** | Clutters the happy path | Separate diagrams for error flows |
| **Numbering across branches** | Implies single sequence when paths are optional | Separate diagrams per path (multi-view) |

## Relationship to C4 Static Diagrams

- **Participants MUST match elements from your C4 model** — same names, same types
- A sequence diagram is a **runtime view** of a C4 static model
- Use sequence diagrams to **complement** C3 component diagrams — the C3 shows all components spatially, the sequence shows one flow temporally
- When you have **branching paths** (multiple alternative flows through the same components), use the **multi-view approach**: one sequence per path, consistent participant cards across the set

## Checklist

Before finalizing a sequence diagram, verify:

- [ ] **Single scenario** — diagram tells one story, not multiple
- [ ] **Participants match C4 model** — same names from C1/C2/C3
- [ ] **≤9 participants**, ≤20 messages
- [ ] **Every arrow labeled** with verb phrase
- [ ] **Every interaction numbered** with blue circles
- [ ] **Return arrows shown** (dashed) for every synchronous call
- [ ] **Participants ordered** left-to-right by first appearance
- [ ] **Consistent abstraction level** across all labels
- [ ] **Fragments used sparingly** (≤2 nesting levels)
- [ ] **Legend included** if custom notation is used
- [ ] **Title follows format**: `PROJECT — Sequence: [Scenario Name]`
