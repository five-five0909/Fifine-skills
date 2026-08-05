# 00 仓库审计（细化版）

> 对应 Trellis 任务 `07-15-audit`；供 `01-requirements.md` / `02-architecture.md` / `03-implementation-plan.md` 引用。所有结论基于实际读码，非猜测。

## 1. 交付形态

`trans-criptase` 是 **Claude Code 插件**（不是独立 npm 包，`package.json` 无 `bin`/`exports`）：

- `.claude-plugin/plugin.json`：插件元数据。
- `.claude-plugin/marketplace.json`：插件市场清单，`source: "./"` 即仓库自身。
- 插件加载依赖固定路径 `~/.claude/skills/trans`（Claude Code 按此路径自动发现 `SKILL.md`/`hooks/hooks.json`/`.mcp.json`）。

## 2. 文件引用关系图

```
plugin.json / marketplace.json ── 声明插件身份（无运行时依赖）

SKILL.md ── 用户触发 /trans → 指导模型：
   ├─ 优先调 MCP 工具（trans_scan/trans_list/trans_search/trans_expand/trans_index/trans_projects）
   └─ MCP 不可用时 fallback → scripts/scan-transcript.ps1（PowerShell，仅 Windows 语法层面，
      内容依赖 ~/.claude/projects 布局，非 Claude 专有）

.mcp.json ── 声明 MCP Server：
   └─ command: node scripts/mcp-server.mjs  (${CLAUDE_PLUGIN_ROOT} 隐式注入 cwd/env，实际未在 .mcp.json 里显式用到该变量；SKILL.md 里的
      PowerShell 示例路径才用了 $env:USERPROFILE\.claude\skills\trans，是文档层硬编码，不是运行时依赖)

scripts/mcp-server.mjs ── stdio JSON-RPC server
   ├─ import * as lib from './lib.mjs'
   ├─ TOOLS: trans_search / trans_scan / trans_list / trans_projects / trans_expand / trans_index
   └─ handleCall() 分发到 lib.* 各函数

scripts/lib.mjs ── 核心逻辑（唯一真相层，CLI 与 MCP 共用）
   ├─ SKILL_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
   │     → 按 lib.mjs 自身文件位置反推，不写死路径（唯一天然客户端无关的设计，可直接复用）
   ├─ CONFIG_PATH = <SKILL_DIR>/embed-config.json
   ├─ INDEX_ROOT = process.env.TRANS_INDEX_ROOT || <SKILL_DIR>/index   （已支持测试期覆盖）
   ├─ PROJECTS_ROOT = process.env.TRANS_PROJECTS_ROOT || ~/.claude/projects  （已支持测试期覆盖，但生产默认硬编码 Claude 路径）
   ├─ loadConfig()/CFG/refreshConfig() ── 配置读取，env var 优先于文件
   ├─ 转录解析：extractRecord/readRecords/firstUserMsg/transcriptCwd/sessionFiles/resolveTranscript/realUserMsgs
   ├─ 只读业务函数：scanLines/expandLines/listLines/projectsLines
   ├─ 索引：chunkText/normalize/embedBatch/extractFileChunks/buildIndexLines/indexCommand/autoRefreshIndex/spawnBackgroundIndex/loadIndex
   └─ 检索：keywordScores/rrfFuse/rerankHits/queryLines/statusLines

scripts/semantic.mjs ── CLI，import * as lib，子命令 index/query/status/projects，参数用手写 parseArgs()

scripts/scan-transcript.ps1 ── PowerShell 版 scanLines 等价实现（脚本内直接读 JSONL，不 import lib.mjs，
   逻辑与 lib.mjs 的 scanLines 是「同一套算法两处实现」——潜在的行为漂移风险点，见第 6 节）

scripts/write-config.mjs ── 生成/更新 embed-config.json；交互向导 + 非交互 --key value 两态；
   testEmbed() 会 dynamic import('./lib.mjs') 做连通性自检；SKILL_DIR/serverPath/libPath 均硬编码为
   scripts/mcp-server.mjs、scripts/lib.mjs（若这两个文件搬到 mcp/ 目录，这里必须同步改）

hooks/hooks.json ── Claude Code 专有 hook 格式
   ├─ UserPromptSubmit → scripts/prompt-hint.mjs（正则扫描用户输入的"回顾/续接"意图词，命中则注入 additionalContext 提示 AI 调 MCP 工具；纯启发式，无外部依赖，零副作用设计良好）
   └─ SessionEnd → scripts/session-end-index.mjs（import { spawnBackgroundIndex } from './lib.mjs'，
      detached spawn 增量建索引，只维护"已建过索引"的项目，新项目不主动建）

embedder/embedder.mjs ── 本地 ONNX embedding 实现，被 lib.mjs 的 embedBatch() 在 provider=local 时动态 import

test/lib.test.mjs ── node --test，覆盖 encodeProject/extractRecord/chunkText/rrfFuse/keywordScores（纯函数单测）
test/smoke.mjs ── 端到端，spawn scripts/semantic.mjs 子进程，用 TRANS_PROJECTS_ROOT/TRANS_INDEX_ROOT 沙箱隔离
```

