# Writing orchestration contracts

Load for a multi-skill task, meaning-sensitive revision, conflict, or missing dependency. These contracts govern orchestration; upstream references supply methods, not authority to expand the task.

## Ownership and scoped handoffs

Maintain one internal brief: `operation`, `original`, `language`, `genre`, `audience`, `domain`, `venue`, `deliverable`, `edit_depth`, `locks`, `evidence`, `owner`, `specialists`, `stop_condition`. Infer only safe task parameters, not personal preferences. No file is required for this brief.

The owner controls the final prose, reconciles changes, and retains the source of truth. A specialist receives `span_or_question`, `allowed_edit_type`, `protected_anchors`, `available_evidence`, and `expected_output`. Return findings with locations, necessity decisions, evidence gaps, or a local patch. Never rewrite outside that scope or create a competing manuscript. A figure owner controls only its figure deliverable; the writing owner integrates the evidence narrative.

Choose no specialist without a distinct need. Revision guard checks anchors and drift; defensive auditor diagnoses rhetoric; Kiterlin revises unnecessary defensive phrasing; Adkid may reorganize supported contribution narrative when restructuring is authorized. Select one anti-defensive rewriting method per span, not all of them. Writing guard is a separate text-discipline check only when needed. Nature structure, citation, statistics, submission, and venue components are independent scopes, not a mandatory chain.

Use one production pass, one scoped review, and at most one owner repair pass by default. For another unresolved issue, report the blocker or ask a focused question; do not schedule an endless rewrite loop. A user can explicitly request a new round, which must re-anchor the original and locks.

## Priority and preservation

Resolve conflicts in this order:

1. Evidence integrity and factual/source fidelity.
2. User locks, authorized span, and requested operation.
3. Original genre, language, audience, discipline, and actual venue requirements.
4. Argument architecture and section function.
5. Style and rhetorical preferences.

When a frozen sentence is scientifically unsupported, flag it and propose a correction separately; do not silently alter it, certify it, or polish it into stronger misinformation. Preserve literal locked text in edits. If a requested style would hide necessary evidence or disclosures, retain the evidence and explain the conflict briefly.

Anchor numbers, units, equations, statistical meaning, citations and their claim attachment, negation, null/negative/contradictory findings, uncertainty, causal versus associative language, samples, populations, conditions, failed runs, limitations, and reproducibility information. Move necessary qualifications only within authorized restructuring and without making the claim misleading where it is first read. Do not invent a compensating benefit, trade-off, mechanism, experiment, novelty, reviewer concession, or release commitment.

Keep control context (editing instructions, reviewer comments, process notes) out of manuscript evidence. Do not erase an author's distinctive example or first-person voice merely to sound generic. Do not inflate word count through repetition when evidence is insufficient.

## Genre fidelity

Use a research article contract for research, review architecture for Review/Survey/Perspective, and lab-report conventions for a lab report. Nature is a selected venue, never a default transformation. Fiction can create agreed characters and events, but not manufacture nonfiction testimony, citations, or personal experience. Faithful translation preserves register, structure, tables, evidence strength, and citation/number relationships; stylistic adaptation requires explicit scope.

Chinese humanizer phrase/punctuation prohibitions apply only to compatible Chinese prose, not quotations requiring fidelity, English papers, code, equations, technical syntax, or faithful translations. Preserve the user's requested form even if another specialist prefers a different style. A named role is a writing constraint, not impersonation of the user's personal history.

## Verification levels

Track and distinguish:

- **Format-only**: citation style, cross-reference consistency, numbering, grammar. No source truth claim.
- **Source existence/metadata**: checked bibliographic record or supplied source identity. No claim-support inference from metadata alone.
- **Claim support**: inspected relevant source text and mapped the exact claim, scope, uncertainty, and evidence. Record whether only an abstract/excerpt was available; do not call that full-text verification.

