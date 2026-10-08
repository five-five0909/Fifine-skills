# Concentric Rings / Containment Diagram Reference

> Deep reference for Concentric Ring diagrams showing layers of protection, isolation, or abstraction. Supplements `diagram-types.md` with guidance from defense-in-depth models, Clean Architecture, cloud blast radius patterns, Zero Trust, and AI agent containment architectures.
>
> **Sources**: Microsoft Azure defense-in-depth, Robert C. Martin's Clean Architecture, AWS fault isolation boundaries, CSA cloud blast radius, Zero Trust architecture, OWASP agentic application security, CPU protection rings (Ring 0–3), consulting bullseye diagrams.

## What is a Concentric Ring Diagram?

A concentric ring diagram shows **layers radiating outward (or inward) from a central element**, where each layer represents a boundary of protection, abstraction, or containment. It answers: "What layers of protection/abstraction surround the core, and what does each layer provide?"

- **Scope**: Defense-in-depth, architectural layering, blast radius containment, or strategic prioritization
- **Primary shape**: Concentric circles/rings with a distinct center element
- **Audience**: Security teams, architects, executives — anyone assessing layered protection or abstraction
- **Key insight**: Each ring is a boundary — breaching one ring doesn't mean breaching all

## When to Use

- **Defense-in-depth**: Showing security control layers from perimeter to data
- **Blast radius containment**: Showing what's affected if a component fails or is compromised
- **Architectural layering**: Clean Architecture / Onion Architecture — dependency direction
- **Agent containment**: Showing isolation layers around an AI agent's capabilities
- **Strategic prioritization**: Core/adjacent/transformational rings (bullseye pattern)
- **Trust boundaries**: Zero Trust architecture — verification gates at each ring

## Core Elements

| Element | Visual Treatment | Description |
|---------|-----------------|-------------|
| **Center element** | Circle at the core, visually distinctive | The protected asset, core capability, or primary concern |
| **Ring** | Concentric band around center | One layer of protection/abstraction/containment |
| **Ring label** | Text on or inside the ring | What this layer provides or represents |
| **Boundary gate** | Small icon on ring border | Verification checkpoint, API boundary, or security control |
| **Breach/flow arrow** | Arrow crossing rings | Attack path, data flow, or dependency direction |
| **Legend item** | Color swatch + label | Explains what each ring color means |

## Composition Rules

### Ring Count
| Count | Character | Best For |
|-------|-----------|----------|
| 3 | Simplest effective model | Executive summaries, strategic bullseyes (Core/Adjacent/Transformational) |
| 4 | Clean Architecture standard | Onion Architecture, basic defense-in-depth |
| 5 | Balanced detail | Security layers, agent containment models |
| 6–7 | Maximum detail | Full defense-in-depth (Physical → Identity → Perimeter → Network → Compute → Application → Data) |
| 8+ | Almost never | Decompose or use nested rectangles instead |

### Center Element Design
The center must be the **most visually distinctive element**:
- Largest text or icon in the diagram
- Strongest color saturation
- Clear label: what is being protected, contained, or prioritized
- For security: the protected asset (data, agent runtime)
- For architecture: the core domain/business logic
- For strategy: the core offering or competency

### Direction Convention
Two valid directions — choose one and be explicit:
| Convention | Center Meaning | Outer Meaning | Use When |
|------------|---------------|---------------|----------|
| **Protect inward** | Most protected/valuable | First line of defense | Defense-in-depth, blast radius |
| **Depend inward** | Most abstract/stable | Most concrete/volatile | Clean Architecture, dependency inversion |

### Boundary Emphasis
Ring boundaries are where the action happens — where verification, translation, or protection occurs:
- Show boundaries as **thick lines** (thicker than ring fill)
- Add **gate icons** (lock, shield, checkpoint) at boundaries where verification occurs
- Label boundaries with what happens there: "Authentication", "Input validation", "Sandboxing"

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Rings | 3–5 | 7 |
| Labels per ring | 2–4 | 6 |
| Breach/flow arrows | 1–2 | 4 |
| Boundary gate annotations | 3–5 | 8 |
| Total text elements | 15–20 | 30 |

