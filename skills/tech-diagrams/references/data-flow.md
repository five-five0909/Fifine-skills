# Data Flow Diagram Reference

> Deep reference for Data Flow diagrams. Supplements `diagram-types.md` with guidance from traditional DFD theory, Google Cloud Architecture patterns, C4 dynamic diagrams, and AI/ML system conventions.
>
> **Sources**: Miro, Visual Paradigm, GeeksforGeeks, Lucidchart, SmartDraw, c4model.com, Google Cloud Architecture Center, cognitive load research (Sweller, Mayer & Moreno, Yoghourdjian et al.).

## What is a Data Flow Diagram?

A data flow diagram shows **how data moves through a system** — from external sources, through processing steps, into and out of data stores, and back to external consumers. It answers: "What happens to data when it enters the system?"

- **Scope**: One end-to-end request lifecycle or data pipeline
- **Primary elements**: Processes, data stores, external entities, data flows (arrows)
- **Audience**: Everyone — the most accessible diagram type
- **C4 alignment**: Equivalent to a C4 Dynamic Diagram with a data-centric lens

## When to Use

- Showing the **end-to-end request lifecycle** (user question → answer)
- Documenting **data transformations** between systems
- Explaining **multi-source data aggregation** (e.g., multiple APIs feeding into context assembly)
- Communicating to **non-technical stakeholders** who need to understand what the system does

## Core Elements

| Element | Shape | Description |
|---------|-------|-------------|
| **Process** | Rounded rectangle | Transforms data — verb-noun name (e.g., "Classify Intent", "Assemble Context") |
| **External Entity** | Rectangle (or person card) | Source/sink outside the system boundary (e.g., "Business User", "MicroStrategy") |
| **Data Store** | Cylinder or open-ended rectangle | Persists data (e.g., "Vector Index", "Session Store") |
| **Data Flow** | Named arrow | Data in transit — label with what's being transmitted |

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Processes per diagram | 5–7 | 9 |
| Data stores per diagram | 3–5 | 7 |
| External entities per diagram | 3–5 | 7 |
| Total elements (all types) | 12–15 | 20 |
| Data flows (arrows) | 15–20 | 30 |

The 7 ± 2 heuristic applies: any single diagram should not require the viewer to hold more than ~7 distinct conceptual chunks in working memory.

## Naming Conventions

### Processes
- **Verb-noun format**: "Validate Claim", "Generate Response", "Retrieve Context"
- Never leave a process unnamed or use generic labels ("Process 1")
- Use consistent abstraction — don't mix HTTP-level detail with conceptual labels

### Data Flows (Arrows)
- **Label EVERY arrow** with the data being transmitted
- Use noun phrases: "operational metrics JSON", "prediction request", "natural language response"
- Unlabeled arrows are the #1 DFD anti-pattern
- Use the same name for the same data everywhere it appears

### Data Stores
- Noun phrases describing stored content: "Session History", "Bot Configuration", "Vector Index"

### External Entities
- Name by role or system identity: "Business User", "MicroStrategy", "Azure Databricks"

## Layout Rules

### Flow Direction
- **Left-to-right** for request paths (primary flow direction)
- **Top-to-bottom** for hierarchy or persistence (data going to storage)
- **Never mix directions** within a single diagram
- Response/return flows go right-to-left, shown lighter or dashed

### Spatial Arrangement
- **User/initiator on far left**
- **Primary system processing in the center**
- **External dependencies on the right**
- **Data stores below** or along the bottom
- Align elements on an implicit grid

### Swim Lanes / Tiers
Group elements into horizontal bands by architectural concern:
- **Ingestion**: Entry points, API gateways, chat interfaces
- **Processing**: Business logic, transformation, orchestration
- **Intelligence**: LLM inference, ML model invocation
- **Storage/Retrieval**: Data stores, caches, external data APIs
- **Delivery**: Response formatting, output channels

### Whitespace
- Generous spacing (≥40px between elements)
- At least one element-width of spacing between nodes
- Crossing minimization — rearrange layout rather than allowing crossings

