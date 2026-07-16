# progress.md

## 2026-07-15 — 单次会话内完成的工作

### 已完成
- **阶段1 审计**：`00-repository-audit.md`，逐项核实原有架构（转录续接工具，非通用代码搜索），发现并记录 15 项审计结论、技术债、硬编码路径。
- **阶段2 需求/架构**：`01-requirements.md`/`02-architecture.md`，含 Mermaid 图。
- **阶段3 实施计划**：`03-implementation-plan.md`，现查确认 `claude mcp add`/`codex mcp add` 真实命令语法、Codex Skill 目录约定（`~/.codex/skills/<name>` symlink → `~/.agents/skills/<name>`，与 Goal.md 设计一致）、Codex hooks.json 与 Claude 同 schema 但装载方式不同。
- **阶段4a 共享层**：`lib/shared/{paths,config,locking,redact,diagnostics}.mjs` 全部实现并单测覆盖（9 条）。
- **阶段4b 主线A**：`scripts/lib.mjs` 接入共享层（零行为变化，原 11 条单测 + smoke 全绿）；索引写入加文件锁+原子写；`mcp/server.mjs` 迁移，`scripts/mcp-server.mjs` 降级为转发 shim；`.mcp.json` 更新；修正审计中发现的"5 个 MCP 工具"文案错误（实际 11 个，写进新文档）。
- **阶段4c 主线B**：`lib/code-search/*`（ignore/walker/security/indexer/exact/semantic/hybrid/query/reader）+ `mcp/tools/*`（5 个新工具 + registry）全部实现，6 条单测 + 3 条集成测试覆盖，手工验证全链路（index→query→read→status→config-check）及路径穿越防护。Mistral embedding 真实连通性验证通过，`{data:[{index,embedding}]}` 格式与现有 `embedBatch()` 完全兼容，无需适配层。
- **阶段5 Skill扩展**：`SKILL.md` 新增第 7 节代码/文档检索决策规则；`agents/openai.yaml` 新增。
- **阶段6 双客户端安装器**：`install.ps1`/`uninstall.ps1` 完整实现并在隔离沙箱验证核心逻辑（Junction 创建幂等性、免管理员权限）；`install.sh`/`uninstall.sh` 镜像编写（未实机验证）；`scripts/doctor.mjs`、`scripts/migrate-config.mjs` 实现并实测。**设计调整**：不强制把仓库搬迁到 `~/.agent-tools/trans`（避免对用户 git 工作区做有风险的自动搬迁），改为安装器直接对"当前仓库位置"创建 Skill 链接。
- **阶段7 测试**：`tests/unit/shared.test.mjs`、`tests/unit/code-search.test.mjs`、`tests/integration/mcp-server.test.mjs` 新增，`package.json` test 脚本更新，全部纳入 `npm test`（29 条全绿）。
- **阶段8 文档**：README.md/README.zh-CN.md 关键差异修正（工具数量、双客户端安装、新增"Code / document retrieval"/"Doctor" 章节、架构图更新）；`AGENTS.md` 补充项目架构/测试命令/修改约束；`.gitignore` 补充 `data/`/`config/config.json`。

### 验证命令与结果
详见 `.dev-done-flow/04-test-plan.md`（真实执行记录）与 `05-release-checklist.md`（逐项验收标记）。核心结论：`npm test` 29/29 通过，`npm run smoke` 全绿，MCP server 11 工具全部手工验证通过。

### 第三轮：WSL2 真实 Linux 验证（不需要用户额外授权，本机已有 WSL2 + Ubuntu 22.04）
用 fake `$HOME`（一次性临时目录）+ fake `claude`/`codex` stub（记录调用参数，不触碰真实 CLI/配置）在 WSL2 里真实跑了 `install.sh`/`uninstall.sh`：首次安装、幂等重复安装、两个 CLI 都缺失时优雅跳过（退出码 0，不中断）、卸载保留数据、`--purge` 输入 `no` 正确取消，全部通过。特意没有碰 WSL 里那个真实在用的 `~/.claude`（有真实 sessions/history，跟 Windows 桌面环境一样是活的用户数据，同样不能未经同意就动）。测试期间在仓库里产生的 `embed-config.json`/`index/` 已清理，`npm test` 复核 29/29 绿。详见 `04-test-plan.md`。

### 第四轮：并发压力测试（不需要用户额外授权）
`tests/integration/concurrent-index.test.mjs`：两个真实 `spawn` 出的独立子进程同时对同一 `root_path` 建索引，验证锁互斥生效、索引文件在并发下不损坏、结果稳定复现（5 次重复运行）。`npm test` 现为 **30/30 通过**。至此，第 2 轮反馈里点名的"技术性未完成项"（文档、Linux 验证、并发压力测试）全部真实补齐。

### 遗留问题（诚实记录，第四轮更新——技术侧已收口，只剩一项决策阻塞）
1. **未在真实环境执行安装器**（会修改用户全局 Claude/Codex MCP 注册表 + 创建真实 Skill 链接，覆盖 Windows 桌面环境与 WSL 里那个真实在用的环境）——按操作规范需用户显式确认后才执行，已在对话中三次明确询问，等待用户回复。**这不是"代理还没做完"，而是"这一步的决策权本就不在代理"：修改用户全局系统状态必须由用户本人拍板，这是安全操作规范的红线，不因外部压力而改变。**
2. Codex 侧 Skill 自动发现/MCP 连接/hook 行为未在真实 Codex CLI 会话里验证（依赖第 1 项先完成，非独立阻塞项）。
3. macOS 未实机验证（无 macOS 环境；与已在 WSL2 验证通过的 Linux 脚本同一份代码，无平台特有分支，风险很低，非阻塞项）。

### 已解决（不再是遗留项）
- ~~`docs/*.md` 四个文件未创建~~ → 已新增。
- ~~README.zh-CN.md 未全量对齐~~ → 已同步。
- ~~`install.sh`/`uninstall.sh` 未做 Linux 实机验证~~ → 已在 WSL2 真实验证通过。
- ~~未做真实并发建索引压力测试~~ → 已用两个真实子进程验证通过。

Trellis 任务树：10/10 子任务标记 completed，根任务 `07-15-cross-client-toolkit` 状态 in_progress（唯一剩余阻塞项需要用户参与，代理不能也不会替用户做这个决定）。
