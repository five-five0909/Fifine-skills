# Google Cloud Architecture Style

This style follows the official Google Cloud Architecture visual design system as documented in the GCP Official Icons and Solution Architectures guide and published reference architectures at cloud.google.com/architecture. Use it for GCP architectures, multi-cloud diagrams, or any diagram where clean Google-style aesthetics are desired.

**Official icon source**: https://cloud.google.com/icons (SVG + PNG, 2025 icon system)

## Design System Block

Prepend this to every prompt when using the Google Cloud style:

```
Create a professional, publication-quality architecture diagram following the official Google Cloud Architecture visual design system. Apply these strict rules:

CANVAS: Pure white background (#FFFFFF). No background pattern, gradient, texture, or watermark. Generous whitespace — minimum 40px between all elements. Clean, uncluttered composition.

PRODUCT CARDS — this is the standard card used for ALL components (containers, services, data stores, external systems):
- Shape: Rounded rectangle, 6px corner radius
- Background: White (#FFFFFF)
- Border: Thin gray (#DADCE0), 1px
- NO colored header bar. NO shadow. Clean and flat.
- Layout inside the card:
  - LEFT side: Product/service icon, ~32-40px, monochrome blue (#4285F4) or official product icon
  - RIGHT of icon, two lines of text:
    - Line 1: Component name in bold dark text (#202124), 11-12pt
    - Line 2: Product/technology name in regular gray text (#5F6368), 10pt
  - Optional Line 3: Brief description in gray 9pt (only when needed for clarity)
- Card sizing: roughly 160-220px wide, 50-70px tall. Keep cards compact.
- ALL cards follow this same pattern regardless of whether they are internal containers, data stores, or external systems. The zone background color communicates ownership, not the card style.

CARD VARIATIONS FOR DIFFERENT ELEMENT TYPES:
- Internal containers: Standard product card (icon-left, name, technology). Sits inside the system boundary zone.
- Data stores: Same card layout. Use a database/storage icon. Sits inside the system boundary zone.
- External systems: Same card layout. Sits inside an external/consumer zone (pink/salmon background) or outside all zones.
- The visual distinction between internal and external comes from the ZONE they sit in, not from a different card style.

USER/PERSON CARDS:
- Shape: Rounded rectangle with a user silhouette icon (circle head + shoulders) inside
- Soft blue-gray (#E8EAED) background fill — this is the ONE card type that gets a tinted background
- Name and one-line description in dark text
- Placement: LEFT side or TOP of diagram, VERTICALLY CENTERED with the system boundary

ZONES (containment boxes for grouping and boundaries):
Zones are colored background rectangles that group related cards. They communicate ownership, domain boundaries, and infrastructure topology.

Zone color palette:
- Light blue (#E8F0FE ~30%) — primary system boundary, "Google Cloud", main domain
- Light yellow/cream (#FEF7E0 ~30%) — sub-groupings within the domain: "Product interface", "Data ingest", "All curated data"
- Light pink/salmon (#FCE8E6 ~25%) — external consumers, outside boundaries
- Light green (#E6F4EA ~25%) — alternative domain or partner grouping
- Light gray (#F8F9FA) — on-premises, generic external

Zone rules:
- Rounded rectangle, no visible border (or very faint #DADCE0 if nesting requires clarity)
- Zone label: top-left corner, in colored text matching the zone's accent color, 12-14pt medium weight
  - Blue zone → blue label text (#4285F4)
  - Yellow zone → dark text (#202124) or golden text
  - Pink zone → dark text (#202124) or muted red
- Zones nest: Organization > Project > VPC > Region > Zone > Subnet > Services
- Consistent internal padding (~16-24px)
- DASHED borders ONLY for infrastructure boundaries (regions, availability zones, VPCs) — not for logical groupings

ANNOTATIONS AND FLOW NUMBERING:
- Numbered steps: Blue (#4285F4) filled circles with white numbers (1, 2, 3...) placed along the flow path
- Step descriptions in an explanatory legend (numbered list) at the bottom or side
- This numbered-step pattern is a hallmark of official Google Cloud reference architectures
- Annotation callouts: Light yellow (#FFF9C4) rounded box with dark text for caveats or notes

COLORS — The diagram palette is primarily gray + white + blue. Color restraint is key.
Accent colors appear mainly in the product icons themselves, NOT splashed across card backgrounds or connectors.

Primary palette:
- Google Blue #4285F4: Primary accent, zone highlights, flow step numbers, connector lines
- Blue 100 #D2E3FC: Light blue fills for emphasized zones
- Blue 50 #E8F0FE: Lightest blue tint for zone backgrounds
- Gray 900 #202124: Primary text, card names (bold)
- Gray 700 #5F6368: Secondary text, product names, descriptions, arrow labels
- Gray 500 #9AA0A6: Tertiary text, disabled states
- Gray 300 #DADCE0: Card borders, divider lines
- Gray 200 #E8EAED: Person card background
- Gray 100 #F1F3F4: Light zone backgrounds
- Gray 50 #F8F9FA: Lightest zone fill
- White #FFFFFF: Card backgrounds, diagram canvas
- Yellow 50 #FEF7E0: Sub-grouping zone fills
- Pink 50 #FCE8E6: External/consumer zone fills
- Green 50 #E6F4EA: Alternative domain zone fills

Brand colors (appear in official 4-color product icons ONLY — do not use for zones or connectors):
- Google Red #EA4335
- Google Yellow #FBBC04
- Google Green #34A853

TYPOGRAPHY: Sans-serif font family. Preference order: Google Sans > Open Sans > Roboto > system sans-serif.
- Diagram title: 18-24pt Bold, #202124
- Zone labels: 12-14pt Medium, colored to match zone accent
- Card name (line 1): 11-12pt Bold, #202124
- Card technology (line 2): 10pt Regular, #5F6368
- Card description (line 3): 9pt Regular, #5F6368
- Annotations/notes: 9-11pt Regular/Italic, #5F6368
- Arrow labels: 9-10pt Regular, #5F6368
- Legend text: 9-10pt Regular, #5F6368
- Product names in Title Case; descriptions in sentence case
- Max 3 lines of text per card

CONNECTORS:
- ORTHOGONAL ONLY — every segment perfectly horizontal or vertical, 90-degree turns. NO diagonals. NO curves. NO arcs.
- Blue (#4285F4) solid lines, 1.5px stroke width
- Arrowheads: Small filled blue triangles, pointing in direction of flow
- All arrows UNIDIRECTIONAL — no two-headed arrows
- Dashed blue lines for: return paths, optional flows, async communication, infrastructure relationships
- Arrow labels: 9pt #5F6368, placed ABOVE horizontal segments, RIGHT of vertical segments
- One label per arrow, verb-led phrase (2-6 words)
- Each relationship has exactly ONE arrow — no duplicate arrows between the same two elements
- Minimize crossings — reorganize spatial layout rather than allowing lines to cross

HIERARCHY & LAYOUT:
- The PRIMARY SYSTEM is placed in the center of the diagram, inside a light blue zone
- Person elements on the LEFT side, VERTICALLY CENTERED with the system boundary
- External systems on the RIGHT side or in pink/salmon zones
- Left-to-right primary flow: Users → System → Dependencies
- Elements aligned on an invisible grid; equal spacing between cards
- No arrow should cross another arrow — rearrange layout to prevent crossings

LEGEND: Bottom-right corner. Small horizontal row. Only include categories actually present. Use the zone color swatches (blue = internal, pink = external, etc.) rather than card-style differences, since all cards share the same white style.

GENERAL:
- NO duplicate components — each appears exactly once; route multiple arrows to it
- NO decorative elements — no background patterns, watermarks, textures, ornamental elements
- The aesthetic is clean, flat, and minimal — very "Google". White cards on colored zones. Blue connectors and icons provide the only color accents.
- 16:9 aspect ratio
- All text must be crisp, legible, and correctly spelled
```

