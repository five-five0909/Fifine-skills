---
name: research-writing-skill
description: Chinese-first research paper writing, revision, polishing, section drafting, rebuttal, peer-review response, thesis prose improvement, and manuscript argument planning. Use when the user asks to write or revise论文正文, abstracts, introductions, methods, results, discussion, conclusions, related work, responses to reviewers, LaTeX/Overleaf text, or academic prose. Preserve formulas, English paper titles, terms, citations, and measured results.
---

## BELP 2026-09-12 路由补充

POFSS 任务优先读取 `docs/POFSS/科研技能使用与维护.md` 和
`JournalArticleWriting-POFSS/论文行文与绘图规范.md`。采用一个主流程，已有阶段结果直接复用。
新阶段化写作使用 academic-research-suite；Supervisor 提供专题方法。当前技能按所需模式或局部参考使用。
正文保持平实、自信，禁止项目列出的对比句型、自我贬低、工作汇报和自我审查语言；写完逐句复读。
证据与待补项进入 Markdown 工作表，真实实验记录保持完整。绘图使用 uv 环境与 Matplotlib，
先参考 sci-box，再按最终正文宽度检查图片和整页。Beamer 汇报继续使用项目指定模板。
角色提示在当前任务内执行；用户明确请求委派时才启动 subagent。


# Research Writing Skill

## Scope

Use this skill for research writing and revision when the output is prose, LaTeX, Markdown, or manuscript text. Use `office-academic-skill` instead when the main deliverable is Word/PPT. Use `scientific-toolkit-skill` when the task is primarily MATLAB, Python, plotting, statistics, simulation, or literature search.

## Writing Principles

- Default to Chinese academic expression unless the user requests English.
- Preserve English titles, formulas, variables, methods, software names, citations, and reference entries.
- Do not invent data, DOI, journal details, experiment settings, results, or author claims.
- Separate `原文/已有数据`, `用户确认内容`, `根据上下文推断`, and `建议性扩展`.
- Prefer verifiable technical statements over generic claims.
- When revising, preserve the user's intended meaning and terminology unless a change is clearly needed.

## Manuscript Workflow

For a new section or paper draft:

1. Clarify target: journal/conference/thesis/course report, language, length, audience, and required format.
2. Identify source material: paper notes, experiment results, figures, tables, MATLAB/Python outputs, references, advisor comments.
3. Build an argument outline before full prose: problem, gap, method, evidence, contribution, limitation.
4. Draft in coherent paragraphs, not empty slogan bullets.
5. Add source or evidence labels for quantitative claims and literature claims.
6. Revise for logic, specificity, terminology consistency, and citation accuracy.

For revision or polishing:

- Keep claims tied to evidence.
- Replace vague words such as "显著", "先进", "有效", "鲁棒" with measured conditions, comparison baselines, or remove them.
- Check whether each paragraph advances the section's purpose.
- Keep formulas with variable definitions, units, assumptions, and applicable conditions.
- For experimental sections, state dataset/sample, hardware/software, parameters, metrics, baselines, and uncertainty when available.

## Section Guides

Use these default moves unless the user's school or journal template overrides them:

- Abstract: problem, method, experiment/data, key result, contribution.
- Introduction: background, unresolved gap, why it matters, proposed approach, contributions.
- Related work: organize by technical theme, compare assumptions and limitations, avoid simple paper-by-paper summaries.
- Methods: model assumptions, variables, workflow, algorithm, implementation details needed for reproduction.
- Experiments: data/source, platform/software, parameters, metrics, baseline, repeated trials, visualization plan.
- Results and discussion: claim first, evidence second, mechanism/explanation third, limitation last.
- Conclusion: answer the research question, summarize evidence, state limitations and next steps.

## Bundled References

The folder `references/paper-writing/` contains external writing checklists and section patterns adapted as references. Load only the relevant file when needed:

- `brainstorming_guide.md` for turning an unclear idea into a paper plan.
- `section_rhetorical_moves/` for section structure.
- `writing_checklists/` for self-diagnosis.
- `figure_templates/` for figure planning.
- `author_profile/` for editorial heuristics.

These references come from an external systems/networking-oriented repository. Treat them as optional craft guidance, not binding rules, and adapt them to光电信息科学与工程, optics, optoelectronics, sensing, communication, signal processing, and MATLAB simulation work.

## Final Checks

Before delivery, state:

- What was drafted or revised.
- Which source material was used.
- Which claims still need user-provided data or citation support.
- Any uncertainty about terminology, parameters, or references.

