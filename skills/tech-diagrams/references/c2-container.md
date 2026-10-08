# C2 — Container Diagram

A comprehensive reference for building publication-quality Container diagrams. Based on Simon Brown's C4 model (c4model.com), his GOTO 2024 talk on C4 misconceptions/misuses/mistakes, empirical readability research (Helen Purchase, Univ. of Queensland), and practitioner field experience.

## Purpose

Zoom into the system box from C1. Show the major **deployable units** (containers) inside the system and how they communicate. Answer: "What are the big building blocks and how do they talk to each other?"

**Audience**: Technical people inside and outside the team — architects, developers, ops/support.

**Quality bar**: A technical reader can understand the high-level shape of the architecture, how responsibilities are distributed, and what major technology choices were made — without a verbal walkthrough (the stand-alone test).

## What Is a "Container" in C4?

**"Container" does NOT mean Docker.** In C4, a container is a **runtime boundary around some code being executed or some data being stored.** It is a separately deployable/runnable unit.

### Is a Container
- Server-side web application (Python Flask, Node.js Express)
- Proxy or gateway process (LiteLLM, Envoy, NGINX)
- Background worker or batch job
- Serverless function (Azure Function, Lambda)
- Database schema you own
- Blob/object store you own (Azure Blob Storage, S3)
- Key vault or secret store you own (Azure Key Vault)
- Mobile app, SPA, CLI tool
- Message broker topic/queue (model individually, not the whole broker)

### Is NOT a Container
- JAR files, DLLs, Python packages — packaging mechanisms *within* a container
- Classes, modules, interfaces — code-level, belongs at C3
- Shared libraries — not independently deployable
- Deployment infrastructure (Kubernetes, Azure Container Apps, load balancers) — belongs in a Deployment diagram

### The Litmus Test
Can it be independently deployed or started/stopped? If yes → container. If it runs in the same process as other things and cannot be independently deployed → component (C3).

## Element Inventory

A C2 diagram has these element types:

### 1. System Boundary
A dashed or solid rectangle enclosing ALL containers that belong to your system.

**Required labels:**
- **Name**: The system name from C1 (e.g., "AI Insights PoC")
- **Type**: `[Software System]`

**Rules:**
- Everything inside is something your team owns, builds, and deploys
- Everything outside is a Person, an External Software System, or not part of your application logic
- The boundary is the single most important visual element — it communicates ownership

### 2. Containers (inside the boundary)
The deployable units your team owns and operates.

**Required labels (three lines per card):**
- **Name**: Actual name of the container
- **Technology**: `[Container: Python / Google ADK]` or `[Container: Azure Blob Storage]`
- **Description**: One sentence on its responsibility

### 3. People (outside the boundary)
Reappear from C1 for context. Same treatment as C1 — role name, `[Person]`, description.

### 4. External Software Systems (outside the boundary)
Reappear from C1 for context. Same treatment as C1 — opaque boxes. Do NOT show their internal details.

## The Ownership Boundary

### What Goes Inside

If you **own the data or configuration** in a service, it is a container inside your boundary — even if the infrastructure is managed by a cloud provider.

> Simon Brown: "If you're building a software system that is using Amazon S3 for storing data, it's true that you don't run S3 yourself, but you do have ownership and responsibility for the buckets you are using. Similarly with Amazon RDS, you have complete control over any database schemas that you create. For this reason, treat them as containers."

| Service | Inside or Outside? | Reasoning |
|---|---|---|
| Your application processes | Inside | You build and deploy them |
| Data stores you own (Blob Storage, databases) | Inside | You own the data/schemas |
| Secret stores you own (Key Vault) | Inside | You own the configuration and secrets |
| Proxy/gateway you deploy (LiteLLM) | Inside | Separately deployed process you manage |

### What Goes Outside

| Service | Inside or Outside? | Reasoning |
|---|---|---|
| Managed AI services (Azure OpenAI, Vertex AI) | Outside | You consume it, don't own it |
| External data platforms (MicroStrategy, Databricks) | Outside | Another team owns the data and platform |
| Third-party APIs | Outside | Independent lifecycle |

### What to Omit Entirely

| Service | Why Omit |
|---|---|
| Container Registry (ACR, ECR) | Deployment infrastructure — not a runtime participant. Belongs in Deployment diagram only. |
| Application Insights / monitoring | Observability platform — does not participate in the functional architecture. Omit to reduce clutter, or show as external system if monitoring is architecturally significant. |
| CI/CD pipelines (GitHub Actions) | Deployment concern, not runtime architecture. |
| Load balancers, replicas, networking | Deployment details. Container diagram must be deployment-environment-independent. |

## Relationships (Arrows)

### Technology-specific at C2
Unlike C1 (business-level labels), C2 arrows include **protocol and technology**:

