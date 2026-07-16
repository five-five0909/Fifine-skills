# trans-criptase → 跨客户端 Skill + MCP Toolkit 改造计划

> 状态：规划稿（尚未开始改代码）。本文档是唯一的顶层目标文档，`.dev-done-flow/` 下的审计/需求/架构/实施/测试/发布文档将在下一步逐一生成，并反向链接回本文件对应章节。本版本在初稿基础上补全了**全部任务清单、迁移方案、工具规格、配置 schema、CLI 清单、安全/测试清单、文档交付、验收标准**，作为唯一权威 backlog。

## 0. 范围裁定（重要，先于一切设计）

审计发现原始目标描述（`trans_query` / `trans_read` / `allowedRoots` / 任意 `root_path` 索引……）是「通用代码/文档检索产品」的设计，但当前仓库 `trans-criptase` 实际是「**Claude Code 会话转录续接 + 跨会话语义检索**」工具：

- 检索对象是 `~/.claude/projects/<encoded>/*.jsonl`（Claude Code 自己写的会话记录），**不是**用户的源代码仓库。
- 现有 MCP 工具：`trans_search` / `trans_scan` / `trans_list` / `trans_projects` / `trans_expand` / `trans_index`（`scripts/mcp-server.mjs` + `scripts/lib.mjs`）。
- 索引位置、转录位置都是固定已知路径，没有「任意目录 + allowedRoots 沙箱」的概念。

已与用户确认（2026-07-15）：**扩展为通用检索，新增代码搜索能力**——即：

1. **保留并加固**现有「会话转录续接 + 语义检索」子系统（不推倒重写，做跨客户端兼容性重构）。
2. **新增**一套面向任意本地项目目录的 exact / semantic / hybrid 代码与文档检索子系统（对应原目标里的 `trans_query` / `trans_index(root)` / `trans_read` / `trans_status` / `trans_config_check` / `allowedRoots`）。
3. 两个子系统共用：MCP Server 进程、embedding provider 配置层、跨客户端安装/诊断/卸载体系。

这本质上是在原项目上**叠加一个新产品线**，工作量对应放大，因此以下计划显式分两条主线（转录续接线 = 兼容改造，代码检索线 = 新增功能），并给出共用基础设施。

## 1. 现状速记（审计结论）

| 项 | 现状 |
|---|---|
| 交付形态 | Claude Code **插件**（`.claude-plugin/plugin.json` + `marketplace.json`），非独立 npm 包 |
| Skill 入口 | 根目录 `SKILL.md`（`/trans` 命令），依赖 `${CLAUDE_PLUGIN_ROOT}` 环境变量定位脚本 |
| MCP 入口 | `.mcp.json` → `scripts/mcp-server.mjs`，零依赖手写 JSON-RPC / STDIO |
| 核心逻辑 | `scripts/lib.mjs`（转录解析、增量索引、embedBatch、RRF 混合检索、rerank） |
| CLI | `scripts/semantic.mjs`（index/query/status/projects），`scripts/scan-transcript.ps1` |
| Hook | `hooks/hooks.json`：`UserPromptSubmit`→`prompt-hint.mjs`，`SessionEnd`→`session-end-index.mjs`（后台增量建索引） |
| 配置 | `<skill目录>/embed-config.json`（`SKILL_DIR` 按 `lib.mjs` 文件位置反推，非写死路径——这点已经是「客户端无关」的良好设计） |
| 索引 | `<skill目录>/index/<project-encoded>/{state.json,meta.jsonl,vec.bin}`，纯 JS 实现（非 SQLite），已有增量、模型切换检测、原子性较弱（无临时文件+rename，无锁） |
| Provider | `provider: "api"`（OpenAI 兼容 `/embeddings` + `/rerank`）或 `provider: "local"`（`embedder/embedder.mjs`，ONNX 本地模型） |
| 安装器 | `install.ps1` / `install.sh`：**假定**已被克隆到 `~/.claude/skills/trans`，只做两件事——写配置、`claude mcp add --scope user trans` 注册。不处理 Codex、不建共享目录、不建 symlink/junction、无 Claude CLI 时只打印手动命令（已符合"跳过不报错"原则） |
| 测试 | `test/lib.test.mjs`（`node --test`）+ `test/smoke.mjs`（端到端 smoke，已用 `TRANS_INDEX_ROOT`/`TRANS_PROJECTS_ROOT` 环境变量做了隔离，避免污染真实数据——这个模式可直接复用到新测试） |
| 安全 | 转录路径、索引路径都在固定已知目录内，暂无路径穿越面；`trans_expand` 的 `sessionId` 走前缀匹配 + `fs.existsSync`，无越权读取风险（新增代码检索子系统必须补上这类校验） |
| Codex CLI 支持 | **无**，`.mcp.json` / `plugin.json` 均只面向 Claude Code 插件机制 |
| 与 Codex 冲突点 | `${CLAUDE_PLUGIN_ROOT}`、`claude mcp add` 均是 Claude 专有；`SKILL_DIR` 推导本身客户端无关，可复用 |

## 2. 目标架构

