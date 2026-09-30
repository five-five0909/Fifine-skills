# Environment

`fifine-trans-criptase` 的所有凭据与端点都走环境变量：私有 env 文件自动加载，进程已有的环境变量永远优先，skills 仓库里不含任何明文密钥。

## 1. 环境变量清单

| 变量 | 必需性 | 默认 | 作用 |
| --- | --- | --- | --- |
| `TRANS_EMBED_PROVIDER` | 可选 | `api` | 嵌入提供方；`local` 时改用本地模型。 |
| `TRANS_EMBED_BASE_URL` | provider=api 时必需 | 空 | OpenAI 兼容端点，**必须以 `/v1` 结尾**。留空则请求打到 skill 自身路径，直接失败。 |
| `TRANS_EMBED_API_KEY` | provider=api 时必需 | 空 | 嵌入接口密钥。兜底：未设置时读 `MISTRAL_API_KEY`（`lib/shared/config.mjs:73`）。 |
| `TRANS_EMBED_MODEL` | 可选 | `BAAI/bge-m3` | 嵌入模型名。必须是嵌入模型，不能是聊天/代码模型。 |
| `TRANS_RERANK_MODEL` | 可选 | 空 | rerank 模型。空串表示关闭 rerank（`semantic.mjs query --rerank` 不可用）；Mistral 官方没有 rerank 模型。 |
| `FIFINE_SKILLS_ENV` | 可选 | 空 | 自定义私有 env 文件路径，优先级最高（`lib/shared/config.mjs:15-19`）。 |

以下变量有默认值，一般不需要改：

| 变量 | 默认 | 作用 |
| --- | --- | --- |
| `TRANS_LOCAL_EMBEDDER` | 空 | `provider=local` 时的本地模型路径。 |
| `TRANS_CODE_INDEX_ROOT` | `<skill-dir>/data/code-index` | 代码检索索引根目录（`lib/code-search/indexer.mjs:12`）。 |
| `TRANS_INDEX_ROOT` | `<skill-dir>/index` | 转录检索索引根目录（`scripts/lib.mjs:17`）。 |
| `TRANS_PROJECTS_ROOT` | `~/.claude/projects` | Claude Code 会话目录（`scripts/lib.mjs:18`）。 |
| `TRANS_CODEX_SESSIONS_ROOT` | `~/.codex/sessions` | Codex CLI 会话目录（`scripts/lib.mjs:19`）。 |
| `TRANS_CODEX_WALK_LIMIT` | `20000` | Codex 会话目录递归遍历上限（`scripts/lib.mjs:32`）。 |

## 2. 取值来源与优先级

加载发生在 `lib/shared/config.mjs` 模块被 import 时：

1. **私有 env 文件**（`config.mjs:15-44`），按序读取，**已存在的 `process.env` 不被覆盖**：
   1. `$FIFINE_SKILLS_ENV` 指向的文件
   2. `~/.config/fifine-skills/secrets.env`
   3. `~/.config/fifine-skills/fifine-trans-criptase.env`
2. **`config/config.json`**（`embedding.*` 字段，`config.mjs:60-85`）；不存在则回退 `embed-config.json`（`config.mjs:87-105`）。
3. **环境变量覆盖**（`config.mjs:112-119`）：`TRANS_EMBED_PROVIDER` / `TRANS_EMBED_BASE_URL` / `TRANS_EMBED_API_KEY` / `TRANS_EMBED_MODEL` / `TRANS_RERANK_MODEL` / `TRANS_LOCAL_EMBEDDER` 高于一切配置文件。

> 注意「只加载一次」的后果：env 文件在模块 import 时读取，而 MCP stdio 子进程的环境在启动时冻结。**新建或修改 secrets.env 后必须重启 agent / MCP 连接才生效**；在同一台机器上改文件不会热更新。

密钥不要写进 skills 仓库。仓库根 `.gitignore` 屏蔽 `.env`、`.env.*` 与 `*.env`（后者覆盖 `secrets.local.env` 这类「前缀 + .env」文件名），可提交的模板只有 `examples/fifine-skills-secrets.env.example`。

## 3. 已验证的 provider 事实

以下均在 Mistral OpenAI 兼容接口上实测：

- `TRANS_EMBED_BASE_URL` 必须以 `/v1` 结尾。写错成 `https://api.mistral.ai` 时请求落到 `<host>/embeddings`，返回 **404 `no Route matched with those values`**。正确值：`https://api.mistral.ai/v1`。
- `TRANS_EMBED_MODEL=codestral-latest` → **HTTP 400 `Invalid model`**：它是代码模型，不是嵌入模型。
- `TRANS_EMBED_MODEL=mistral-embed` → **HTTP 200，返回 1024 维向量**。
- 换模型会触发索引全量重建：`scripts/lib.mjs:557-565` 比对 `state.model` 与当前模型，不一致时删除 meta/vec 并重建。换 embedding provider 前先想清楚这笔重算成本。

## 4. 代理

Node 的内置 `fetch`（undici）**不读** `HTTP_PROXY` / `HTTPS_PROXY`。在必须经代理出网的机器上，症状是所有外网请求 `fetch failed`，而同一 URL 用 `curl` 带 `http_proxy` 却正常。Node 22.14 上已实测；`--use-env-proxy` 是 Node 24+ 才有的开关。

两种解法：

**Node ≥ 24**：直接让 Node 认代理环境变量，不需要任何依赖：

```bash
NODE_OPTIONS=--use-env-proxy
```

**Node 22**：用仓库自带的 `scripts/proxy-boot.mjs` 注入 undici dispatcher：

```bash
NODE_OPTIONS="--import file:///<skill-dir>/scripts/proxy-boot.mjs"
```

`proxy-boot.mjs` 依赖 `undici`（`EnvHttpProxyAgent`），需要装在它的同级或某个祖先目录的 `node_modules` 里。**不要把 node_modules 装进 skills 仓库树**：`scripts/validate-skills.mjs:184-260` 会因为检测到 `node_modules` 目录而让校验失败。建议装到仓库外的独立运行时目录（例如 `~/sdk-tools/mcp-proxy`），并把 `proxy-boot.mjs` 复制到那里，用 `--import` 指向副本。undici 缺失时脚本只打一条警告，不会让 MCP 进程崩掉。

MCP 客户端配置示例（`mcp.json` 的 `mcpServers.trans.env`，去掉了密钥，改由 secrets.env 提供）：

```json
"env": {
  "HTTP_PROXY": "http://127.0.0.1:7897",
  "HTTPS_PROXY": "http://127.0.0.1:7897",
  "NO_PROXY": "localhost,127.0.0.1,::1",
  "NODE_OPTIONS": "--import file:///home/you/sdk-tools/mcp-proxy/proxy-boot.mjs"
}
```

`NO_PROXY` 必须包含本机地址，否则本机服务也会被送进代理。修改这段配置后同样需要重启 MCP/agent。