## Arrow Conventions

| Arrow Style | Meaning |
|-------------|---------|
| Solid, filled arrowhead | Synchronous data flow / direct call |
| Dashed, open arrowhead | Asynchronous flow / return response |
| Labeled with data name | What data is being transmitted |
| Numbered circle on arrow | Step order in the request lifecycle |

### Numbered Steps (Google Cloud Pattern)
- Blue filled circles (#4285F4) with white numbers on each arrow
- Follow temporal order of the request lifecycle
- Include a numbered prose legend below the diagram explaining each step
- This is the hallmark of Google Cloud reference architecture diagrams

## AI/ML System Patterns

For systems with LLM inference, RAG, or agent orchestration:

### Show the Context Assembly Pipeline
The most important thing to diagram is not the model call itself, but the **data preparation** that feeds it:

1. **Query Understanding** — User query enters, pre-processing (intent classification, query rewriting)
2. **Retrieval Fan-out** — Parallel retrieval from multiple sources (vector DB, relational DB, cached results)
3. **Context Assembly** — All retrieved data + system instructions + conversation history converge into assembled context
4. **LLM Inference** — Model call (distinct visual treatment — e.g., different icon or zone color)
5. **Post-processing** — Output parsing, validation, citation extraction
6. **Response Delivery** — Formatted output to user

### Data Transformation Steps
When data passes through transformation logic (grain alignment, derived fields, pivots):
- Show each transformation as a labeled process
- Label incoming arrow with raw format, outgoing arrow with transformed format
- Annotate transformation rules (e.g., "TopBoxPct = Satisfied / Total")

### LLM as Infrastructure
If every component uses the LLM (e.g., via a proxy):
- Show the LLM proxy as a **horizontal infrastructure band** at the bottom (not a peer process)
- Don't route every arrow through it — just annotate that "All agents use LLM via proxy"
- This matches the pattern established in C3 component diagrams

### Multi-Source Aggregation
When multiple data sources feed into a single process:
- Use a **convergence point** — multiple arrows entering one process from different sources
- Label each arrow with its specific data contribution
- The process that receives them does the merging/assembly

## Reconciliation / Exception Routing (subpattern)

A specialization of multi-source aggregation for the case where the sources carry
the **same fact** and the point of the diagram is to **check whether they agree and
route each disagreement**. This is the classic accounts-payable **three-way match**
(PO ↔ receipt ↔ invoice) and general **data reconciliation** (control-total /
source-vs-target comparison) flow.

> **Sources**: AP three-way match (PO ↔ goods-receipt ↔ invoice); IBM data
> reconciliation (source-vs-target verification).

**Shape of the pattern**:

> N independent sources of the same fact **converge** → **align/normalize** to a
> common key & grain → **compare** (an emphasized "pivot" process node) → **classify**
> each discrepancy → **route** to an outcome/recommendation.

### Front half — convergence (stays in data-flow grammar)
- Follow this reference's **Multi-Source Aggregation** rules: 2–4 peer source entities
  on the left, each arrow labeled with the noun it carries (the specific value each
  source asserts).
- All sources flow into one **Align/Normalize** process that states the join key/grain
  — comparing before aligning is the reconciliation equivalent of the "apples to
  oranges" error. Attach tolerance/materiality here as an **annotation callout** (what
  variance counts as a discrepancy, e.g. "ignore < $X / < N units").
- Alignment flows into ONE **Compare** node — the pivot. Make it an **emphasized process
  node** (heavier border or its own tinted zone); it is the diagram's centre of gravity.

### Back half — classification (hand off to `decision-tree.md`)
This reference **forbids control flow as data flow** (see Anti-Patterns) — so the
comparison result exits into decision territory. **Do not draw the classification rules
here.** The compare node has two exits:
- a short, visually **quiet** clean path to a **"matched — no action"** terminal, and
- a **"discrepancy"** path that hands off to a **decision tree** for root-cause
  classification. Use `references/decision-tree.md` for the classification logic
  (MECE branches, one-line rationale, outcomes column). Keeping the rule matrix in a
  sibling decision diagram is the correct decomposition, not a shortcut.

