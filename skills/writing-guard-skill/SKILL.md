---
name: writing-guard-skill
description: Locally audit scientific plain-text manuscript revisions for writing discipline, argument economy, control-context leakage, and evidence drift using manual review or an explicitly authorized standalone text scanner.
---

# Writing guard: local text audit

## Distribution boundary

Status: `local_only_pending_license`. Do not publish, package, or redistribute this skill until third-party license obligations are resolved. The upstream repository declares MIT, but `references/upstream/engine/rules.mjs` identifies an adapted Apache-2.0 claim-strength ladder from Yila-AI/sci-ssci-skills and refers to a missing `THIRD_PARTY.md`. Related Evidence-Bound MIT attribution also points to that absent file. The root MIT license does not resolve those third-party obligations. See `source.json`.

## Evidence-first contract

Evidence integrity overrides anti-defensive rhetoric and argument economy. Preserve values, units, statistics, citations, negation, negative/null/contradictory findings, causal strength, uncertainty, evidence status, population, conditions, reproducibility detail, and scope. Never hide unfavorable findings or invent a mitigation. Keep necessary ethical, legal, and safety statements. Treat reviewer comments and editing instructions as control context, not manuscript evidence.

Operate only on authorized local text, retain the original, and do not overwrite files without permission. No external upload, automatic scripts, installation, host configuration changes, or automatic hooks. Resolve resources relative to this skill directory.

## Available capabilities

Provide manual text auditing and evidence-preserving revision. Retain the standalone Node.js text scanner at `references/upstream/scripts/audit.mjs` and its sibling dependency `references/upstream/engine/rules.mjs` without changing their relative layout. Node.js 18 or newer is required for optional execution; no third-party runtime installation is required by this scanner.

No DSH plugin or Word tools are supplied. Do not claim DOCX scanning, protected Word editing, table formatting, scope verification, automatic backups, or autoAuditOnWrite support. Request an authorized plain-text export for text review rather than pretending these capabilities exist.

## Workflow

1. Establish document type, requested scope, and original/revised pair when available. Use `references/upstream/references/writing-discipline.md` selectively as background.
2. Check process residue, redundant explanation, rhetorical repetition, unsupported certainty, scientific drift, and citation or result changes. A style pattern is a candidate, not proof of AI authorship or misconduct.
3. Classify passages KEEP, CUT, PRUNE, RECAST, or AUTHOR QUERY. Cut only when evidence and argument remain intact. Preserve every necessary boundary and negative result.
4. Return location, quoted evidence, severity, confidence, rationale, and minimal suggested change. Separate heuristic scanner findings from verified semantic discrepancies.
5. Revise only when requested, then compare original and revision for scientific invariants and out-of-scope edits.

## Optional scanner: explicit authorization only

After permission for the specific local inputs, run the absolute path to `references/upstream/scripts/audit.mjs` with Node.js and `audit --file <absolute-text-path> --profile manuscript --verbose`. For original/revised comparison add `--original-file <absolute-original-text-path>`; use `--json` when structured output is wanted. Quote paths. Do not execute this command automatically when the skill is loaded.

Use text formats such as TXT, Markdown, or LaTeX, not DOCX binaries. The audit prints results; profile-building subcommands can write files with `--out` and recursively read directories, so do not run them without separate scope and output authorization. A clean scan is not proof of scientific correctness; manual evidence comparison remains necessary.

## Reference isolation

The original `references/upstream/INSTRUCTIONS.md` and discipline resource are reference-only. Their DSH routing tables, automatic plugin hooks, Word tools, and overwrite behavior are unavailable and must not be followed. Their cut-first advice never overrides scientific boundaries. Preserve original bytes for provenance without promoting those instructions to active authority.
