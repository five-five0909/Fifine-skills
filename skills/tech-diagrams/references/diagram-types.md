# Diagram Type Guidelines

> **Prerequisite**: Read `references/best-practices.md` before composing any diagram. It covers labeling rules, boundary decisions, scope discipline, honesty/provenance, and anti-patterns that apply across all types. Also see `styles/google-cloud.md` → **Shared Visual Primitives** for reusable building blocks (stat card, status badge + colors, milestone / "you are here" markers, collapsed-subsystem card, scope/posture callout) — reuse these across types rather than reinventing them.

## C1 — System Context

**Audience**: Stakeholders, PMs, anyone unfamiliar with the system — both technical and non-technical.
**Purpose**: Show the system as a single black box surrounded by the people and external systems it directly interacts with. Answer: "What is this thing and what does it talk to?"
**Quality bar**: A VP and a new team member can both understand it in under 60 seconds.

### Composition Rules
- ONE central element (the system) as the focal point — largest box, center of diagram
- Person elements for human actors — placed at TOP or LEFT
- External systems as smaller boxes around the perimeter
- 4-6 external systems maximum; under 10 total elements
- **Unidirectional arrows only** — no bidirectional arrows. Use verb-led labels that imply the response.
- Every arrow label starts with a verb: "Retrieves data from", "Sends queries to" — never bare nouns or "Uses"

### Element Labels (required on every box)
- **Name**: The actual name (e.g., "AI Insights PoC", "MicroStrategy")
- **Type**: Explicitly shown — `[Person]`, `[Software System]`
- **Description**: One sentence on key responsibility or purpose

### Layout
- Central system occupies ~30% of diagram area
- External systems evenly distributed (not all on one side)
- Left-to-right primary flow: Users → System → Dependencies
- No arrow should cross another — rearrange layout if needed

### Title Format
`System Context diagram for PROJECT`

### Include
- System name, type label, and one-line description
- Actor roles (not individual names), with type and description
- External system names, types, and what they provide
- Verb-led arrow labels describing business-level interactions

