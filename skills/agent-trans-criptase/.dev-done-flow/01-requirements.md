# 01 需求文档

> 权威来源是仓库根目录 `Goal.md`（第 0-4、10-19 节）。本文件只做"需求→验收标准"的精炼映射，不重复展开架构细节，架构图见 `02-architecture.md`。

## 功能需求

**FR1 保留转录续接子系统行为不变**
`trans_search`/`trans_scan`/`trans_list`/`trans_projects`/`trans_expand`/`trans_index` 6 个 MCP 工具与 `scripts/semantic.mjs` 的 `index`/`query`/`status`/`projects` 子命令，迁移文件位置后行为 100% 一致（`test/lib.test.mjs` + `test/smoke.mjs` 迁移前后全绿）。

**FR2 新增代码/文档检索子系统**
新增 `trans_code_query`/`trans_code_index`/`trans_code_status`/`trans_code_read`/`trans_code_config_check` 5 个 MCP 工具，支持 exact/semantic/hybrid 三种模式，对任意 `root_path` 建索引与检索，无 embedding 配置时 exact 仍可用。规格见 Goal.md 第 12.2 节。

**FR3 双客户端支持**
Claude Code 与 Codex CLI 均可发现 Skill、连接同一 MCP Server、读写同一份配置与索引。

**FR4 统一安装/卸载/诊断**
`install.ps1`/`.sh` 支持 `-Clients claude,codex`，某客户端 CLI 缺失时跳过而非中断；`uninstall.ps1`/`.sh` 支持 `-KeepData`/`-Purge`；`doctor.mjs` 一键诊断全链路。

**FR5 旧版迁移路径**
已直接 clone 到 `~/.claude/skills/trans` 的用户可通过 `migrate-config.mjs` 无损迁移到共享安装目录，MCP 注册自动更新，不产生半成品状态。

## 非功能需求

- **NFR1 向后兼容**：不改变现有 6 个转录 MCP 工具的 `inputSchema`/输出格式；CLI 旧参数（`--exact` 等）继续可用。
- **NFR2 安全边界**：代码检索子系统的 `root_path`/`path` 参数必须校验落在 `allowedRoots` 内，防路径穿越与符号链接逃逸；API Key 不落日志、不落仓库明文。
- **NFR3 并发安全**：两个客户端的 MCP 进程可同时查询；同时建索引不得损坏数据（文件锁 + 原子写）。
- **NFR4 优雅降级**：semantic 不可用时自动降级 hybrid→exact，返回体注明降级原因；某客户端 CLI 未安装时不阻断另一客户端的安装。
- **NFR5 不臆测官方接口**：Codex CLI 的 MCP 注册命令、hook 机制等价性，必须现查而非凭旧知识假设（见 Goal.md 第 7 节）。

## 验收标准

见 Goal.md 第 17 节（逐条勾选），兼容性矩阵模板见第 18 节（基于真实测试结果回填，不臆填）。

## 范围边界

**In scope**：见 Goal.md 第 10 节任务清单全部条目。
**Out of scope**（明确延后，见 Goal.md 第 8 节）：SQLite 索引重写、废弃 `.claude-plugin/` 插件市场通道、`trans_reindex`/`trans_clear_cache`/`trans_list_roots` 等可选工具。