## 3. 逐项审计结论（对应用户原始 15 问）

1. **Skill 入口**：根目录 `SKILL.md`，无子目录版本。
2. **MCP Server 入口**：`scripts/mcp-server.mjs`（`.mcp.json` 声明）。
3. **MCP 暴露的工具**：`trans_search`、`trans_scan`、`trans_list`、`trans_projects`、`trans_expand`、`trans_index`（6 个，全部是转录相关，无代码检索工具）。
4. **配置文件位置**：`<SKILL_DIR>/embed-config.json`（`SKILL_DIR` 由 `lib.mjs` 自身路径反推，实际运行时落在 `~/.claude/skills/trans/embed-config.json`）。
5. **索引保存位置**：`<SKILL_DIR>/index/<project-encoded>/{state.json,meta.jsonl,vec.bin}`。
6. **exact 搜索实现**：`keywordScores()`——纯 JS 子串/分词命中打分（无 ripgrep 依赖，无外部二进制）。
7. **semantic 搜索实现**：`embedBatch()` 取查询向量 → 与索引里每条 `Float32Array` 做点积（因为向量已归一化，点积=余弦相似度）→ 取 top 200 → 可选 `rerankHits()` 二次精排。
8. **Embedding provider 配置**：`embed-config.json` 的 `provider: "api"` 分支，`baseUrl` 需以 `/v1` 结尾，POST `{baseUrl}/embeddings`，OpenAI 兼容格式 `{model, input}` → 期望响应 `{data:[{index,embedding}]}`。
9. **本地模型配置**：`provider: "local"`，`localEmbedder` 指向 `embedder/embedder.mjs`（相对路径会拼到 `SKILL_DIR` 下），导出 `embed(texts, {model, dtype, isQuery})`。
10. **install.ps1/.sh 当前操作**：仅两件事——① 调 `write-config.mjs` 生成/更新配置 ② `claude mcp add --scope user trans -- node <server>`。不拷贝文件（插件形态下文件必须原地保留）、不处理 Codex、不建任何 symlink/junction、无 `claude` CLI 时只打印手动命令（不报错退出，行为已符合"跳过不阻断"原则，可复用这个模式扩展到 Codex 分支）。
11. **是否已支持 Claude Code**：是，且是当前唯一支持的客户端。
12. **与 Codex CLI 冲突的实现**：`${CLAUDE_PLUGIN_ROOT}`（仅出现在 `.mcp.json` 的隐式约定与 `SKILL.md` 文档示例里，非 `lib.mjs` 强依赖）；`hooks/hooks.json` 的 `UserPromptSubmit`/`SessionEnd` 事件名是 Claude Code 专有格式；`claude mcp add` 命令是 Claude CLI 专有。**`lib.mjs` 本体不含任何 Claude 专有 API**，是可以直接被 Codex 侧复用的部分。
13. **硬编码路径清单**：
    - `scripts/write-config.mjs`：`serverPath`/`libPath` 硬编码 `scripts/mcp-server.mjs`、`scripts/lib.mjs`（相对 `SKILL_DIR`）——迁移 `mcp/server.mjs` 时必须同步改。
    - `install.ps1`/`install.sh`：`$expectedDir = ~/.claude/skills/trans`（写死 Claude 路径，仅用于"位置校验+提示"，不阻断执行）。
    - `lib.mjs`：`PROJECTS_ROOT` 默认值硬编码 `~/.claude/projects`（Codex CLI 若有自己的会话记录格式和路径，这里需要新增可配置项或 Codex 专属默认值——**待现查 Codex 是否有等价的会话转录文件**，若没有，转录续接子系统在 Codex 侧天然只能是"读 Claude 的转录"，这是产品语义问题需要在文档中明确，而非纯技术问题）。
    - `SKILL.md`：PowerShell 示例路径硬编码 `$env:USERPROFILE\.claude\skills\trans\scripts\...`。