| Good (C2) | Bad |
|---|---|
| "Sends inference requests [HTTP/REST]" | "Uses" |
| "Retrieves secrets [HTTPS, Managed Identity]" | "Connects to" |
| "Queries BI reports [REST API]" | "Data" |
| "Forwards to GPT-5.2 [HTTPS, API Key]" | "API calls" |

Format: **verb phrase + [protocol, auth mechanism]**

### Unidirectional only
Same rule as C1. If data flows both ways, pick the primary initiator direction and label accordingly.

### One label per arrow
Short phrase with protocol. If you need more, the relationship may be doing too much.

### Auth mechanism on arrows (not as separate boxes)
Do NOT draw managed identity, RBAC, or auth as separate containers. They are not running processes. Instead, annotate the auth mechanism on the relationship arrow:

```
ADK Agent Service --> Key Vault: "Retrieves secrets [HTTPS, Managed Identity]"
LiteLLM Proxy --> Azure AI Foundry: "Forwards requests [HTTPS, API Key from Key Vault]"
```

If the auth pattern is complex (multi-step token exchange), create a separate Dynamic/Sequence diagram rather than cluttering the container diagram.

## Layout

### Tier-based flow (left to right)
- **Leftmost**: Users/Actors (outside boundary)
- **Middle**: Your containers inside the system boundary (presentation → logic → data flow)
- **Rightmost/bottom**: External systems and data stores

### Edge crossings are the #1 readability killer
Helen Purchase's empirical research: reducing edge crossings improves reader accuracy by 30-40%. For a diagram with fewer than 7 containers, **target zero crossings.**

### Visual weight and differentiation
- **Primary containers** (your main application processes): Prominent, full-color treatment
- **Data stores** (Blob Storage, Key Vault): Same color family but with a different icon or `[Data Store]` label to visually differentiate
- **External systems**: Visually muted (gray) — they should recede so the reader's eye is drawn to what you control
- **System boundary**: Subtle light background with dashed border

### Deployment-agnostic
Simon Brown (Aug 2025): "The container diagram should show a deployment environment independent view of the applications and data stores inside a software system boundary."

Do NOT show:
- Azure Container Apps, Kubernetes, EC2
- Replicas, scaling, failover
- Subnets, VNets, networking
- Load balancers, traffic managers

## Density

### Hard limits
- **Maximum 8 containers per diagram**
- If more, split by concern: "C2a — Compute & Data Flow", "C2b — Security & Identity"
- Each split should be self-contained with its own legend and system boundary

### When to omit
If a service doesn't participate in the functional architecture (monitoring, deployment tooling, CI/CD), omit it to reduce visual noise. Less is more.

## Required Metadata

1. **Title**: "Container diagram for [System Name]"
2. **Legend**: Explain card styles, colors, and line types — even if notation seems obvious

## Anti-Patterns Checklist

| Anti-Pattern | What To Do Instead |
|---|---|
| Deployment details on the diagram (K8s, ACA, load balancers) | Remove — use a separate Deployment diagram |
| Showing internals of external systems | Treat external systems as opaque boxes |
| Container cards with no technology label | Add `[Container: Technology]` to every card |
| Arrows with no protocol | Add `[HTTP/REST]`, `[gRPC]`, `[AMQP]`, etc. |
| Arrows labeled "Uses" | Verb phrase + protocol |
| Managed identity / RBAC as a separate box | Annotate on relationship arrows instead |
| Container Registry on the diagram | Omit — deployment infrastructure |
| Application Insights on the diagram | Omit or show as external system — observability, not functional |
| Shared libraries as containers | Remove — they're components within a container |
| Mixing C3 details (class names, endpoints) | Remove — belongs at C3 level |
| No legend | Add one |
| Edge crossings | Rearrange layout — zero crossings is the target |
| Bidirectional arrows | Unidirectional + descriptive label |

## Proxy/Gateway Pattern

When a proxy or gateway container sits between your application and an external service:

1. Model it as a **Container inside your boundary** — it is a separately deployed process you manage
2. Show the inbound arrow: `App → Proxy: "Sends requests [HTTP/REST]"`
3. Show the outbound arrow: `Proxy → External: "Forwards to endpoint [HTTPS, API Key]"`
4. Do NOT collapse the proxy into the application just because it "only routes" — if it's separately deployed, it's architecturally significant

## Executive / Input-Process-Output (IPO) Layout Variant

A **layout variant of C2** for an executive audience — not a new diagram type. It
reads the same container diagram as a single-page **Inputs → Core → Outputs**
(IPO / functional-block) story: what feeds the system, what it does, and what it
produces, left to right. Prior art: the classic **Input-Process-Output** model,
**functional block diagrams**, and **IDEF0** (inputs enter from the left, outputs
leave to the right). It trades some C4 completeness for a clean one-slide read for
sponsors and delivery leadership, while still obeying C2's ownership boundary,
card grammar, and arrow rules.

### What changes vs. a standard C2 (and what does not)

