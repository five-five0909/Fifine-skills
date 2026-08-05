# 04 测试计划与结果

## 已执行并通过（本轮会话内真实跑过，非纸面）

```
npm test    → node --test "test/*.test.mjs" "tests/unit/*.test.mjs" "tests/integration/*.test.mjs"
```
- `test/lib.test.mjs`（原有 11 条，零改动）：11 pass
- `tests/unit/shared.test.mjs`（新增，lib/shared）：9 pass
- `tests/unit/code-search.test.mjs`（新增，lib/code-search）：6 pass
- `tests/integration/mcp-server.test.mjs`（新增，MCP server 全链路）：3 pass
- **合计 29 pass / 0 fail**

```
npm run smoke   → node test/smoke.mjs
```
- 转录端到端沙箱测试：8 项断言全绿（造转录→建索引→检索命中→projects 发现→清空后不再命中）

## 手工验证（本轮会话内真实执行）

- `mcp/server.mjs` `tools/list` 返回全部 11 个工具（6 转录 + 5 代码检索）——JSON-RPC 手工调用验证。
- `trans_code_index`（noEmbed）→ 对本仓库自身建索引：207 文件 / 1977 块，忽略统计正确（3 忽略/7 二进制/0 超限/0 符号链接逃逸）。
- `trans_code_query`（exact）命中已知内容，`snippet`/`path`/`start_line`/`end_line` 字段正确。
- `trans_code_read` 正常读取 + 路径穿越（`..\..\..\Windows\...`）正确拒绝并返回 `isError:true`。
- `trans_code_status` / `trans_code_config_check` 输出结构正确，`apiKey` 全程脱敏（只显示 `(未设置)` 或末 4 位）。
- **Mistral `/v1/embeddings` 真实连通性**：用用户提供的 key（通过环境变量注入，未写入任何文件）经代理直连验证，响应体 `{data:[{index,embedding}]}`，1024 维，与 `embedBatch()` 现有解析逻辑完全兼容，无需适配层。（Node 内置 `fetch` 在本机代理环境下未自动走 `HTTP_PROXY`——环境特性，记入 FAQ，非代码缺陷。）
- `node scripts/doctor.mjs` 在真实开发机上跑通，正确识别：Node 版本、Claude/Codex CLI 存在、Claude MCP 已注册（本仓库 `.mcp.json`）、Codex MCP 未注册（预期，未跑安装器）、Skill 链接未安装（预期，未跑安装器）、无锁文件残留。
- `New-SkillLink`（install.ps1 内部函数）在隔离临时目录验证 Junction 创建/幂等性：首次创建成功、重复调用检测到"已存在且指向正确"、Junction 创建**不需要管理员权限**（解决 Goal.md 遗留问题）。
- PowerShell 语法检查：`install.ps1`、`uninstall.ps1` 均通过 `[scriptblock]::Create()` 解析，无语法错误。

## Linux 实机验证（第二轮补做，真实执行，非镜像审查）

用 WSL2（Ubuntu 22.04）真实跑通 `install.sh`/`uninstall.sh`，完全隔离于任何真实环境——`$HOME` 指向一次性临时目录，`claude`/`codex` 换成记录调用参数的 stub 脚本挂在 `PATH` 最前面，绝不触碰 WSL 里那个真实在用的 `~/.claude`（有真实 sessions/projects/history.jsonl，跟 Windows 侧一样是活的环境，同样不能未经同意就动）。Node 用官方 v20.18.0 二进制（apt 默认的 v12 因为不支持 optional chaining 语法而跑不动本项目代码）。

结果：
- 首次安装：两个客户端的 symlink 正确创建，指向仓库真实路径；`--exact-only` 正确跳过 embedding 配置；`--skip-index` 正确跳过建索引；fake `claude`/`codex` 收到的调用参数完全正确（`mcp add --scope user trans -- node <path>/mcp/server.mjs` 与 `mcp add trans -- node <path>/mcp/server.mjs`）。
- 重复安装：幂等——第二次运行识别"已存在且指向正确"，不重复创建、不重复报错。
- `claude`/`codex` 两个 CLI 都不存在时：**不中断**，两个客户端的 Skill 链接仍正确创建，各自打印补装命令，退出码 0。
- `uninstall.sh`（默认 KeepData）：正确移除两个 symlink，保留配置/索引。
- `uninstall.sh --purge` 输入 `no`：正确列出将删除路径后取消，未删除任何文件（用真实的 embed-config.json 验证过"取消不删"这条路径；"确认删除"的真实执行路径因涉及删除仓库自身文件、风险与收益不对等，改为纯代码审查确认逻辑正确，未做真实执行）。
- 测试产生的 `embed-config.json`/`index/` 已从仓库清理干净，`git status`/`npm test` 复核无残留、29 测试全绿。

## 并发建索引压力测试（第三轮补做，真实执行）

`tests/integration/concurrent-index.test.mjs`：两个真实独立子进程（非同一进程内的并发 Promise，是货真价实的 `spawn` 出的两个 Node 进程）同时对同一 `root_path` 调 `buildCodeIndex(noEmbed:true)`。验证点：
- 至少一个成功建索引；若另一个抢锁失败，返回体清晰标注"索引正被 pid@host 占用"。
- 索引文件（`state.json`/`meta.jsonl`）在并发场景下始终保持完整可解析——不存在半写入的损坏 JSON。
- 重复跑 5 次，结果稳定一致（非偶然通过）。

`npm test` 现为 **30/30 通过**。

## 仍未执行（如实记录，均涉及影响用户真实全局环境，未经明确同意不主动做——这是本项目唯一剩余的非纯技术阻塞项）

- **未在用户真实的 `~/.claude/skills/`（Windows 侧）/ 真实 WSL `~/.claude/skills/` 上跑安装器**：会创建真实 Skill 链接并向用户的全局 Claude/Codex MCP 注册表写入 `trans` 条目。已在对话中明确询问，等待用户回复。
- **Codex 侧的 Skill 自动发现 / hook 触发**未在真实 Codex CLI 交互会话里验证（依赖先完成真实安装）。

## 兼容性矩阵（依据以上真实结果回填，见 Goal.md 第 18 节）

| 功能 | Claude Code | Codex CLI | 依据 |
|---|---|---|---|
| STDIO MCP tools/list | 实测通过 | 语法/命令验证通过，未实机连接 | mcp/server.mjs 手工 JSON-RPC 测试 |
| Exact/Hybrid/Semantic 代码检索 | 实测通过 | 同一 MCP 进程，逻辑无客户端分支 | mcp-server 集成测试 + 手工验证 |
| Windows Junction Skill 链接 | 沙箱验证通过 | 沙箱验证通过（同一函数） | install.ps1 New-SkillLink 隔离测试 |
| Claude MCP 注册命令 | `claude mcp add --scope user trans -- node mcp/server.mjs`（已现查、已用于本仓库 `.mcp.json`） | — | 本机 `claude mcp --help` + `claude mcp list` |
| Codex MCP 注册命令 | — | `codex mcp add trans -- node mcp/server.mjs`（已现查语法，未实际注册） | 本机 `codex mcp --help` |
| Hook 自动加载 | 是（插件机制） | 否（Codex hook 按项目挂载，非随 Skill） | 本机 `.codex/hooks.json` 实例对比 |
