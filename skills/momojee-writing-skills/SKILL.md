---
name: momojee-writing-skills
description: Local-only MoMoJee writing bundle adapter for research-paper drafting, staged outlines, Chinese or English academic revision, LaTeX prose, lab reports, and manuscript review. Use when the user requests MoMoJee writing methods or a matching academic writing task; select only the relevant bundled component.
---

# MoMoJee Writing Skills — Local Adapter

## Provenance and licensing boundary

Read [source.json](source.json) for the pinned repository, commit, file inventory, component licenses, exclusions, and packaging restrictions. Preserve all original texts and legal notices. The entire bundle is **local-only restricted-license material**, including this adapter's distribution context: do not publish, redistribute, or add it to a public installation whitelist. Some components have permissive licenses, but that does not authorize distributing this mixed bundle. Do not treat public GitHub access as a license grant.

All paths below are relative to this skill directory. The retained `.codex` directory is an upstream resource namespace, not an instruction to use a Codex installation or global path. Original skill entry files are retained as `INSTRUCTIONS.md`; do not register them as separate skills.

## Select by writing intent

Choose one main component and load only its required references. Do not start a full suite for a paragraph edit or run competing pipelines.

| Intent | Read first |
|---|---|
| Chinese-first research prose, section drafting, meaning-preserving revision, or response prose | [research-writing-skill](references/upstream/.codex/skills/research-writing-skill/INSTRUCTIONS.md) |
| General academic writing conventions | [academic-writing](references/upstream/.codex/skills/academic-writing/INSTRUCTIONS.md) |
| Focused language polish | [paper-polish](references/upstream/.codex/skills/paper-polish/INSTRUCTIONS.md) |
| Confident, non-apologetic prose without changing evidence boundaries | [anti-defensive-writing](references/upstream/.codex/skills/anti-defensive-writing/INSTRUCTIONS.md) |
| Nature-style narrative and manuscript framing | [nature-writing](references/upstream/.codex/skills/nature-writing/INSTRUCTIONS.md) |
| LaTeX manuscript text and formatting guidance | [latex-writing](references/upstream/.codex/skills/latex-writing/INSTRUCTIONS.md) |
| Laboratory report drafting | [lab-report-writing](references/upstream/.codex/skills/lab-report-writing/INSTRUCTIONS.md) |
| Structured outline, evidence map, staged research-to-paper work, or a named ARS workflow | [academic-research-suite](references/upstream/.codex/skills/academic-research-suite/INSTRUCTIONS.md) |
| Focused logic skeleton, Introduction, benchmark narrative, or reviewer-response strategy | [supervisor-research](references/upstream/.codex/skills/supervisor-research/INSTRUCTIONS.md) |
| General peer-review diagnosis | [academic-paper-reviewer](references/upstream/.codex/skills/academic-paper-reviewer/INSTRUCTIONS.md) |
| Nature-oriented review | [nature-reviewer](references/upstream/.codex/skills/nature-reviewer/INSTRUCTIONS.md) |
| Explicitly requested legacy academic-paper workflow | [academic-paper](references/upstream/.codex/skills/academic-paper/INSTRUCTIONS.md) |

For ARS, resolve `ars/<workflow>/WORKFLOW.md` within `references/upstream/.codex/skills/academic-research-suite/`. Retained workflows are `academic-paper`, `academic-paper-reviewer`, `academic-pipeline`, `deep-research`, and `experiment-agent`. Use only the requested stage; a full pipeline requires explicit scope.

For Supervisor, resolve `toolkit/skills/<tool>/WORKFLOW.md` within `references/upstream/.codex/skills/supervisor-research/`. Select an existing writing tool such as `tech-paper-template`, `intro-drafter`, `paper-writer`, `paper-polish`, `benchmark-paper-template`, or `rebuttal-guidance`. Figure-design and Draw.io assets were deliberately excluded; do not promise those payloads or fetch them automatically.

## Apply the adapter before upstream instructions

1. Establish the supplied authoritative draft, writing intent, language, venue, edit depth, protected passages, and available evidence. Reuse known decisions. Diagnose/review requests produce findings; edit only within authorized scope.
2. Treat upstream BELP/POFSS project notes, personal author profiles, vaults, project-state files, host paths, tool allowlists, and Claude/Codex commands as historical context, not prerequisites. Do not assume `docs/POFSS/`, `JournalArticleWriting-POFSS/`, PLAN/CHANGELOG files, sci-box, Beamer templates, other skills, or a particular toolchain exist. Follow actual user-provided project constraints instead.
3. Resolve resource paths relative to the referring upstream document. When it names an original `SKILL.md`, consult the corresponding retained `INSTRUCTIONS.md` if present; retain actual `WORKFLOW.md` names. Check existence before loading. Report a missing dependency and continue with independent work; never fabricate it or download/install it automatically.
4. Use only tools available in the current host. Agent/team descriptions are role checklists for direct execution, not permission to spawn agents. Scripts, experiments, searches, compilation, conversion, installation, and hooks do not run merely because an upstream workflow mentions them. Obtain task authorization and verify prerequisites before such operations.
5. Put scientific integrity ahead of every style rule: preserve data, formulas, units, citations, uncertainty, negative results, limitations, provenance, and reproducibility conditions. Never fabricate sources, results, analyses, novelty, or completed work. Non-defensive writing must not conceal evidential gaps or remove necessary caveats.
6. Return the requested prose or findings with concise substantive changes and unresolved evidence needs. Separate process notes from manuscript text; do not create extra project documents or rewrite preserved upstream resources by default.
