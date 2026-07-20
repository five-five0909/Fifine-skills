# 03 实施计划

> 现查结论（本机实测，2026-07-15，非臆测）：

```
claude mcp add [--scope user] <name> [-e KEY=VAL] -- <command> [args...]
codex  mcp add <name> [--env KEY=VALUE] -- <command> [args...]      # 写入 ~/.codex/config.toml [mcp_servers.<name>]
```

- Codex Skill 目录约定：`~/.codex/skills/<name>` 是指向 `~/.agents/skills/<name>` 的 symlink（本机其余 18 个 skill 均如此），**印证 Goal.md 提出的 `~/.agents/skills/trans` 共享目录设计是对的**，直接采用。
- Codex `hooks.json` schema 与 Claude 完全一致（`hooks.UserPromptSubmit[].hooks[].{type,command}`），但装载方式不同：Claude 插件机制随 Skill 自动加载；Codex 是**按项目**的 `.codex/hooks.json` + `config.toml` 里的信任哈希，不会随 Skill 目录自动生效。**结论**：`hooks/hooks.json` 文件格式不用改，但 Codex 侧不会自动获得 `SessionEnd` 后台索引能力，这是文档化的已知限制（Goal.md 第 7 节已预判正确）。
- 额外发现：Codex 有自己的会话记录 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`，事件 schema（`session_meta` 等）与 Claude 的 `~/.claude/projects/*.jsonl`（`type: user/assistant/summary`）不同。**决定：本轮不实现 Codex 转录解析**（新增一套 parser 是明显的范围膨胀，原始诉求是"MCP/Skill 跨客户端"，不是"读 Codex 自己的会话记录"）；记入 `docs/migration.md`"已知限制/未来工作"。

## 执行顺序与文件级改动（对应 Goal.md 第 10 节，此处补充验证命令与回滚方式）

| # | 步骤 | 改动文件 | 验证命令 | 回滚 |
|---|---|---|---|---|
| 1 | 建共享层 | 新增 `lib/shared/{paths,config,locking,redact}.mjs` | `node --test tests/unit/shared.test.mjs` | 删除新文件，无其他依赖方 |
| 2 | `lib.mjs` 接入共享层（零行为变化） | `scripts/lib.mjs` 改为 import `lib/shared/*` | `node --test test/lib.test.mjs && node test/smoke.mjs` 对比迁移前后输出一致 | `git checkout scripts/lib.mjs` |
| 3 | 索引加锁+原子写 | `scripts/lib.mjs` 的 `buildIndexLines`/`indexPaths` | 新增并发建索引单测；`node test/smoke.mjs` | 同上 |
| 4 | MCP Server 迁移 | 新增 `mcp/server.mjs`（内容=现 `scripts/mcp-server.mjs` + 新代码检索工具），`scripts/mcp-server.mjs` 改为转发 shim，`.mcp.json` 更新 args | `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \| node mcp/server.mjs` | 恢复 `.mcp.json` 旧 args，删除新文件 |
| 5 | 代码检索核心 | 新增 `lib/code-search/*` | 新增单测 + `node scripts/semantic.mjs code-query "x" --root . --mode exact` | 删除新文件，MCP 工具注册回退 |
| 6 | Mistral 接入验证 | `config/config.example.json` | 用环境变量注入真实 key 跑一次 `embedBatch` 探测（不写入仓库） | N/A（只读探测） |
| 7 | Skill 扩展 | `SKILL.md` 追加章节，新增 `agents/openai.yaml` | 人工读审 + Claude Code 内 `/trans` 触发测试 | `git checkout SKILL.md`，删除新文件 |
| 8 | 安装器 | `install.ps1`/`.sh` 重写，新增 `uninstall.*`/`doctor.mjs`/`migrate-config.mjs` | 见 Goal.md 15.3 节安装器测试清单 | 保留旧版 `install.ps1`/`.sh` 的 git 历史，可 revert |
| 9 | 测试收尾 | `tests/` 新增单元/集成 | `npm test` | N/A |
| 10 | 文档 | README / docs/* | 人工核对命令可执行 | N/A |

## 本轮实际执行范围声明

鉴于任务体量（多阶段、跨平台安装器、双 CLI 联调），本次会话按以下优先级**真实落地**（写代码+跑测试，非纸面）：
1. `lib/shared/*` 共享层（全部）
2. 主线 A 零风险搬迁（`lib.mjs` 接入共享层、加锁原子写、`mcp/server.mjs` 迁移+shim）
3. 主线 B 核心（`lib/code-search/*` + 5 个新 MCP 工具 + Mistral 验证）
4. `SKILL.md` 扩展 + `agents/openai.yaml`
5. `doctor.mjs`、Windows `install.ps1`/`uninstall.ps1`（当前是 Windows 环境，`.sh` 版本按同等逻辑镜像编写但受限于无 Linux 环境跑不了实测，会标注"静态审查，未实机验证"）
6. 单元测试补齐 + 现有测试回归
7. README/docs 更新

进度持续记录在 `progress.md`。