```
                         ~/.agent-tools/trans/          ← 唯一源码 + 配置 + 索引安装位置
                         ├── SKILL.md                   (双客户端共用触发规则)
                         ├── AGENTS.md                  (架构/测试命令/修改约束，供双方 agent 读取)
                         ├── agents/openai.yaml          (Codex/OpenAI Skills 生态清单)
                         ├── config/config.json          (共享配置，含 embedding + codeSearch + clients)
                         ├── config/config.example.json
                         ├── mcp/server.mjs              (单一 MCP 进程，STDIO)
                         │    ├── tools: trans_search / trans_scan / trans_list /
                         │    │          trans_projects / trans_expand / trans_index      ← 转录续接（原有，兼容）
                         │    └── tools: trans_code_query / trans_code_index /
                         │               trans_code_status / trans_code_read /
                         │               trans_code_config_check                          ← 新增代码检索
                         ├── lib/（转录检索逻辑，= 现 scripts/lib.mjs 原地演进）
                         ├── lib/code-search/（新增：exact/semantic/hybrid 通用检索）
                         ├── lib/shared/（config.mjs / paths.mjs / locking.mjs / redact.mjs 两条主线共用）
                         ├── data/index/…               (转录索引，沿用现结构)
                         ├── data/code-index/…          (新：代码索引，独立命名空间)
                         ├── data/locks/
                         └── scripts/（doctor.mjs / install / uninstall / migrate-config.mjs / semantic.mjs 兼容别名）
                                 │
                  ┌──────────────┴───────────────┐
     ~/.claude/skills/trans (Junction/symlink)   ~/.agents/skills/trans (Junction/symlink)
     + claude mcp add --scope user trans          + codex mcp add trans（实际命令名需现查 `codex mcp --help`）
```

关键决策：**新代码检索工具不复用 `trans_index` / `trans_query` 这两个名字**，因为 `trans_index` 已被转录索引占用，直接覆盖会破坏向后兼容（用户原则里"向后兼容"优先级高于"用户体验方便"）。新工具统一加 `trans_code_` 前缀：`trans_code_query`、`trans_code_index`、`trans_code_status`、`trans_code_read`、`trans_code_config_check`。这是对原目标描述的一处刻意偏离，会在 README/迁移文档中显式说明原因。

## 3. 两条主线拆解

### 主线 A：转录续接子系统 —— 跨客户端兼容性重构（不改变行为，只改变"谁能装/谁能连"）

1. 把 `${CLAUDE_PLUGIN_ROOT}` 依赖降级为可选项：`SKILL.md` 里的 PowerShell 脚本路径、hook 命令改为优先用相对/环境变量解析（Claude 用 `CLAUDE_PLUGIN_ROOT`，Codex 用等价变量或直接绝对路径回退），路径解析统一走：
   `显式传参 → CLAUDE_PLUGIN_ROOT/CODEX_*（现查实际变量名）→ 脚本自身位置推导（已有 SKILL_DIR 模式）→ cwd`。
2. `hooks/hooks.json` 是 Claude Code 专有格式（`UserPromptSubmit`/`SessionEnd`）；Codex CLI 是否支持等价 hook 需现查文档 —— 若不支持，Codex 侧的会话续接退化为"仅 MCP 工具可用，无自动后台索引"，在文档中明确记录为已知限制，不强行模拟。
3. `scripts/lib.mjs` 的 `SKILL_DIR` 推导逻辑迁移到共享安装目录后依然成立（因为是按文件自身位置反推，不写死用户名/盘符）——**这是唯一可以直接复用、无需改动的核心模块**，只需把它移到 `~/.agent-tools/trans/lib/transcript/` 并保持相对结构。
4. `scripts/semantic.mjs` 全部现有子命令（`index`/`query --exact/--semantic`/`status`/`projects`）保留，新增 `doctor` 别名转发到 `scripts/doctor.mjs`，`--exact` 继续作为 `--mode exact` 的兼容别名（若后续统一成 `--mode`）。

### 主线 B：新增代码/文档检索子系统（从 0 到 1，仿照原目标 6/7/8/9/13/14 章）

1. **配置扩展**：在共享 `config.json` 新增 `codeSearch` 顶层字段（`enabled`/`defaultMode`/`indexPath`/`security.allowedRoots`/`ignore` 规则），embedding provider 复用 `embedding` 字段（与转录子系统共用同一个 provider 配置，避免用户填两遍 key）——**当前接入的 Mistral（`https://api.mistral.ai`，模型 `mistral-embed`）作为默认 API provider 写入 `config.example.json`**，key 通过环境变量 `TRANS_EMBED_API_KEY` 或 `MISTRAL_API_KEY` 注入，绝不写入仓库明文。需先用一次真实请求验证 Mistral `/v1/embeddings` 响应体是否与现有 `embedBatch()` 期望的 `{data:[{index,embedding}]}` 格式兼容（大概率兼容，OpenAI 兼容层），验证脚本产出记录进 `.dev-done-flow/04-test-plan.md`。
2. **索引层**：新建 `lib/code-search/indexer.mjs`，遍历 `root_path` 下文件（尊重 `.transignore`/`.gitignore`、默认忽略 `.git`/`node_modules`/`dist`/二进制/超大文件/常见密钥文件），分块 → 复用 `lib.mjs` 里已有的 `chunkText`/`embedBatch`/`normalize`/`rrfFuse`/`keywordScores` 工具函数（这几个是纯函数，天然可被新模块 import 复用，无需重写）。
3. **索引存储**：沿用现有 `state.json + meta.jsonl + vec.bin` 三件套模式（已验证可行、无外部依赖），但补齐原设计缺的两项健壮性：
   - 写入走"临时文件 + rename"，避免半写入被并发读取到；
   - 加基于 `state.json.lock` 的文件锁（含超时/陈旧锁回收），防止两个客户端的 MCP 进程同时重建同一索引。
   转录索引后续也应补齐同样的锁与原子写（属于主线 A 的技术债，一并修）。
