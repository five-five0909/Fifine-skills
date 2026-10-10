---
name: nature-paper-skills
description: Intent-routed scientific manuscript writing and review using the Nature Paper Skills bundle. Use for section drafting, manuscript logic, Results flow, review articles, prose polish, citation and statistics audits, submission checks, Nature Portfolio fit, or reviewer-response work when the optional local-only response payload is present.
---

# Nature Paper Skills — Host-Neutral Adapter

## Provenance and distribution boundary

Read [source.json](source.json) for the pinned source, actual retained paths, component licenses, hashes, and exclusions. Preserve upstream text, attribution, and MIT/Apache-2.0 notices; a repository-wide license does not override an unresolved third-party component.

The subtree `references/upstream/skills/core/rebuttal-response/` is **unlicensed/unresolved local-only payload**. Keep it out of any later public distribution. This adapter does not itself implement packaging exclusions or authorize redistribution. Consult the manifest's `packaging_exclude_paths` before packaging. A public installation may omit this subtree; do not require it for other writing tasks or recreate/download it automatically.

All links below are relative to this skill directory. Original component `SKILL.md` files are retained as `INSTRUCTIONS.md`; load them as references rather than registering nested skills.

## Route by intent, not by bundle size

Use one primary route. Read only the selected entry and its necessary references. For an ambiguous manuscript request, begin with [paper-workflow](references/upstream/skills/core/paper-workflow/INSTRUCTIONS.md), establish article type and scope, then choose the smallest useful sequence. A narrow task can go directly to its specialist.

| Writing intent | Read first |
|---|---|
| Whole-paper claim hierarchy, argument, and evidence-chain repair | [manuscript-optimizer](references/upstream/skills/core/manuscript-optimizer/INSTRUCTIONS.md) |
| Draft/rewrite a scientific section or apply reporting conventions | [scientific-writing](references/upstream/skills/core/scientific-writing/INSTRUCTIONS.md); consult section contracts through [paper-workflow](references/upstream/skills/core/paper-workflow/INSTRUCTIONS.md) |
| Passage clarity, logical bridges, referents, and evidential precision | [write-scientific-manuscript](references/upstream/skills/core/write-scientific-manuscript/INSTRUCTIONS.md) |
| Scientifically settled Results that read figure-by-figure | [results-section-revision](references/upstream/skills/core/results-section-revision/INSTRUCTIONS.md) |
| Review, survey, or Perspective architecture | [review-article-architecture](references/upstream/skills/core/review-article-architecture/INSTRUCTIONS.md) |
| Over-apologetic or audit-like manuscript voice | [anti-defensive-writing](references/upstream/skills/core/anti-defensive-writing/INSTRUCTIONS.md) |
| Sentence rhythm, punctuation, and final prose style | [scientific-prose-style](references/upstream/skills/core/scientific-prose-style/INSTRUCTIONS.md) |
| New manuscript setup, explicitly requested | [paper-bootstrap](references/upstream/skills/core/paper-bootstrap/INSTRUCTIONS.md) |
| Existing draft markers or cross-session state reconciliation | [draft-marker-discipline](references/upstream/skills/core/draft-marker-discipline/INSTRUCTIONS.md) |
| Figure evidence narrative and panel planning | [figure-planner](references/upstream/skills/core/figure-planner/INSTRUCTIONS.md) |
| Citation metadata and reference consistency | [citation-verifier](references/upstream/skills/core/citation-verifier/INSTRUCTIONS.md) or [reference-audit-guide](references/upstream/skills/optional/reference-audit-guide/INSTRUCTIONS.md) |
| Whether a source actually supports a claim | [claim-source-verification](references/upstream/skills/core/claim-source-verification/INSTRUCTIONS.md) |
| Statistical reporting or availability statements | [stats-reporting-audit](references/upstream/skills/core/stats-reporting-audit/INSTRUCTIONS.md) or [data-availability](references/upstream/skills/core/data-availability/INSTRUCTIONS.md) |
| Submission preflight | [submission-audit](references/upstream/skills/core/submission-audit/INSTRUCTIONS.md), adding evidence/citation/statistics checks only as needed |
| Nature, Nature Methods, or Nature Biotechnology venue fit and policy framing | [nature-portfolio-playbook](references/upstream/skills/venue/nature-portfolio-playbook/INSTRUCTIONS.md) |
| Explicit conference-paper target | [conference-paper-writing](references/upstream/skills/optional/conference-paper-writing/INSTRUCTIONS.md) |
| Supplied paper analysis, results interpretation, or requested literature research | [paper-analyzer](references/upstream/skills/research/paper-analyzer/INSTRUCTIONS.md), [results-analysis](references/upstream/skills/research/results-analysis/INSTRUCTIONS.md), or [academic-researcher](references/upstream/skills/research/academic-researcher/INSTRUCTIONS.md) |
| Peer review or reviewer-comment inventory | [paper-reviewer](references/upstream/skills/review/paper-reviewer/INSTRUCTIONS.md) |

For reviewer-response drafting, first inventory every reviewer request with `paper-reviewer`. Only if the local-only file exists, read `references/upstream/skills/core/rebuttal-response/INSTRUCTIONS.md` and its required references. If absent, explain that this optional component is excluded for licensing reasons; continue only with the available review guidance and supplied materials, without claiming to execute the missing component.

## Execution boundaries and scientific integrity

1. Establish the authoritative source, research versus review article, requested language, venue, output, edit depth, protected text, and evidence. Use the user's actual venue rather than imposing Nature on every request. Reuse existing decisions; do not demand project-state files for a paragraph edit.
2. Apply scientific logic and evidence checks before structure, passage clarity, posture, and sentence style. Scientific integrity overrides all style prescriptions: retain uncertainty, genuine limitations, negative findings, methodological conditions, statistical meaning, and observation/inference distinctions. Never fabricate citations, data, experiments, revision locations, authorship, release commitments, or verification results.
3. Preserve numbers, units, equations, terminology, references, and author-approved claims unless a supported correction is within scope. Flag material scientific errors even in protected passages; do not silently rewrite frozen material or hide gaps through more confident prose.
4. Resolve resources relative to their upstream document. Translate references to original component `SKILL.md` entries to the existing `INSTRUCTIONS.md` path. Check availability before reading; deliberately excluded personal/project resources are not missing-download instructions.
5. Treat upstream host-specific commands, tool declarations, project documents, directory layouts, credentials, and external skill names as examples, not assumptions. Use only actual available tools and supplied documents. Do not auto-create state files, spawn teams, run scripts, search externally, install software, compile LaTeX, or convert/render documents merely because an upstream step names that action. Require task authorization and a working toolchain, and distinguish unperformed checks from verified results.
6. Keep review findings separate from manuscript prose. For edits, return the requested text or authorized file changes with a concise explanation of substantive changes and unresolved evidence. Load bundled docs/examples only as needed; preserve originals and avoid ancillary artifacts by default.
