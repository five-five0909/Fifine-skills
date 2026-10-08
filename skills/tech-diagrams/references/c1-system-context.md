# C1 — System Context Diagram

A comprehensive reference for building publication-quality System Context diagrams. Based on Simon Brown's C4 model (c4model.com), his GOTO 2024 talk on C4 misconceptions/misuses/mistakes, and practitioner field experience.

## Purpose

Show the system as a **single black box** surrounded by the people who use it and the external systems it directly depends on. Answer three questions:

1. What is this system?
2. Who uses it?
3. What does it depend on?

**Audience**: Everyone — stakeholders, PMs, executives, new team members, technical and non-technical alike.

**Quality bar**: Someone who has never seen this diagram understands it in under 60 seconds without anyone explaining it (the "stand-alone test").

## Element Inventory

A C1 diagram has exactly three kinds of elements:

### 1. The System (focal point)
Your system. ONE box. The largest element, placed at center. It is a **black box** — nothing inside it is visible at this level.

**Required labels:**
- **Name**: The actual system name (e.g., "AI Insights PoC")
- **Type**: `[Software System]`
- **Description**: One sentence on what it does and why it exists

### 2. People (actors)
The humans who interact with the system. Represented as person silhouettes or distinct person-shaped elements.

**Required labels:**
- **Name**: A role, never a named individual (e.g., "Business User", "Developer")
- **Type**: `[Person]`
- **Description**: One sentence on who they are and what they need

**Placement**: Top or left of the diagram (entry points to the architecture).

### 3. External Software Systems
Systems your system directly interacts with that are owned/operated by someone else. Represented as smaller boxes around the perimeter.

**Required labels:**
- **Name**: The actual system name (e.g., "MicroStrategy", "Azure OpenAI Service")
- **Type**: `[Software System]`
- **Description**: One sentence on what it provides to your system

## The Internal vs. External Boundary

This is the hardest decision. Apply this rule:

**If your team builds it, deploys it, or is responsible for its operation → INTERNAL (invisible at C1).**
**If another team owns it and you consume it as a service → EXTERNAL (shows on the diagram).**

### What is INTERNAL (do NOT show at C1)

| Element | Why It's Internal |
|---|---|
| Individual agents, bots, or microservices | Implementation detail — these are containers (C2) or components (C3) |
| Agent frameworks (Google ADK, LangGraph, CrewAI) | Library/framework — goes in the subtitle of the container that uses it at C2 |
| Hosting platforms (Azure Container Apps, GKE, EC2) | Deployment infrastructure — belongs in a Deployment diagram |
| Internal databases, caches, queues | Internal containers — visible at C2 |
| Routing logic, prompt engineering, RAG pipelines | Component-level detail — visible at C3 |
| Model versions or LLM capabilities | Too granular for any architecture diagram |

### What is EXTERNAL (show on the diagram)

| Element | Why It's External |
|---|---|
| Managed cloud AI services (Azure OpenAI, Vertex AI) | Separate SLA, availability, cost model; you don't own it |
| Data platforms owned by other teams (MicroStrategy, Databricks, Snowflake) | You orchestrate access but don't own the data or platform |
| Third-party APIs you consume | External dependency with independent lifecycle |
| Identity providers (Azure AD, Okta) | Only if identity is a major story for the audience; otherwise defer to C2 |

### The "first-degree" rule
Only show systems your system **directly** interacts with. If your system talks to System A and System A talks to System B, System B does NOT appear on your C1. No second-degree dependencies.

## Relationships (Arrows)

### Unidirectional only
The C4 model does not use bidirectional arrows. A unidirectional arrow with a descriptive label implies the response. "Retrieves operational data from" tells you data comes back without needing a second arrow. Two-way arrows obscure which party initiates communication.

### Labels start with a verb
Every arrow label must begin with a verb describing the business-level interaction:

| Good | Bad |
|---|---|
| "Asks natural language questions about restaurant operations" | "Uses" |
| "Retrieves operational analytics and KPI data via specialized bots" | "Data" |
| "Requests prescriptive recommendations from analytics models" | "Connects to" |
| "Sends prompts for natural language understanding and response generation" | "API calls" |

### Business-level, not technical
At C1, describe *what* flows, not *how*. No protocols, no ports, no technology names in arrow labels.