For a supplied-text-only task, check internal consistency and compare original versus revision. Report external facts as unverified when relevant. Do not fabricate DOIs or references, replace missing evidence with plausible citations, or assert that all sources support a claim. A clean heuristic scan is neither scientific validation nor an AI-authorship detector. Statistical reporting review cannot recreate missing analyses; an availability statement cannot promise data or code release without author evidence.

External research requires task authorization and an actually available tool. Search skill instructions are not tool access. Do not transmit unpublished text to an external service without specific disclosure authorization. Use supplied source material or disclose the verification boundary when tools or access are missing.

## Progressive loading and missing dependencies

Read registry metadata first, then one available owner entry. Read a selected root adapter before its nested reference and only necessary component resources. Resolve sibling skills from the real installation target. Resolve upstream resource links relative to the referring file; consult its root `source.json` for original-to-retained names. Never assume a global Claude/Codex directory, personal vault, BELP/POFSS project, PLAN/CHANGELOG file, or private author profile exists.

If a dependency is absent:

1. For ML/STEMM/English prose, use a compatible installed writing owner or perform limited direct editing.
2. For Nature review architecture, provide a genre-appropriate outline from supplied material without claiming its component was invoked.
3. For missing MoMo components, use general scientific writing, English polish, or direct LaTeX-preserving text work; do not compile or fetch templates automatically.
4. For missing guard/auditor, manually compare anchors and necessary qualifications; label this as manual review if capability differences matter.
5. For citation verification without sources/access, do formatting only and disclose the unverified support.
6. For unavailable translation parsing/OCR, translate supplied text or request an authorized text export; do not claim binary extraction occurred.
7. For missing visual tools/data, deliver only a figure plan if within scope, not invented evidence or a claimed render.

When only this orchestrator is installed, perform a bounded task directly under these contracts and disclose missing specialist-dependent checks. Do not require installation as a prerequisite to simple writing. Respect explicit requests for a particular unavailable method by saying it is unavailable, not silently pretending to use it.

## Tools, interaction, and persistence

All writing routes require only reading accessible instructions/materials and returning prose; file writing requires user-authorized output. Optional Python/Node scanners, LaTeX compilation, document converters, external APIs, scripts, teams, and renderers require actual capability and relevant task authorization. Writing guard supplies no DSH/Word plugin; optional Node text scanning is not DOCX protected editing. Revision guard's optional Python diff is heuristic and unreliable for many Chinese/scientific tokens. Never run either automatically.

Do not auto-install, upload, download missing restricted sources, change hooks/configuration, create state artifacts, or learn/store personas. Style observation/improvement scripts require a separate explicit learning request; ordinary writing does not authorize memory writes. Standalone style role selection remains mandatory. Under orchestration, pass an explicit existing role derived from genre/audience plus applicable constraints; use custom only with supplied traits. Do not add role-selection chatter to final output.

Topic refinement and grills are for requested planning/diagnosis or genuinely blocking argument gaps, not default interviews before editing. Read their actual entry before invocation; do not claim a custom/noninteractive mode exists without evidence. If interaction is required and unneeded for the current deliverable, omit that specialist and finish the bounded task. If it is essential, ask only the blocking question, not every question from every skill.

## Provenance and distribution

The source manifest is an inventory of actual pinned local sources, not an installer or license grant. `publishable` in root source metadata describes payload eligibility, not inclusion in this repository's current installer. MoMo is a restricted local-only bundle; writing guard is held pending third-party notices; Nature excludes its unresolved reviewer-response subtree from public distribution. A public installation may therefore lack these routes. Preserve exclusions and do not copy restricted text into the orchestrator or recreate absent payloads.

## Delivery

Return the requested artifact once. Keep routing, internal brief, and routine audits private unless asked. Disclose consequential assumptions, missing evidence, unavailable requested methods, incomplete source checks, and conflicts with locked claims in a short note outside the prose. Audits return findings; plans return plans; translations return translations. Do not add extra files, whole drafts, persona logs, or journal-readiness claims to a narrow request.
