---
name: tech-diagrams
description: Generate professional technical diagrams for architecture, C4 models, networks, data flows, sequences, use cases, and cloud-style visual representations.
---


# Technical Diagram Generator

Generate publication-quality technical diagrams via Gemini 3.1 Flash image generation. Supports multiple visual styles and diagram types.

## Requirements

**Auth (pick one):**

- **Vertex + ADC (recommended for GCP / Cloud Run):** `GOOGLE_GENAI_USE_VERTEXAI=1`, `GOOGLE_CLOUD_PROJECT`, optional `GOOGLE_CLOUD_LOCATION`. Uses Application Default Credentials — no API key.
- **API key (local / AI Studio):** `GEMINI_API_KEY` (https://aistudio.google.com/apikey)

- Production model: `gemini-3.1-flash-image-preview` (fall back to `gemini-2.5-flash-image` for quick drafts)
- Fast rough-option model: `gemini-3.1-flash-lite-image` at 1K. When using it, read `references/flash-lite-rough-options.md` and follow its option-set, text-budget, manifest, and QA rules.
- `scripts/generate.py` (or `generate.sh`, which delegates to it) for image generation

## Icon Library

The skill maintains a library of verified brand icons in `icons/` to ensure visual consistency across diagrams.

**Structure:**
- `icons/registry.json` — manifest mapping system/service names (+ aliases) to icon PNG files
- `icons/*.png` — 256x256 transparent PNG icons

**How it works:**
- When building a request, `scripts/build-request.py` scans the prompt for system names matching the registry
- Matching icons are automatically embedded as inline image parts in the Gemini request
- The prompt is auto-appended with instructions telling Gemini to use the provided icons faithfully
- This ensures logos stay consistent across regenerations instead of being hallucinated differently each time

**Provider filtering (IMPORTANT):**
- Use `--provider gcp` (or `azure`, `aws`) to restrict icon matching to a single cloud provider
- This prevents cross-provider contamination (e.g., Azure Security icon injected into a GCP diagram)
- Icons are organized by provider prefix in their file paths: `gcp/`, `azure/`, `aws/`, `material/`
- Material Design icons are always included as universal fallbacks regardless of provider filter

**Every card must have an icon.** If no cloud-provider-specific icon exists for a service:
1. Check if a Material Design icon in `icons/google/material/` matches (monochrome, #4285F4 blue for GCP)
2. If not, download a Material Design icon from [fonts.google.com/icons](https://fonts.google.com/icons) in the matching style color
3. Save to `icons/google/material/` and register it — Material Design icons work across all providers

**Adding new icons:**
1. Find or download a clean icon PNG (icon-sized, no wordmark, transparent background, ~256x256)
2. Save it to the appropriate provider directory: `icons/gcp/`, `icons/azure/`, `icons/aws/`, or `icons/material/`
3. Add an entry to `icons/registry.json` with name, aliases, file, and description
4. The icon will automatically be injected into any future diagram that mentions that system

## Workflow

### 1. Determine Diagram Type and Style

Ask the user or infer from context:

**Diagram Types:**
- **C1 System Context** — system + external actors/systems
- **C2 Container** — internal deployable units grouped by concern
- **C3 Component** — internals of a single container
- **Network & Security** — access paths, trust boundaries, private endpoints
- **Data Flow** — end-to-end request lifecycle with numbered steps
- **Sequence** — temporal orchestration between components (numbered interactions)
- **Use Case Map** — feature/capability matrix showing scope coverage
- **Comparison / Split-Screen** — before/after, current/future, or option A vs. B side-by-side
- **Roadmap / Milestone Timeline** — phased delivery journey / rollout plan with milestones over time
- **Layered Ecosystem Map** — product positioning within a technology stack (horizontal layers)
- **Cyclical / Measurement Loop** — continuous process cycles (DevOps, FinOps, tokconomics)
- **Decision Tree / Flowchart** — question-driven selection leading to recommended outcomes
- **Deployment Topology** — where software runs on infrastructure (nested containment)
- **Concentric Rings / Containment** — layered protection, blast radius, or abstraction rings
- **Threat Model / Attack Surface** — attack vectors, threat categories, and mitigations

Read `references/best-practices.md` (shared cross-type rules — labeling, scope, honesty/provenance, and the reusable primitives) and `references/diagram-types.md` (summary of all types), then load the deep reference for the specific type:
- `references/best-practices.md` — cross-type rules + pointer to the Shared Visual Primitives in `styles/google-cloud.md`
- `references/c1-system-context.md` — comprehensive C1 rules, boundary decisions, labeling, anti-patterns
- `references/c2-container.md` — comprehensive C2 rules, container definition, ownership boundary, protocol labels
- `references/c3-component.md` — comprehensive C3 rules, component granularity, agent-specific patterns, layout checklist
- `references/sequence.md` — comprehensive sequence rules, agent delegation conventions, density limits, anti-patterns
- `references/data-flow.md` — comprehensive data flow rules, AI/ML patterns, DFD levels, transformation conventions
- `references/network.md` — comprehensive network & security rules, swim lanes, trust boundaries, private endpoints, hub-and-spoke, cloud-specific patterns
- `references/comparison.md` — split-screen conventions, shared structure principle, change marking
- `references/roadmap.md` — roadmap / milestone-timeline: phase bands, milestone & current-position markers, swimlanes
- `references/layered-ecosystem.md` — layer count guidance, ownership coloring, cross-cutting sidebars
- `references/cyclical-loop.md` — circular layout rules, center element patterns, tokconomics specifics
- `references/decision-tree.md` — ISO 5807 shapes, clinical algorithm conventions, convergence
- `references/flash-lite-rough-options.md` — 1K rough-option sets with three genuinely different compositions, stable IDs, manifests, and review rules
- `references/deployment-topology.md` — GCP resource hierarchy, C4 deployment conventions, scaling
- `references/concentric-rings.md` — defense-in-depth, agent containment, ring vs. rectangle
- `references/threat-model.md` — OWASP Agentic Top 10, STRIDE, MAESTRO, attack trees, bow-ties

**Styles:** Read the appropriate style file from `styles/`:
- `styles/google-cloud.md` — Google Cloud Architecture visual design system (default)
- More styles can be added (azure.md, aws.md, minimal.md, etc.)

### 2. Gather Content

Read relevant source files (architecture docs, design docs, code) to extract:
- Component names — use actual resource names, not generic labels
- Relationships and data flows
- External systems and integrations
- Network topology details (if applicable)

### 3. Assess Density

Before composing the prompt, count elements. Apply these hard limits:
- C1: max 6 external systems
- C2: max 8 containers per diagram — split if more
- C3: 5-15 components per diagram (sweet spot), max 20
- Network: max 3 swim lanes
- Data Flow: max 8 numbered steps
- Sequence: 6–9 participants (7 ± 2 sweet spot), max 15–20 messages

If over limit, split by concern and generate separate diagrams with clear titles (e.g., "C2a — Compute & Data Flow", "C2b — Security & Identity").

### 4. Compose the Prompt

Build the prompt by concatenating these layers:

```
[Style Design System Block]  ← from styles/*.md
+
[Diagram Type Instructions]  ← from references/diagram-types.md
+
[Content Specifics]          ← from your analysis in step 2
```

**CRITICAL RULES:**
- **Never pass external reference layout/diagram images to Gemini.** The model copies layouts too literally. All style rules must be encoded as text. (Small brand icons ARE fine — see Icon Library above.)
- **DO pass your own previously generated diagram** when creating variant views of the same base layout (e.g., path-highlight views). This ensures pixel-consistent card positions, sizes, icons, and labels across the set. See "Multi-View Diagram Sets" below.
- **Always use the icon library** — check `icons/registry.json` for matching systems and embed them via `build-request.py`.
- **Always include an ASCII layout diagram** in the prompt to ground spatial positions. Label rows/columns and describe which element goes where. This dramatically improves layout accuracy vs. text-only position descriptions.
- **Never use generic names** — use actual resource names from the project.
- **Never put named individuals** on diagrams — use team/org roles.
- **Always include a LEGEND** at the bottom with only the categories actually used.
- **Always specify 16:9 aspect ratio** for consistency.

### 5. Generate

Write the prompt text to a file, then use `build-request.py` to auto-inject matching icons and create the Gemini request JSON:

```bash
# Step 1: Write prompt text to a temp file
cat > /tmp/diagram-prompt.txt << 'PROMPT'
... your full prompt text here ...
PROMPT

# Step 2: Build request JSON with auto-injected icons (use --provider to avoid cross-cloud contamination)
python3 scripts/build-request.py /tmp/diagram-prompt.txt /tmp/diagram-request.json --provider gcp

# Step 3: Generate the image
scripts/generate.sh /tmp/diagram-request.json /path/to/output.png

# Flash Lite rough option (1K; pass the model explicitly)
scripts/generate.sh /tmp/diagram-request.json /path/to/output.png gemini-3.1-flash-lite-image
```

The `build-request.py` script:
- Scans the prompt for system names matching `icons/registry.json`
- Embeds matching icon PNGs as inline image parts
- Appends icon usage instructions if not already in the prompt
- Supports `--icons name1 name2` to explicitly select icons
- Supports `--aspect-ratio` (default: 16:9)

For simple diagrams with no registered icons, you can still build the request inline:

```python
import json

request = {
    "contents": [{"parts": [{"text": FULL_PROMPT}]}],
    "generationConfig": {
        "responseModalities": ["TEXT", "IMAGE"],
        "imageConfig": {"aspectRatio": "16:9"}
    }
}

with open("/tmp/diagram-request.json", "w") as f:
    json.dump(request, f)
```

### 6. Verify and Iterate

After generation:
1. Read the PNG with the Read tool to visually verify
2. Check: all labels legible? All elements present? Connectors orthogonal? No duplicates?
3. If issues found, **adjust the prompt text and regenerate** — do NOT pass the flawed image back as a reference

**Common fixes:**
- **Text garbled**: Simplify labels, reduce total text, spell out abbreviations
- **Too crowded**: Split into multiple diagrams, reduce element count
- **Wrong layout**: Be more explicit about spatial positions (TOP, CENTER, LEFT, BOTTOM-RIGHT)
- **Diagonal lines**: Re-emphasize "ORTHOGONAL ONLY" and "NO diagonals NO curves"
- **Missing icons**: Describe the icon shape explicitly (hexagon for GKE, cylinder for database, etc.)

### 7. Output

Save generated diagrams with descriptive filenames:
- Use the pattern: `{document-prefix}-{diagram-type}-{subject}.png`
- Example: `aip-sdd-c1-system-context.png`, `aip-sdd-data-flow.png`
- Place diagrams adjacent to the source document unless the user specifies otherwise

## Multi-View Diagram Sets

When a diagram needs to show multiple flows or paths (e.g., a C3 with alternate routing paths), generate a **set of views** from the same base layout rather than cramming everything into one cluttered diagram.

**Pattern (inspired by Google Cloud RAG reference architecture):**

1. **Generate the Overview first.** This is the base diagram showing all components at full color with relationship labels but NO numbered flow steps. Get this approved before proceeding.

2. **Generate path-highlight views** by passing the approved overview PNG as `--base-image` to `build-request.py`. Write a **short, delta-only prompt** — do NOT repeat the full style system. Instead, frame the prompt as modifications to the reference:
   - "Reproduce this diagram EXACTLY. The ONLY changes are:"
   - List arrows to REMOVE (inactive path)
   - List numbered arrows to ADD (active path, with circle number, label, and routing)
   - List arrows to KEEP unchanged (shared infra)
   - Specify grayed-out cards if applicable
   - Change the subtitle
   - Explicitly say "Do NOT move any cards. Do NOT change any labels."

3. **Each view highlights ONE flow path.** Inactive elements remain visible but faded, providing spatial context without visual competition. The shorter and more surgical the prompt, the more faithfully Gemini reproduces the base layout.

**Workflow:**
```bash
# Step 1: Generate and approve the overview
scripts/generate.sh overview-request.json overview.png

# Step 2: Build path view requests that include the overview as a reference
python3 scripts/build-request.py path-prompt.txt path-request.json --base-image overview.png
```

**Graying technique:**
- Active cards: full color, dark text, colored icons
- Inactive cards: #F8F9FA background, #DADCE0 text and icons, no arrows
- Zones stay at full color in all views
- LiteLLM/shared infra band stays active in all views

**Naming convention:**
- `{prefix}-c3-{subject}-overview.png`
- `{prefix}-c3-{subject}-{path-name}.png`

## Numbered Flow Steps (Google Cloud Pattern)

When showing a specific flow path through a diagram, use the Google Cloud Architecture Center convention:

- **Blue filled circles** (#4285F4, ~20-24px) with white numbers inside
- Place circles **ON or adjacent to** the arrow they describe
- **Short action labels** (2-4 words) next to arrows — protocol details go in a legend below
- Numbers follow **temporal order** for that path only
- **Only number the primary flow** — shared infrastructure connections (like LLM proxy → AI endpoint) are unnumbered
- **Return/response arrows** get their own number and run parallel below the outgoing arrow
- When a diagram has **branching paths** (not sequential), do NOT use a single numbered sequence — use separate path-highlight views instead

**Stacked cards** for multiplicity:
- When a service has multiple instances (e.g., 7 bot APIs), show 2-3 slightly offset white cards behind the front card
- Only the front card has icon + text; back cards are blank white rectangles with gray borders
- The offset is ~4-6px to the right and below

## Anti-Patterns

- **Never pass external reference layout/diagram images** — Gemini copies layouts too literally. Small brand icons from `icons/` ARE fine. Your own previously generated diagrams ARE fine when creating variant views (see Multi-View Diagram Sets).
- **Never let Gemini hallucinate logos** — if a system has an icon in the registry, always embed it. Add new icons to the registry when you encounter new systems.
- **Never cram >8 elements** into one diagram — split by concern
- **Never use generic names** — use actual resource names from the project
- **Never commit to undecided topology** — add "illustrative — TBD" annotations
- **Never mix styles** — one style per diagram set
- **Never skip the legend** — always include one at the bottom
