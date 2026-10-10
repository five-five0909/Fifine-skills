---
name: fifine-writing-orchestrator
description: Automatically coordinate writing, drafting, rewriting, polishing, editing, outlining, reviewing, and translation from ordinary language requests. Use for papers, theses, reviews/surveys/Perspectives, proposals, reports, articles, posts, stories, dialogue, scripts, speeches, emails, and platform copy; requests such as 帮我写、改一下、润色、去 AI 味、理顺结构、写引言、审稿、翻译 need no skill names. Select one writing owner and only necessary scoped specialists, preserving evidence, user locks, original genre, language, and voice. Not for code implementation, OCR-only extraction, literature search alone, mathematical proof, or standalone figure rendering.
---

# Writing Orchestrator

Act as a thin coordination layer, not another full writing pipeline. Deliver one coherent result through one owner. Natural-language discovery depends on the host's skill metadata mechanism; do not claim guaranteed triggering or change hooks, permissions, or global configuration.

## 1. Identify the real task

Extract an internal brief from the request and supplied materials: operation (plan/draft/edit/audit/translate), authoritative original, language, genre, audience, field, venue if given, deliverable, edit depth, protected passages, evidence, and stopping condition. Preserve the user's article type and genre; do not turn a lab report into a Nature paper, a faithful translation into marketing copy, or a story into an academic essay.

For a typo, grammar, sentence, or small clarity edit, revise directly with the smallest effective change. Skip interviews, research-topic refinement, whole-paper planning, persona questions, and project-state files. If sufficient material exists, do not ask the user to name skills. Ask only a question that materially blocks correctness; otherwise use a safe, bounded assumption. Never invent research evidence or personal experience to fill a gap. Plan-only means no full draft; audit-only means no rewrite.

## 2. Select one owner, then scoped specialists

Consult relevant entries in [writing-registry.json](references/writing-registry.json), not every skill body. Paths in the registry resolve from the parent directory containing installed skill folders (the source repository's `skills/`, or the current distribution target), never from an author's machine or a hard-coded host directory.

| Task | Default owner or focused route |
|---|---|
| ML/CV/NLP paper story or sections | `fifine-research-paper-writing` |
| General STEMM paper, thesis, scientific report | `fifine-science-research-writing-skills` |
| English scientific sentence/paragraph polish | `fifine-english-research-write` |
| Chinese reader-facing nonfiction or fiction | `fifine-live-humanizer`, only within its compatible genre |
| Explicit role, platform voice, or supplied style | `fifine-writing-style`; pass an explicit task-derived role when appropriate |
| Faithful or batch translation | `fifine-translation-multiple-kanban` |
| Review/Survey/Perspective architecture | `nature-paper-skills` selected `review-article-architecture` component |
| Whole-manuscript structure or Nature-family work | Keep the field-appropriate owner; add `nature-paper-skills` selected structure/venue specialist |
| Requested MoMoJee method, LaTeX prose, lab-report guidance | `momojee-writing-skills` selected component, if locally available |
| Original-preserving revision | Owner edits; add `ai-revision-guard` for meaning/voice-sensitive or iterative edits |
| Defensive-language diagnosis | `academic-defensive-writing-auditor`, audit scope only |
| Unnecessary defensive rhetoric rewrite | `kiterlin-anti-defensive-writing`; choose `adkid-anti-defensive-writing` instead for evidence-supported contribution narrative reorganization |
| Local text discipline/evidence-drift audit | `writing-guard-skill`, manual review by default |
| Missing research question or explicitly requested pressure test | Topic refiner or one appropriate grill, not a routine prerequisite |
| Figure evidence chain | `fifine-visual-creation-orchestrator`, only the figure scope |

General English emails, stories, speeches, or copy are not scientific-English tasks. Use a compatible style role or direct writing under this contract. Academic English AI-like prose belongs to the scientific/English owner, not automatically to the Chinese humanizer.

Use exactly the seven root adapter names above; `adkid-anti-defensive-writing-en` and nested upstream components are not independently registered skills. Read the selected root adapter before any upstream reference. For Nature/MoMo, read only the selected registry component's exact `INSTRUCTIONS.md`, then necessary references resolved relative to that document. Keep actual nested `WORKFLOW.md` filenames; consult the root `source.json` to map renamed upstream entries. Do not load an entire bundle, start ARS or Supervisor pipelines, or appoint `paper-workflow` as a second top-level dispatcher. Use it only as a scoped section/plan adviser.

## 3. Execute a bounded workflow

Read [orchestration-contracts.md](references/orchestration-contracts.md) for specialist handoffs, conflicts, verification, and fallback. Keep the brief and routing internal unless requested.

1. Confirm available owner and required inputs; read only its entry and relevant resources.
2. Plan only if the deliverable requires it. For an edit, anchor facts and locked text before changing anything.
3. Produce one draft or authorized local revision.
4. Use zero specialists for a trivial edit; normally use at most two for distinct, concrete risks. For an explicitly broad audit, add only non-overlapping checks justified by its scope. Each specialist receives a span/question and returns findings or a proposed patch, not a competing whole draft.
5. Let the owner reconcile findings and do one targeted repair pass. Compare with the original for evidence, locks, scope, genre, and meaning. Stop when the requested improvement is achieved. Do not cycle anti-defensive adapters or keep self-polishing. An unresolved evidence gap is not a reason to rewrite indefinitely.

No actual subagents, script execution, network research, rendering, compilation, or persistent artifacts are implied by the term specialist. Use direct scoped application unless the user's task and host explicitly support another mode. Never create state files merely because upstream instructions mention them.

## Shared boundaries

Apply **evidence integrity > user locks and edit scope > genre/language/actual venue > structure > style**. Flag an unsupported locked claim without silently editing the lock. Keep citations, numbers, units, equations, terminology, null/negative results, negation, uncertainty, causal strength, populations, conditions, necessary limitations, and reproducibility details. No new claims, sources, data, or completed experiments without support.

Distinguish citation formatting, source existence/metadata, and whether the source supports the claim. Formatting is not verification; a title or abstract is not full-text verification. Disclose incomplete checks. Do not upload drafts, install dependencies, download missing bundles, learn/persist personas, or run upstream scripts automatically. Fiction may invent within its agreed fictional world; nonfiction may not invent testimony or lived experience.

## Availability and output

Check that each selected skill and component actually exists. All dependencies are optional; registry membership is not proof of installation, tool availability, license clearance, or successful invocation. Fall back to a compatible installed owner or direct bounded writing, disclosing material loss of capability. Do not recreate missing restricted payloads. See [source-manifest.json](references/source-manifest.json) only for provenance/licensing or component availability questions; do not read all seven source inventories on every request.

Return the requested text, translation, outline, or audit first. Omit the routing diary, role announcement, internal brief, and routine change log unless requested. Add only short consequential assumptions, substantive edit notes when useful, and important evidence/dependency/verification gaps. Do not imply a journal-ready certification, completed source check, or executed tool when only editorial review occurred.
