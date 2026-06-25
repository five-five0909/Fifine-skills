---
name: dev-done-flow
description: universal development workflow guide for software engineering, java backend work, llm applications, agent/rag projects, architecture refactoring, bug diagnosis, performance/security work, and long-running engineering goals. use when the user wants to start, plan, structure, diagnose, or iterate on a development task and expects the AI assistant to create local markdown workflow documents under `.dev-done-flow/`, update `Agents.md` or `AGENTS.md`, ask structured questions, record answers, and guide the project through discovery, requirements, design, planning, implementation, verification, release, observability, feedback, and iteration.
---

# Dev Done Flow

## 核心原则

- **主干阶段序列由脚本写死，AI 不得自行调整 required 阶段的顺序。**
- **AI 拥有 optional 阶段的判断空间**：可跳过、合并或重排 optional 阶段，但必须在 `stages/skipped.md` 记录原因。
- **每个阶段详情独立存储**：`stages/<name>.md` 存问答和产出，`active.md` 只存摘要和 TODO。
- **TODO 由脚本驱动**：skill 触发时输出 TODO 列表；每个阶段结束时 AI 调用 `update_stage.py` 刷新，不手动编辑 TODO。
- **本地文档是主记忆**：所有问答、假设、决策必须写入对应的 `stages/<name>.md`，不能只存在于对话中。

## 用户入口

- `@dev-done-flow 我想做 <任务描述>`
- `@dev-done-flow 有个 bug: <症状描述>`
- `@dev-done-flow 需要重构 <目标模块>`

用户只需描述任务，后续分类、阶段排列、TODO 输出、问答记录全部由脚本 + AI 处理。

## AI 的判断空间（重要）

脚本只锁定主干，AI 在以下范围内可以自主判断：

| 可以判断 | 不可以判断 |
|---------|-----------|
| 跳过标注为 optional 的阶段 | 跳过标注为 required 的阶段 |
| 将两个相邻 optional 阶段合并为一步 | 改变 required 阶段的相对顺序 |
| 在阶段内决定子步骤顺序和侧重点 | 在没有运行 plan_flow.py 的情况下开始工作 |
| 根据上下文决定每轮提问的数量（1-4个）| 将用户答案只留在对话中不写入文件 |
| 判断某个阶段是否已有足够信息可以跳过提问 | 在 requirements 不明确时生成代码 |

**跳过或合并 optional 阶段时，必须立刻调用 update_stage.py 标记为 skipped，并在 stages/skipped.md 写明原因。**

## 脚本入口（三步必须按序执行）

### Step 1：规划阶段队列 + 输出 TODO

```bash
python <当前skill目录>/scripts/plan_flow.py \
  --root <项目根目录> \
  --request-text "<用户原始描述>"
```

若任务类型已明确：

```bash
python <当前skill目录>/scripts/plan_flow.py \
  --root <项目根目录> \
  --task-type <类型> \
  --request-text "<用户原始描述>"
```

支持的任务类型：`new-feature` / `java-backend` / `llm-app` / `rag` / `agent` / `architecture` / `refactoring` / `bug-diagnosis` / `performance` / `security` / `long-running`

**脚本输出包含：**
- 写入 `.dev-done-flow/manifest.json`（含任务类型、有序阶段列表、required/optional 标记、每阶段 status）
- 打印 TODO 列表（▶ 指向当前阶段，✅ 标记已完成，⏭ 标记已跳过）
- 打印第一阶段提问清单

**AI 必须展示 TODO 列表给用户，让用户了解接下来的工作节奏。**

### Step 2：初始化工作目录文档

```bash
python <当前skill目录>/scripts/init_dev_done_flow.py \
  --root <项目根目录> \
  --task-name "<简短任务名>" \
  --task-type <类型> \
  --user-request "<用户原始描述>"
```

脚本执行后：
- 创建/更新 `.dev-done-flow/active.md`（摘要 + TODO 区块）
- 预建 `.dev-done-flow/stages/<name>.md`（每个阶段独立骨架文件）
- 创建 `.dev-done-flow/stages/skipped.md`（optional 阶段跳过记录）
- 创建 `.dev-done-flow/decisions.md` 和 `artifacts/` 模板
- 更新项目 `AGENTS.md`

### Step 3：每个阶段结束时更新进度

