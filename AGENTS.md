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
  "include": ["fifine-lit-speed-read", "fifine-pdf-ref-classify"],
  "targets": ["claude", "codex"]
}
```

Omit `include` to install all publishable skills. Omit `targets` to auto-detect from existing directories.

## Publishable skills

| Skill | Description |
|-------|-------------|
| fifine-rethlas | AI 驱动的数学公式形式化证明工具，驱动完整证明工作流 |
| fifine-paper-idea-hook-forge | 论文 PDF 结构化解构工具，提取 hook 并输出 HTML 分析报告 |
| fifine-paper-weaver | 统一论文阅读 skill，支持 first-pass / second-pass / full / custom 模式 |
| fifine-paddleocr-vl | PaddleOCR-VL 官方 AI Studio API 文档解析工具，将 PDF/图片/扫描件解析为 Markdown 和图片资产 |
| fifine-handoff | 将当前会话压缩为脱敏的临时目录交接文档，供下一位 agent 继续工作 |
| fifine-lit-speed-read | 学术文献速读/精读引导工具，输出 HTML 阅读报告 |
| fifine-paper-topic-refiner | 研究选题精炼工具 |
| fifine-pdf-ref-rename | 文献文件批量重命名 |
| fifine-pdf-ref-classify | 文献自动分类 |
| fifine-grill-me-cn | 方案压力测试工具 |
| fifine-paper-llm-research-grill | LLM/PyTorch 研究方向自检 |
| fifine-paper-write-research-grill | 写稿前结构化审问 |
| fifine-live-humanizer | 中文创作与改稿，保留材料事实、自然中文韵律和活人感 |
| fifine-writing-style | 可选择角色的写作风格工具，支持按角色特点写作/改写，并通过 original/final 自动学习风格规则 |
| fifine-research-radar | 论文方向追踪雷达，调用 Node 脚本检索 arXiv/OpenAlex/S2，生成 H1/H2/H3 分级 HTML 报告 |
| fifine-research-search | 学术检索方法论知识库 skill，提供平台路由、API 优先策略、元数据 schema 和站点经验 |
| fifine-prompt-amplifier | 指令强化工具 |
| fifine-media-to-txt | 本地视频/音频转文稿工具，使用 ffmpeg + DashScope ASR 输出 transcript.txt |
| fifine-research-paper-writing | ML/CV/NLP 论文 Abstract / Introduction / Method / Experiments / Conclusion 写作与改写 |
| fifine-tavily-search | Tavily 实时网络搜索 |
| fifine-parallel-executor-with-trellis | Trellis 并行任务执行器 |
| fifine-trans-criptase | 会话续接与本地代码/文档检索工具 |

## Skill Routing

| 用户意图 | Skill |
|----------|-------|
| ML/CV/NLP 论文分章节写作、改写、段落逻辑和审稿人自检 | fifine-research-paper-writing |
| 学术写作有模板化或 AI 味，需在不改变事实的前提下修订 | fifine-live-humanizer |
| 写作/改写时需要先选择角色、按角色特点输出 | fifine-writing-style |
| 证明数学题，形式化验证 | fifine-rethlas |
| 方案压力测试、找逻辑漏洞 | fifine-grill-me-cn |
| 论文 PDF 结构化拆解、提取 hook | fifine-paper-idea-hook-forge |
| 文献快速阅读、输出摘要报告 | fifine-lit-speed-read |
| LLM/PyTorch 研究方向审查 | fifine-paper-llm-research-grill |
| 本地视频或音频转文稿 | fifine-media-to-txt |
| 论文全流程精读（摘要/引言/方法/实验） | fifine-paper-weaver |
| OCR、解析扫描件/图片/PDF 为 Markdown | fifine-paddleocr-vl |
| 需要把当前会话交接给下一位 agent | fifine-handoff |
| 大任务拆分为并行子流程 | fifine-parallel-executor-with-trellis |
| 强化/改写一条 AI 指令 | fifine-prompt-amplifier |
| PDF 文献自动分类到主题桶 | fifine-pdf-ref-classify |
| PDF 文献按元数据批量重命名 | fifine-pdf-ref-rename |
| 需要实时联网搜索当前信息 | fifine-tavily-search |
| 研究选题模糊，需要聚焦精炼 | fifine-paper-topic-refiner |
| 写稿/论文前的结构化自我审问 | fifine-paper-write-research-grill |

## Distribution targets

| Tool | Skills path |
|------|------------|
| Claude Code | `.claude/skills/{name}/` |
| Codex | `.codex/skills/{name}/` |
| Generic agents | `.agents/skills/{name}/` |

## Important boundary

Users who install this GitHub repository should ultimately receive only skill-related files in their project skill directories. Development resources in the source repository are not part of the distributed skill payload.