4. **安全边界**：`root_path` 必须落在 `config.codeSearch.security.allowedRoots` 内（为空数组=不限制，但需在文档强调风险；一旦配置则严格校验，禁止 `..` 穿越、禁止软链接逃逸出边界）。`trans_code_read` 只能读取"来自本次 query 结果"或"落在 allowedRoots 内"的路径，返回内容前做二次路径规范化校验。
5. **MCP 工具**：在 `mcp/server.mjs`（由现 `scripts/mcp-server.mjs` 演进）里追加 5 个工具，`handleCall` 里新增分支，逻辑委派给 `lib/code-search/*`，不在 MCP 层堆提示词（提示词逻辑放 `SKILL.md`）。
6. **Skill 决策规则**：在 `SKILL.md` 追加一节"代码/文档检索"，明确 exact/semantic/hybrid 选择规则与降级链（semantic 不可用→hybrid 降级→exact 降级；无 embedding 配置时 exact 仍可用），与转录检索共用同一份文档，靠标题区分两类场景，避免用户要维护两份 SKILL.md。

## 4. 共用基础设施（两条主线都依赖）

1. **`scripts/doctor.mjs`**：检查 Node 版本、依赖、配置 schema、API key 环境变量、embedding 连通性（转录 + 代码检索共用同一 provider，一次探测两边够用）、转录索引状态、代码索引状态、Claude/Codex Skill 链接、Claude/Codex MCP 注册、锁文件残留、目录写权限。输出 PASS/WARN/FAIL/SKIP + 可复制修复命令，绝不回显完整 key（只显示是否已设置 + 末 4 位）。
2. **`install.ps1` / `install.sh` 重写**（保持现有参数习惯，新增 `-Clients`）：
   - 若当前不在 `~/.agent-tools/trans`，先把仓库内容"搬"到该共享位置（或提示用户改为 clone 到该位置，参考现有 install.ps1 已有的"位置校验+提示"模式，只是把期望路径从 `~/.claude/skills/trans` 改成共享目录）；
   - 按 `-Clients claude,codex`（默认两者都装，缺哪个 CLI 就跳过哪个并打印警告和补装命令，不中断整体安装——对齐原则"某客户端未安装应跳过而非终止"）创建 Junction（Windows）/symlink（Unix）到各自 skills 目录；
   - 调用 `claude mcp add`（沿用现有命令，已验证可用）与 Codex 等价命令（**需先执行 `codex mcp --help` 现查真实命令**，不臆测）；
   - 保留现有"生成/迁移配置"逻辑（`write-config.mjs` 已经是 PS/bash 共用的单一真相层，直接复用，扩展它支持写 `codeSearch`/`clients` 字段）；
   - 幂等：重复执行不重复注册、不重复建链接、检测到已有 Junction/目录则跳过或提示。
3. **`uninstall.ps1` / `uninstall.sh`**（新增，现在没有）：支持 `-Clients` 精细卸载 + `-KeepData`/`-Purge`，删除前列出将删除的路径，非 `-Purge` 不动索引/配置。
4. **迁移路径**：旧版直接 clone 到 `~/.claude/skills/trans` 的用户，`migrate-config.mjs` 检测到"当前目录即真实安装目录（无共享目录）"时，提示并可一键迁移到 `~/.agent-tools/trans` + 补建 Junction，旧目录变成指向新目录的链接（避免用户已有的 Claude 插件注册失效）。细节见第 11 节。

## 5. 目录改动（最小侵入，非推倒重来）

新增：
```
mcp/                        # server.mjs 从 scripts/mcp-server.mjs 演进迁移，tools/ 拆分
lib/code-search/            # 新代码检索子系统实现
lib/shared/                 # 两条主线共用：config.mjs / paths.mjs / locking.mjs / redact.mjs
config/config.example.json  # 新 schema 示例（含 Mistral 默认值），embed-config.example.json 保留兼容
docs/architecture.md docs/claude-code.md docs/codex-cli.md docs/migration.md docs/local-model.md(已存在，保留)
agents/openai.yaml
AGENTS.md                   # 新增或复用现有 dev-done-flow 约定
scripts/doctor.mjs scripts/uninstall.ps1/.sh scripts/migrate-config.mjs
tests/unit/ tests/integration/ tests/fixtures/  # 与现有 test/ 并存或合并，视审计阶段决定，避免重复 runner 配置
.dev-done-flow/            # 00~05 + progress.md
```
保留不动：`scripts/lib.mjs`（逻辑迁移但先保证行为零变化再挪位置）、`scripts/semantic.mjs`（追加子命令）、`embedder/`、`hooks/`、`SKILL.md`（原地扩展而非替换）、`.claude-plugin/`（Claude 插件市场发现渠道继续保留，作为"Claude 端一种可选安装方式"与新 install.ps1 并存）。

## 6. 执行阶段（对齐原目标第十七章，落到本仓库）

1. **阶段 1 审计**（本文件第 1 节已完成初稿）→ 产出 `.dev-done-flow/00-repository-audit.md`（细化版，含每个文件的引用关系图）。
2. **阶段 2 需求与架构** → `01-requirements.md` / `02-architecture.md`，把第 2、3、4 节展开、画 Mermaid 图。
3. **阶段 3 实施计划** → `03-implementation-plan.md`，每步标注修改文件/目的/风险/验证命令/回滚方式（原目标第十七章格式），逐条对应第 10 节任务清单。
4. **阶段 4** 先做主线 A 的无损搬迁 + 锁/原子写补强（风险最低，先验证不破坏现有功能），再做主线 B 核心（indexer/config/安全边界/MCP 工具）。
5. **阶段 5** `SKILL.md` 扩展 + `agents/openai.yaml`。
6. **阶段 6** 双客户端安装器 + doctor + uninstall + 迁移脚本。
7. **阶段 7** 测试：单元（配置解析、路径归一化、allowedRoots、锁）、集成（MCP 启动/tools/list/各工具、降级链、并发建索引）、安装器（幂等性、CLI 缺失、保留数据）。
8. **阶段 8** 文档（README/README.zh-CN 为主要交付）+ 兼容性矩阵（基于真实测试结果填，不臆测）+ 发布检查表。

