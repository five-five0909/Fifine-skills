---
name: claude-sync-bridge
description: 安全地把 Claude Code 的全局 skills 与 MCP 配置同步到 Pi。用于执行“同步 Claude Code skills/MCP 到 Pi”“刷新 Pi 全局 skills”“修复 Pi MCP 中由 Claude 导入导致的坏 server（如 brave-search）”等任务。
---

# Claude Sync Bridge

这个 skill 的目标是：**以 Claude Code 为源头，把全局 skills 与 MCP 配置安全同步到 Pi**。

同步方向固定为：

```text
Claude Code → Pi
```

不要反向覆盖 Claude Code 配置。

---

## 设计原则

执行此 skill 时必须遵守：

1. **不直接把 Pi 配成 `imports: ["claude-code"]`**  
   这样会把 Claude Code 中的坏 MCP server 一起导入，曾导致 `brave-search` 无 `command/url` 报错。

2. **Pi 使用独立 `mcp.json`**  
   从 `~/.claude.json` 读取 Claude Code 的 `mcpServers`，过滤后写入：
   `~/.pi/agent/mcp.json`

3. **过滤不合法 MCP server**  
   无 `command` 且无 `url` 的 server 必须跳过。默认也跳过 `brave-search`，除非用户明确要求允许。

4. **不泄露密钥**  
   不要打印 `.claude.json`、`mcp.json` 原文。所有诊断输出必须隐藏 API Key、Bearer Token 等敏感信息。

5. **skills 真正迁移到 Pi 原生目录**  
   从：
   `~/.claude/skills/`
   复制到：
   `~/.pi/agent/skills/`

6. **移除 Pi 对 Claude skills 目录的直接引用**  
   同步完成后，Pi `settings.json` 中不应再依赖 `~/.claude/skills`，避免重复加载。

7. **先 dry-run，再正式执行**  
   每次执行都先预演，确认无异常后再写入。

---

## 推荐执行方式

### 在 Claude Code 中执行

```powershell
$script = "$env:USERPROFILE\.claude\skills\claude-sync-bridge\scripts\sync-claude-to-pi.ps1"
pwsh -NoProfile -ExecutionPolicy Bypass -File $script -DryRun
pwsh -NoProfile -ExecutionPolicy Bypass -File $script
```

### 在 Pi 中执行

```powershell
$script = "$env:USERPROFILE\.pi\agent\skills\claude-sync-bridge\scripts\sync-claude-to-pi.ps1"
pwsh -NoProfile -ExecutionPolicy Bypass -File $script -DryRun
pwsh -NoProfile -ExecutionPolicy Bypass -File $script
```

### 可选：执行后验证 Pi MCP

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File $script -VerifyPi
```

---

## 同步脚本行为

脚本位置：

```text
scripts/sync-claude-to-pi.ps1
```

脚本会自动完成：

- 读取 `~/.claude.json`
- 提取 root-level `mcpServers`
- 跳过无效 server
- 默认跳过 `brave-search`
- 生成 Pi 原生 `~/.pi/agent/mcp.json`
- 备份旧 Pi MCP 配置
- 复制 `~/.claude/skills/*` 到 `~/.pi/agent/skills/`
- 给 Pi 侧复制出来的 `SKILL.md` 注入 Pi 兼容层提示
- 从 Pi `settings.json` 的 `skills` 数组中移除 `~/.claude/skills`
- 验证写出的 JSON 能正常解析

---

## 参数

| 参数 | 作用 |
|---|---|
| `-DryRun` | 只预览，不写文件 |
| `-VerifyPi` | 同步后运行一次 Pi MCP 状态验证 |
| `-AllowBraveSearch` | 允许同步名为 `brave-search` 的 server，默认关闭 |
| `-KeepPiClaudeSkillsReference` | 不移除 Pi `settings.json` 中的 `~/.claude/skills` 引用，默认会移除 |

---

## 执行后提醒用户

同步完成后提醒用户：

```text
请在 Pi 中执行 /reload，或重启 Pi，让新的 MCP 与 skills 生效。
```

如果是 Claude Code 侧执行，也提醒：

```text
Claude Code 的配置没有被修改；本次只同步到 Pi。
```

---

## 禁止事项

执行此 skill 时不要：

- 不要手写完整 MCP JSON，除非同步脚本失败且已定位原因。
- 不要把 `.claude.json` 原文贴给用户。
- 不要把含 API Key 的 URL 原样输出。
- 不要把 Pi 的 `mcp.json` 改回 `imports: ["claude-code"]`。
- 不要删除 Claude Code 侧任何配置。
- 不要用 MSYS2 `pacman` 安装 Node、Python、Git 或 MCP 相关开发工具。

---

## 异常处理

如果脚本报错：

1. 输出错误原因。
2. 不要停止；检查以下文件是否存在：
   - `~/.claude.json`
   - `~/.claude/skills/`
   - `~/.pi/agent/settings.json`
3. 再运行一次 `-DryRun`。
4. 如果仍失败，只给出最小修复建议，不要盲目重写用户配置。
