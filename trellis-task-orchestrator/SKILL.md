---
name: trellis-task-orchestrator
description: |
  Trellis 任务编排器。当用户给出任何开发任务、研究任务、日常任务、Bug修复、功能开发、重构、Spec更新时，
  按 Trellis 最佳工作流自动编排 Claude Code 会话：判断任务类型 → 初始化检查 → 生成启动提示词 →
  生成 PRD 骨架 → 约束先 brainstorm 再动代码 → 推进实现 → 验收 → finish-work 收尾。
  触发词：新功能、Bug、重构、review、spec更新、开始做、帮我做、任务规划、trellis、PRD、
  项目初始化、开发任务、我要实现、怎么开始、开始一个任务。
  重要：只要用户描述的是一个需要编写代码或管理任务的需求，都应该主动使用此 skill，不要等用户说"用 trellis"。
argument-hint: "[任务描述，如：新增用户权限模块 / 修复登录 500 / 重构 spectral_preprocessing.py]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# Trellis Task Orchestrator

将任意任务按 Trellis 最佳实践拆解、编排、生成可直接粘贴到 Claude Code 的完整启动套件。

---

## 第一步：任务类型判断

收到任务描述后，首先识别任务类型，这决定后续的编排策略：

| 类型 | 识别信号 | 编排策略 |
|------|---------|---------|
| **NEW_FEATURE** | 新增、实现、开发、添加功能 | brainstorm → PRD → before-dev → 实现 → check → finish |
| **BUG_FIX** | 修复、报错、异常、NaN、崩溃、500 | 诊断 → 最小复现 → 修复 → 验收 → finish |
| **REFACTOR** | 重构、优化、拆分、解耦、清理 | spec审查 → 影响分析 → 渐进重构 → 回归测试 → finish |
| **REVIEW** | 检查、审查、review、对照规范 | check命令 → spec对照 → 输出报告 |
| **SPEC_UPDATE** | 总结规范、记录约定、update-spec | 提炼规律 → 写入spec → 同步团队 |
| **RESEARCH_CODE** | PISFM、模型训练、实验脚本、数据集 | 实验设计 → 单元验证 → 集成 → 结果记录 |
| **FREELANCE** | Spring Boot、Vue、接外包、交付 | 需求确认 → PRD → 分模块并行 → 联调 → 交付 |

判断完成后，输出：

```
◼ 任务类型识别
━━━━━━━━━━━━━━━━━━━━━━━━━━
类型：[TYPE]
任务：[用户描述]
预估阶段：[N 个阶段]
编排策略：[一句话说明]
━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 第二步：Trellis 环境检查

生成用户应在终端执行的检查命令，输出可直接复制的代码块：

```bash
# ① 检查 trellis 是否安装
trellis --version

# ② 检查项目是否已初始化（.trellis/ 目录是否存在）
ls -la .trellis/

# ③ 若未初始化，执行（替换 your-name）：
trellis init --claude -u your-name
```

**根据任务类型，补充额外检查：**

- RESEARCH_CODE：检查 WSL2/CUDA 环境、虚拟环境激活
- FREELANCE：检查 Spring Boot 端口、前端 proxy 配置
- BUG_FIX：检查 git log、当前 branch 状态

---

## 第三步：生成 Trellis PRD 骨架

根据任务类型，输出可直接放进 `.trellis/tasks/[task-slug]/prd.md` 的 PRD 模板：

```markdown
# [任务名称]

## 状态
- 创建时间：[今日]
- 负责人：[用户名]
- 类型：[任务类型]
- 优先级：[高/中/低]

## 背景与动机
> 为什么要做这个任务？解决什么问题？

[待填写]

## 目标与成功标准
- [ ] [可量化的验收标准1]
- [ ] [可量化的验收标准2]

## 技术范围
### 涉及模块
- [模块/文件路径]

### 不在范围内
- [明确排除的内容]

## 实现思路（brainstorm 后填写）
> 先留空，由 /trellis:brainstorm 补充

## 任务拆分
> 先留空，由 brainstorm 确认后补充

## 参考资料
- 相关 spec：`.trellis/spec/[相关规范].md`
- 相关文档：[链接]

## 验收清单
- [ ] 单元测试通过
- [ ] lint/type-check 无报错
- [ ] spec 对照检查通过
- [ ] 功能在目标环境验证
```

---

## 第四步：生成 Claude Code 启动提示词

这是核心输出。生成一段可以**直接粘贴进 Claude Code 第一条消息**的提示词，格式如下：

---

根据任务类型选择对应模板（见 `references/prompt-templates.md`），**不要生成通用模板，要根据具体任务内容填充**。

**重要约束，必须写入提示词：**

1. **禁止直接改代码**：必须先执行 `/trellis:brainstorm`，产出实现方案并经用户确认后再动手
2. **先读 spec**：在 `/trellis:brainstorm` 之前，先运行 `/trellis:before-dev` 加载相关规范
3. **推进节奏**：每个子任务完成后，用 `/trellis:check` 验收，再推进下一个
4. **收尾**：所有子任务完成后，运行 `/trellis:finish-work`

生成的启动提示词结构：

```
[会话目标一句话说明]