| Good (C1) | Bad (belongs at C2) |
|---|---|
| "Retrieves operational analytics" | "REST API call over HTTPS to /v1/cubes" |
| "Sends prompts for inference" | "gRPC streaming to GPT-5.2 endpoint" |

### One label per arrow
Short phrase, not a sentence. If you need more than one clause, the arrow may be doing too much — consider splitting the interaction.

## Layout

### Spatial arrangement
- **Center**: The system (protagonist of the diagram)
- **Top or left**: People/users (convention: humans at top or left)
- **Surrounding perimeter**: External systems, distributed evenly (not all on one side)
- **Primary flow**: Left-to-right — Users → System → Dependencies

### Sizing
- Central system occupies ~30% of the diagram area
- External systems are smaller and roughly equal in size to each other
- Person elements are visually distinct from software systems (different shape)

### Arrow routing
- **Orthogonal only** — horizontal and vertical segments, 90-degree turns, no diagonals, no curves
- **No crossings** — if arrows cross, the layout needs rearranging
- **Consistent direction** — primary flow left-to-right; avoid arrows flowing against the grain

## Density

### Hard limits
- **Under 10 total elements** (1 system + people + external systems)
- **4-6 external systems** maximum
- If you have more, ask: "Does this system directly interact with mine, or is it mediated?" Only direct dependencies belong.
- Group related external systems if they serve the same purpose (e.g., "Operational Data Sources" instead of listing 7 individual cubes)

### When it feels crowded
Splitting a C1 into multiple diagrams is rare. If you're tempted to, you probably have scope leakage — containers or components sneaking into C1 that belong at C2.

## Required Metadata

Every C1 diagram must include:

1. **Title**: "System Context diagram for [System Name]"
2. **Legend**: Explain what colors, shapes, and line styles mean — even if they seem obvious. Simon Brown: "All diagrams should have a key/legend to make the notation explicit." People print diagrams in black-and-white, share them without context, and may be colorblind.

## Anti-Patterns Checklist

Verify none of these before finalizing:

| Anti-Pattern | What To Do Instead |
|---|---|
| Arrows labeled "Uses" or "Connects to" | Verb-led description of what flows |
| Bidirectional arrows | Unidirectional + descriptive label |
| Boxes with name only (no type, no description) | Add `[Software System]` and one-line description |
| A database or queue visible at C1 | Remove — it's a container, belongs at C2 |
| Framework or library as a separate box | Remove — it's an implementation detail |
| "Hosted on Azure" annotation | Remove — deployment detail |
| Technology in arrow labels ("REST", "gRPC") | Replace with business-level description |
| Second-degree dependencies shown | Remove — only direct connections |
| Named individuals on diagram | Replace with role ("Business User") |
| No legend | Add one |
| No title | Add: "System Context diagram for [Name]" |
| >10 elements total | Reduce — check for scope leakage |
| Colors as only differentiator | Ensure shape/label/position also convey meaning |

## AI/ML System Considerations

When the system being diagrammed uses AI, ML, or multi-agent orchestration:

- The entire agent topology, routing logic, prompt engineering, and model selection are **invisible at C1**. The system is "an AI-powered chatbot" — a single box.
- The AI nature appears only in the **description** of the system box ("AI-powered prescriptive analytics chatbot that...").
- The **external LLM service** (Azure OpenAI, Vertex AI) is a separate external system because it has its own SLA, availability, and cost model.
- Individual agents, bots, or tools are NOT external systems — they are internal components of your system.

## What Separates Mediocre from Excellent

### Mediocre C1
- System box with a name but no description
- Arrows labeled "Uses"
- No legend
- Some containers leaking through (a database, an API)
- Missing person elements
- No title

### Excellent C1
- **Immediately answers**: What is this? Who uses it? What does it depend on?
- **Every box**: name + type + description — passes the stand-alone test
- **Arrow labels tell a story**: reading them aloud produces a coherent narrative
- **Ruthless scope**: only direct, first-degree dependencies
- **Visual hierarchy**: system is prominent, external systems are subordinate
- **Clear legend and title**: no guessing about notation
- **Showable to a VP or a new hire**: both understand it in under 60 seconds