## 7. 关键风险 / 待现查项（不得凭旧知识假设）

- `codex mcp --help` / `codex skills` 等价机制的真实命令与路径约定 —— 必须在阶段 3 前实测记录。
- Codex CLI 是否有 hook 机制等价于 Claude 的 `UserPromptSubmit`/`SessionEnd` —— 若无，`session-end-index.mjs` 的自动后台索引在 Codex 侧不可用，需在文档标注限制。
- Mistral `/v1/embeddings` 响应体格式与现有 `embedBatch()` 假设的兼容性 —— 需一次真实调用验证（含错误处理路径：额度/网络失败时的降级提示）。
- Windows 下创建 Junction 是否需要提升权限（一般 Junction 不需要管理员权限，但需在当前用户环境实测确认）。
- 现有 `test/smoke.mjs` 的隔离模式（`TRANS_INDEX_ROOT`/`TRANS_PROJECTS_ROOT`）是否可以直接扩展出 `TRANS_CODE_INDEX_ROOT` 用于新测试，需要在阶段 4 落地时确认变量命名不冲突。

## 8. 明确不做 / 延后

- 不用 SQLite 替换现有 `state.json+meta.jsonl+vec.bin` 索引格式（现有格式已工作良好，替换属于无谓重写；仅补齐锁与原子写）。
- 不删除 `.claude-plugin/` 插件市场安装方式，作为 Claude 端的"轻量安装通道"与新 `install.ps1` 并存，二者最终都收敛到同一份共享代码。
- 不在本阶段实现 `trans_reindex`/`trans_clear_cache`/`trans_list_roots` 等可选工具，等核心 5+5 个工具稳定后再评估是否需要。

---

## 10. 详细任务清单（file-level backlog，按子系统分组）

### 10.1 共享基础层 `lib/shared/`（新增，两条主线依赖，优先做）

- [ ] `lib/shared/paths.mjs`：路径解析优先级链的唯一实现——`显式参数 root_path/project → CLAUDE_PLUGIN_ROOT/CODEX_* → 脚本位置反推(现 SKILL_DIR 模式) → cwd`；导出 `resolveInstallRoot()`、`resolveSkillDir()`，供 `lib.mjs`、新 `code-search` 模块、`mcp/server.mjs`、所有脚本统一调用，避免重复实现。
- [ ] `lib/shared/config.mjs`：合并读取共享 `config/config.json`（新 schema）与旧 `embed-config.json`（兼容层，字段映射见第 13 节），暴露 `loadSharedConfig()`；`embedding` 字段两个子系统共用一份。
- [ ] `lib/shared/locking.mjs`：`acquireLock(lockPath, {timeoutMs, staleMs})` / `releaseLock` / `withAtomicWrite(targetPath, writerFn)`（临时文件+rename），转录索引与代码索引都改用它。
- [ ] `lib/shared/redact.mjs`：`redactSecret(value)`（只留末 4 位）、`redactConfigForDisplay(cfg)`，供 `trans_status`/`trans_code_status`/`trans_code_config_check`/`doctor.mjs` 统一调用，杜绝到处手写脱敏逻辑。

### 10.2 主线 A：转录续接子系统（兼容改造）

- [ ] `scripts/lib.mjs` 中 `SKILL_DIR`/`CONFIG_PATH`/`INDEX_ROOT` 的推导逻辑抽到 `lib/shared/paths.mjs` + `lib/shared/config.mjs`，`lib.mjs` 内部改为调用共享层，**行为零变化**（先跑一遍现有 `test/lib.test.mjs` + `test/smoke.mjs` 记录 baseline，再改，改完复跑对比）。
- [ ] `lib.mjs` 里 `buildIndexLines()` 的 `fs.writeFileSync(P.state, ...)` 与 `.meta`/`.vec` 的 `fs.openSync(..., 'a')` 追加写改为走 `lib/shared/locking.mjs` 的原子写 + 建索引期间持锁，避免与另一客户端的并发 `trans_index` 撞车。
- [ ] `hooks/hooks.json` 的两个 hook 脚本（`prompt-hint.mjs`/`session-end-index.mjs`）内部路径解析改用 `lib/shared/paths.mjs`，保留 `${CLAUDE_PLUGIN_ROOT}` 作为 Claude 侧优先信号。
- [ ] `SKILL.md` 里 `scan-transcript.ps1` 的调用路径从硬编码 `$env:USERPROFILE\.claude\skills\trans\...` 改为"MCP 优先，脚本路径由 paths.mjs 解析"的表述（保留 PowerShell 示例作为 Claude Code 场景的 fallback 说明，不删除，因为它是"MCP 不可用时的手工兜底"，仍有价值）。
- [ ] `scripts/mcp-server.mjs` → 迁移为 `mcp/server.mjs`，`TOOLS` 数组保留原 6 个转录工具定义 100% 不变（工具名、inputSchema、description 逐字保留，只搬文件位置），新增第 12 节的 5 个代码检索工具。
- [ ] 迁移后在原 `scripts/mcp-server.mjs` 位置留一个**转发 shim**（`import('../mcp/server.mjs')`），防止用户或第三方文档里硬编码的旧路径瞬间失效（过渡期兼容，发布说明里标注一个大版本后移除）。
- [ ] `.mcp.json` 的 `args` 从 `scripts/mcp-server.mjs` 更新为 `mcp/server.mjs`。

### 10.3 主线 B：新增代码/文档检索子系统