## 任务信息
- 任务类型：[TYPE]
- PRD 位置：.trellis/tasks/[slug]/prd.md
- 主要涉及：[文件/模块列表]

## 执行步骤（严格按顺序）

**Step 0（会话启动）**
/start

**Step 1（加载规范）**
/trellis:before-dev

**Step 2（需求澄清 + 方案设计）**
/trellis:brainstorm
→ 产出：实现方案 + 任务拆分 + 接口定义（若有）
→ 等待用户确认后再继续

**Step 3（实现）**
[根据 brainstorm 结果，逐子任务推进]
- 每个子任务完成后运行 /trellis:check
- check 通过后再进入下一个子任务

**Step 4（收尾）**
/trellis:finish-work

## 技术约束
[根据任务类型自动填充，见 references/tech-constraints.md]

## 验收标准
[从 PRD 成功标准提取]
```

---

## 第五步：看板状态追踪

输出任务初始看板，采用你熟悉的 Kanban 格式：

```
╔══════════════════════════════════════════════════════════╗
║  Trellis Task Board ─ [任务名]                           ║
╠══════════════════════════════════════════════════════════╣
║  ◼ 待执行          ◼ 进行中         ◼ 待验收             ║
╠════════════════════╦═════════════════╦═══════════════════╣
║  ◻ Step 0: start   ║                 ║                   ║
║  ◻ Step 1: before- ║                 ║                   ║
║    dev             ║                 ║                   ║
║  ◻ Step 2: brain-  ║                 ║                   ║
║    storm           ║                 ║                   ║
║  ◻ Step 3: 实现    ║                 ║                   ║
║  ◻ Step 4: check   ║                 ║                   ║
║  ◻ Step 5: finish  ║                 ║                   ║
╚════════════════════╩═════════════════╩═══════════════════╝
```

---

## 第六步：验收标准 Checklist

根据任务类型，输出最终验收 Checklist（对应 `/trellis:finish-work` 的内容）：

读取 `references/acceptance-checklist.md` 获取各类型的完整验收项。

---

## 特殊场景处理

### 场景：用户说"直接帮我写代码"

拒绝，输出：

```
⚠️  检测到跳过 brainstorm 的请求

按 Trellis 最佳实践，直接写代码会导致：
- 实现方向可能与实际需求偏差
- 缺乏 spec 约束，产出难以复用
- 后续 check 失败率高

建议先完成 /trellis:brainstorm（通常 5-10 分钟），
方案确认后实现质量更高、返工更少。

是否继续走 brainstorm 流程？
```

### 场景：RESEARCH_CODE（PISFM 等科研代码）

补充以下约束到启动提示词：

```
## 科研代码额外约束
- 每个实验脚本改动前，记录 baseline 指标到 .trellis/workspace/[user]/journal.md
- NaN/loss 异常：先用最小数据集（10条样本）复现，确认后再修复
- 模型改动须先单元测试各子模块（forward pass shape check）
- 实验结果记录格式：见 .trellis/spec/research/experiment-log-format.md
```

### 场景：FREELANCE（Spring Boot + Vue 外包）

补充以下约束到启动提示词：

```
## 外包交付额外约束
- 需求确认：brainstorm 阶段必须输出接口文档草稿（Swagger/OpenAPI 格式）
- 分层隔离：Controller/Service/Mapper 严格分层，禁止跨层调用
- 前后端联调：先 mock API 跑通前端，再对接真实后端
- 交付物清单：代码 + README + SQL 建表语句 + 操作说明
```

---

## 输出顺序总结

每次收到任务时，严格按以下顺序输出，不跳过任何步骤：

1. 任务类型识别面板
2. Trellis 环境检查命令（可复制）
3. PRD 骨架（可复制到 `.trellis/tasks/`）
4. Claude Code 启动提示词（可直接粘贴）
5. 初始看板
6. 验收 Checklist

整个输出控制在一个回复内，分 section 清晰展示。

---

## 参考文件

- `references/prompt-templates.md` — 各任务类型的启动提示词完整模板
- `references/acceptance-checklist.md` — 各任务类型的验收 Checklist
- `references/tech-constraints.md` — 技术栈约束（科研/外包/重构 专项）