14. **潜在安全风险**：
    - `scripts/scan-transcript.ps1` 与 `lib.mjs` 的 `scanLines()` 是两套独立实现（一个 PowerShell 一个 JS），行为可能随时间漂移不一致——不算安全风险，但是正确性/维护性风险，记入第 6 节技术债。
    - `embed-config.json` 若用户在 `write-config.mjs` 交互向导里直接填了 `apiKey`（而非用环境变量），该文件明文含 key；当前 `.gitignore` 需核实是否已排除该文件（见第 4 节）。
    - 新增代码检索子系统若不做路径校验，`root_path`/`trans_code_read` 存在路径穿越/任意文件读取风险——**现状还不存在这个面**，但一旦实现必须补（已在 Goal.md 第 14 节列出）。
    - `keywordScores()`/`embedBatch()` 均不解析用户输入为 shell 命令，无命令注入面；新增 exact-search 若调用系统 `rg` 二进制，必须用 `spawn(cmd, argsArray)` 而非字符串拼接。
15. **文档与代码不一致点**：
    - `SKILL.md` 里 MCP 工具描述与 `mcp-server.mjs` 的 `TOOLS` 定义逐一核对，**一致**（无漂移）。
    - `install.ps1`/`.sh` 输出提示"5 个 MCP 工具（trans_search/scan/list/expand/index）"——**实际是 6 个**（漏数了 `trans_projects`）。这是一处需要顺手修的文档纰漏（记入阶段 4b 任务）。

## 4. 待核实项（本轮审计未覆盖，下一步执行）

- [ ] `.gitignore` 是否排除 `embed-config.json`、`index/`、`data/`（防止用户误提交明文 key 或索引数据）——需读 `.gitignore` 内容确认。
- [ ] `PRIVACY.md` 内容与本审计的安全结论是否一致。
- [ ] `docs/local-model.md` 与 `embedder/` 实现是否一致（本地模型下载/放置路径说明）。
- [ ] `README.md`/`README.zh-CN.md` 的安装步骤是否与 `install.ps1`/`.sh` 实际行为一致（不能仅凭 README 猜实现，已通过读源码交叉核实，剩 README 文本本身的准确性待第 8 阶段统一校对）。

## 5. 可直接复用的模块清单（不推倒重写）

- `scripts/lib.mjs` 全部纯函数：`chunkText`/`normalize`/`rrfFuse`/`keywordScores`/`embedBatch`（新代码检索子系统直接 import 复用，无需重新实现）。
- `SKILL_DIR` 反推模式（文件自身位置推导安装根目录）——迁移到 `lib/shared/paths.mjs` 后对两条主线都成立。
- `write-config.mjs` 的"单一真相层"设计（PS/bash 都只是转发参数给它）——扩展参数集直接复用这个模式。
- `test/smoke.mjs` 的沙箱隔离模式（`TRANS_PROJECTS_ROOT`/`TRANS_INDEX_ROOT` 环境变量覆盖）——新测试直接仿照加 `TRANS_CODE_INDEX_ROOT`。
- `install.ps1`/`.sh` 的"位置校验但不阻断+跳过未安装的 CLI"模式——扩展到 Codex 分支时复用同一套克制原则。

## 6. 技术债记录（本次改造顺手处理）

- `scan-transcript.ps1` 与 `lib.mjs.scanLines()` 重复实现：暂不合并（跨语言，合并成本高于收益），但在 `docs/architecture.md` 里显式标注"两处实现需保持语义一致"的维护提示。
- `install.ps1`/`.sh` 的"5 个 MCP 工具"提示文案错误（实际 6 个）：随阶段 4b 一并修正。
- 转录索引写入无锁、无原子写（`buildIndexLines()` 里 `fs.openSync(..., 'a')` 直接追加，`fs.writeFileSync(P.state, ...)` 非原子）：随阶段 4a 补齐（Goal.md 10.2 节）。

---
下一步：`01-requirements.md` / `02-architecture.md`（Trellis 任务 `07-15-requirements-architecture`）。