- **Fixed three-zone layout**: `Inputs / Sources` (left) → `Core` (center, your
  system boundary) → `Outputs / Consumers` (right). The Core zone is widest and
  is the protagonist; the outer zones are visually subordinate.
- **Ownership is conveyed by ZONE, not by card style.** Keep the **same white
  product cards** everywhere (name + `[Technology]` + one-line description).
  Do **not** introduce muted/grey/pink card fills or cylinder-only data-store
  shapes to signal "external" or "store" — that fights the house style. The
  Core-zone background (light blue) and boundary already communicate what you own;
  a card's zone tells the reader whose it is. (Data stores may still carry a
  `[Data Store]` label per C2's differentiation rule, but as the same card, not a
  different shape.)
- **Everything else is standard C2**: the ownership boundary decision, three-line
  cards, verb-led unidirectional arrows with `[protocol, auth]`, deployment-
  agnostic content, zero edge crossings, legend, and title all still apply.

### Collapse internal rosters (the density move)

An exec overview cannot show a full internal roster and stay readable. Use the
shared **Collapsed-subsystem card** primitive: represent an internal layer (e.g.
an agent tier, a worker pool, a set of microservices) as **one card with a
cardinality hint** — `Agent Layer [N specialist agents]` — sitting in the Core
zone. A sibling **C3 roster/component diagram** explodes it. This is the primary
technique that keeps the overview under its density ceiling. Never draw the full
roster here.

### Scope / posture note

State the overview's thesis with the shared **Scope / posture callout** primitive
(yellow `#FFF9C4` annotation box, one declarative line, bottom-center or a
corner). It captures the one caveat an executive most needs — the current posture
or scope boundary — in a single sentence. One per view, two max.

### When to use this variant vs. C1 vs. Data Flow

| Reader's question | Use |
|---|---|
| "What is this system, who uses it, what does it depend on?" — the core can stay a **black box** | **C1** |
| "What are the deployable units and technologies, arranged as a one-slide inputs→core→outputs story for stakeholders?" — **technology / deployable units matter** | **C2 — this IPO variant** |
| "What are the deployable units and how do they talk?" — pure architect/dev audience | **Standard C2** |
| "How does data move through its lifecycle?" — the main question is **data movement/lifecycle**, not structure | **Data Flow** |

### Density (exec overview)

- **Recommended ~8–12 elements**; **hard ceiling 16** (tighter than standard C2's
  container-only cap, because zones, sources, and consumers all count here).
- Rough zone budget: 3–5 source cards · 3–5 Core containers + data stores · 2–4
  consumer cards · exactly 3 zones · 1 posture callout.
- If you're over, **collapse** (roster → one card) before you **split**. If you
  must split, keep zones intact and divide the Core by concern.

### ASCII skeleton (IPO layout)

```
+--------------+   +---------------------------+   +--------------+
|  INPUTS /    |   |          CORE             |   |  OUTPUTS /   |
|  SOURCES     |   |   (system boundary)       |   |  CONSUMERS   |
| +----------+ |-->|  +----------------------+ |-->| +----------+ |
| | Source A | |   |  | Agent Layer          | |   | | Consumer | |
| +----------+ |   |  | [N specialist agents]| |   | |   X      | |
| +----------+ |   |  +----------+-----------+ |   | +----------+ |
| | Source B | |   |  +----------v-----------+ |   | +----------+ |
| +----------+ |   |  | Core Engine          | |   | | Consumer | |
| +----------+ |   |  | [Technology]         | |   | |   Y      | |
| | Source C | |   |  +----------+-----------+ |   | +----------+ |
| +----------+ |   |  [ Store 1 ]  [ Store 2 ] |   |              |
+--------------+   +---------------------------+   +--------------+
     [ Scope/posture: one declarative line about current posture ]
```

Sources feed **only** the Core; the Core feeds **only** Consumers — zero
crossings. Every card keeps name + `[Technology]`; every arrow keeps verb +
`[protocol, auth]`, exactly as standard C2.

## What Separates Mediocre from Excellent

### Mediocre C2
- Container cards with name only (no technology, no description)
- Arrows labeled "Uses" with no protocol
- Deployment details mixed in (Kubernetes, load balancers, subnets)
- Monitoring and CI/CD tools shown as containers
- No system boundary or unclear boundary
- No legend
- Edge crossings everywhere

### Excellent C2
- **Every container card**: name + technology + description — three lines
- **Every arrow**: verb phrase + protocol + auth mechanism where relevant
- **Clean ownership boundary**: what you own is inside, what you consume is outside
- **Deployment-agnostic**: no infrastructure details
- **Visually differentiated**: primary containers prominent, data stores distinct, externals muted
- **Zero edge crossings**
- **Omits non-functional services**: monitoring, deployment tooling left off to reduce noise
- **Stand-alone test passes**: understandable without explanation
