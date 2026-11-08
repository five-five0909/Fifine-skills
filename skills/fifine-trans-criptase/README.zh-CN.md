# fifine-trans-criptase

通过 skill 续接 Claude Code / Codex CLI 会话，并检索历史对话、本地代码和文档。无需 MCP 服务或注册；宿主需支持执行本地命令，Node.js 版本需为 18 或以上。

## 使用

将此 skill 安装到宿主的 skills 目录后，直接要求 agent「恢复上次会话」或「检索这个项目的代码」。agent 按 `SKILL.md` 调用本地命令。技能目录不必叫 `trans`。

手动使用时，将下例中的 `<skill-dir>` 和 `<project>` 替换为实际路径：

```sh
node "<skill-dir>/scripts/semantic.mjs" list --project "<project>"
node "<skill-dir>/scripts/semantic.mjs" scan --id "<session-id>" --project "<project>"
node "<skill-dir>/scripts/semantic.mjs" index --project "<project>" --no-embed
node "<skill-dir>/scripts/semantic.mjs" search "关键词" --project "<project>" --exact
node "<skill-dir>/scripts/semantic.mjs" code-index --root "<project>" --no-embed
node "<skill-dir>/scripts/semantic.mjs" code-query "关键词" --root "<project>" --mode exact
```

具体选项运行 `node "<skill-dir>/scripts/semantic.mjs"` 查看。历史会话是只读的；恢复工作前必须核对当前磁盘状态。

## 配置与隐私

关键词检索不需要 API key。语义检索需要已配置的远程 embedding 服务或本地模型；远程服务会接收待嵌入的会话或代码文本，可能产生费用。配置和私有环境文件优先级见 [环境配置](docs/environment.md)，本地模型见 [本地模型](docs/local-model.md)。不要将密钥写入仓库、命令行参数或对话。索引可能包含会话和源代码明文。

旧版配置文件仍可读取；旧 MCP 注册不会被此包自动删除。若客户端仍配置了指向已删除服务的旧注册，需要在对应客户端中移除该注册。
