# Fifine-skills

> 可复用的 AI 编程技能包，支持 Claude Code、Codex 等主流 AI 编程工具。

一次安装，自动分发到项目内所有 AI 工具目录（`.claude/skills/`、`.codex/skills/`、`.agents/skills/`）。

---

## 安装

无需发布到 npm registry，直接从 GitHub 安装：

```bash
npm install github:five-five0909/Fifine-skills
```

安装后 `postinstall.js` 自动检测项目内已有的 AI 工具目录，并将 skills 分发进去。

---

## 按需安装（可选）

在项目根目录创建 `skills.json`，控制安装哪些 skills 以及分发到哪些工具：

```json
{
  "include": ["lit-speed-read", "ref-classify"],
  "targets": ["claude", "codex"]
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `include` | 要安装的 skill 名称列表 | 全部安装 |
| `targets` | 目标工具：`claude` / `codex` / `agents` | 自动检测 |

---

## 技能清单

### 学术研究类

| Skill | 触发词 / 说明 |
|-------|-------------|
| **lit-speed-read** | 学术文献速读/精读引导工具。给一篇论文（URL / PDF / HTML），自动解析 Abstract、提炼核心 4 问、生成思考题，输出 HTML 阅读报告 |
| **topic-refiner** | 研究选题精炼工具。帮助从模糊想法收敛到可执行的论文选题 |
| **ref-rename** | 文献 PDF 批量重命名。统一为 `作者-年份-关键词` 格式 |
| **ref-classify** | 文献自动分类。按研究方向将 PDF 分组归档 |
| **llm-research-grill** | LLM / PyTorch 研究方向自检。交互式收集研究状态，生成结构化审问报告 |
| **write-research-grill** | 写稿前结构化审问。逼你想清楚再动笔 |

### 通用效率类

| Skill | 触发词 / 说明 |
|-------|-------------|
| **grill-me-cn** | 方案压力测试。用于方案审查、执行任务前的盲点检查 |
| **prompt-amplifier** | 指令强化工具。把普通指令加工成高执行度版本 |
| **tavily-search** | 实时网络搜索（Tavily MCP）。遇到需要最新信息时自动触发 |

### Trellis 工作流类

| Skill | 触发词 / 说明 |
|-------|-------------|
| **trellis-task-orchestrator** | Trellis 任务编排器。新功能 / Bug / 重构等开发任务的全流程编排 |
| **parallel-executor-with-trellis** | 并行任务执行器。大型任务自动拆分 + 并行 Agent 执行 |
| **claude-sync-bridge** | Claude Code skills 与 MCP 配置同步工具 |

---

## 工作原理

```
npm install github:five-five0909/Fifine-skills
        │
        ▼
postinstall.js 运行
        │
        ├── 读取项目根目录的 skills.json（不存在则安装全部）
        ├── 检测 .claude/ .codex/ .agents/ 是否存在
        └── 复制 skill 目录 → {tool-dir}/skills/{name}/
```

分发后，每个 skill 的 `SKILL.md` 被对应 AI 工具加载为上下文，无需额外配置。

---

## 各工具对应目录

| AI 工具 | Skills 目录 | 上下文文件 |
|---------|------------|-----------|
| Claude Code | `.claude/skills/` | `CLAUDE.md` |
| Codex | `.codex/skills/` | `AGENTS.md` |
| 通用 Agent | `.agents/skills/` | `AGENTS.md` |

---

## 新增 Skill

每个 skill 最少只需一个文件：

```
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

```
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

直接用 `claude` 或 `codex` 打开此仓库，Trellis 工作流自动注入。

---

## 仓库结构

```
Fifine-skills/
├── README.md
├── CLAUDE.md              ← Claude Code 专用指令
├── AGENTS.md              ← Codex / 跨工具说明
├── package.json
├── scripts/
│   └── postinstall.js     ← 安装分发逻辑
├── {skill-name}/          ← 每个 skill 一个目录
│   ├── SKILL.md
│   └── ...
├── .claude/               ← Claude Code 工作流配置
├── .codex/                ← Codex 工作流配置
└── .trellis/              ← Trellis 任务系统
```
