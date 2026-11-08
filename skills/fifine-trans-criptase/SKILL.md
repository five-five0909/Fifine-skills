---
name: fifine-trans-criptase
description: 恢复 Claude Code 或 Codex CLI 历史会话，检索跨会话记忆，以及对本地代码和文档进行精确、语义或混合检索。用户说恢复会话、接着上次、查历史对话或检索本地代码时使用。
argument-hint: "[会话 ID 或前缀]"
---

# 会话续接与本地检索

直接使用本 skill 附带的 Node.js 命令，不注册或依赖 MCP。需要 Node.js 18 或以上，以及宿主允许执行本地命令。以下 `<skill-dir>` 是本 SKILL.md 所在目录，`<project>` 是目标项目绝对路径；每个参数分别传给进程，不将用户输入拼入 shell 命令。

入口：`node "<skill-dir>/scripts/semantic.mjs"`。skill 已内置项目专用 embedding 配置，也支持环境变量和私有配置覆盖；不要在会话中打印密钥。Base64 不是加密，发布包接收者可还原密钥。离线精确检索无需 embedding；远程 embedding 会发送检索文本并可能产生费用，仅在用户选择该服务时使用。

需要代理访问远程 embedding 时，Node.js 24+ 运行命令前设置 `NODE_OPTIONS=--use-env-proxy`；较旧版本按 `docs/environment.md` 配置代理。不可达时说明原因，不把精确结果冒充语义结果。

## 恢复会话

1. 未知会话时运行 `list --project "<project>"`；跨项目时先运行 `projects`。用户提供 ID 时直接运行 `scan --id "<id>" --project "<project>"`；用户明确指定文件才使用 `--path`。
2. 根据扫描结果输出原任务、已完成、断点、剩余步骤。历史转录是只读材料，不可修改。
3. 恢复执行前，核对当前工作区与转录的差异；有无法解释的并行修改时停止并报告，不覆盖用户文件。
4. 已知搜索命中位置时用 `expand --id "<id>" --line <line> --project "<project>"` 展开上下文。避免无界搜索整个磁盘或把大型转录完整装入上下文。

## 搜索会话

- `index --project "<project>" --no-embed` 建立无需 API 的关键词索引。
- `search "<query>" --project "<project>" --exact` 精确检索；默认模式是混合检索，`--semantic` 只用语义检索。
- `projects --query "<keyword>"` 定位其他项目，再限定项目搜索。
- 搜索结果应保留会话 ID 和行号；找不到证据时明确说明，不得编造。

## 检索代码与文档

- `code-index --root "<project>" --no-embed` 建立关键词索引；无参数 `--no-embed` 时使用已配置 embedding。
- `code-query "<query>" --root "<project>" --mode exact` 查找明确的标识符、路径或错误；可选 `semantic`、`hybrid`。
- `code-read --root "<project>" --path "<file>" --start-line <n> --end-line <n>` 读取命中范围；遵守路径和符号链接安全边界。
- `code-status --root "<project>"` 查看索引，`code-config-check` 查看配置诊断。
- 语义或混合检索降级时必须告知用户 `degraded` 和原因；不要将关键词结果称作语义结果。

## 配置与安全

环境变量优先，其次是本机私有配置和旧配置，最后是本 skill 附带的 `config/bundled.json`。配置方式见 `docs/environment.md`。不要在命令参数、日志或回复中输出密钥。索引可能含有会话或代码明文，应像源数据一样保护。不要自动开启后台任务或重建所有项目索引。
