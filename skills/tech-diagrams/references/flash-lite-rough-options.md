# Gemini 3.1 Flash Lite Rough-Option Profile

Use this profile when the objective is rapid visual exploration with
`gemini-3.1-flash-lite-image`, not final publication artwork. All normal diagram-type,
Google Cloud style, icon, honesty/provenance, and card rules still apply unless this
profile is stricter.

## Output contract

- Generate at `16:9`; the model output is 1K.
- Produce **three genuinely different options** for every visual ID. Options must
  change composition or information hierarchy, not just color or decoration.
- Save each option under one visual-specific directory with:
  - `brief.md` — content contract and source notes
  - `rough.txt` — an ASCII or box-and-arrow sketch of the intended composition
  - `prompts/{id}-{option}.txt`
  - `requests/{id}-{option}.json`
  - `images/{id}-{option}.png`
  - `manifest.json` — filenames, model, status, sources, and known limitations
- Use stable option letters `a`, `b`, and `c`. Use stable node IDs in `brief.md` and the
  authoring `rough.txt` so later revisions can refer to exact cards and connectors.
  **Strip IDs from the model-facing prompt and its ASCII composition.** Flash Lite can
  render instruction identifiers even when told not to, so the request should contain
  only printable display labels.

## Three-option diversity

Choose three distinct structural lenses that answer the same communication question.
Good trios include:

1. **Layered / stacked** — architecture layers, clear platform foundation.
2. **Flow / spine** — left-to-right sequence with gates or evidence handoffs.
3. **Split / matrix / orbit** — comparison, decision canvas, or governed loop.

State the distinguishing composition in the prompt title and manifest. Do not produce
three near-identical layouts.

## 1K text and density budget

Flash Lite roughs are composition studies. Do not ask the raster model to typeset a
document.

- Title: at most 8 words.
- Subtitle: at most 12 words.
- Cards: target 6–12; hard ceiling 16 only for matrices or network zones.
- Card title: 1–4 words. Card detail: zero or one short line, at most 6 words.
- Arrow labels: 1–3 words; label every semantic arrow.
- Long claims, citations, owners, dates, and definitions belong in the surrounding
  document or a later deterministic overlay, not in the rough image.
- Prefer numbered cards and a compact legend when exact language would overflow.
- Every card still has an icon or a simple registered symbol; never use decorative
  illustration as a substitute for architecture semantics.

## Required prompt blocks

Every prompt must include, in this order:

1. **Purpose** — the one question the diagram answers.
2. **Truth posture** — confirmed facts, proposed/illustrative items, and exclusions.
3. **Exact content** — printable short labels, relationships, and status; no authoring IDs.
4. **ASCII composition** — explicit rows/columns/zones and connector routing using the
   printable labels; no authoring IDs.
5. **Card grammar** — white rectangular cards, small corner radius, thin gray border,
   icon-left/title-right, no shadow, no gradient, no floating pills as main nodes.
6. **Diagram-type rules** — density, direction, gates, zones, or loop conventions.
7. **Render constraints** — 16:9, 1K, whitespace, legend, no decorative art, no fake
   logos, no named individuals, and no unreadably small text.

End every prompt with a separate **renderable-copy firewall**:

- Stable node IDs and ASCII coordinates are authoring-only and must never be printed.
- Render only the short display labels, permitted one-line details, semantic state
  badges, arrow labels, title/subtitle, and the requested legend entries.
- Never print hex codes, pixel values, color names used as instructions, layout notes,
  option-construction notes, prompt headings, or phrases such as `no shadow` and
  `small corner radius`.
- Do not print embedded-image labels, icon names, filenames, or image identifiers.
  Do not use node IDs as icons. Use registered icons or simple semantic line symbols.

## Truth and source handling

- A visual may contain confirmed facts, explicitly labeled proposals, or explicitly
  labeled TBDs. It may not silently convert an assumption into a current-state fact.
- Never invent product mappings, dates, owners, current estate, metrics, security
  controls, or production topology.
- In the manifest, record the source files used and list any intentionally omitted
  fact-dependent content.
- If the current-state evidence is stale or incomplete, generate only the conceptual
  target-state composition and label it `Illustrative target state`.

## Generation command

Build requests through the normal icon-aware request builder, then pass the model
explicitly:

```bash
python3 scripts/build-request.py prompt.txt request.json --provider gcp --aspect-ratio 16:9 --image-size 1K
scripts/generate.sh request.json output.png gemini-3.1-flash-lite-image
```

For rough composition studies, default to `--icons` with no names and request simple
semantic line symbols. Embedded reference labels can leak into the rendered copy.
Use an explicit icon list only when a specific brand/product identity is essential to
the communication question; never use auto-detection on prose-heavy prompts.

## QA and selection

Inspect each PNG before marking it ready. Record pass/fail and notes in `manifest.json`.
At minimum check:

- communication question is answerable without narration;
- all required cards are present exactly once;
- product cards follow the card grammar;
- connectors are legible, orthogonal where the diagram type requires it, and do not
  cross through cards;
- confirmed, proposed, and TBD content are visually distinguishable and explained;
- no unsupported metrics, dates, owners, products, or current-state claims appear;
- labels are readable at normal slide size;
- the three options are structurally distinct.

Do not pass a flawed rough back as a base image. Correct the prompt and regenerate.
Base images are reserved for approved multi-view sets where geometry must remain fixed.

For a fast preflight, run `scripts/qa-roughs.py <image-or-directory>`. It verifies the
16:9 PNG geometry and, when Tesseract is installed, flags probable printed node IDs,
hex values, pixel instructions, and leaked construction copy. Treat it as a heuristic;
visual inspection remains required.
