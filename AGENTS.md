# Fifine-skills

Reusable agent skills source repository for Claude Code, Codex, and other AI coding tools.

## Install

```bash
npm install github:five-five0909/Fifine-skills
```

This repository is installed directly from GitHub. The source repository may contain development resources such as `.trellis/`, `.codegraph/`, task files, and maintainer docs, but `postinstall.js` only distributes an explicit whitelist of publishable skills into the target project.

## Canonical skill standard

Inside this repository, skill content should follow a **`.agents`-compatible neutral standard**:

- skill docs should not assume Claude-only global paths
- skill docs should not hard-code the author's machine path
- `.claude/.codex/.agents` are **distribution targets**
- the skill content itself should stay host-neutral

## Per-project config

Create `skills.json` in your project root to control which skills are installed and where:

```json
{
  "include": ["lit-speed-read", "ref-classify"],
  "targets": ["claude", "codex"]
}
```

Omit `include` to install all publishable skills. Omit `targets` to auto-detect from existing directories.

## Publishable skills

| Skill | Description |
|-------|-------------|
| dev-done-flow | 通用开发工作流引导工具，硬编码阶段序列 + required/optional 标记 + TODO 动态追踪 |
| rethlas | AI 驱动的数学公式形式化证明工具，驱动完整证明工作流 |
| idea-hook-forge | 论文 PDF 结构化解构工具，提取 hook 并输出 HTML 分析报告 |
| paper-weaver | 统一论文阅读 skill，支持 first-pass / second-pass / full / custom 模式 |
| lit-speed-read | 学术文献速读/精读引导工具，输出 HTML 阅读报告 |
| topic-refiner | 研究选题精炼工具 |
| ref-rename | 文献文件批量重命名 |
| ref-classify | 文献自动分类 |
| grill-me-cn | 方案压力测试工具 |
| llm-research-grill | LLM/PyTorch 研究方向自检 |
| write-research-grill | 写稿前结构化审问 |
| humanizer | 去除文本中的 AI 写作痕迹，基于 Wikipedia 的 33 条 AI 写作模式检测与修正规则 |
| prompt-amplifier | 指令强化工具 |
| tavily-search | Tavily 实时网络搜索 |
| trellis-task-orchestrator | Trellis 任务编排器 |
| parallel-executor-with-trellis | Trellis 并行任务执行器 |

## Distribution targets

| Tool | Skills path |
|------|------------|
| Claude Code | `.claude/skills/{name}/` |
| Codex | `.codex/skills/{name}/` |
| Generic agents | `.agents/skills/{name}/` |

## Important boundary

Users who install this GitHub repository should ultimately receive only skill-related files in their project skill directories. Development resources in the source repository are not part of the distributed skill payload.
