# Layered Ecosystem Map Reference

> Deep reference for Layered Ecosystem diagrams that show how a product/framework sits within a larger technology stack. Supplements `diagram-types.md` with guidance from cloud platform models, analyst firm conventions, and strategic positioning patterns.
>
> **Sources**: Google Cloud Enterprise GenAI Blueprint, Forrester three-plane model, PlatformSpec.io canonical layers, AIMultiple agentic AI stack, Wardley mapping concepts, Gartner AI Control Plane.

## What is a Layered Ecosystem Map?

A layered ecosystem map shows **where a product/framework sits within a technology stack** using horizontal layers that represent abstraction levels, dependencies, or ownership boundaries. It answers: "How does this fit into the bigger picture?"

- **Scope**: Full technology stack from infrastructure to application/user layer
- **Primary elements**: Horizontal layers, services/components within layers, cross-cutting sidebars
- **Audience**: Executives, practice leaders, sales — anyone needing to understand strategic positioning
- **Key insight**: The diagram's value is in showing what you own vs. what you depend on vs. what customers bring

## When to Use

- **Product positioning**: Showing where your framework sits relative to cloud provider services
- **Technology stack overview**: Full view from infrastructure up to application delivery
- **Dependency mapping**: What layers depend on what
- **Sales enablement**: Communicating value-add relative to existing customer investments
- **Strategic planning**: Identifying gaps, overlaps, and build-vs-buy decisions

## Core Elements

| Element | Visual Treatment | Description |
|---------|-----------------|-------------|
| **Layer** | Full-width horizontal band with label | Abstraction level (e.g., "Infrastructure", "AI Platform", "Application") |
| **Service/Component** | Rounded rectangle within a layer | Individual technology or capability (e.g., "Cloud Run", "Agent Engine", "Model Armor") |
| **Cross-cutting Concern** | Vertical sidebar spanning multiple layers | Capability that applies across layers (e.g., "Security", "Observability", "Governance") |
| **Ownership indicator** | Color coding | Distinguishes "our layer" from "platform" from "customer" |
| **Integration point** | Small connector icon between layers | Where layers interact — APIs, events, shared data |

## Layer Composition Rules

### Layer Count
| Count | Use When |
|-------|----------|
| 3 layers | Executive summary — maximum simplification |
| 4–5 layers | Standard presentation — balances detail and clarity |
| 6–7 layers | Technical deep dive — only with expert audience |
| 8+ layers | Almost never — decompose into multiple diagrams instead |

### Layer Ordering
- **Bottom**: Infrastructure / foundation (closest to hardware/cloud primitives)
- **Middle**: Platform services, orchestration, shared capabilities
- **Top**: Application layer, user-facing experiences, business logic
- **Reading direction**: Bottom-up for "what supports what", top-down for "what the user sees first"

### Layer Content
- **3–7 items per layer** — enough to communicate capability without overwhelming
- Items within a layer are **peers** (same abstraction level, same ownership tier)
- If a layer has more than 7 items, consider splitting the layer or grouping related items

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Layers | 4–5 | 7 |
| Items per layer | 3–5 | 7 |
| Total items across all layers | 15–25 | 35 |
| Cross-cutting sidebars | 1–2 | 3 |
| Integration point annotations | 3–5 | 8 |

## Layout Rules

### Standard Layout
```
┌─────────────────────────────────────────────┐
│  APPLICATION LAYER                          │  ← User-facing
│  ┌─────┐  ┌──────┐  ┌──────┐              │
│  │App A│  │App B │  │App C │              │
│  └─────┘  └──────┘  └──────┘              │
├─────────────────────────────────────────────┤
│  PLATFORM SERVICES            ┌──────────┐ │
│  ┌──────┐ ┌──────┐ ┌──────┐  │          │ │
│  │Svc 1 │ │Svc 2 │ │Svc 3 │  │ SECURITY │ │  ← Cross-cutting
│  └──────┘ └──────┘ └──────┘  │          │ │     sidebar
├──────────────────────────────│          │─┤
│  INFRASTRUCTURE               │          │ │
│  ┌──────┐ ┌──────┐ ┌──────┐  │          │ │
│  │Infra │ │Infra │ │Infra │  └──────────┘ │
│  └──────┘ └──────┘ └──────┘              │
└─────────────────────────────────────────────┘
```

### Spatial Rules
- Layers span **full diagram width** — no partial layers
- Items within a layer are **left-aligned or evenly distributed**
- Cross-cutting sidebars sit on the **right edge** as a vertical bar
- Layer labels on the **left side** outside the layer boundary, or as a bold header inside

### Ownership Coloring
- **Blue (#4285F4 family)**: Cloud provider / platform services you depend on
- **Green (#34A853 family)** or **Orange (#F29900 family)**: Your value-add layer — what you build/own
- **Grey (#9AA0A6 family)**: Customer-owned or third-party components
- **Saturated color** for the focal layer (your product); **muted tones** for surrounding context

### Emphasis Technique
The layer where your product/framework lives should be visually prominent:
- Slightly taller band height
- Stronger border
- Saturated fill color
- Items within it labeled with more detail

## Arrow Conventions

- **Vertical arrows between layers**: Show dependencies (lower layers support upper layers)
- Use sparingly — implied by layer ordering. Only draw arrows when the dependency path is non-obvious
- **Horizontal arrows within a layer**: Show peer interactions (generally avoid — clutters the diagram)
- If showing data flow, use thin grey arrows with labels; don't let flow arrows dominate the layer structure

## Title Format

`PROJECT — Technology Ecosystem [optional: for AUDIENCE]`

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Too many layers (8+) | Collapse related layers or split into multiple diagrams |
| All layers same visual weight | Emphasize the focal layer (your product) with color and detail |
| No ownership differentiation | Color-code by who owns/operates each layer |
| Items at wrong abstraction level | Ensure items within a layer are true peers — don't mix "Kubernetes" and "Cloud Run" with "Python" |
| Missing cross-cutting concerns | Security, observability, and governance typically span all layers — show as sidebars |
| Arrows everywhere | Only draw dependency arrows when the relationship is non-obvious |
| Generic labels | Use specific names ("Vertex AI Agent Engine", not "Agent Platform") |
| No legend | Include a legend mapping colors to ownership tiers |
| Mixing implementation and conceptual | Either show specific products (implementation) or capability categories (conceptual), not both |
| Layer boundaries unclear | Use distinct background colors or clear separator lines between layers |
