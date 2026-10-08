# Threat Model / Attack Surface Diagram Reference

> Deep reference for Threat Model diagrams showing attack vectors, threat categories, and mitigations. Supplements `diagram-types.md` with guidance from OWASP, STRIDE, MAESTRO, attack trees, bow-tie diagrams, and AI/LLM-specific threat frameworks.
>
> **Sources**: OWASP Threat Modeling Cheat Sheet, OWASP Top 10 for Agentic Applications (2026), CSA MAESTRO framework, Microsoft STRIDE, Bruce Schneier attack trees, NIST CSF 2.0 wheel, bow-tie risk diagrams, MITRE ATT&CK/ATLAS.

## What is a Threat Model Diagram?

A threat model diagram shows **what can go wrong with a system and how it's protected** — mapping attack surfaces, threat categories, and mitigations onto the system architecture. It answers: "Where are we vulnerable, what are the threats, and what controls are in place?"

- **Scope**: One system's threat landscape, optionally mapped to a specific framework (STRIDE, OWASP, MAESTRO)
- **Primary technique**: Architecture overlay with threat annotations, or standalone radial/attack tree
- **Audience**: Security teams, compliance reviewers, architects assessing risk
- **Key insight**: The diagram must show threats AND mitigations — threats without mitigations is just a scary list

## When to Use

- **Security architecture review**: Showing where controls exist and where gaps remain
- **Framework compliance**: Mapping system to OWASP Top 10, STRIDE, MAESTRO
- **Agent security**: Showing attack surfaces specific to agentic AI systems
- **Risk communication**: Helping non-security stakeholders understand the threat landscape
- **Audit preparation**: Documenting what's protected and how

## Layout Patterns

Choose the layout pattern that matches your communication goal:

### Pattern 1: Radial/Star — Multi-Threat Overview
Best for showing many threat categories around a central system.

```
                [Prompt Injection]
                      ↓
    [Supply Chain] ← AGENT → [Tool Misuse]
                      ↑
               [Memory Poisoning]
```

- Center: The system/agent being assessed
- Spokes: Threat categories radiating outward
- Barriers on spokes: Mitigations between center and threats
- Color by risk level (red unmitigated → green mitigated)

### Pattern 2: DFD + Trust Boundaries — Architecture Overlay
Best for showing where threats exist on the actual system architecture (STRIDE-native).

- Base layer: Data flow diagram with processes, stores, entities, flows
- Overlay: Trust boundaries as dashed boxes
- Annotations: Threat IDs at each boundary crossing
- Companion table: Detailed threat descriptions and mitigations

### Pattern 3: Attack Tree — Single Threat Deep Dive
Best for decomposing one attack goal into all possible paths.

- Root (top): Attacker's goal
- Branches: Sub-goals (OR = alternative paths, AND = required combination)
- Leaves: Concrete attack actions
- Defense nodes: Green counterparts to red attack nodes

### Pattern 4: Bow-Tie — Cause → Event → Consequence
Best for showing preventive and mitigative controls around a single threat event.

```
CAUSES → [PREVENTIVE BARRIERS] → TOP EVENT → [MITIGATIVE BARRIERS] → CONSEQUENCES
```

### Pattern 5: Layered Stack — Framework Mapping
Best for MAESTRO-style 7-layer threat mapping.

- Horizontal layers (Foundation Models → Data Ops → Agent Framework → Deployment → Security → Ecosystem → Observability)
- Threats mapped per layer
- Cross-cutting Security bar spanning all layers

## Core Elements (Radial Layout)

| Element | Visual Treatment | Description |
|---------|-----------------|-------------|
| **Central system** | Large circle/rectangle at center | The system/agent under assessment |
| **Threat category** | Red/orange node at spoke end | Named threat (e.g., "ASI01: Goal Hijacking") |
| **Attack vector** | Smaller nodes along spoke | Specific attack methods within a category |
| **Mitigation/barrier** | Green shield icon on spoke | Security control between system and threat |
| **Risk indicator** | Color coding | Red = unmitigated, yellow = partial, green = controlled |
| **Framework tag** | Small badge/label | OWASP ID, STRIDE category, MAESTRO layer |

## OWASP Top 10 for Agentic Applications (2026)

The primary framework for AI agent threat modeling:

| ID | Risk | Key Attack Surface |
|----|------|-------------------|
| ASI01 | Agent Goal Hijacking | Poisoned inputs (emails, PDFs, RAG documents) |
| ASI02 | Tool Misuse & Exploitation | Ambiguous tool invocations, argument manipulation |
| ASI03 | Identity & Privilege Abuse | Overprivileged service accounts, confused deputy |
| ASI04 | Agentic Supply Chain | Compromised tool registries, unsigned MCP servers |
| ASI05 | Unexpected Code Execution | Code injection via LLM output, unsafe eval |
| ASI06 | Memory & Context Poisoning | Embedding injection, memory manipulation |
| ASI07 | Insecure Inter-Agent Comms | Message injection, agent impersonation |
| ASI08 | Cascading Failures | Fault propagation, circular reasoning loops |
| ASI09 | Human-Agent Trust Exploitation | Social engineering via agent output |
| ASI10 | Rogue Agents | Dormant malicious logic, slow exfiltration |

