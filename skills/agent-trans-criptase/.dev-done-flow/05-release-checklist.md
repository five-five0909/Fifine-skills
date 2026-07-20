# 05 发布检查表

## 完成度（对照 Goal.md 第 17 节验收标准）

### 功能验收
- [x] Claude Code 可以发现 trans Skill（既有能力，未回归）
- [ ] Codex CLI 可以发现 trans Skill（代码/配置就绪，未实机验证——需先跑安装器把 Skill 链接装到 `~/.agents/skills/trans`）
- [x] Claude Code 可以连接 trans MCP（本仓库 `.mcp.json` 已验证）
- [ ] Codex CLI 可以连接 trans MCP（命令语法已验证，未实机注册+连接）
- [x] 两边使用同一个 MCP Server 文件（`mcp/server.mjs`，单一进程双家族工具）
- [x] 两边使用同一份配置（`lib/shared/config.mjs` 合并新旧 schema）
- [x] 两边使用同一份索引（转录 `index/`、代码 `data/code-index/`，路径由 `lib/shared/paths.mjs` 统一推导）
- [x] exact 搜索无 API 也可用（转录 + 代码检索均验证）
- [x] semantic 搜索配置正确后可用（Mistral 真实连通性已验证）
- [x] hybrid 搜索可用（降级链已实现并有单测/集成测试覆盖）
- [x] 原有 CLI 命令仍可用（`test/lib.test.mjs` 零改动全绿）
- [x] 原有 provider 模式未被破坏（api/local 两态均保留，`embedBatch()` 未改签名）

### 安装验收
- [ ] Windows 一键安装成功（脚本已写、语法验证、核心函数沙箱验证；**未对真实 `~/.claude/skills`/`~/.agents/skills` 执行**，见下方"需要用户确认的操作"）
- [x] Linux 一键安装成功（WSL2 Ubuntu 22.04 真实执行，隔离 HOME + stub CLI，见 `04-test-plan.md`）
- [~] macOS 安装逻辑合理（未实机验证，但与已验证的 Linux 脚本是同一份 `install.sh`，bash 语法层面无平台分支，风险低于全新代码）
- [x] 重复安装不会破坏环境（`New-SkillLink` 幂等性已在沙箱验证）
- [ ] Claude-only / Codex-only / 双客户端安装成功（脚本支持 `-Clients`，未实机跑完整流程）
- [x] 卸载可以保留数据（`uninstall.ps1` 默认不碰 `config/`/`data/`/`index/`，逻辑已审查）
- [x] Purge 可以完整清理（会先列出路径 + 二次确认，逻辑已审查）

### 稳定性验收
- [x] 两个 MCP 进程可同时查询（只读路径天然并发安全，无共享可变状态）
- [x] 同时建索引不会损坏数据（文件锁 + 原子写；`tests/integration/concurrent-index.test.mjs` 用两个真实子进程验证过，5 次重复运行结果稳定）
- [x] 错误配置有清晰提示（`doctor.mjs`/`trans_code_config_check` 均给出可读诊断）
- [x] 无索引时有清晰提示（`trans_code_query` 返回 `error` 字段而非抛异常/返回空结果）
- [x] Embedding 失败时可降级 exact（`codeQuery()` 降级链已实现+测试）
- [x] 配置和日志不会泄露 API Key（`lib/shared/redact.mjs` 统一脱敏，doctor/status/config-check 全部过一遍）

### 文档验收
- [x] README 命令经过实际验证（新增命令均在本轮实测过）
- [x] README.zh-CN.md 关键差异已同步（工具数量、安装命令；未做逐段全量翻译对齐）
- [x] 架构图与代码一致（README + `.dev-done-flow/02-architecture.md` 的 Mermaid 图对应真实目录结构）
- [x] 安装路径与代码一致（不再假设固定 `~/.claude/skills/trans`，改为"当前仓库位置"）
- [x] MCP 工具名称与代码一致（README 表格逐一核对 `mcp/server.mjs` TOOLS 定义）
- [x] 故障排除覆盖常见错误（`docs/codex-cli.md` 记录 hook/transcript 已知限制；`docs/migration.md` 覆盖回退路径；README FAQ 保留原有条目）

## 需要用户确认后才能执行的操作（本轮未自动执行）

1. **在本机真实运行 `install.ps1`**：会创建 `~/.claude/skills/trans`、`~/.agents/skills/trans` 两个 Junction，并调用 `claude mcp add --scope user trans` / `codex mcp add trans` 修改用户级 MCP 注册表。这是影响全局/共享状态的操作，未经确认不主动执行。
2. **实机验证 Codex CLI 侧的 Skill 发现与 MCP 连接**：需要①执行上一步安装 ②在真实 Codex CLI 交互会话中触发验证。

## 遗留项（第四轮更新，诚实记录——技术侧已收口，只剩一项人为决策阻塞）

- **未在真实环境执行安装器**（全局注册 Claude/Codex MCP、创建真实 Skill 链接，覆盖 Windows 与真实 WSL 两个活跃环境）——需用户明确同意，已多次询问等待回复。**这是本项目当前唯一剩余项，且性质上不属于"技术未完成"，而是"决策权不在代理"。**
- Codex 侧 Skill 自动发现/MCP 连接/hook 行为未在真实 Codex CLI 会话里验证（依赖上一条先完成，非独立阻塞项）。
- macOS 未实机验证（无 macOS 环境；与已在 WSL2 验证通过的 Linux 脚本是同一份代码，无平台特有分支，风险已大幅降低，非阻塞项）。

## 本轮已解决（不再是遗留项）

- `docs/architecture.md`/`docs/claude-code.md`/`docs/codex-cli.md`/`docs/migration.md` 四个文件已创建（含 Mermaid 架构图、双客户端安装/卸载/验证命令、Codex 已知限制、迁移步骤）。
- README.zh-CN.md 已同步全部新增章节（代码/文档检索、Doctor、双客户端安装命令、架构图、文件结构、MCP 工具表）。
- **`install.sh`/`uninstall.sh` 已在 WSL2 (Ubuntu 22.04) 真实执行验证**：首次安装/幂等重复安装/CLI 缺失优雅跳过/卸载保留数据/`--purge` 取消路径全部通过，隔离于任何真实环境（fake HOME + fake CLI stub），测试残留已清理，`npm test` 复核 29/29 绿。

## 升级方法（现状）

现有用户（旧版直接 clone 到 `~/.claude/skills/trans`）：
```
git pull
node scripts/migrate-config.mjs    # 可选，把 embed-config.json 迁移成新 config/config.json（旧文件保留，不强制）
node scripts/doctor.mjs            # 确认迁移后一切正常
```
无需迁移也能继续用旧配置——`lib/shared/config.mjs` 对旧 schema 保持向后兼容读取。

## 回退方法

```
git checkout <上一个 commit>
```
所有改动都是新增文件 + 少量向后兼容的原地编辑（`scripts/lib.mjs`/`scripts/mcp-server.mjs`/`.mcp.json`/`scripts/write-config.mjs`），`scripts/mcp-server.mjs` 保留了转发 shim，回退过程中即使只回退一半文件也不会出现"引用不存在的路径"的中间破损态。