### Exclude
- Internal components, databases, services, or agents (this is a black box)
- Technology choices, frameworks, or libraries (no "Python", "Google ADK", "GPT-5.2")
- Authentication details, protocols, ports (unless identity is the main story)
- Deployment or hosting details (no "Hosted on Azure")
- Second-degree dependencies (systems your externals talk to, but you don't)

---

## C2 — Container

**Audience**: Infrastructure team, DevOps, architects.
**Purpose**: Zoom into the system box from C1. Show the major deployable units (containers, services, databases) and how they communicate. Answer: "What are the big building blocks?"
**Deep reference**: `references/c2-container.md` — ownership boundary, protocol labels, and the **Executive / Input-Process-Output (IPO) layout variant** for a single-page stakeholder solution-overview.

### Composition Rules
- Outer boundary box (dashed) representing the system from C1
- Containers as rounded rectangles, data stores as cylinders
- Group related containers into labeled zones with light grey backgrounds
- Each container shows: **name**, **type** (including technology), and **one-line purpose**
- Frameworks/libraries go in the container's subtitle, not as separate boxes (e.g., "Agent Runtime [Container: Python / Google ADK]")
- External systems from C1 reappear at the perimeter for context
- **Unidirectional arrows only** with verb-led labels; technology/protocol can appear here (e.g., "Pulls images via HTTPS")

### Density Management
- **Maximum 8 containers per diagram**
- Split by concern: "Compute & Data Flow", "Security & Identity", "Observability"
- Title each split: "C2a — Compute & Data Flow", "C2b — Security & Identity"
- Each split should be self-contained with its own legend

### Layout
- Zones in a grid or left-to-right flow
- External systems outside the boundary on the right
- Trust boundaries as dashed grey borders
- People from C1 can reappear at the left/top for context

### Title Format
`Container diagram for PROJECT [optional: concern]`

### Include
- Actual resource names (not "the database" — use "devkvmstraiagent")
- Container types with technology choice ("Container: Python / FastAPI")
- Key relationships: image pull, secrets, RBAC, telemetry
- Private endpoints, NAT gateways, egress paths
- Internal databases, caches, message queues

### Exclude
- Internal code structure or agent topology (save for C3)
- Detailed RBAC role names (save for security diagram)
- Code-level details (classes, functions)

---

## C3 — Component

**Audience**: Dev team, technical leads, software architects.
**Purpose**: Zoom into one container from C2. Show internal logical components — architecturally significant groupings of related functionality. Answer: "What's inside this service?"
**Deep reference**: `references/c3-component.md` — comprehensive rules, agent-specific patterns, layout checklist; includes the **Agent Roster (stakeholder) variant** for a build-scope agent-team map.

### Composition Rules
- Outer boundary is the container from C2, labeled with container name + technology
- Components as rounded rectangles — each with name, technology/type, and one-line responsibility
- **5–15 components** per diagram (sweet spot). Max 20. Fewer than 5 → fold into C2.
- External dependencies (other containers, external systems) placed outside the boundary as supporting elements
- Every arrow labeled with verb phrase + optional protocol
- Components are **one level above code** — NOT individual classes, functions, or files

### Layout
- Top-to-bottom or left-to-right internal flow
- Entry points (controllers, orchestrators, routers) at top or left
- Data stores and external integrations at bottom or right
- Shared internal infrastructure (proxies, caches) at bottom or side
- External dependencies on the right, outside the container boundary
- **Include an ASCII layout diagram** in the prompt to ground spatial positions

### Agent-Specific Rules
When the container hosts a multi-agent system:
- Each agent is a component; use type label to distinguish `[Orchestrator Agent]` vs `[Sub-Agent]` vs `[Tool]`
- Orchestrator/root agent positioned prominently at top-center
- Specialist agents in middle row, positioned near their external targets
- Tools grouped near owning agent (or represented as a count in agent's type label)
- Infrastructure (LLM proxy, state manager) at bottom
- Dashed arrows for internal delegation; solid for external API calls
- Label multi-step orchestrations explicitly ("Step 1: ...", "Step 2: ...")

### Title Format
`Component diagram for [Container Name]`

### Include
- Component names, technology/type, and one-line responsibilities
- Data flow and delegation between components
- External API calls with protocol labels
- Shared infrastructure (proxy layers, caches, state managers)

### Exclude
- Code-level details (classes, functions, methods)
- Database schemas
- Trivial/obvious relationships (e.g., every component → logging)
- Detailed error handling paths

### When to Split
- >15 components → split by functional area or domain
- Distinct flows (user request vs background processing) → separate diagrams
- Different team ownership → separate diagrams per team
- Pair with Dynamic/Sequence diagrams for specific scenario walkthroughs

---

## Network & Security

**Audience**: Networking, security, compliance teams.
**Purpose**: Show traffic flow, trust boundaries, and access controls. Answer: "How is this secured?"

### Composition Rules
- Organize into labeled swim lanes/zones
- Show full access chain from user to resource
- Trust boundaries as dashed borders
- Private endpoints as green boxes
- Blocked paths shown explicitly (red box with X or strikethrough)

### Layout
- Left-to-right: External access → Network boundary → Internal resources → External egress
- Subnets as nested boxes with CIDR notation where known
- PaaS services connected via Private Link labels

### Title Format
`PROJECT — Network & Security`

### Key Elements
- VPN, conditional access chain
- Hub & spoke or VNet topology with peering
- Subnet CIDRs and purposes
- Private endpoints with service mapping
- NAT Gateway for outbound
- Private DNS Zone hostnames
- "publicNetworkAccess: disabled" annotations

---

## Data Flow

**Audience**: Everyone — the most accessible diagram type.
**Purpose**: Show end-to-end request lifecycle with a concrete example. Answer: "What happens when a user asks a question?"
**Deep reference**: `references/data-flow.md` — comprehensive rules, AI/ML patterns, DFD levels, transformation conventions; includes the **Reconciliation / Exception Routing subpattern** (three-way match → classify → route).

### Composition Rules
- Left-to-right flow with numbered steps (blue filled circles, white numbers)
- User/initiator on far left, external dependencies on far right
- **5–7 processes max** per diagram (hard ceiling: 9)
- **12–15 total elements max** (hard ceiling: 20)
- **Label every arrow** with the data being transmitted (noun phrase)
- Processes named with verb-noun format ("Classify Intent", "Retrieve Data", "Generate Response")

### Layout
- **Left-to-right** for request paths (primary flow)
- **Top-to-bottom** for persistence (data stores below)
- Group elements into horizontal tiers: Ingestion → Processing → Intelligence → Delivery
- Data stores along the bottom or beneath their primary consumer
- Minimize arrow crossings — rearrange layout rather than allowing crossings

### AI/ML System Pattern
For systems with LLM inference or agent orchestration, show the context assembly pipeline:
1. Query Understanding — intent classification, routing
2. Retrieval Fan-out — parallel data retrieval from multiple sources
3. Context Assembly — all data converges into assembled context
4. LLM Inference — model call (shown with distinct visual treatment or infrastructure band)
5. Post-processing — validation, formatting
6. Response Delivery — formatted output to user

### Arrow Conventions
- Solid arrows for synchronous data flow / direct calls
- Dashed arrows for async flow / return responses
- Label every arrow with data content ("operational metrics JSON", "prediction request")
- Numbered blue circles on arrows for temporal ordering

### Title Format
`PROJECT — Data Flow: [Scenario Name]`

---

## Sequence

**Audience**: Developers, architects, technical leads.
**Purpose**: Show temporal orchestration between components for a specific scenario. Answer: "In what order do things happen?" Equivalent to a C4 Dynamic Diagram in sequence style.
**Deep reference**: `references/sequence.md` — comprehensive rules, agent-specific conventions, density limits, anti-patterns.

### Composition Rules
- Participants as labeled cards across the top with vertical lifelines
- Horizontal arrows between lifelines showing interactions, numbered with blue circles
- **6–9 participants max** (7 ± 2 sweet spot). Fewer is better.
- **15–20 messages max**. Beyond ~20, split or use `ref` fragments.
- **Always show return arrows** (dashed) — omitting creates sync/async ambiguity
- Activation bars (thin rectangles) on lifelines during synchronous processing
- **One scenario per diagram** — separate diagrams for alternate paths

### Layout
- **Left-to-right**: Initiator (person) far left → orchestrators → sub-agents → external systems far right
- Order participants by **first appearance** in the flow (minimizes arrow crossing)
- Time flows **top-to-bottom**
- Solid arrows for synchronous calls, dashed for returns and delegation
- Return arrows placed **below** their corresponding request (parallel, slight vertical gap)
- Group related interactions with vertical whitespace between phases

### Agent-Specific Rules
When diagramming multi-agent orchestration:
- Dashed arrows for internal delegation (orchestrator → sub-agent)
- Solid arrows for external calls (agent → API endpoint)
- Label multi-step orchestrations explicitly ("Step 1: Data request", "Step 2: Predict")
- Show LLM infrastructure as unnumbered band or note (not a participant) if every agent uses it
- Self-arrows for internal reasoning only if it's the diagram's focus

### Fragment Rules
- Use `alt`/`opt`/`loop`/`par` fragments **sparingly** — max 1–2 nesting levels
- Prefer separate diagrams per scenario over complex alt fragments
- Use `ref` to point to sub-sequences defined in other diagrams

### Title Format
`PROJECT — Sequence: [Scenario Name]`

### Include
- Participant names matching C4 static model elements
- Every arrow labeled with verb phrase (2–6 words)
- Every interaction numbered (blue filled circles, white numbers)
- Return arrows for every synchronous call
- Activation bars for blocking calls

### Exclude
- Error handling paths (unless that's the point of the diagram)
- Internal processing details within a participant (unless focus of diagram)
- Every LLM inference call (show as infrastructure if ubiquitous)

---

## Use Case Map

**Audience**: Product managers, stakeholders.
**Purpose**: Show feature/capability coverage as a structured matrix. Answer: "What capabilities exist and what's their scope?"

### Composition Rules
- Matrix/grid layout with categories as columns or rows
- Color-coded cells indicating status (active, planned, out of scope)
- Clean headers with category labels
- Optional grouping rows for related capabilities

### Layout
- Categories across the top as column headers
- Features/capabilities listed as rows
- Cells filled with status indicators (colored dots, checkmarks, or fill colors)

### Title Format
`PROJECT — Use Case Map`

### Colors for Status
- Green (#34A853): In scope / active / implemented
- Blue (#4285F4): Planned / in progress
- Orange (#F29900): Stretch goal / conditional
- Grey (#9AA0A6): Out of scope / deferred
- Red (#EA4335): Blocked / risk

---

## Comparison / Split-Screen

**Audience**: Executives, steering committees, decision-makers evaluating a change.
**Purpose**: Show two states side-by-side — current vs. future, option A vs. option B, or before vs. after migration. Answer: "What changes and what stays the same?"
**Deep reference**: `references/comparison.md` — shared structure principle, change marking conventions, color conventions.

### Composition Rules
- Two equal-width panels separated by a dashed grey vertical divider
- **Identical spatial layout** for shared elements across both panels (same position, same size)
- New elements highlighted (green border), removed elements ghosted (grey/dashed), modified elements marked (amber border)
- **5–7 elements per panel** (hard ceiling: 9)
- Include a **change summary callout** listing key differences with directional indicators
- Unchanged elements in muted grey — present for context, not the focus

### Layout
- Equal panel width — never bias by size
- Clear panel headers: "Current State" / "Target State"
- Shared legend at bottom (not duplicated)
- Apply the same spatial grammar (C2-style, network-style) identically to both panels

### Title Format
`PROJECT — Comparison: [Current/Future | Option A/Option B]`

---

## Roadmap / Milestone Timeline

**Audience**: Executives, steering committees, delivery leads, sponsors funding the work.
**Purpose**: Show a linear progression of phases toward an end state over time, with milestones/gates. Answer: "What's the journey from here to the target, and in what order?"
**Deep reference**: `references/roadmap.md` — phase bands, milestone / current-position markers, swimlanes, prior-art conventions (SAFe / product roadmaps / Mermaid timeline).

### Composition Rules
- **3–5 phases** (hard ceiling: 6) as left-to-right bands; each phase **named** (not "Phase 1/2/3" alone) with one concrete progress signal
- **2–4 key activities** per phase; **1 gating milestone per phase boundary** (usually 2–6 total, with exit criteria)
- Phases **advance toward the target state** (cumulative growth only for rollout/maturity journeys)
- Reuse shared primitives: **milestone markers**, **"you are here" marker**, **status badge + colors** (see `styles/google-cloud.md`)
- Strictly left-to-right toward one destination — never a loop; mark uncommitted dates "illustrative — TBD"

### Exclude
- Detailed task schedules / dependency-heavy Gantt charts
- Repeating processes (use Cyclical / Measurement Loop); two-state before/after (use Comparison)

### Title Format
`PROJECT — Roadmap: [Journey Name]`

---

## Layered Ecosystem Map

**Audience**: Executives, practice leaders, sales — strategic positioning audience.
**Purpose**: Show where a product/framework sits within a technology stack using horizontal layers. Answer: "How does this fit into the bigger picture?"
**Deep reference**: `references/layered-ecosystem.md` — layer count guidance, ownership coloring, cross-cutting sidebars.

### Composition Rules
- **4–5 horizontal layers** (hard ceiling: 7). Bottom = infrastructure, top = application/user
- **3–5 items per layer** (hard ceiling: 7). Items within a layer are peers (same abstraction)
- Color-code by ownership: blue = cloud provider, green/orange = your value-add, grey = customer
- **1–2 cross-cutting sidebars** on the right edge for concerns that span layers (Security, Observability)
- Focal layer (your product) gets saturated color, extra height, and more label detail

### Layout
- Layers span full diagram width
- Items evenly distributed within layers
- Cross-cutting sidebars as vertical bars on the right edge
- Layer labels on the left side or as bold headers inside

### Title Format
`PROJECT — Technology Ecosystem`

---

## Cyclical / Measurement Loop

**Audience**: Operations teams, leadership — anyone understanding a continuous process.
**Purpose**: Show a repeating process that feeds back into itself. Answer: "How does this process sustain and improve itself?"
**Deep reference**: `references/cyclical-loop.md` — node count rules, center element patterns, tokconomics-specific guidance.

### Composition Rules
- **4–6 stage nodes** arranged in a circle (hard ceiling: 8)
- **Always clockwise flow**, starting at 12 o'clock
- Center element: core purpose, key metric, or primary artifact
- Curved arrows following the arc (never straight lines cutting across)
- **Dual-label pattern** for measurement loops: stage name + KPI annotation
- Annotation callouts outside the circle, connected by thin leader lines
- At most 1–2 feedback arrows cutting across the circle (dashed)

### Layout
- Equal angular intervals between nodes
- Even node sizing
- Annotations outside the circle
- External inputs/outputs shown as arrows entering/exiting the circle

### Title Format
`PROJECT — [Cycle Name] Loop`

---

## Decision Tree / Flowchart

**Audience**: Architects, developers, decision-makers evaluating options.
**Purpose**: Show a series of questions leading to recommended outcomes. Answer: "Given my constraints, which option should I choose?"
**Deep reference**: `references/decision-tree.md` — ISO 5807 shapes, clinical algorithm conventions, convergence patterns.

### Composition Rules
- **Top-to-bottom layout** with binary (Yes/No) decision diamonds
- Decision nodes phrase as **questions** in plain language, not abstract conditions
- **Consistent branch convention**: "Yes" always goes down, "No" always goes right
- Terminal nodes (rounded rectangles) name the **recommended outcome + one-line rationale**
- **5–7 levels deep** maximum (hard ceiling: 7). Decompose into linked sub-trees if deeper.
- **15–20 total nodes** (hard ceiling: 30). **5–8 terminal outcomes** (hard ceiling: 12).
- Color-code terminals by complexity: green (simple), yellow (moderate), red (advanced)
- Highlight the "happy path" with thicker line weight or accent color

### Layout
- Root at top center
- Standard ISO 5807 shapes: rounded rectangle (start/end), diamond (decision), rectangle (process), small circle (connector)
- Even spacing, consistent node sizing
- Minimize line crossings — use connectors if needed

### Title Format
`PROJECT — Decision Tree: [Decision Domain]`

---

## Deployment Topology

**Audience**: DevOps, infrastructure engineers, operations, architects.
**Purpose**: Show where software runs within infrastructure — mapping logical containers to physical/virtual deployment targets. Answer: "What runs where?"
**Deep reference**: `references/deployment-topology.md` — GCP resource hierarchy, C4 deployment conventions, scaling annotations.

### Composition Rules
- **Nested rectangles** showing containment: Organization → Folder → Project → Service
- **One diagram per environment** (dev, staging, prod) — per C4 guidance
- Map C2 containers to **named service instances** within GCP projects
- **3–4 nesting levels** (hard ceiling: 5)
- **4–6 services per project** (hard ceiling: 8), **15–20 total elements** (hard ceiling: 25)
- Scaling shown as annotations ("x3", "min 1 / max 10"), not by drawing N copies
- Communication paths labeled with protocol ("HTTPS", "gRPC", "Pub/Sub")
- **Keep separate from C2** — don't merge logical architecture with physical deployment

### Layout
- Outermost boundary: cloud region or organization
- Load balancers and gateways at infrastructure boundaries
- Data stores at bottom or right
- Supporting infrastructure (DNS, CDN) along edges
- Use GCP product icons alongside text labels with a legend

### Title Format
`PROJECT — Deployment Topology: [Environment Name]`

---

## Concentric Rings / Containment

**Audience**: Security teams, architects, executives — anyone assessing layered protection.
**Purpose**: Show layers radiating from a central element, each representing a boundary of protection, abstraction, or containment. Answer: "What layers surround the core?"
**Deep reference**: `references/concentric-rings.md` — defense-in-depth models, agent containment patterns, ring vs. rectangle decision.

### Composition Rules
- **3–5 concentric rings** (hard ceiling: 7). Center = most protected/valuable/abstract
- Center element is the **most visually distinctive**: strongest color, largest text
- **Equal ring width** — don't let inner rings be proportionally tiny
- Boundary gates (shield/lock icons) on ring borders where verification occurs
- **2–4 labels per ring** (hard ceiling: 6)
- At most 1–2 breach/attack arrows crossing rings
- Include a legend mapping ring colors to their meaning

### Layout
- Inside-out or outside-in reading order — pick one and label clearly
- Ring labels inside the ring band (curved or straight)
- Detailed annotations outside the outermost ring with leader lines
- Boundary labels on the ring border, not inside the ring

### Specific Pattern: Agent Blast Radius
Rings (inside-out): Model Inference → Memory & State → Agent Runtime → Tool Access → External Systems. Boundary gates: Model Armor, guardrails, sandboxing, auth/RBAC.

### Title Format
`PROJECT — [Containment Model | Blast Radius | Architecture Layers]: [Focus]`

---

## Threat Model / Attack Surface

**Audience**: Security teams, compliance reviewers, architects assessing risk.
**Purpose**: Show attack vectors, threat categories, and mitigations mapped to system architecture. Answer: "Where are we vulnerable and what controls are in place?"
**Deep reference**: `references/threat-model.md` — OWASP Agentic Top 10, STRIDE, MAESTRO, attack trees, bow-tie diagrams.

### Composition Rules
- Choose layout by goal: **Radial** (multi-threat overview), **DFD overlay** (architecture-mapped), **Attack tree** (single threat deep dive), **Bow-tie** (cause → event → consequence)
- **Radial**: Central system + 6–10 threat spokes + mitigation barriers on spokes
- **DFD overlay**: Standard DFD + trust boundaries (dashed boxes) + threat annotations at boundary crossings
- **Attack tree**: Root goal at top, OR/AND branching, defense nodes (green) paired with attack nodes (red)
- Always show **threats AND mitigations** — threats without mitigations is just a scary list
- Color by risk level: red (unmitigated), yellow (partial), green (controlled)
- Tag threats with framework IDs (ASI01, STRIDE category, MAESTRO layer)
- **20–30 total elements** (hard ceiling: 50)

### Layout
- Radial: spokes evenly distributed, mitigations between center and threats
- DFD: standard left-to-right with trust boundaries as dashed partitions
- Attack tree: top-to-bottom, 3–4 levels deep
- Always include a companion threat-mitigation table for detail

### Title Format
`PROJECT — Threat Model: [Framework] [optional: Focus Area]`
