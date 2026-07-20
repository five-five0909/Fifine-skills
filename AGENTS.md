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
  "include": ["academic-lit-speed-read", "academic-ref-classify"],
  "targets": ["claude", "codex"]
}
```

Omit `include` to install all publishable skills. Omit `targets` to auto-detect from existing directories.

## Publishable skills

| Skill | Description |
|-------|-------------|
| workflow-dev-done-flow | 通用开发工作流引导工具，硬编码阶段序列 + required/optional 标记 + TODO 动态追踪 |
| math-rethlas | AI 驱动的数学公式形式化证明工具，驱动完整证明工作流 |
| academic-idea-hook-forge | 论文 PDF 结构化解构工具，提取 hook 并输出 HTML 分析报告 |
| academic-paper-weaver | 统一论文阅读 skill，支持 first-pass / second-pass / full / custom 模式 |
| document-paddleocr-vl | PaddleOCR-VL 官方 AI Studio API 文档解析工具，将 PDF/图片/扫描件解析为 Markdown 和图片资产 |
| academic-lit-speed-read | 学术文献速读/精读引导工具，输出 HTML 阅读报告 |
| academic-topic-refiner | 研究选题精炼工具 |
| academic-ref-rename | 文献文件批量重命名 |
| academic-ref-classify | 文献自动分类 |
| review-grill-me-cn | 方案压力测试工具 |
| academic-llm-research-grill | LLM/PyTorch 研究方向自检 |
| academic-write-research-grill | 写稿前结构化审问 |
| academic-humanizer | 学术文本去公式化、去空泛表达并保持事实、术语和逻辑关系不变 |
| writing-style | 可选择角色的写作风格工具，支持按角色特点写作/改写，并通过 original/final 自动学习风格规则 |
| academic-radar | 论文方向追踪雷达，调用 Node 脚本检索 arXiv/OpenAlex/S2，生成 H1/H2/H3 分级 HTML 报告 |
| academic-search | 学术检索方法论知识库 skill，提供平台路由、API 优先策略、元数据 schema 和站点经验 |
| writing-prompt-amplifier | 指令强化工具 |
| media-transcript | 本地视频/音频转文稿工具，使用 ffmpeg + DashScope ASR 输出 transcript.txt |
| web-tavily-search | Tavily 实时网络搜索 |
| workflow-trellis-task-orchestrator | Trellis 任务编排器 |
| workflow-parallel-executor-with-trellis | Trellis 并行任务执行器 |
| agent-trans-criptase | 会话续接与本地代码/文档检索工具 |

## Skill Routing

| 用户意图 | Skill |
|----------|-------|
| 学术写作有模板化或 AI 味，需在不改变事实的前提下修订 | academic-humanizer |
| 写作/改写时需要先选择角色、按角色特点输出 | writing-style |
| 证明数学题，形式化验证 | math-rethlas |
| 开发任务启动、规划工作流 | workflow-dev-done-flow |
| 方案压力测试、找逻辑漏洞 | review-grill-me-cn |
| 论文 PDF 结构化拆解、提取 hook | academic-idea-hook-forge |
| 文献快速阅读、输出摘要报告 | academic-lit-speed-read |
| LLM/PyTorch 研究方向审查 | academic-llm-research-grill |
| 本地视频或音频转文稿 | media-transcript |
| 论文全流程精读（摘要/引言/方法/实验） | academic-paper-weaver |
| OCR、解析扫描件/图片/PDF 为 Markdown | document-paddleocr-vl |
| 大任务拆分为并行子流程 | workflow-parallel-executor-with-trellis |
| 强化/改写一条 AI 指令 | writing-prompt-amplifier |
| PDF 文献自动分类到主题桶 | academic-ref-classify |
| PDF 文献按元数据批量重命名 | academic-ref-rename |
| 需要实时联网搜索当前信息 | web-tavily-search |
| 研究选题模糊，需要聚焦精炼 | academic-topic-refiner |
| Trellis 任务编排、生成 PRD | workflow-trellis-task-orchestrator |
| 写稿/论文前的结构化自我审问 | academic-write-research-grill |

## Distribution targets

| Tool | Skills path |
|------|------------|
| Claude Code | `.claude/skills/{name}/` |
| Codex | `.codex/skills/{name}/` |
| Generic agents | `.agents/skills/{name}/` |

## Important boundary

Users who install this GitHub repository should ultimately receive only skill-related files in their project skill directories. Development resources in the source repository are not part of the distributed skill payload.