- [ ] `lib/code-search/ignore.mjs`：`.transignore` 优先，否则回退 `.gitignore`；默认忽略列表（`.git`/`node_modules`/`dist`/`build`/`target`/`.venv`/`venv`/`__pycache__`/`.env`/`*.key`/`*.pem`/常见密钥文件名）写死为内置 baseline，用户规则做**追加**而非替换；文件大小上限可配置（默认例如 2MB，超限跳过并计数）。
- [ ] `lib/code-search/walker.mjs`：递归遍历 `root_path`（校验落在 `allowedRoots` 内），跳过二进制文件（简单启发式：前 8KB 出现 NUL 字节即判定二进制）、跳过软链接逃逸出 root 的条目。
- [ ] `lib/code-search/indexer.mjs`：读取文件 → 分块（复用 `lib.mjs` 的 `chunkText`）→ `embedBatch`（复用）→ 写入 `data/code-index/<root-encoded>/{state.json,meta.jsonl,vec.bin}`，元数据额外记录 `path`/`start_line`/`end_line`（区别于转录索引的 `sid`/`line`）。
- [ ] `lib/code-search/exact-search.mjs`：基于 ripgrep 语义的关键词/子串检索（优先尝试调用系统 `rg` 提升性能与准确性，不可用时退化为 JS 逐行 `includes`/正则扫描——两种路径都要测试覆盖）。
- [ ] `lib/code-search/semantic-search.mjs`：复用 `lib.mjs` 的向量检索核心逻辑（余弦相似度打分排序），適配代码索引的 meta 结构。
- [ ] `lib/code-search/hybrid-search.mjs`：复用 `lib.mjs` 的 `rrfFuse`，同代码索引的 exact/semantic 结果融合。
- [ ] `lib/code-search/security.mjs`：`assertPathAllowed(path, allowedRoots)`（`path.resolve` 规范化 + `..` 检测 + 符号链接 `fs.realpathSync` 校验实际落点仍在边界内）。
- [ ] `mcp/tools/query.mjs`、`index.mjs`、`status.mjs`、`read.mjs`、`config-check.mjs`：MCP 层薄封装，只做参数校验 + 调用 `lib/code-search/*`，不含业务逻辑。

### 10.4 CLI 扩展

- [ ] `scripts/semantic.mjs` 新增子命令（不影响现有 `index`/`query`/`status`/`projects`）：
  - `code-index --root <path> [--incremental|--force]`
  - `code-query "<text>" --root <path> [--mode exact|semantic|hybrid] [--limit 10]`
  - `code-status [--root <path>]`
  - `doctor`（转发 `scripts/doctor.mjs`）
- [ ] `--exact` 保留为 `--mode exact` 兼容别名（转录 `query` 命令已有 `--exact`/`--semantic`，新代码检索命令直接采用 `--mode`，两套命令行为不强行统一写法，因为转录 CLI 是既有公开接口，改参数名本身就破坏兼容）。

### 10.5 安装 / 卸载 / 诊断

- [ ] `scripts/write-config.mjs` 扩展：新增 `--codeSearchAllowedRoots`、`--codeSearchIndexPath` 等参数，写入共享 config.json 的 `codeSearch` 字段；保留原有 `--provider/--baseUrl/--apiKey/--model/--rerankModel/--localDtype` 参数 100% 兼容。
- [ ] `install.ps1` 新增参数：`-Clients claude,codex`（默认两者）、`-SkipIndex`、`-ExactOnly`（跳过 embedding 配置，仅关键词检索可用）；内部拆分为：环境检测 → 共享目录搬迁/校验 → 配置生成 → Skill 链接创建（每客户端一个函数）→ MCP 注册（每客户端一个函数，捕获异常单独跳过不中断整体）→ 可选建初始索引 → 输出路径汇总 + 回退/卸载提示。
- [ ] `install.sh` 镜像同样的参数与流程（bash 版）。
- [ ] `scripts/uninstall.ps1` / `scripts/uninstall.sh`（新增）：`-Clients claude,codex`、`-KeepData`（默认）、`-Purge`；删除前打印将删除的路径清单，等待用户在非 `-Purge` 模式下不触碰 `data/`、`config/`。
- [ ] `scripts/doctor.mjs`（新增）：检查项见第 4.1 节，输出 PASS/WARN/FAIL/SKIP 表格 + 一键修复命令。
- [ ] `scripts/migrate-config.mjs`（新增）：检测旧版"直接装在 `~/.claude/skills/trans`、无共享目录"场景，执行第 11 节迁移步骤。

---

## 11. 迁移方案详解（旧版 → 共享安装）

### 11.1 迁移前状态判定

`migrate-config.mjs` 启动时执行判定逻辑：
1. 若 `~/.agent-tools/trans` 已存在且是真实目录（非 Junction）→ 已是新版共享安装，跳过。
2. 若当前脚本运行目录（`SKILL_DIR` 推导结果）等于 `~/.claude/skills/trans` 且该目录是**真实目录**（非 Junction/symlink）→ 判定为旧版直接安装，进入迁移流程。
3. 若 `~/.claude/skills/trans` 已是指向 `~/.agent-tools/trans` 的 Junction/symlink → 已迁移，跳过。

### 11.2 迁移步骤（对用户可见、需确认后执行，不静默操作）

