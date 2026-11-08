# Environment

本 skill 附带项目专用 embedding 配置 `config/bundled.json`。其中 Base64 编码的 key 可被任何拿到项目或发布包的人直接解码；Base64 不是加密。环境变量、私有配置和旧配置可覆盖内置配置。

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
2. 配置文件：`~/.config/fifine-skills/trans-criptase.json` 优先；不存在时使用安装目录的 `config/config.json`、旧版 `embed-config.json`，最后使用随 skill 发布的 `config/bundled.json`。
3. **环境变量覆盖**（`config.mjs:112-119`）：`TRANS_EMBED_PROVIDER` / `TRANS_EMBED_BASE_URL` / `TRANS_EMBED_API_KEY` / `TRANS_EMBED_MODEL` / `TRANS_RERANK_MODEL` / `TRANS_LOCAL_EMBEDDER` 高于一切配置文件。

私有 env 文件在每次启动 CLI 时读取；修改后下一次命令生效。

项目内置 key 随 skill 分发；如需撤销访问，应在服务商处轮换密钥并更新内置配置。

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

`proxy-boot.mjs` 依赖 `undici`；需要单独安装到脚本可解析的位置。也可在支持的 Node 版本上使用 `NODE_OPTIONS=--use-env-proxy`。代理环境变量在运行 CLI 的进程中设置；`NO_PROXY` 应包含本机地址。