## Layout Rules

### Ring Sizing
- **Equal ring width** — each ring should be approximately the same radial thickness
- Don't let inner rings be proportionally tiny — this distorts visual importance
- Center element radius ≈ smallest ring width

### Reading Order
- Label rings from **inside out** or **outside in** — pick one and be consistent
- If numbered, number from center outward (Ring 0 = center, Ring 1 = first layer, etc.)
- Or number from outside in if showing an attack path (attacker starts outside)

### Text Placement
- **Inside the ring**: Short labels, curved or straight along the band
- **Outside with leader lines**: For detailed annotations — keeps rings clean
- **Avoid crossing text over ring boundaries** — text belongs clearly to one ring

### Quadrant Annotations
For detailed rings, divide into quadrants or sectors:
- Top-right: Primary capability/control for this layer
- Bottom-right: Monitoring/detection at this layer
- Bottom-left: Response/recovery at this layer
- Top-left: Prevention/hardening at this layer

## Color Conventions

### Warm-to-Cool Gradient (Defense-in-Depth)
- **Red/warm center**: Highest value, needs most protection
- **Orange → Yellow → Green → Blue outward**: Decreasing proximity to the core
- Creates visual urgency toward the center

### Cool-to-Warm Gradient (Blast Radius)
- **Blue/cool center**: The source of the blast
- **Green → Yellow → Orange → Red outward**: Increasing blast damage
- Shows impact expanding outward

### Distinct Hues (Clean Architecture / Strategic)
- Each ring gets its own color from a harmonious palette
- Ensures clear visual separation between layers
- Works best with 3–4 rings

### Breach Visualization
- **Attack arrow**: Red arrow cutting through rings from outside to inside
- **Swiss Cheese overlay**: Gaps in ring boundaries showing where controls have holes
- **Cascade failure shading**: Progressive darkening of rings as a failure propagates

## Specific Pattern: Agent Blast Radius

For AI agent containment (the primary ADF use case):

```
Ring 5 (outermost): External Systems / Data Sources
Ring 4: Tool Access Layer (MCP servers, APIs)
Ring 3: Agent Runtime (execution sandbox)
Ring 2: Memory & State (context, long-term memory)
Ring 1 (center): Model Inference (LLM core)
```

**Unique duality**: The agent is both the **protected asset** (center needs defense from external threats) AND the **potential source of harm** (agent actions need containment from spreading outward). Show this with bidirectional arrows or dual-color boundary treatment.

**Boundary gates**: Model Armor (Ring 1→2), guardrails (Ring 2→3), sandboxing (Ring 3→4), auth/RBAC (Ring 4→5)

## Concentric Rings vs. Nested Rectangles

| Rings | Rectangles |
|-------|-----------|
| Conceptual symmetry — all directions equally protected | Asymmetric detail — different edges can show different aspects |
| Better for abstract/strategic communication | Better for implementation detail |
| Works with 3–5 layers | Works with any number of layers |
| Harder to annotate densely | Easier to add detailed labels and sub-components |
| Immediate visual "protection" metaphor | Better for showing actual deployment structure |

**Rule of thumb**: Use rings for conceptual/strategic diagrams, rectangles for implementation detail.

## Title Format

`PROJECT — [Containment Model | Blast Radius | Architecture Layers]: [Focus]`

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Too many rings (8+) | Consolidate related layers or use nested rectangles instead |
| Area distortion (tiny inner rings) | Use equal ring widths so all layers have comparable visual weight |
| No reading order indicated | Number rings or clearly label inside-out vs. outside-in |
| Cluttered annotations inside rings | Move detailed text to external callouts with leader lines |
| Missing boundary labels | Show what happens at each ring boundary (the verification/control) |
| Center element too small | The center should be the most visually prominent element |
| Color without meaning | Every color must map to a documented meaning in the legend |
| No legend | Include a legend mapping rings to their purpose and colors to their meaning |
| Mixing abstraction levels | All rings should be at the same conceptual level (all security controls, or all architectural layers, not mixed) |
| Showing only defense, no threat | Include at least one breach/attack arrow to show what the rings protect against |