## Official GCP Icon System (2025)

In 2025 Google overhauled all product icons, reducing from 250+ unique icons to ~40. Two tiers:

### Core Product Icons (4-color, unique shape per product)
These use the full Google brand 4-color palette with distinctive shapes:

AlloyDB, Anthos, Apigee, BigQuery, Cloud Run, Cloud SQL, Cloud Storage, Compute Engine, GKE, Google Distributed Cloud, Google Security Operations, Hyperdisk, Looker, Mandiant, Operations, Security Command Center, Spanner, Vertex AI, AI Hypercomputer, Google Threat Intelligence

### Category Icons (2-color, shared across products in same category)
All other products use a 2-color category icon:

AI/ML, Business Intelligence, Compute, Containers, Data Analytics, Databases, Developer Tools, DevOps, Hybrid & Multicloud, Integration Services, Management Tools, Networking, Observability, Security and Identity, Serverless, Storage

**Important**: Legacy 2-tone blue console icons are deprecated. Use the 2025 icon system.

**Download**: https://cloud.google.com/icons (SVG and PNG ZIP)

## When to Use This Style

- Google Cloud Platform (GCP) architectures
- Multi-cloud or cloud-agnostic diagrams (neutral professional look)
- Azure or AWS diagrams when no provider-specific style is available yet
- Any diagram where clean, minimal, Google-style aesthetics are desired

## What Makes It Look "Google"

