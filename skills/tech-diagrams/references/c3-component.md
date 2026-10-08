# C3 — Component Diagram Reference

> Deep reference for C3 Component diagrams. Supplements `diagram-types.md` with authoritative guidance from Simon Brown's C4 model, Visual C4 best practices, and multi-agent architecture patterns.
>
> **Sources**: c4model.com, Simon Brown GOTO 2024 talk, Visual C4, Revision.app, LangChain multi-agent patterns, Zylos orchestration research.

## What is a C3 Diagram?

A C3 component diagram zooms into **a single container** from C2. The outer boundary IS the container. Everything inside is a **component** — a grouping of related functionality encapsulated behind a well-defined interface. Everything outside is a **supporting element** that components interact with.

- **Scope**: One container (one deployable unit)
- **Primary elements**: Components within the container
- **Supporting elements**: Other containers (same system), external systems, people
- **Audience**: Software architects and developers (not business stakeholders)

## What is a "Component"?

Per Simon Brown: a component is **one level of abstraction above code**. It groups code-level building blocks into a coherent, named unit with a clear responsibility.

| Language | Component maps to |
|----------|-------------------|
| Java/C# | Collection of classes behind an interface |
| TypeScript/JS | A module (logical grouping of related exports) |
| Python | A package or module with a clear public interface |
| Go | A package |

**Components are NOT:**
- Individual classes, functions, or files
- Utility/helper modules
- DTOs or configuration objects
- Every single module in the codebase

## Element Count and Granularity

**Sweet spot: 5–15 components per diagram.** (Max 20 hard limit.)

- Fewer than 5 → fold into C2
- More than 15 → split by functional area, flow, or team ownership
- Ask: "Would a developer need to know about this component to understand the high-level internal structure?" If no, omit it.
- Only show **architecturally significant** building blocks

## Labeling Convention

Every element on a C3 diagram needs **three pieces of information**:

1. **Name**: Short, descriptive (e.g., "Root Agent", "LiteLLM Proxy")
2. **Technology/Type**: Implementation technology or stereotype (e.g., "Google ADK LlmAgent", "OpenAI-compatible router")
3. **Description/Responsibility**: One sentence on what it does (e.g., "Classifies intent and routes to specialist sub-agents")

Every **arrow** needs:
1. **Verb phrase**: What the interaction does ("Delegates data queries to", "Queries bot APIs")
2. **Technology** (optional): Protocol or mechanism ("[REST API]", "[ADK delegation]", "[in-process]")

## Layout Rules

### Spatial Arrangement
- **Entry points at top or left** — controllers, routers, orchestrators
- **Data stores and external integrations at bottom or right**
- **Group related components spatially** — components that collaborate heavily should be near each other
- **Align to an implicit grid** — even in freeform layouts, grid alignment improves readability
- **The container boundary is the primary visual frame** — draw it explicitly with name + technology label

### Flow Direction
- **Top-to-bottom or left-to-right** for the primary request flow
- **Consistent direction within the diagram** — don't mix left-to-right in one part and right-to-left in another
- For agent architectures: orchestrator at top, specialist agents in middle, infrastructure at bottom, external systems on the right

### Shared Infrastructure
- **External shared infrastructure** (Redis, message queues, databases) → outside the container boundary
- **Internal shared infrastructure** (in-process cache, logging, proxy) → inside boundary but positioned to the side or bottom, out of the main flow
- Draw shared elements **once** and route multiple arrows to them — never duplicate

## Arrow Best Practices

- **Every arrow MUST have a label** — unlabeled arrows are the #1 source of confusion
- **Unidirectional arrows** in the direction of the call/request, not the data return
- **Minimize crossings** — rearrange layout to prevent crossings; if unavoidable, split the diagram
- **Eliminate trivial arrows** — if every component uses logging, don't draw that arrow
- **Line style convention:**
  - Solid → synchronous call / direct invocation
  - Dashed → asynchronous, delegation, or infrastructure relationship
- **Arrow direction follows the request**, not the data return

## Agent-Specific Patterns

When the container hosts a multi-agent system, apply these additional conventions:

### Element Types
Use the technology/type label to distinguish:

| Element | Type Label | Position |
|---------|-----------|----------|
| Orchestrator/Root Agent | `[Orchestrator Agent]` or `[LlmAgent]` | Top-center, prominent |
| Specialist/Sub-Agent | `[Sub-Agent]` or `[Agent]` | Middle row, near their external targets |
| Tool group | `[Tool]` or `[Tools]` | Grouped near owning agent |
| Infrastructure (proxy, state) | `[Infrastructure]` | Bottom or side |
| External system | (same as C2 cards) | Outside boundary, right side |

### Orchestration Patterns to Show