```bash
# 标记阶段完成，自动推进到下一阶段
python <当前skill目录>/scripts/update_stage.py \
  --root <项目根目录> \
  --stage <阶段名> \
  --status done

# 跳过一个 optional 阶段（必须提供原因）
python <当前skill目录>/scripts/update_stage.py \
  --root <项目根目录> \
  --stage <阶段名> \
  --status skipped \
  --reason "<跳过原因>"
```

脚本执行后：
- 更新 `manifest.json` 中该阶段 status
- 自动将下一个 pending 阶段设为 in_progress
- 刷新 `active.md` 中的 TODO 区块
- 更新 `stages/<name>.md` 中的 status 行

## 本地文档结构

```text
.dev-done-flow/
  manifest.json          ← 任务类型、有序阶段列表、required/optional、status（由脚本维护）
  active.md              ← 摘要 + TODO 区块 + 阶段摘要（精简，快速浏览）
  decisions.md           ← 持久决策记录
  stages/
    <stage-name>.md      ← 每阶段独立：问答、假设、开放问题、产出
    skipped.md           ← optional 阶段跳过/合并记录
  artifacts/
    requirements.md
    flow-design.md
    tech-spec.md
    task-plan.md
    tdd-plan.md
    eval-plan.md
    release-plan.md
    observability-plan.md
```

## 硬编码阶段序列

required 阶段不可跳过，optional 阶段 AI 可判断：

| 任务类型 | 阶段序列（加粗为 required） |
|---------|--------------------------|
| `new-feature` | **goal → context-discovery → requirements → flow-design → technical-design → task-planning** → tdd-plan → **implementation → verification** → release → observability → feedback → iteration |
| `java-backend` | **goal → existing-code-discovery → backend-requirements → business-flow-state-design → java-technical-design → api-db-transaction-design → task-planning** → tdd-plan → **unit-integration-regression-verification** → release → jvm-api-db-observability → iteration |
| `llm-app` / `rag` / `agent` | **goal → use-case-discovery → requirements → flow-design → llm-technical-design → eval-planning → implementation → offline-evaluation** → release → observability → bad-case-feedback → iteration |
| `architecture` | **goal → current-architecture-discovery → problems → architecture-requirements → rfc-technical-design → migration-plan → task-planning → characterization-tests → refactor → regression-verification** → release → observability → iteration |
| `refactoring` | **goal → current-code-discovery → problems → refactoring-requirements → technical-design → task-planning** → characterization-tests → **refactor → regression-verification** → release → iteration |
| `bug-diagnosis` | **symptom → triage → reproduction → expected-vs-actual → evidence-collection → root-cause-analysis** → failing-test → **fix-plan → implementation → regression-test** → release → postmortem |
| `performance` | **goal → performance-baseline → profiling → bottleneck-analysis → optimization-design → task-planning → implementation → benchmark-verification** → release → performance-observability → iteration |
| `security` | **goal → threat-model → vulnerability-discovery → security-requirements → security-design → task-planning → implementation → security-verification** → release → security-observability → iteration |
| `long-running` | **goal → context-discovery → requirements → technical-design → milestone-planning → task-planning** → tdd-plan → **implementation → verification** → release → observability → feedback → iteration |

## 每轮对话节奏

AI 在每个阶段内自主判断节奏，但遵守以下规则：

1. 每轮最多 4 个问题；已有答案的问题不重复问
2. 将用户答案、假设、开放问题追加写入当前阶段的 `stages/<name>.md`
3. 判断阶段是否完成（关键问题已有答案，或已记录为 assumption）
4. 阶段完成后：
   - 在 `active.md` 的 Stage Summaries 区块追加一段摘要
   - 将稳定产出写入对应 `artifacts/` 文件
   - 调用 `update_stage.py --status done` 刷新 TODO
5. 展示刷新后的 TODO 列表，让用户知道下一步

## 禁止行为

- 不能在未运行 `plan_flow.py` 的情况下开始工作
- 不能跳过 required 阶段
- 不能改变 required 阶段的相对顺序
- 不能手动编辑 active.md 的 TODO 区块（由脚本维护）
- 不能将用户答案只留在对话中不写文件
- 不能在 requirements / acceptance criteria 不明确时生成代码
- 不能凭空发明项目事实（语言、框架、模块结构等）
