---
name: supervisor-research
description: Use Supervisor-Skills for a focused research task such as a technical paper logic skeleton, Introduction drafting, meaning-preserving polish, figure planning, or a requested reviewer assessment. Also use when the user names Supervisor-Skills or one of its subtools. In POFSS, use tech-paper-template for the initial logic skeleton; leave ARS stage tracking to academic-research-suite.
---

# Supervisor research：BELP 入口

这是 HKUSTDial/Supervisor-Skills 的项目适配入口。先读根目录 `AGENTS.md` 和
`docs/POFSS/科研技能使用与维护.md`，论文写作和绘图再读
`JournalArticleWriting-POFSS/论文行文与绘图规范.md`。

## 调用

`$supervisor-research tech-paper-template 优化 POFSS 的论证结构`

选择一个子工具，读 `toolkit/skills/<子工具>/WORKFLOW.md`，再读它要求的必要 references。
子工具内原称 `SKILL.md` 的入口已统一命名为 `WORKFLOW.md`；相对路径按所在文件解析，
兄弟工具在 `toolkit/skills/`，handbook 在 `toolkit/handbook/`。
所有子工具通过本入口调用，不另建同名全局技能。

| 子工具 | 使用时机与产物 |
|---|---|
| tech-paper-template | 大纲之前或论证重构：研究问题、设计选择、证据与章节对应表。 |
| intro-drafter | 主线已有依据后写 Introduction；需要大纲时注明 outline。 |
| paper-writer | 从已确认材料起草其他正文段落或章节。 |
| paper-polish | 已有正文的语法、衔接、中译英；保持科学含义。 |
| figure-designer | 决定每个 panel 的表达目的、排列与标注。 |
| pre-submission-reviewer | 用户要求投稿前审阅时检查逻辑、语法、LaTeX 和图。 |
| idea-evaluator | 用户要比较研究方向或改变论文问题时评估。 |
| deep-research | 用户要求专题深度调研时使用；与 ARS deep-research 二选一。 |
| benchmark-paper-template | 主要贡献为评测体系或数据集时使用；普通传感器对照实验无需切换。 |
| rebuttal-guidance | 收到审稿意见后拟定逐条回应策略。 |
| vibe-research-workflow | 用户询问 AI 科研协作方式时提供方法参考。 |
| drawio-reconstruction | 用户明确要求可编辑 Draw.io 复刻时使用。 |

## POFSS 适配约定

- 每个任务保留一个主流程。ARS 可以采用本工具产出的逻辑表、图计划或正文；不要再启动 Supervisor 全过程。既有研究问题、证据表和授权继续有效。
- 默认中文草稿；用户要求英文时输出英文。引言段数、文献数、贡献数由内容决定，不硬套六段、15–25 篇文献或三四项贡献。
- 采用简洁、自信、有证据支持的正文。缺项写入 PLAN 或证据表，正文不插入审查报告。正式结果所需条件、误差与必要对照如实表达。
- 单纯润色保持原意；用户已授权结构修改时可重组段落。任何新增数据、因果关系或更强结论都需要相应证据。
- 科研图默认 Matplotlib，优先读 sci-box 的图型模板。真实三维变量允许曲面图；上游“禁用 3D”的装饰规则不限制有物理含义的三维图。论文照片可保留足够分辨率的位图，数据图优先矢量 PDF。
- 上游分数与格式偏好是参考。不要用 CS 顶会、强制 running example、固定模块数替代光学传感器的论证需求。
- 在当前任务内执行所需步骤。独立 subagent、跨模型、外部上传、自动 hooks 不因安装而启动；仅在用户请求相应行为时使用。未做独立核验时如实记录核验范围。

来源与修改记录见 `.codex/skill-sources.lock.json` 及 `docs/POFSS/科研技能审阅记录_20260912.md`。