1. **White product cards with icon-left layout** — no colored header bars. Icon on left, name + technology on right. Thin gray border. Every card looks the same.
2. **Colored zones communicate boundaries** — light blue for internal, yellow for sub-groups, pink for external/consumers, green for alternate domains. The zone background — not the card style — tells you where something belongs.
3. **White canvas** — always white background
4. **Official icons** — every GCP product uses its official monochrome blue icon; non-GCP services get an icon from the icon library
5. **Blue as the dominant accent** — #4285F4 ties everything together: connector lines, icons, step numbers, zone labels
6. **Generous whitespace** — elements breathe, never cramped
7. **Orthogonal connectors in blue** — straight blue lines with 90-degree turns only
8. **Numbered flow steps** — blue circles with white numbers, explanatory legend
9. **Dashed borders for infrastructure** — regions and zones use dashed lines for a lighter feel
10. **Sans-serif typography** — Google Sans / Open Sans / Roboto
11. **Color restraint** — palette is gray + white + blue + subtle zone tints. Clean and flat.
12. **Hierarchical containment** — nested zones communicate topology through visual nesting
13. **No decoration** — no patterns, watermarks, textures, gradients, shadows, or ornamental elements

## Color Quick Reference

| Color | Hex | Usage |
|-------|-----|---------|
| Google Blue | #4285F4 | Primary accent, icons, connectors, step numbers |
| Blue 100 | #D2E3FC | Light blue zone fills |
| Blue 50 | #E8F0FE | System boundary zone background |
| Yellow 50 | #FEF7E0 | Sub-grouping zone fills |
| Pink 50 | #FCE8E6 | External/consumer zone fills |
| Green 50 | #E6F4EA | Alternative domain zone fills |
| Gray 900 | #202124 | Primary text, card names |
| Gray 700 | #5F6368 | Secondary text, product names, descriptions |
| Gray 500 | #9AA0A6 | Tertiary text, disabled |
| Gray 300 | #DADCE0 | Card borders, dividers |
| Gray 200 | #E8EAED | Person card background |
| Gray 50 | #F8F9FA | Default zone fill |
| White | #FFFFFF | Canvas, card backgrounds |
| Google Red | #EA4335 | In product icons only |
| Google Yellow | #FBBC04 | In product icons only |
| Google Green | #34A853 | In product icons only |
| Yellow | #FFF9C4 | Annotation/caveat boxes |

## Shared Visual Primitives

Reusable building blocks used across multiple diagram types. Define once here;
reference by name from the per-type references rather than re-specifying. (See
`references/best-practices.md` §7.)

### Status badge + standardized status colors

A small pill/badge attached to a card to convey its status. **One color set for
the whole skill** — never invent a per-diagram green/amber/red meaning; if a type
needs a domain mapping, state it in that diagram's legend and keep the palette.

- Green `#34A853` — on-track / complete / net-new (BUILD) / matched
- Amber `#F29900` — at-risk / in-progress / needs-attention
- Red `#EA4335` — blocked / error / non-compliant
- Grey `#9AA0A6` — external / existing / not-in-scope / n-a
- Blue `#4285F4` — informational / current

Two common label families ride on this palette: **lifecycle** (`NEW` / `BUILD` /
`EXISTING` / `EXTERNAL`) and **RAG** (`On track` / `At risk` / `Blocked`). Badge:
small rounded pill, colored border + light fill of the same hue, 8–9pt label.
Always pair with a legend row — color alone is never the sole signal.

### Stat / KPI callout card

A tile that states one number prominently. Used in exec/overview contexts and any
diagram summarizing outcomes.

- One **big number** (24–44pt, Google Blue or status color) + a short label
  (≤4 words) + optional delta arrow (▲▼) and/or a benefit icon.
- Prefer **contrast pairs** ("40 hrs → 4 hrs") or **deltas** ("−90%") over bare
  figures — a number needs a baseline.
- **Provenance is mandatory** (best-practices §4): every stat is sourced or
  visibly labeled `illustrative` / `target` / `projected`.
- Keep to **3–4 per view**; a wall of numbers reads as noise.

### Milestone & current-position markers

- **Milestone marker** — a small diamond or `Material: Flag` on a
  boundary/timeline point; green if achieved, blue if upcoming. Always named and
  (where relevant) dated.
- **Current-position ("you are here") marker** — a vertical `#4285F4` accent line
  + pin label indicating the present point on a timeline/progression.

### Collapsed-subsystem card

A single card standing in for N hidden internal elements, used to respect density
limits (best-practices §2). Label it with the subsystem name + a cardinality hint
(e.g., "Agent Layer [6 specialist agents]"). A sibling diagram may explode it.
Uses the standard product-card grammar — not a new card style.

### Scope / posture callout

A labeled use of the existing **annotation callout** (yellow `#FFF9C4` rounded
box, dark text) that states a diagram's scope, posture, or caveat in one
declarative line (e.g., "Recommendations-only today; extensible to action";
"Pilot scope — Great Lakes East"). Place bottom-center or a corner. One per view,
two max.