1. **备份**：把 `~/.claude/skills/trans/embed-config.json`（若存在）、`~/.claude/skills/trans/index/`（若存在）复制到临时备份路径，打印备份路径。
2. **创建共享目录**：`New-Item -ItemType Directory ~/.agent-tools/trans`（存在则跳过）。
3. **搬迁源码**：把当前仓库文件（不含 `index/`、`embed-config.json` 这类用户数据/密钥）复制/移动到 `~/.agent-tools/trans`。
4. **搬迁用户数据**：`embed-config.json` 内容按第 13 节字段映射转换写入新 `config/config.json`；`index/` 目录整体移动到 `data/index/`（转录索引路径不变化含义，只挪根目录）。
5. **替换旧目录为链接**：删除原 `~/.claude/skills/trans` 目录内容（**仅在确认步骤 2-4 都成功后**），改建 Junction 指向 `~/.agent-tools/trans`，使已有 Claude 插件注册/`claude mcp add` 记录的路径（若指向旧脚本绝对路径）依然可解析——若 MCP 注册记录的是绝对脚本路径而非通过 skill 目录动态解析，需额外执行 `claude mcp remove trans` + 重新 `claude mcp add` 指向新路径，两步都要在迁移脚本里自动化，避免用户手动补救。
6. **校验**：跑一次 `node scripts/doctor.mjs`，确认转录索引条数、配置读取都与迁移前一致，再提示"迁移完成，备份路径为 …，确认无误后可手动删除备份"。
7. 全程幂等：中途失败（如权限不足）不删除任何原始文件，报错并给出手动回退命令。

### 11.3 迁移验证命令（Windows 示例，Linux/macOS 见第 19 节）

```powershell
node scripts/migrate-config.mjs --dry-run   # 只打印将执行的步骤，不改动任何文件
node scripts/migrate-config.mjs             # 实际执行，需二次确认
node scripts/doctor.mjs                     # 迁移后校验
```

---

## 12. MCP 工具完整规格

### 12.1 现有转录工具（原样保留，仅搬文件位置）

| 工具 | 用途 | 关键入参 |
|---|---|---|
| `trans_search` | 跨历史会话模糊检索 | `query`(必填) `mode: hybrid\|exact\|semantic` `top` `rerank` `allProjects` `project` |
| `trans_scan` | 生成五段式续接简报 | `id` `path` `project` `tail` `maxMsgs` `detailLine` |
| `trans_list` | 列出候选会话 | `project` `limit` |
| `trans_projects` | 列出所有已知项目 | `query` `limit` |
| `trans_expand` | 展开指定行前后上下文 | `sessionId`(必填) `line`(必填) `before` `after` `project` |
| `trans_index` | 构建/重建转录索引 | `force` `noEmbed` `dry` `allProjects` `project` |

### 12.2 新增代码/文档检索工具

**`trans_code_query`**
```json
{
  "query": "Task spawn failed: oneshot canceled",
  "mode": "hybrid",
  "root_path": "E:\\projects\\example",
  "limit": 10
}
```
返回：
```json
{
  "mode": "hybrid",
  "query": "Task spawn failed",
  "results": [
    { "path": "src/example.ts", "start_line": 20, "end_line": 36, "score": 0.95, "match_type": "exact|semantic|hybrid", "snippet": "..." }
  ]
}
```
- `mode` 缺省 `hybrid`；`root_path` 必填且必须落在 `allowedRoots` 内（若已配置）；无 embedding 配置时 `semantic`/`hybrid` 自动降级为 `exact` 并在返回里注明 `degraded: true` + 原因。

**`trans_code_index`**
```json
{ "root_path": "E:\\projects\\example", "force": false, "incremental": true }
```
支持全量/增量/强制重建；建索引期间持文件锁，锁被占用时返回明确提示（含占用者 PID/时间戳，便于用户判断是否陈旧）。

**`trans_code_status`**
返回：配置是否存在、配置文件路径、provider 类型、embedding 是否可用、索引是否存在、索引更新时间、文件数量、chunk 数量、缓存状态、当前 `root_path`、MCP Server 版本。**不回显完整 API Key**（走 `lib/shared/redact.mjs`）。

**`trans_code_read`**
```json
{ "path": "src/example.ts", "start_line": 20, "end_line": 36, "root_path": "E:\\projects\\example" }
```
读取前必须：`path` 经 `security.mjs` 校验落在 `root_path`/`allowedRoots` 内 → 拒绝 `..` 穿越、拒绝越界符号链接 → 拒绝读取不在本次已知搜索结果范围外的任意绝对路径（除非该路径本身落在 `allowedRoots` 内）。

**`trans_code_config_check`**
检查：Node 版本、配置文件格式、Base URL、API Key 是否存在（不回显）、Embedding 模型、Provider 连通性（真实探测一次 `/embeddings`）、索引目录权限、缓存目录权限、MCP 启动状态、Claude CLI 是否存在、Codex CLI 是否存在。输出结构与 `doctor.mjs` 共享同一套检查函数（避免重复实现，`doctor.mjs` 是 CLI 包装，这个工具是 MCP 包装，底层调同一批 `lib/shared` 检查函数）。

---

## 13. 共享配置 Schema（新旧字段映射）

### 13.1 新 `config/config.json`（默认路径 `~/.agent-tools/trans/config/config.json`）

```json
{
  "version": 1,
  "embedding": {
    "provider": "api",
    "baseUrl": "https://api.mistral.ai/v1",
    "apiKeyEnv": "TRANS_EMBED_API_KEY",
    "model": "mistral-embed",
    "rerankModel": "",
    "dimensions": null,
    "batchSize": 32,
    "maxChars": 800,
    "stride": 720,
    "local": { "enabled": false, "dtype": "q8", "modelPath": "embedder/embedder.mjs" }
  },
  "transcript": {
    "autoRefresh": true,
    "autoRefreshMaxChunks": 300,
    "indexPath": "./data/index",
    "projectsRoot": null
  },
  "codeSearch": {
    "enabled": true,
    "defaultMode": "hybrid",
    "indexPath": "./data/code-index",
    "maxFileSizeBytes": 2097152,
    "ignore": { "useGitignore": true, "extra": [] },
    "security": { "allowedRoots": [] }
  },
  "clients": { "claude": { "installed": null }, "codex": { "installed": null } }
}
```

### 13.2 兼容层：旧 `embed-config.json` 字段 → 新 schema 映射

