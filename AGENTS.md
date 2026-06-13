# Fifine-skills

Reusable agent skills package for Claude Code, Codex, and other AI coding tools.

## Install

```bash
npm install github:fifine/Fifine-skills
```

After install, `postinstall.js` automatically distributes skills to detected AI tool directories in the project.

## Per-project config

Create `skills.json` in your project root to control which skills are installed and where:

```json
{
  "include": ["lit-speed-read", "ref-classify"],
  "targets": ["claude", "codex"]
}
```

Omit `include` to install all skills. Omit `targets` to auto-detect from existing directories.

## Available skills

| Skill | Description |
|-------|-------------|
| lit-speed-read | 学术文献速读/精读引导工具，输出 HTML 阅读报告 |
| topic-refiner | 研究选题精炼工具 |
| ref-rename | 文献文件批量重命名 |
| ref-classify | 文献自动分类 |
| grill-me-cn | 方案压力测试工具 |
| llm-research-grill | LLM/PyTorch 研究方向自检 |
| write-research-grill | 写稿前结构化审问 |
| prompt-amplifier | 指令强化工具 |
| tavily-search | Tavily 实时网络搜索 |
| trellis-task-orchestrator | Trellis 任务编排器 |
| parallel-executor-with-trellis | Trellis 并行任务执行器 |
| claude-sync-bridge | Claude Code skills 同步工具 |

## Target directories

| Tool | Skills path |
|------|------------|
| Claude Code | `.claude/skills/{name}/` |
| Codex | `.codex/skills/{name}/` |
| Generic agents | `.agents/skills/{name}/` |