### Outcome terminals — generic labeled badges
- Classify by **root cause**, not symptom, into **mutually exclusive & collectively
  exhaustive** categories. Each terminal states **category → meaning → action**
  (e.g. "Source-of-record error → upstream value wrong → correct the record").
- Label outcomes with the shared **Status badge** primitive
  (`styles/google-cloud.md` → Shared Visual Primitives) plus a **text label** — never a
  bare color. **Reserve green for "matched / no action."** Use the badge palette + a
  written cause label for each category; do **not** hard-code a fixed
  color→cause mapping (that is project-specific).
- **Anti-pattern**: two same-color terminals with two different meanings in one view
  (e.g. green for both "matched" and a "customer-behaviour" cause). Disambiguate by
  text label and column position, or recolor one; state the choice in the legend.

### Sinks & routing note
- Add an optional **audit-log / exception-queue sink** — a data store that captures
  every break and its classification. This is standard for reconciliation (the run is
  auditable) and keeps discrepancies off the happy path.
- **Process-flow vs. DMN**: draw this as a data-flow + decision-tree pair when the value
  is the **operational handoff** (who receives which exception). When the **rule matrix
  itself dominates** — many conditions × outcomes — express the classification as a
  **decision table / DMN** instead of fanning out branches, and reference it from the
  compare node.
- Use a **Scope / posture callout** (`styles/google-cloud.md`) to bound the subject to
  **one reconciliation unit** (one contract/account/object) — not the batch
  orchestration, which is a separate data-flow or sequence diagram.

**Density**: this subpattern is tighter than a full data flow — target **8–12 elements**
and **8–14 arrows**. If it grows past that, the classification has outgrown a fan-out;
move it to a dedicated decision tree or DMN table.

## DFD Levels

| Level | Name | What It Shows |
|-------|------|---------------|
| Context (Level 0) | System as single process | All external entities, all boundary-crossing data flows |
| Level 1 | Major processes | Primary processes, data stores, flows between them |
| Level 2 | Sub-processes | Decomposition of one Level 1 process into detail |

**Balancing rule**: Every data flow entering/leaving a parent process must appear in the child diagram.

For our purposes, most diagrams are **Level 1** — showing the major processing steps within the system boundary with numbered steps for the request lifecycle.

## Common Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|---|---|---|
| **Unlabeled arrows** | Readers guess at data content | Label every arrow with data name |
| **Entity-to-entity flow** | Data can't flow directly between externals | Route through a process |
| **Data store-to-store flow** | Data can't teleport between stores | Route through a process |
| **Black hole process** | Inputs but no outputs | Add output or remove process |
| **Miracle process** | Outputs but no inputs | Add input or remove process |
| **Control flow as data flow** | DFDs show data, not decisions | Keep conditionals out; use separate diagrams per path |
| **Too many elements** | Cognitive overload beyond 15 elements | Decompose into sub-diagrams |
| **Inconsistent naming** | Same data called different things | Use one name per data item everywhere |
| **Mixing abstraction levels** | HTTP verbs mixed with business concepts | Pick one level per diagram |

## Checklist

Before finalizing a data flow diagram, verify:

- [ ] **Single story** — diagram shows one end-to-end lifecycle or pipeline
- [ ] **≤15 total elements**, ≤20 arrows
- [ ] **Every arrow labeled** with data being transmitted
- [ ] **Every process named** with verb-noun format
- [ ] **Numbered steps** with blue circles for temporal ordering
- [ ] **No entity-to-entity or store-to-store flows** (everything routes through a process)
- [ ] **Consistent flow direction** (left-to-right primary, top-to-bottom for persistence)
- [ ] **External entities match C4 model** — same names from C1/C2/C3
- [ ] **Legend included** explaining shapes, colors, line styles
- [ ] **Title follows format**: `PROJECT — Data Flow: [Scenario Name]`
