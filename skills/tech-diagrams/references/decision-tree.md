# Decision Tree / Flowchart Diagram Reference

> Deep reference for Decision Tree and Flowchart diagrams used for technology selection, pattern selection, or process routing. Supplements `diagram-types.md` with guidance from ISO 5807, UML activity diagrams, clinical decision algorithms, and cloud provider decision guides.
>
> **Sources**: ISO 5807 flowchart standard, UML activity diagram conventions, NCCN/ACEP clinical decision algorithms, Azure/AWS/GCP decision trees, flowchart design best practices.

## What is a Decision Tree Diagram?

A decision tree shows **a series of questions or conditions that lead to a recommended outcome** — each branch point narrows the options until arriving at a specific recommendation. It answers: "Given my constraints, which option should I choose?"

- **Scope**: One decision domain (e.g., "which agent pattern?" or "which database service?")
- **Primary elements**: Decision diamonds, process rectangles, terminal rounded rectangles
- **Audience**: Architects, developers, decision-makers evaluating options
- **Key insight**: The tree's value is in the questions it asks, not just the answers it gives

## When to Use

- **Technology selection**: Which cloud service, framework, or pattern for a given use case
- **Pattern selection**: Which agent architecture pattern given task complexity
- **Process routing**: Which workflow path based on input characteristics
- **Troubleshooting**: Diagnostic flowcharts for debugging common issues
- **Compliance checks**: Regulatory or policy decision flows

## Core Elements

| Element | Shape | Description |
|---------|-------|-------------|
| **Start** | Rounded rectangle (stadium) | Entry point — states the decision domain |
| **Decision** | Diamond | Question node — ask a discriminating question |
| **Process** | Rectangle | Information-gathering or intermediate action step |
| **Terminal** | Rounded rectangle (stadium) | Recommended outcome — names the answer + brief rationale |
| **Connector** | Small circle with label | Cross-reference to another part of the tree (avoids long crossing lines) |
| **Annotation** | Open bracket + text (dashed line to node) | Evidence level, edge case, caveat, or footnote |

## Composition Rules

### Decision Node Design
- **Phrase as questions**, not conditions: "Does the task require multiple tools?" not "[tools > 1]"
- **Binary branching preferred** (Yes/No) — forces clarity
- Multi-way branching allowed (up to 4 exits) when options are truly parallel
- **Guard conditions must be mutually exclusive and collectively exhaustive** — every possible state must be covered

### Branch Labeling
- **Consistent direction convention**: "Yes" always goes **down** (main path continues), "No" always goes **right** (alternative)
- If multi-way: label each exit with its condition value
- **Never leave an exit unlabeled** — this is the #1 flowchart error

### Terminal Nodes
- Name the **recommended outcome** (e.g., "Use Orchestrator-Worker Pattern")
- Include a **one-line rationale** (e.g., "Best for parallel tasks with a central coordinator")
- Color-code by complexity tier or confidence level

### Convergence
When multiple paths lead to the same recommendation:
- **2–3 converging paths**: Use a shared terminal node with multiple incoming arrows
- **4+ converging paths**: Use labeled connector circles pointing to a shared outcome
- Place terminal nodes in a **right-side or bottom "outcomes column"** for visual clarity

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Tree depth (root to deepest terminal) | 5 levels | 7 levels |
| Branch factor (exits per decision) | 2 (binary) | 4 |
| Total nodes in diagram | 15–20 | 30 |
| Terminal nodes (unique outcomes) | 5–8 | 12 |
| Text per node | 5–15 words | 25 words |
| Line crossings | 0 | 2–3 |

### When Limits Are Exceeded
- **Too deep (>7 levels)**: Decompose into linked sub-trees with connector circles
- **Too wide (>4 branches at one node)**: Chain binary decisions or convert to a table
- **Too many total nodes (>30)**: Split by decision dimension (separate tree per concern)
- **Too many terminals (>12)**: Group recommendations into categories; two-stage decision

## Layout Rules

### Flow Direction
- **Top-to-bottom** — matches natural reading order and is the dominant convention
- Root/start node at **top center**
- Decision nodes centered, with "Yes" going down and "No" going right
- Terminal nodes accumulate at the **bottom or right edge**

### Spacing
- **Even spacing** between nodes on the same level
- Extra space around diamonds to accommodate branch labels
- Consistent node sizing — all diamonds same size, all rectangles same width
- Align nodes on an implicit grid

### Readability
- Maximum width: viewable without horizontal scrolling (~1200px at readable font sizes)
- If wider, decompose into linked sub-diagrams
- Minimize line crossings — use connectors or rearrange layout

## Color Conventions

| Purpose | Color |
|---------|-------|
| Decision diamonds | White fill, standard border |
| Terminal — simple/common | Green fill (#34A853) or green border |
| Terminal — moderate complexity | Yellow/amber fill (#F29900) or amber border |
| Terminal — advanced/complex | Red/orange fill (#EA4335) or red border |
| Process boxes | Light grey fill (#F1F3F4) |
| Recommended/"happy path" | Thicker line weight or accent-colored arrows |
| Annotations | Grey text, dashed connector line |

### Happy Path Highlighting
- Use **thicker line weight** or a distinct accent color for the most common path
- This creates a "fast path" that experienced readers can follow without reading every decision
- Include a callout: "Most common path: If [condition], go directly to [outcome]"

## Annotation Conventions

- **Numbered footnotes**: Superscript number next to node, detail below the tree
- **ISO 5807 style**: Open bracket with text, connected by dashed line to the relevant node
- **Evidence/confidence levels**: "Based on [source]", "Strong recommendation", "Emerging pattern"
- **Edge case warnings**: "Not recommended for latency-sensitive workloads"
- **Version/date info**: Decision trees for technology choices should include a date

## Companion Materials

A decision tree works best paired with:
- **Quick-reference table**: "If your use case is X, use Pattern Y" — lets experienced users skip the tree
- **Feature comparison matrix**: Detailed comparison of the terminal outcomes
- **Entry-point shortcuts**: For users who already know some constraints, provide multiple entry points

## Title Format

`PROJECT — Decision Tree: [Decision Domain]`

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Unlabeled decision branches | Every exit from a diamond MUST be labeled with its condition |
| Ambiguous questions | "Is the system complex?" → "Does the system require more than 3 data sources?" |
| Missing paths / dead ends | Every decision must account for all possible outcomes |
| Inconsistent branch direction | Pick a convention (Yes=down, No=right) and maintain it throughout |
| Process steps in diamonds | Diamonds contain ONLY questions/conditions, never actions |
| No start/end nodes | Every tree must have a clear entry and at least one terminal |
| Too much text in nodes | Keep to 5–15 words; use annotations for detail |
| Spaghetti lines | Use connector circles rather than long crossing lines |
| No "fast path" indication | Highlight the most common recommendation path |
| Duplicate terminal nodes | Use convergence (shared terminals or connectors) instead |
| Missing legend | Include a legend for color coding, line styles, and annotation conventions |
| No date/version | Technology selection trees go stale — always include a version date |