**Hierarchical (Supervisor/Worker)** — most common for production agent systems:
```
        Root Agent
       /          \
  Agent A      Agent B
     |              |
  External A    External B
```

Position the supervisor/root at top, workers below, externals on the right.

**Two-step delegation** — when one agent delegates to another before calling external:
```
  Forecasting Agent --step 1--> MSTR Agent --> MicroStrategy
       |
       +--step 2--> Databricks
```
Label steps explicitly ("Step 1: ...", "Step 2: ...") so the orchestration order is clear.

### Tool Ownership
- Draw tools **grouped near their owning agent** (or note tool count in the agent's type label: "Sub-Agent — 7 bot tools")
- If tools are individually significant, show them as separate components with `[Tool]` type
- If tools are a homogeneous group (e.g., 7 MSTR bot tools that all work the same way), represent as a single card with a count

### LLM Routing
- An LLM proxy/router (like LiteLLM) is an **infrastructure component** inside the container
- The actual LLM endpoint (Azure OpenAI, Claude API) is an **external system** outside the boundary
- Show: Agent → LLM Proxy → External LLM Endpoint

### Agent Roster (stakeholder) variant

A **stakeholder-facing "roster" mode** of the same supervisor/worker topology
above — for sponsors and delivery leads, not just developers. It answers "who is
on the agent team, what does each own, and what are we building?" Use it when the
point is scope and ownership rather than internal wiring.

Differences from the standard developer C3 layout:

- **Symmetric fan, one system.** One supervisor top-center; specialists in an
  evenly spaced, equal-sized fan (e.g. a **2×3 grid for 6**) — peers, never
  staggered or unequal in size. Enclose the supervisor **and** all specialists in
  a **single** system-boundary zone so the "one system" reading is unmissable.
- **Uniform delegation arrows.** One arrow from the supervisor to each
  specialist, all labeled identically ("Supervises / routes to") or annotated once
  for the whole fan. Do **not** invent a distinct verb per arrow — uniform arrows
  reinforce "one team" (this deliberately relaxes the verb-variety norm above).
- **Two-field specialist card body.** Each specialist carries exactly two labeled
  micro-rows instead of a one-line responsibility. **The two field labels are
  supplied per prompt** to fit the domain (e.g. "Owns / Uses",
  "Capability / Inputs", "Scope / Reconciles") — there is no fixed pair.
- **Build-scope emphasis.** Mark net-new agents with the **Status badge**
  primitive (lifecycle family: `NEW`/`BUILD` vs `EXISTING`; see
  `styles/google-cloud.md` → Shared Visual Primitives) and include the matching
  legend row. The legend is what kills the "are these external integrations?"
  ambiguity — do not redefine the colors here.
- **Data sources recede.** Show the systems specialists read as **muted
  supporting/external cards outside the boundary** (grey, `EXTERNAL`/`EXISTING`),
  using the standard product-card grammar — **not** a new "chip" style (per
  best-practices §7 single-card-grammar rule). Keeping them subordinate keeps the
  agents-we-build in the foreground.

**Density**: 1 supervisor + 4–6 (≤8) specialists; beyond 8, split into sub-teams.

**Routing**: use this roster mode for **static agent ownership/scope**; use a
**Sequence** diagram for interaction order, **Data Flow** for data paths, and the
**Use Case Map** for capability/status coverage.

## Common Anti-Patterns

1. **Mixing abstraction levels** — showing both agents (components) and individual tool functions (code) on the same diagram
2. **Missing container boundary** — forgetting to draw the outer container box
3. **Missing labels** — boxes or arrows without descriptions
4. **Every class is a component** — C3 is NOT a UML class diagram
5. **Missing supporting elements** — showing internal components without the external systems they connect to
6. **Too many arrows** — if everything connects to everything, components are too granular; merge them
7. **Creating C3 when unnecessary** — Simon Brown: "Only create component diagrams if they add value"

## When to Split

Split a single C3 into multiple diagrams when:
- **>15 components** — split by functional area or domain boundary
- **Distinct flows** — e.g., "user request" flow vs "background processing" flow
- **Different team ownership** — each team's component group gets its own diagram
- **Pair with Dynamic diagrams** — static C3 showing all components + Dynamic diagrams tracing specific scenarios

## Checklist

Before finalizing a C3 diagram, verify:

- [ ] Container boundary drawn and labeled (name + technology)
- [ ] Every component has name, technology/type, and responsibility
- [ ] Every arrow has a verb-phrase label (+ optional protocol)
- [ ] Only architecturally significant components shown (5–15)
- [ ] Supporting elements (other containers, external systems) shown outside boundary
- [ ] Layout follows logical flow (top-to-bottom or left-to-right)
- [ ] Arrow crossings minimized through positioning
- [ ] Legend included if custom notation is used
- [ ] Answers: "What are the major building blocks inside this container?"
