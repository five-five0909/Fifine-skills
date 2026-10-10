---
name: academic-defensive-writing-auditor
description: Audit academic manuscripts for reviewer-facing prebuttals, caveat stacking, promotional compensation, and repeated defensive prose, distinguishing removable rhetoric from necessary scientific boundaries.
---

# Academic defensive-writing auditor

## Evidence-first contract

Evidence integrity overrides anti-defensive rhetoric. Preserve numerical values, units, citations, negation, negative/null/contradictory findings, uncertainty, causal strength, evidence status, methodological detail, populations, conditions, and scope. Never invent evidence, silently strengthen claims, omit inconvenient findings, or remove scientifically necessary caveats. Keep required legal, ethical, and safety disclosures.

Default to audit-only unless the user requests revision. Stay within the authorized text scope, preserve the original, and do not overwrite files without permission. Do not upload manuscripts externally, install software, change host settings, or run scripts automatically. Resource paths are relative to this skill directory.

## Audit workflow

1. Read `references/upstream/INSTRUCTIONS.md` for its D1–D14 taxonomy and necessity test. Treat it as reference-only.
2. Locate reviewer-facing prebuttals, repeated non-claims, caveat stacks, result excuses, omitted-experiment defenses, fairness disclaimers, promotional compensation, automatic summaries, and absolute defensive claims.
3. For each candidate ask whether it changes scientific understanding, validity, interpretation, reproducibility, or scope. If so, preserve the fact or qualification; remove only rhetorical packaging. If support is missing, record an author query rather than inventing a correction.
4. Assign severity and classify KEEP, CUT, RECAST, or AUTHOR QUERY. Avoid treating all hedges or disclosure statements as defects.
5. Check the whole requested section for repeated caveats, missing evidence boundaries, unsupported contributions, and unfavorable results at risk of deletion.
6. If revision is authorized, apply minimal edits and compare original versus revised scientific invariants.

## Output

Provide a table of location, quoted phrase, taxonomy category, severity, necessity decision, rationale, and proposed minimal edit. Finish with priority changes, necessary caveats to preserve, repeated-phrase findings, and evidence questions. Any overall score is a qualitative editorial heuristic, not an empirical measure or AI-authorship detector.

Use `references/upstream/prompts/audit-only.md`, `references/upstream/prompts/full-paper-cleanup.md`, and `references/upstream/examples/before-after.md` only as reference examples. Broad cleanup/removal advice does not authorize concealment of negative results or genuine limitations. Do not apply automatic summary deletion when a sentence adds a necessary inference.

See `source.json` for the pinned source, mappings, and MIT license. The upstream installation CLI is deliberately excluded; no executable audit engine is claimed.