| 旧字段 | 新位置 |
|---|---|
| `provider` | `embedding.provider` |
| `baseUrl` | `embedding.baseUrl` |
| `apiKey` | 不再写入文件；若检测到旧文件里有明文 `apiKey`，迁移时提示"建议改用环境变量"，仍原样迁移一次并打 WARN |
| `model` | `embedding.model` |
| `rerankModel` | `embedding.rerankModel` |
| `localEmbedder` | `embedding.local.modelPath` |
| `localDtype` | `embedding.local.dtype` |
| `batchSize`/`maxChars`/`stride` | `embedding.*` 同名 |
| `autoRefresh`/`autoRefreshMaxChunks` | `transcript.*` 同名 |

`lib/shared/config.mjs` 的 `loadSharedConfig()` 逻辑：优先读新 `config/config.json`；不存在则读旧 `embed-config.json` 并按上表在内存里映射成新结构（不强制迁移文件，只在运行时兼容），同时打印一次性提示"检测到旧配置格式，建议运行 `node scripts/migrate-config.mjs`"。

### 13.3 Mistral 默认接入（当前已知凭据仅用于验证，不写入仓库）

- `config.example.json` 中 `embedding.baseUrl` 默认值设为 `https://api.mistral.ai/v1`，`model` 默认 `mistral-embed`，`apiKeyEnv` 默认 `TRANS_EMBED_API_KEY`。
- 验证步骤（阶段 4 前完成一次，记录进 `.dev-done-flow/04-test-plan.md`，测试脚本读环境变量而非硬编码 key）：
  ```powershell
  $env:TRANS_EMBED_API_KEY = "<从安全位置注入，不写入任何文件>"
  node scripts/write-config.mjs --provider api --baseUrl https://api.mistral.ai/v1 --model mistral-embed
  node scripts/semantic.mjs index --dry
  node scripts/semantic.mjs query "test" --semantic
  ```
- 若 Mistral `/v1/embeddings` 响应体与 `embedBatch()` 期望的 `{data:[{index,embedding}]}` 不完全一致（例如字段名差异），在 `lib/shared/config.mjs` 或新增 `lib/code-search/providers/mistral.mjs` 里做适配层，不改动通用 `embedBatch()` 的默认 OpenAI 兼容路径。

---

## 14. 安全清单（新增代码检索子系统专属，转录子系统已有的不重复列）

- [ ] 路径穿越：`trans_code_read`/`trans_code_query`/`trans_code_index` 的 `path`/`root_path` 全部经 `security.mjs` 规范化校验。
- [ ] 符号链接逃逸：`fs.realpathSync` 校验最终物理路径仍在边界内，拒绝跳出 `allowedRoots`。
- [ ] 超大文件/二进制文件：跳过并计数，不读入内存。
- [ ] 敏感文件：默认忽略清单覆盖 `.env`/`*.key`/`*.pem`/常见凭据目录，用户可通过 `.transignore` 追加但**不能**移除内置 baseline（防止用户无意中把 `.env` 从忽略列表里删掉导致密钥被索引进向量库）。
- [ ] API Key 不落日志：`doctor.mjs`/`trans_code_status`/`trans_code_config_check` 一律走 `redact.mjs`。
- [ ] MCP 参数校验：所有工具的 `inputSchema` 严格校验类型，拒绝非预期字段导致的注入（如 `root_path` 携带 shell 元字符——本项目不拼 shell 命令，风险主要在路径穿越而非命令注入，但 exact-search 若调用系统 `rg` 二进制，参数必须走 `spawn(cmd, argsArray)` 而非拼字符串，避免命令注入）。
- [ ] DoS 风险：单次索引/查询设合理上限（`maxFileSizeBytes`、`autoRefreshMaxChunks` 同款预算机制复用到代码索引）。

---

## 15. 测试清单

### 15.1 单元测试（`tests/unit/` 或并入现有 `test/`）
- [ ] 配置解析（新 schema + 旧 schema 兼容映射）
- [ ] 路径归一化（Windows 盘符 + Linux 路径）
- [ ] `allowedRoots` 校验（含穿越、符号链接逃逸用例）
- [ ] exact 搜索（含 ripgrep 可用/不可用两条路径）
- [ ] hybrid 排序（RRF 融合，复用现有 `rrfFuse` 的既有单测思路）
- [ ] 索引元数据 schema
- [ ] 锁文件（正常获取/释放、超时回收陈旧锁）
- [ ] 敏感信息脱敏（`redact.mjs`）
- [ ] CLI 参数兼容（`--exact` 别名、旧参数不报错）

### 15.2 集成测试
- [ ] MCP Server 启动 + `initialize` + `tools/list`（应包含全部 11 个工具：6 转录 + 5 代码检索）
- [ ] `trans_status`（若保留/`trans_code_status`）
- [ ] `trans_code_query` exact 模式（无 embedding 配置也能跑通）
- [ ] `trans_code_index` 全量 + 增量
- [ ] 建完代码索引后 `trans_code_query` semantic/hybrid
- [ ] 无 embedding 时 semantic/hybrid 自动降级 exact，返回体含降级说明
- [ ] 错误配置（baseUrl 缺失/apiKey 缺失）报错信息清晰
- [ ] 无索引时查询提示清晰
- [ ] 并发建索引（两个进程同时 `trans_code_index` 同一 `root_path`，验证锁生效、不损坏数据）
- [ ] 旧 `embed-config.json` 迁移到新 schema 后行为一致

