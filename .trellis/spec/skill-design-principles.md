# Skill 设计原则

> **适用范围**：本仓库所有 `skills/*/SKILL.md` 的编写与维护。
> **权威来源**：基于 Anthropic 官方 skill-creator 文档及 Claude Code skill 路由机制深度分析。

---

## 一、工作机制：渐进式披露（Progressive Disclosure）

Skill 内容分三层，按需加载，**不全量注入上下文**：

| 层级 | 内容 | 加载时机 | 大小建议 |
|------|------|----------|----------|
| Level 1 | `name` + `description`（frontmatter 元数据） | **始终常驻**上下文 | ≤150 词 |
| Level 2 | SKILL.md body（正文指令） | 触发时才加载 | ≤5000 词 |
| Level 3 | `references/`、`scripts/` 伴随文件 | body 内部判断后按需加载 | 无限制 |

> **推论**：36 个 skill 全部元数据常驻 ≈ 3600 词。若全部展开正文 > 100000 词，不可能放入上下文。
> 因此，description 质量决定路由准确性；body 质量决定执行质量。

---

## 二、Description 字段规范（最高优先级）

### 核心原则

> **description 描述"何时触发"，不描述"skill 是什么"。**

模型基于 description 决定是否调取 skill。描述 skill 身份无助于触发；描述触发情境才是有效信号。

### 必须包含的要素

1. **触发情境**：`Use this skill when [具体情境]`
2. **Trigger 关键词**：`Trigger: /skill-name, keyword1, keyword2, 中文词1, 中文词2`
3. **产出物简述**：说明 skill 会产生什么（一句话）
4. **负向排除**（推荐）：说明什么情况下不应触发

### 模板

```
Use this skill when [具体触发情境，包括用户意图和上下文线索]. Trigger: /name, keyword1, keyword2, 中文触发词. [产出物一句话]. [可选：Not for X — use Y instead.]
```

### 正反例

```yaml
# ❌ 错：描述 skill 身份，而非触发条件
description: The humanizer skill analyzes text and removes AI writing patterns using 33 rules.

# ✅ 对：触发条件 + 关键词 + 产出 + 排除
description: Use this skill when the user wants to remove AI-generated writing patterns
  from text to make it sound more natural. Trigger: /humanizer, humanize, ai writing,
  de-ai, make it sound human, AI味. Detects 33 patterns from Wikipedia's Signs of AI
  writing guide. Not for code, math, or planning tasks.
```

### 关键注意事项

- Claude 有 **undertrigger（触发不足）** 倾向——描述应稍微"积极"，主动说明触发边界
- 简单单步查询（"读这个文件"）即使 description 完全匹配也不会触发——skill 只对**复杂多步骤任务**可靠触发
- 中英双语关键词覆盖中文用户的自然语言输入
- description 必须是**单行**（本仓库 validator 不支持多行 YAML 块标量）

---

## 三、Body 正文规范

### 3.1 Trigger Check Block（正文入口必须项）

每个 skill 正文的**第一个 H2 之前**必须有触发核验块：

```markdown
## Trigger check
This skill applies when [触发条件]. If [负向条件], stop — [替代行动或"this skill doesn't apply"].

```

**作用**：即使 skill 被错误触发，模型也能在执行前自我纠正，不乱跑流程。

### 3.2 正文结构建议

```markdown
## Trigger check         ← 入口核验（必须）
## [核心流程/任务]       ← 主体指令
## [输出格式]            ← 固定输出格式（保证调用结果一致）
```

### 3.3 References / Scripts 的延迟加载

- `references/` 中的文件**不要在正文开头全量 Read**
- 正文应根据当前任务类型判断需要读哪个 reference，按需加载
- 这是防止大型知识库污染上下文的核心手段

### 3.4 发现重复工作则打包脚本

若测试发现多个调用场景都在重写同一个辅助脚本（如 `parse_pdf.py`），应将其打包到 `scripts/`，在正文中直接引用，而非每次让模型重新生成。

---

## 四、大规模 Skill 库的路由防污染机制

### 4.1 AGENTS.md Skill Routing Table

在项目 AGENTS.md 中维护意图→skill 映射表，提供显式路由参照：

```markdown
## Skill Routing

| 用户意图 | Skill |
|----------|-------|
| 写作有 AI 味，想更自然 | humanizer |
| 证明数学题 | rethlas |
| ...      | ...   |
```

模型不靠猜，有路由表做参照。

### 4.2 AGENTS.md 触发率提升指令

在 AGENTS.md 加入以下语句可显著提升 skill 触发率：

```
IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning.
```

这明确要求模型优先调取 skill，而非依赖训练数据推断。

### 4.3 Style / Spec 文件的 JSONL 定向注入

对于有大量 spec/style 文件的项目，**不要在 AGENTS.md 全量列出所有 style 文件**。
改用 Trellis 任务级别的 `implement.jsonl` 按需注入：

```jsonl
{"file": ".trellis/spec/frontend/components.md", "reason": "Component conventions for this task"}
{"file": ".trellis/spec/backend/api-style.md", "reason": "API naming conventions"}
```

规则：
- 只包含当前任务实际需要的 spec 文件
- 不包含将被修改的源文件
- 不注入代码文件（子代理有 Read/Grep，自己按需取）

### 4.4 大型 Spec 文件的两层 Index 结构

对于 500 行以上的 spec/reference 文件，使用两层结构：

```
.trellis/spec/frontend/
├── index.md        ← 导航表（~100 行）：任务类型 → 章节 + 行号范围
└── guide.md        ← 完整内容（500+ 行）
```

`index.md` 示例格式：

```markdown
| 开发任务 | 读取章节 | 行范围 |
|----------|----------|--------|
| 新建 React 组件 | Component Structure | L10-80 |
| 颜色 token 使用 | Design Tokens | L201-350 |
```

**收益**：AI 先读 100 行导航，精确读取 ~200 行目标内容，节省 70%+ token。

---

## 五、Description 优化的工程化流程（进阶）

当 skill 触发率不理想时，按以下流程系统优化：

1. **生成测试集**：20 条查询（10 条应触发，10 条不应触发，后者包含"近似误触发"案例）
2. **自动优化循环**：60% 训练 / 40% 测试，每轮跑 3 次取平均触发率，调用模型改进 description，最多 5 轮
3. **用测试集得分选最优**，避免过拟合训练集
4. **近似误触发的反例最有价值**：与 skill 共享关键词但实际需要不同行为的查询

---

## 六、AGENTS.md vs SKILL.md 职责分工

| | AGENTS.md | SKILL.md |
|---|---|---|
| 加载时机 | 每次会话始终加载 | 仅触发时加载 |
| 类比 | 贴在显示器上的便利贴 | 抽屉里的专业手册 |
| 写什么 | 全局约束、routing table、工具链规范、安装说明 | 单个 skill 的触发条件 + 完整执行指令 |
| 大小约束 | 严格控制，每行都在常驻上下文中 | 正文 ≤5000 词，超出部分移到 references/ |

---

## 七、本仓库 Validator 约束

`node scripts/validate-skills.mjs` 强制要求：

- frontmatter 所有字段必须是**单行** `key: value` 格式（不支持 YAML 块标量 `|` 或列表 `- item`）
- `name` 字段必须是 kebab-case，且与目录名一致
- `description` 字段必须存在且非空
- `agents/openai.yaml` 必须存在，包含 `interface.display_name` 和 `interface.short_description`
- 禁止 `__pycache__`、`node_modules`、`.venv` 等目录出现在仓库中

每次新增或修改 skill 后运行验证：

```bash
node scripts/validate-skills.mjs
```