Maps naturally to a **10-spoke radial diagram** with the agent runtime at center and threats radiating along capability axes (tools, memory, comms, code, identity).

## STRIDE Mapping for DFD Overlays

| DFD Element | Applicable STRIDE Categories |
|-------------|------------------------------|
| **Process** | All 6 (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) |
| **Data Store** | Tampering, Information Disclosure, Denial of Service |
| **Data Flow** | Tampering, Information Disclosure, Denial of Service |
| **External Entity** | Spoofing, Repudiation |

**STRIDE limitation for AI**: Assumes predictable control flows. Misses agent manipulation, autonomous scope creep, model poisoning, reward hacking. Combine with OWASP Agentic for full coverage.

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Threat categories (spokes) | 6–8 | 10–12 |
| Attack vectors per category | 2–3 | 4 |
| Mitigations shown per spoke | 1–2 | 3 |
| Total elements in diagram | 20–30 | 50 |
| DFD elements (for overlay) | 10–15 | 20 |
| Attack tree depth | 3–4 levels | 5 levels |
| Attack tree leaves | 15–25 | 50 |

### When Density Is Too High
- Group related threats (e.g., ASI01+ASI06 are both injection-type)
- Use a **primary diagram** (overview) + **detail diagrams** (per threat category)
- Move detailed mitigations to a companion table

## Layout Rules

### Radial Layout
- Agent/system at exact center
- Spokes evenly distributed (10 categories = 36° apart)
- Attack vectors along spokes, increasing severity outward
- Mitigations as barriers **between** center and threat
- Framework IDs (ASI01, etc.) as badges on threat nodes

### DFD Overlay Layout
- Standard DFD layout (left-to-right data flow)
- Trust boundaries as **dashed boxes** partitioning security zones
- Threat annotations at boundary crossings — numbered, with detail in companion table
- Don't annotate more than 10–15 threats on one DFD

### Attack Tree Layout
- Root at top center (attacker's goal)
- Top-to-bottom branching
- OR nodes: separate branches
- AND nodes: arc connecting sibling branches
- Defense nodes (green) paired with attack nodes (red)
- Leaf nodes at bottom

## Color Conventions

| Element | Color |
|---------|-------|
| Threats / attack surfaces | Red (#EA4335) or orange-red (#FF6F61) |
| Mitigations in place | Green (#34A853) |
| Partial mitigations | Yellow/amber (#F29900) |
| Unmitigated risks | Red (#EA4335) with no shield |
| Assets being protected | Blue (#4285F4) or green (#34A853) |
| Information/identification paths | Blue dotted lines |
| Threat connections | Red solid lines |
| Mitigation application paths | Green dashed lines |
| Trust boundaries | Grey dashed borders |
| Residual risk indicators | Orange with exclamation icon |

### Risk Level Visual Treatment
- **Controlled**: Green shield icon, solid green border
- **Partial**: Yellow shield icon, dashed yellow border, "!" annotation
- **Unmitigated**: Red "X" or empty shield outline, red border
- **Unknown**: Grey "?" marker — not yet assessed

## Companion Materials

A threat model diagram should be paired with:
- **Threat-mitigation table**: Detailed mapping of each threat to its controls, evidence, and residual risk
- **Framework crosswalk**: Map threats to multiple frameworks (OWASP, STRIDE, MAESTRO, MITRE ATLAS)
- **Prioritized action list**: Ranked by risk level — what to fix first

## Title Format

`PROJECT — Threat Model: [Framework] [optional: Focus Area]`

Examples:
- `ADF — Threat Model: OWASP Agentic Top 10`
- `Sharp — Threat Model: Agent Attack Surface`
- `ADF — Attack Tree: Prompt Injection via RAG Poisoning`

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Threats without mitigations | Always show what controls exist (or explicitly mark "unmitigated") |
| All threats shown with equal visual weight | Color-code by risk level — prioritize what matters |
| DFD without trust boundaries | Trust boundaries are what make a DFD a threat model — always include them |
| Box-checking STRIDE | Don't mechanically list all 6 categories for every element — consider actual adversary capabilities |
| Static diagram filed away | Include a version date and review cadence |
| Only showing defenses | Include at least one attack path to show what the defenses protect against |
| Too much detail in one diagram | Use overview + detail diagrams, or diagram + companion table |
| Missing framework tags | Label threats with their framework IDs (ASI01, STRIDE category, etc.) |
| Generic architecture instead of threat model | Name specific threats, not just "security" — be precise about what can go wrong |
| Mixing attacker and defender perspectives | Choose one primary perspective per diagram (or use attack-defense trees with clear color coding) |
| No legend | Include a legend for colors, shapes, line styles, and risk indicators |
| Functional DFD passed off as threat model | Ensure DFDs include security context: encryption status, access controls, validation points |