### 15.3 安装器测试
- [ ] 重复安装幂等性（跑两次 `install.ps1`，配置/MCP 注册/链接不重复）
- [ ] 已存在 Junction 场景
- [ ] 已存在普通目录场景（非链接，需提示而非覆盖）
- [ ] MCP 已注册场景（不重复 add）
- [ ] Claude CLI 缺失（跳过 Claude，继续 Codex，打印补装命令）
- [ ] Codex CLI 缺失（对称场景）
- [ ] Node 缺失（清晰报错，终止安装但不产生半成品状态）
- [ ] 配置已存在（保留用户配置，不覆盖 apiKey）
- [ ] 卸载 `-KeepData` 不删除 `data/`/`config/`
- [ ] 卸载 `-Purge` 完整清理并在执行前列出待删路径

---

## 16. 文档交付清单

- [ ] `README.md` / `README.zh-CN.md`：项目简介、架构图、Claude Code 安装、Codex CLI 安装、双客户端一键安装、配置说明（API/本地模型/exact-only）、索引命令、MCP 工具说明（全部 11 个）、Doctor 诊断、升级/卸载/回退方式、常见故障、安全说明、目录说明、开发说明；明确标注"Skill 是操作规范，MCP 是执行工具，两个客户端各自注册 MCP 但共用同一份 MCP 代码/配置/索引"。
- [ ] `docs/architecture.md`：Mermaid 架构图（与第 2 节结构一致）。
- [ ] `docs/claude-code.md` / `docs/codex-cli.md`：各自安装、Skill 发现方式、MCP 注册方式（基于现查的真实命令，不臆测）。
- [ ] `docs/migration.md`：对应第 11 节，给出从 `~/.claude/skills/trans` 迁移到 `~/.agent-tools/trans` 的完整步骤 + 回退方法。
- [ ] `docs/local-model.md`：保留现有内容，补充"本地模型同样被代码检索子系统复用"的说明。
- [ ] `AGENTS.md`：项目架构、测试命令、修改约束（供两类 CLI agent 都能读取的统一入口）。
- [ ] CHANGELOG / 发布检查表：`.dev-done-flow/05-release-checklist.md`。

---

## 17. 验收标准（对齐原目标第十八章）

**功能**
- [ ] Claude Code 可发现 trans Skill；Codex CLI 可发现 trans Skill
- [ ] 两端均可连接同一 MCP Server 文件、同一份配置、同一份转录索引
- [ ] `trans_code_*` 系列在两端均可用，且共用同一份代码索引
- [ ] exact 搜索无 API 也可用（转录 + 代码检索两条线都验证）
- [ ] semantic/hybrid 配置正确后可用（用 Mistral 验证一次）
- [ ] 原有 6 个转录 CLI 命令与 MCP 工具行为不变

**安装**
- [ ] Windows 一键安装成功；Linux 安装逻辑合理（无 Windows 环境验证时至少静态审查 + CI）
- [ ] 重复安装不破坏环境；Claude-only / Codex-only / 双客户端安装分别成功
- [ ] 卸载 `-KeepData` 保留数据；`-Purge` 完整清理

**稳定性**
- [ ] 两个 MCP 进程可同时查询；同时建索引不损坏数据（锁生效）
- [ ] 错误配置/无索引有清晰提示；embedding 失败可降级 exact
- [ ] 配置和日志不泄露 API Key

**文档**
- [ ] README 命令经实际验证；中文 README 完整；架构图与代码一致；MCP 工具名称与代码一致；故障排除覆盖常见错误

---

## 18. 兼容性矩阵模板（待真实测试后填值，禁止臆填）

| 功能 | Claude Code | Codex CLI | 公共实现 |
|---|---|---|---|
| Skill 自动发现 | ? | ? | `SKILL.md` |
| STDIO MCP | ? | ? | `mcp/server.mjs` |
| 转录续接（6 工具） | ? | ? | `lib/`（原 `scripts/lib.mjs`） |
| 代码检索 exact | ? | ? | `lib/code-search/exact-search.mjs` |
| 代码检索 semantic | ? | ? | `lib/code-search/semantic-search.mjs` |
| 代码检索 hybrid | ? | ? | `lib/code-search/hybrid-search.mjs` |
| API Provider（Mistral） | ? | ? | `lib/shared/config.mjs` |
| Local Provider | ? | ? | `embedder/` |
| Windows Junction | ? | ? | `install.ps1` |
| Linux/macOS symlink | ? | ? | `install.sh` |
| Doctor | ? | ? | `scripts/doctor.mjs` |
| 卸载 | ? | ? | `uninstall.ps1/.sh` |

## 19. 验证命令清单（最终发布前逐条跑一遍）

Windows：
```powershell
claude mcp list
codex mcp list
Test-Path "$env:USERPROFILE\.claude\skills\trans\SKILL.md"
Test-Path "$env:USERPROFILE\.agents\skills\trans\SKILL.md"
node scripts/doctor.mjs
node scripts/semantic.mjs query "test" --exact
node scripts/semantic.mjs code-query "test" --root . --mode exact
```
Linux/macOS：
```bash
claude mcp list
codex mcp list
test -f "$HOME/.claude/skills/trans/SKILL.md" && echo ok
test -f "$HOME/.agents/skills/trans/SKILL.md" && echo ok
node scripts/doctor.mjs
node scripts/semantic.mjs query "test" --exact
node scripts/semantic.mjs code-query "test" --root . --mode exact
```

---

## 9. 下一步

用户确认本计划后：
1. 生成 `.dev-done-flow/00-repository-audit.md`（细化，含文件引用关系图）。
2. 现查 `codex mcp --help` / Codex Skills 文档，锁定阶段 3 的真实命令，回填第 7 节与第 18 节。
3. 用真实 Mistral key 跑一次第 13.3 节的验证步骤，确认响应体兼容性。
4. 按第 10 节任务清单逐项执行，优先级：`lib/shared/` 共享层 → 主线 A 无损搬迁 → 主线 B 核心 → 安装器 → 测试 → 文档。
