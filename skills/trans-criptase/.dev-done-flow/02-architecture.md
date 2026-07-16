# 02 架构文档

> 详细版见 Goal.md 第 2 节；本文件补充 Mermaid 图与模块边界说明，供 `docs/architecture.md` 后续直接复用。

## 总体架构

```mermaid
flowchart TB
    subgraph Shared["~/.agent-tools/trans (唯一源码/配置/索引)"]
        SKILL[SKILL.md]
        CFG[config/config.json]
        MCP[mcp/server.mjs]
        LIBT[lib/transcript (= 现 scripts/lib.mjs 演进)]
        LIBC[lib/code-search/*]
        LIBS[lib/shared/* paths/config/locking/redact]
        DATAT[data/index 转录索引]
        DATAC[data/code-index 代码索引]
    end

    ClaudeLink[~/.claude/skills/trans Junction] --> Shared
    CodexLink[~/.agents/skills/trans Junction] --> Shared

    ClaudeCLI[Claude Code] -- MCP stdio --> MCP
    CodexCLI[Codex CLI] -- MCP stdio --> MCP

    MCP --> LIBT
    MCP --> LIBC
    LIBT --> LIBS
    LIBC --> LIBS
    LIBT --> DATAT
    LIBC --> DATAC
```

## 模块职责边界

| 层 | 职责 | 不做的事 |
|---|---|---|
| `SKILL.md` | 何时触发、选哪种检索模式、失败降级顺序、结果呈现规范 | 不承担索引/检索的具体实现 |
| `mcp/server.mjs` | STDIO JSON-RPC 协议层、工具注册、参数透传 | 不堆提示词逻辑（那是 SKILL.md 的事） |
| `lib/transcript/*`（现 `lib.mjs`） | 转录解析/索引/检索纯逻辑 | 不感知是哪个客户端在调用 |
| `lib/code-search/*` | 任意目录的 exact/semantic/hybrid 索引与检索 | 不重新实现 embedding/chunk/RRF（复用 `lib/shared` 与 `lib/transcript` already-proven 的纯函数） |
| `lib/shared/*` | 路径解析优先级链、配置合并、文件锁、脱敏 | 不含任何检索业务逻辑 |
| `scripts/install.ps1`/`.sh` | 环境探测、共享目录搬迁、Skill 链接、MCP 注册、幂等保证 | 不重写用户已有配置里的 apiKey |

## 路径解析优先级链（两条主线统一）

```
显式参数 (root_path / project)
  → 客户端环境变量 (CLAUDE_PLUGIN_ROOT / CODEX_* 现查实际变量名)
  → 脚本自身位置反推 (现 SKILL_DIR 模式，lib/shared/paths.mjs 统一实现)
  → process.cwd()
```

## 并发与数据一致性

- 索引写入：临时文件 + `fs.renameSync` 原子替换。
- 并发建索引：`data/locks/<index-key>.lock`，含 PID + 时间戳，超时（如 10 分钟无更新）判定陈旧并允许抢占。
- 两个客户端各自独立 MCP 进程，只读查询天然可并发；写路径（`trans_index`/`trans_code_index`）互斥。

## 安全边界（代码检索子系统新增面）

```
trans_code_query/read/index 的 root_path/path
  → path.resolve 规范化
  → 拒绝 ".." 穿越
  → fs.realpathSync 校验最终物理路径仍在 allowedRoots 内（若已配置）
  → 忽略清单（内置 baseline + .transignore 追加，不可移除 baseline）过滤敏感文件
```

## 与原目标架构图的偏离说明

原目标里 `trans_query`/`trans_index`/`trans_read`/`trans_status`/`trans_config_check` 五个名字，在本仓库里因为 `trans_index` 已被转录索引占用，新工具改用 `trans_code_*` 前缀，避免破坏 FR1（向后兼容）。详见 Goal.md 第 2 节"关键决策"。

---
下一步：`03-implementation-plan.md`（Trellis 任务 `07-15-implementation-plan`），先现查 Codex CLI 相关命令。
