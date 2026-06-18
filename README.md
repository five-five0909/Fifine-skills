# Fifine-skills

> 可复用的 AI 编程技能包，支持 Claude Code、Codex 和其他兼容 `.agents` 语义的工具。

一次安装，自动把 publishable skills 分发到项目内已有的 AI 工具目录：

- `.claude/skills/`
- `.codex/skills/`
- `.agents/skills/`

---

## 安装前先看

这个仓库的安装逻辑是：

1. 先把本仓库作为依赖装进 `node_modules/@fifine/skills`
2. 再由 `postinstall.js` 检测你的项目里**已经存在**的 AI 工具目录
3. 把 publishable skills 复制到对应的 `skills/` 目录

### 重要前置条件

安装前，你的项目里至少要先有下面目录中的一个：

- `.claude/`
- `.codex/`
- `.agents/`

如果一个都没有，`npm install` 仍然会成功，但 **不会分发任何 skill**。

---

## 快速开始

### 1）准备目标目录

按你的工具先建目录，例如：

```bash
mkdir -p .claude
mkdir -p .codex
mkdir -p .agents
```

> Windows / PowerShell 用户可自行换成等价命令。重点不是命令本身，而是这些目录要先存在。

### 2）从 GitHub 安装

```bash
npm install github:five-five0909/Fifine-skills
```

安装完成后，`postinstall.js` 会：

- 读取项目根目录的 `skills.json`（如果有）
- 检测 `.claude` / `.codex` / `.agents` 哪些存在
- 把白名单中的 publishable skills 复制到 `{tool-dir}/skills/{name}/`

### 3）检查结果

例如：

```text
.claude/skills/paper-weaver/
.codex/skills/paper-weaver/
.agents/skills/paper-weaver/
```

每个 skill 目录至少包含 `SKILL.md`，以及该 skill 运行所需的伴随脚本 / 资源文件。

---

## 按需安装

如果你不想安装全部 skills，可以在项目根目录创建 `skills.json`：

```json
{
  "include": ["lit-speed-read", "ref-classify"],
  "targets": ["claude", "codex"]
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `include` | 要安装的 skill 名称列表 | 全部 publishable skills |
| `targets` | 目标工具：`claude` / `codex` / `agents` | 自动检测已存在目录 |

上面的配置表示：

- 只安装 `lit-speed-read` 和 `ref-classify`
- 只复制到 `.claude/skills/` 和 `.codex/skills/`
- 不分发到 `.agents/skills/`

---

## 安装后到底会拿到什么

需要区分两层内容：

### 1）依赖包本体

也就是：

```text
node_modules/@fifine/skills
```

这里是安装脚本运行时所需的最小内容，只包含：

- `package.json`
- `README.md`
- `scripts/postinstall.js`
- `scripts/publishable-skills.json`
- 所有 publishable skill 目录

它**不应再包含**开发期资源，例如：

- `.trellis/`
- `.codegraph/`
- `.claude/`
- `.codex/`
- 任务文档、维护辅助文件等

### 2）最终分发产物

也就是：

```text
.claude/skills/{skill-name}/
.codex/skills/{skill-name}/
.agents/skills/{skill-name}/
```

这里只会复制 skill 自身内容，不会把开发资源带进你的项目 skill 目录。

---

## 工作原理

```text
npm install github:five-five0909/Fifine-skills
        │
        ▼
依赖被安装到 node_modules/@fifine/skills
        │
        ▼
postinstall.js 运行
        │
        ├── 读取项目根目录的 skills.json（不存在则安装全部）
        ├── 检测 .claude/ .codex/ .agents/ 哪些存在
        └── 复制 publishable skill → {tool-dir}/skills/{name}/
```

---

## Publishable skills

### 学术研究类

| Skill | 说明 |
|-------|------|
| **paper-weaver** | 统一论文阅读 skill，支持 first-pass / second-pass / full / custom 模式 |
| **lit-speed-read** | 学术文献速读/精读引导工具，输出 HTML 阅读报告 |
| **topic-refiner** | 研究选题精炼工具 |
| **ref-rename** | 文献 PDF 批量重命名 |
| **ref-classify** | 文献自动分类 |
| **llm-research-grill** | LLM / PyTorch 研究方向自检 |
| **write-research-grill** | 写稿前结构化审问 |

### 通用效率类

| Skill | 说明 |
|-------|------|
| **grill-me-cn** | 方案压力测试工具 |
| **prompt-amplifier** | 指令强化工具 |
| **tavily-search** | Tavily 实时网络搜索 |

### Trellis 工作流类

| Skill | 说明 |
|-------|------|
| **trellis-task-orchestrator** | Trellis 任务编排器 |
| **parallel-executor-with-trellis** | Trellis 并行任务执行器 |

---

## 各工具对应目录

| AI 工具 | Skills 目录 | 上下文文件 |
|---------|------------|-----------|
| Claude Code | `.claude/skills/` | `CLAUDE.md` |
| Codex | `.codex/skills/` | `AGENTS.md` |
| 通用 Agent | `.agents/skills/` | `AGENTS.md` |

---

## Canonical skill standard

仓库内的 skill 内容以 **`.agents` 兼容的中性标准** 为 canonical standard：

- `.claude/.codex/.agents` 是分发目标，不是 skill 内容的唯一语义来源
- skill 文档不应依赖作者机器路径
- skill 文档不应硬编码 Claude-only 全局路径
- skill 内容本身应尽量保持宿主无关

---

## 新增 Skill

每个 skill 最少只需一个文件：

```text
{skill-name}/
└── SKILL.md
```

`SKILL.md` 格式：

```markdown
---
name: skill-name
description: >
  一句话描述，包含触发词。
  触发词：/skill-name、关键词1、关键词2。
---

# skill-name

（执行流程 / 指令内容）
```

如有伴随脚本，放在同一目录下：

```text
{skill-name}/
├── SKILL.md
├── workflow.py
└── config.json
```

---

## 开发工作流（Trellis）

本仓库使用 Trellis 管理开发任务：

```bash
# 创建任务
python .trellis/scripts/task.py create "添加新 skill：xxx"

# 开始任务
python .trellis/scripts/task.py start <slug>

# 查看当前任务
python .trellis/scripts/task.py current

# 完成任务
python .trellis/scripts/task.py finish
```

直接用 `claude` 或 `codex` 打开此仓库，Trellis 工作流会自动注入。

---

## 源码仓库与安装包边界

这个 GitHub 仓库作为**源码仓库**，本身可以包含开发资源，例如：

- `.trellis/`
- `.codegraph/`
- 任务文档
- 维护说明

但用户通过 `npm install github:five-five0909/Fifine-skills` 安装时，最终应得到的是：

- 最小依赖包本体
- publishable skills
- 分发后的目标 skill 目录内容

开发期资源不应进入最终安装包。

---

## 仓库结构（源码仓库）

```text
Fifine-skills/
├── README.md
├── CLAUDE.md
├── AGENTS.md
├── package.json
├── scripts/
│   ├── postinstall.js
│   └── publishable-skills.json
├── {skill-name}/
│   ├── SKILL.md
│   └── ...
├── .claude/
├── .codex/
├── .trellis/
└── .codegraph/
```
