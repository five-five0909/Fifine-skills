---
title: codebuddy-watchdog：CodeBuddy CLI 的 watchdog 自动继续插件（实现、扩展点证据与实测边界）
summary: 在 CodeBuddy Code 2.176.0 上按 pi-extension-watchdog 的机制实现了原生 mod 插件 codebuddy-watchdog：回合结束后倒计时、到点发一条标注「非用户输入」的检查、强制模型用一个 watchdog_decide 工具在 continue/wait_user/done 间三选一，配合上限停表、用户在场暂停、状态与日志落盘和可回滚安装。报告给出扩展点的源码级与实跑证据、与 pi 版的逐项差异、16 个模拟宿主场景全通过的结果，以及在无登录环境下未能验证的具体边界与自测步骤。
---

# codebuddy-watchdog 实现报告

> 历史报告：以下是原实现时的环境、交付物和测试记录，并非此仓库副本的实时状态。当前源码、配置、测试及操作方式以同目录 `README.md` 和实际文件为准；历史测试日志及 ZIP 未随此副本提供。报告中的真实会话限制仍需针对当前版本和环境重新验证。

**交付物**：`codebuddy-watchdog.zip`（插件源码、安装/卸载、配置示例、说明、测试与测试日志）
**目标环境**：Ubuntu / WSL2 + Node ≥ 18.20.8 + `@tencent-ai/codebuddy-code`（本机实测 2.176.0）
**结论一句话**：机制已按 pi 版等价落地并可安装加载；「插件能装、能加载、事件能到、状态能落盘」是实跑验证过的；
「模型真的被截断后自动继续」在**没有登录态**的环境里没有被验证，且 CodeBuddy 自己已内建一层截断恢复（最多 3 次），
所以本插件的真实增量是「内建兜底用完之后」与「非截断型提前收工」两类场景。

---

## 1. 调查方法与证据分级

| 级别 | 含义 | 本报告中的例子 |
| --- | --- | --- |
| **已验证（实跑）** | 在本机真实二进制上执行并观察到的输出 | `--version`、`--help`、hooks 抓取到的 stdin JSON、`plugin validate/add` 输出、引擎日志 `mods: loaded mod ...`、插件写出的 `watchdog.log` / `state.json` |
| **已验证（源码）** | 从 2.176.0 包内文件读到的实现与字符串 | `dist/codebuddy-headless.js` 里的 `executeStopHooks`、`continueRequest`、`Stop hook feedback:`、`isTruncationRecoveryActive`、`nk=3`；`types/codebuddy-code.d.ts` 的 `$` API |
| **官方口径** | 随包文档/注释声称的行为 | d.ts 注释（例如 `$.prompt.submit`「a turn of its own, once the session is idle」）、README、CHANGELOG |
| **推断** | 由上述证据推出、但未直接观测 | 决策轮的 `tool.call` 事件在真实回合里的具体字段名；`session.compact` 的 `messages` 形状 |

本机事实（`node bin/codebuddy --version` → `2.176.0`；`npm view` 显示 2.176.0 于 2026-10-25 发布）：

- 包名 `@tencent-ai/codebuddy-code`，homepage `https://cnb.cool/codebuddy/codebuddy-code`
- 入口 `bin/codebuddy`，可执行名 `codebuddy` / `codebuddy-code` / `cbc` / `codebuddy-lowmem`（读取自 `package.json.bin`）
- 本机 `-p "hi"` → `Authentication required. Please use /login command to sign in to your account`：**可运行、无登录态**

---

## 2. CodeBuddy 扩展点证据

### 2.1 两层扩展面

1. **settings 命令钩子（classic hooks）**：Claude Code 同名事件，`settings.json` 的 `hooks` 形状为
   `{ PreToolUse: [{ matcher, hooks: [...] }] }`（`types/codebuddy-code.d.ts` 第 405–408 行的注释直接写明）。
   事件名在 `dist/codebuddy-headless.js` 中成组出现：`USER_PROMPT_SUBMIT`、`SESSION_START`、`SESSION_END`、
   `STOP`、`SUBAGENT_STOP`、`PRE_TOOL_USE`、`POST_TOOL_USE`、`PRE_COMPACT`、`FINAL_STOP`、`NOTIFICATION` 等。
2. **mods（functional hooks / 插件）**：包目录 `.codebuddy-plugin/plugin.json` + `hooks/hooks.json` + `hooks/index.js`，
   模块导出 `register(on, options)`。后者是本插件采用的路径。

### 2.2 Stop 钩子的真实输入（实跑抓取）

用 `--settings` 挂一个打印 stdin 的脚本后运行 `-p "say hi"`，捕获到（节选，原样）：

```json
{"session_id":"01a17567-...","transcript_path":"...jsonl","cwd":"...",
 "hook_event_name":"Stop","stop_hook_active":false,"is_truncation_recovery":false,
 "agent_type":"cli","last_assistant_message":"Authentication required. ...",
 "background_tasks":[],"session_crons":[],"permission_mode":"default","client":"CLI",
 "version":"2.176.0","generation_id":"...","model":"default-model"}
```

`UserPromptSubmit` 输入里还有 `prompt` 与 `is_internal_continuation`：

```json
{"hook_event_name":"UserPromptSubmit","prompt":"say hi","is_internal_continuation":false, ...}
```

`is_internal_continuation` 说明引擎自己也会用「内部继续」的方式提交提示，这正是本插件要走的路子。

### 2.3 「block 之后会继续」的源码证据

`dist/codebuddy-headless.js` 的 `SessionHookManager.executeStopHooks` 构造上述输入后：

- 组装 `continueRequest`；随后在运行循环里打印 `Stop hook requested continuation`，置 `stopHookActive = true` 并调度续跑；
- 命令行钩子返回 block（JSON `{"decision":"block","reason":...}` 或退出码 2）时，日志为
  `Stop hook requested continuation with message for model`，发给模型的文本是
  `` `Stop hook feedback:\n${message}` ``，且 `providerData:{isMeta:true}`；
- 只有当 `stopReason === "completed"` 时才续跑，否则打印
  `Stop hook continueRequest discarded (...), no model re-invoke`——本机未登录时正是后者（实测该分支只触发一次 Stop）。

**这条路径成立但不适合做定时器**：钩子是同步等待的（`timeout` 默认 60s），在里面 sleep 会卡住整个回合，
也无法在等待期间感知用户按键。因此本插件改用 mod 层的事件 + 宿主定时器（见 §3）。

### 2.4 关键发现：CodeBuddy 已内建截断恢复（上限 3 次）

`dist/codebuddy-headless.js` 中：

- 常量 `nk = 3`、meta 键 `truncationRecoveryCount`、函数 `isTruncationRecoveryActive` / `claimRecoverySlot` / `releaseRecoverySlot` / `resetRecoveryChain`；
- 恢复提示原文：`Output token limit hit. Resume directly — no apology, no recap. Pick up mid-thought if that is where the cut happened. Break remaining work into smaller pieces.`
- 用尽后：`Response was repeatedly truncated due to length limit. The operation is too large for a single response. Please try breaking the task into smaller steps manually.`
- 另有一条针对「输出中断」的恢复预算（meta 键 `errorRecoveryCount` / `networkErrorRetryCount`），文案：
  `Output interrupted. Resume directly — no apology, no recap. Pick up mid-thought if that is where the cut happened.`

含义：pi 版插件要解决的「截断后要再发一条继续」在 CodeBuddy 里**已经被内置覆盖 3 次**。本插件的增量因此是
(a) 内建 3 次用尽之后仍无人接手时继续推进；(b) 非截断型提前收工（例如说「我接下来会…」就结束回合）。
`Stop` 钩子输入里的 `is_truncation_recovery` 字段正好可以区分这两类，属于后续可优化点（见 §6）。

### 2.5 mods 沙箱：只能用 `$` 宿主 API

实测把 `import fs from 'node:fs'` 写进 `hooks/index.js` 后，引擎日志给出：

```
[CliDispatcher] mods: failed to load .../probe-plugin/1.0.0-...: Mod import node:fs is unavailable; use the $ host API
```

源码侧对应 `bundleContainedMod` 里的判断：`if (ed && !el.startsWith(".") && !eu.isAbsolute(el)) throw new Error('Mod import ... is unavailable; use the $ host API')`，
即 mod 模块只允许相对导入（同插件目录内），第三方 npm 依赖同样被拒。因此本插件是**零依赖纯 ESM**，
持久化与日志全部走 `$`。

从 `types/codebuddy-code.d.ts`（由 Claude Code 2.1.293 的声明生成）读到的 `$` 能力（本插件用到标 ✅）：

| 能力 | 用途 | 本插件 |
| --- | --- | --- |
| `$.clock.after(ms, fn)` / `every(ms, fn)` / `now()` | 宿主定时器，返回 `{ cancel }` | ✅ 倒计时 + 1s ticker |
| `$.prompt.submit({ text, asUser? })` | 「运行一次独立回合，会话空闲时执行」——不是模拟按键 | ✅ 发送检查/工作回合 |
| `$.prompt.read()` | 读输入框草稿 | ✅ 有人正在打字就改期 |
| `$.tool.register(ToolSpec)` + `on('tool.call', { tool })` | 声明并服务工具 | ✅ `watchdog_decide` |
| `$.command.register` + `on('command.run', { command })` | 斜杠命令 | ✅ `/watchdog status|on|off|reset` |
| `$.store.get/set/delete/keys` | 跨会话 JSON 键值 | ✅ 状态与计数 |
| `$.fs.write/read/list/exists` | 宿主中介的文件读写 | ✅ 状态镜像 + 日志 |
| `$.ui.log/status/notice` | 调试日志与状态栏 | ✅ 状态栏倒计时 |
| `$.plugin.root/name` | 插件自身路径 | ✅ 定位出厂配置 |
| `event.turn.complete{reason}` | 回合结束（`answer|aborted|refusal|error`） | ✅ 起表/停表 |
| `event.prompt.submit{text,origin}` | 提示提交（含插件来源） | ✅ 用户活动判定 |
| `event.session.compact{messages}` | 压缩可改写消息 | ⚠️ 默认关闭，见 §6 |
| `event.session.end` | 会话结束 | ✅ 清理定时器、落盘 |

### 2.6 CLI 与配置（实跑 `--help` / `plugin --help`）

- headless：`-p/--print`、`-c/--continue`、`-r/--resume [sessionId]`、`--session-id`、`--output-format text|json|stream-json`、
  `--input-format text|stream-json`、`--fork-session`、`--max-turns`
- 插件：`--plugin-dir <dirs...>`、`--settings <file-or-json>`、`--setting-sources user,project,local`
- 子命令：`plugin init|validate|add|build|pack|import|list|enable|disable|uninstall|marketplace`
- 设置文件：`~/.codebuddy/settings.json`、`.codebuddy/settings.json`、`.codebuddy/settings.local.json`（源码字符串）
- 实测补充：`--plugin-dir` 指向本插件**没有**触发加载；`plugin add <dir> --yes` 会安装并置为 enabled，随后引擎日志出现
  `mods: loaded mod "codebuddy-watchdog" from .codebuddy-plugin (tier user, hooks: session.start turn.complete prompt.submit tool.call command.run session.compact session.end)`
- 实测缺陷：对本地添加的插件执行 `plugin uninstall` 会报 `Marketplace undefined is not found`，卸载脚本已绕开（§7）

---

## 3. 插件设计

```
codebuddy-watchdog/
├── .codebuddy-plugin/plugin.json   # name/version/description（plugin validate 通过）
├── hooks/hooks.json                # {"modules":["./index.js"]}
├── hooks/index.js                  # 事件接线：把引擎事件翻成状态机输入
├── hooks/lib/machine.js            # 纯状态机（无宿主依赖，可单测）
├── hooks/lib/host.js               # $ API 适配层（定时器/发送/日志/落盘）
├── hooks/lib/config.js             # 默认值与逐项校验
├── config/watchdog.config.json     # 出厂默认（安装脚本会把 stateDir 写成绝对路径）
├── config/watchdog.config.example.json
├── bin/watchdogctl                 # 会话外控制器：where/status/log/on/off/set/reset
├── install.sh / uninstall.sh       # 安装、备份、回滚
└── tests/                          # 模拟宿主 + 16 个场景 + 真实 CLI 探针
```

状态机（`hooks/lib/machine.js`）阶段与迁移，全部有对应断言：

| 阶段 | 进入条件 | 行为 |
| --- | --- | --- |
| `idle` | 初始 / 用户输入后 | 不装表 |
| `counting` | `turn.complete(answer)` | `$.clock.after(timeoutMs)`，状态栏显示剩余秒数 |
| `checking` | 倒计时到点且通过全部闸门 | 发检查消息、`decisionPending=true` |
| `working` | `watchdog_decide(continue)` | 发工作回合，等下一轮结束 |
| `stopped` | 上限 / `done` / `wait_user` / `/watchdog off` | 记 `stopReason`，不再动作 |

关键规则（与 pi 版一一对应）：

1. **到点的四道闸门**：输入框有草稿 → 改期；`now - lastUserActivityAt < graceMs` → 改期；
   `now - lastCheckAt < minIntervalMs` → 改期；`checks >= maxChecks` → 停表并记 `limit_reached`。
2. **决策轮独占**：`decisionPending` 期间，`on('tool.call')` 守卫拒绝除 `watchdog_decide` 之外的任何工具，
   理由随拒绝文本回给模型。
3. **没调用工具 = 没答**：决策轮结束时若仍 `decisionPending`，计一次 `skips` 并重新起表。
4. **不叠表**：`continue` 之后，检查轮自己的 `turn.complete` 不装表（`expectQueuedTurn`），工作回合结束后才装表。
5. **不追断**：`turn.complete` 的 `aborted / error / refusal` 不算「模型安静下来」，清表不追。
6. **失败可见**：配置错误、定时器失败、发送失败、落盘失败、`$.store` 不可用，各自一条不同 `event` 名的日志；
   不吞错误、不伪装成功。

消息文本（原文见 `hooks/lib/machine.js` 的 `checkPrompt` / `workPrompt`）刻意写死三条约束：
「这不是用户输入」标记、必须一次 `watchdog_decide`、以及「已写出的答复算已交付，重述不算工作」。

---

## 4. 与 pi-extension-watchdog 的逐项差异

| 机制点 | pi 版 | 本插件（CodeBuddy 2.176.0） | 为什么必须改 |
| --- | --- | --- | --- |
| 空闲判定 | `agent_settled` 事件 + `ctx.isIdle()` | `turn.complete`（`e.reason`） | mod API 没有 settled/isIdle；`turn.complete` 是「回合结束」的官方事件 |
| 起表/停表 | `setTimeout` | `$.clock.after` / `every` / `cancel()` | 沙箱禁 `node:*`，宿主定时器是唯一计时手段 |
| 发送继续 | `pi.sendMessage`（带 customType） | `$.prompt.submit({ text })` | 官方「一个独立回合」的接口；不模拟键盘输入 |
| 「人在屏幕前」 | 1s ticker + `editorHasText` + 按键 2s 宽限 | 1s `$.clock.every` 里读 `$.prompt.read()` 的草稿 + `prompt.submit` 事件 | mod 看不到按键事件；草稿 + 提交事件是能拿到的等价信号 |
| 强制决策 | 自建工具 `watchdog_decide` | 同样自建，经 `$.tool.register` + `on('tool.call')` | 一致；CodeBuddy 会把它暴露为 `mcp__codebuddy-watchdog__watchdog_decide` |
| 决策轮禁其它工具 | 决策阶段禁用其它工具 | `on('tool.call')` 守卫返回 `deny` | 引擎层面的守卫比 prompt 约定更硬 |
| 未调用工具 | 视为没答、重来 | 同（`decisionPending` 未清就重来） | 一致 |
| 上限 / 开关 | `max`、`stop_watchdog` 取消注册 | `maxChecks` + `/watchdog off` + `enabled:false` | 工具注册后不建议中途注销（会击穿 prompt cache），改由守卫短路 |
| 上下文折叠 | 发送前过滤后缀 | `session.compact` 时丢掉带标记的消息（默认关闭） | mod API 没有「发送前改写上下文」的钩子（`turn.step` 的 message count 被 pin），这是最接近的原生等价物 ⚠️ |
| 开销 | 作者自算 ~618 token/次 | 检查文本约 210 token，工作回合约 60 token | 文本更短是刻意的 |
| 触发场景 | 公益站 API 截断 | 截断（内建 3 次之后）+ 非截断型提前收工 | CodeBuddy 已有内建截断恢复，见 §2.4 |
| 会话形态 | Pi TUI | TUI 为主；`-p` 一次性运行里会话结束即退出（见 §6） | `-p` 进程在首轮后收敛，定时器无处可跑 |

---

## 5. 实测结果（真跑过的部分）

命令与日志都在 `tests/logs/`（随包交付）：

```
tests/run-tests.sh --with-cli
  === syntax: every JS module parses            PASS
  === config: defaults, type errors, unknown    PASS
  === scenarios: 16 cases against the mock host PASS   (16/16 cases, 45 assertions)
  === packaging: plugin package layout          PASS
  === real CLI: manifest validation + load probe PASS
  ALL CHECKS PASSED
```

模拟宿主场景（`tests/scenarios.mjs`，逐条断言）：

| # | 场景 | 期望 | 结果 |
| --- | --- | --- | --- |
| 1 | session.start | 注册 `watchdog_decide`（三选一 enum）与 `/watchdog` | PASS |
| 2 | 短任务正常结束 | 只装表，30s 内不发任何消息 | PASS |
| 3 | 模拟截断/空响应 | 到点发**一条**，含「not user input」标记 | PASS |
| 4 | 决策轮工具守卫 | `Bash` 被 deny，`watchdog_decide` 放行 | PASS |
| 5 | `decision=continue` | 发工作回合、带 note、检查轮不叠表、工作回合后重新装表 | PASS |
| 6 | `decision=done` / `wait_user` | 立刻停表，5 分钟内不再发 | PASS |
| 7 | 连续触发到上限 | `maxChecks=2` 时只发 2 条并记 `limit_reached` | PASS |
| 8 | 用户中途输入 | 倒计时取消，之后不发 | PASS |
| 9 | 用户刚输入的宽限期 | 改期而不是抢话 | PASS |
| 10 | 决策轮未调用工具 | 计 `skips` 并重新起表，之后能再发 | PASS |
| 11 | 回合被中断/失败 | 不追 | PASS |
| 12 | `/watchdog off` | 停表；`reset` 清零；`status` 可读 | PASS |
| 13 | `session.end` | 定时器清空、无残留、状态落盘、日志有 `shutdown` | PASS |
| 14 | 配置损坏 | 逐条报错并回落默认值，插件照常加载 | PASS |
| 15 | `enabled:false` | 完全不装表、不发 | PASS |
| 16 | 计数与时间戳 | `checks`/`lastCheckAt` 正确 | PASS |

真实 CLI 探针（`tests/real-cli.sh`，临时 HOME，无需登录）：

1. `plugin validate` → `"valid": true`
2. `plugin add <dir> --yes` → `Installed codebuddy-watchdog@1.0.0 ... (enabled)`
3. `codebuddy -p "watchdog probe"` → 模型调用因未登录失败，但引擎日志出现
   `mods: loaded mod "codebuddy-watchdog" ... (tier user, hooks: session.start turn.complete prompt.submit tool.call command.run session.compact session.end)`
4. 插件在 `session.start` 里读配置、写状态与日志，实跑产出（原样）：

```
2026-10-25T23:40:12.666Z [info] ready {"timeoutMs":60000,"maxChecks":50,"enabled":true,"stateDir":".../state","previousSession":null,"version":"1.0.0"} session=01a1756f-...
2026-10-25T23:40:12.693Z [warn] persist_store_unavailable {"message":"codebuddy-watchdog: Hook operation was cancelled or completed","fallback":"state file mirror"}
2026-10-25T23:40:12.828Z [info] shutdown {"checks":0} session=01a1756f-...
2026-10-25T23:40:12.837Z [info] ready {... "previousSession":"01a1756f-..." } ...
```

注意最后一行：第二次运行**读回了上一次会话 id**（`$.store.get`），因此「跨会话状态可读」是实跑证据；
而 `$.store.set` 在该次运行里被宿主拒绝（原因见 §6），日志如实记为 `persist_store_unavailable` 并按设计退到文件镜像，
`state.json` 与 `watchdog.log` 都确实写成了（探针输出里有路径与内容）。

---

## 6. 未验证边界（不要当成已通过）

| # | 未验证的事 | 为什么没验 | 用户侧一键自测 |
| --- | --- | --- | --- |
| 1 | 模型真的被截断后自动继续 | 本机无登录态，`-p` 直接停在 auth 门 | 登录后在长任务里让输出撞上长度上限，观察是否出现 `[Automated watchdog check 1/…]` 与工作回合 |
| 2 | `watchdog_decide` 对模型可见并且被调用 | 同上（工具目录要等首个模型回合） | 会话里问「列出你可用的工具」，或在检查出现时看模型是否调用它 |
| 3 | `on('tool.call')` 守卫在真实工具派发中的字段名 | 无真实回合 | 打开检查后故意让模型跑 `Bash`，看是否被 deny 且回文本 |
| 4 | `$.prompt.submit` 真的在空闲时起一个新回合 | 同上 | 检查发出后观察是否自动出现新一轮输出 |
| 5 | `session.compact` 折叠（`foldOnCompact`，默认 **false**） | 无压缩事件、`messages` 形状未确认 | 默认别开；要开就先在会话里跑 `/compact` 看日志是否有 `folded_on_compact` |
| 6 | `$.store.set` 能否成功 | 探针两次都被拒（`value is not JSON data (a object)` / `Hook operation was cancelled or completed`），后者可解释为会话在 auth 处终止导致派发被取消 | 正常会话里看 `watchdog.log` 是否仍出现 `persist_store_unavailable`；出现就说明只有文件镜像在生效 |
| 7 | `/watchdog status` 的参数解析 | `command.run` 事件里带参字段名未在真实会话确认 | 输入 `/watchdog status`、`/watchdog off` 各看一次返回文本 |
| 8 | 内置截断恢复与本插件的叠加行为 | 同上 | 先让内建 3 次耗尽（观察引擎自己的 `Break remaining work into smaller pieces`），再看本插件是否接手 |
| 9 | `-p` 一次性运行中的可用性 | 进程首轮后收敛，定时器没有生存期 | 交互式 TUI 使用；或用 `--input-format stream-json` 保持会话存活 |
| 10 | 与本机其他插件/钩子的相互作用 | 只装了本插件 | 并存后看 `watchdog.log` 与引擎日志是否有冲突 |

`install.sh` 与 `uninstall.sh` 的备份/回滚逻辑是**静态 + 语法检查**过的（`bash -n`），
`watchdogctl` 的读写路径在本机（无 CLI 依赖）实跑过；但「在用户自己的 `~/.codebuddy` 上真的安装/卸载一遍」
没有被执行过 —— 本沙箱与用户机器不是同一台，`plugin add` 只在临时 HOME 里跑过。

---

## 7. 安装、卸载与回滚

```bash
./install.sh --dry-run          # 先看它要做什么
./install.sh                    # validate → 备份 settings.json → plugin add --yes → 固定 stateDir → 自检
./install.sh --state-dir ~/.codebuddy/watchdog
./uninstall.sh                  # 禁用 + 移除缓存 + 清 installed_plugins.json（备份后改）
./uninstall.sh --purge          # 连状态目录一起删
```

回滚的三重保障：① 覆盖 `settings.json` 前生成 `settings.json.watchdog-backup-<时间戳>`；
② 改 `installed_plugins.json` 前生成同名备份；③ `plugin uninstall` 失败时按缓存目录 + 清单条目清理
（该失败是 2.176.0 对本地插件的实测行为，原因报 `Marketplace undefined is not found`）。
所有被触碰的路径都可以用 `bin/watchdogctl where` 一次列全。

---

## 8. 需要用户确认的两点

1. **`-p`/脚本化场景**：`-p` 一次性运行下会话结束即退出，定时器没有生存期；如果你主要跑 headless，
   告诉我，我可以把「继续」改成由外层包装脚本用 `-c/--resume` 驱动（外部进程 + headless 续跑），那是另一套语义。
2. **间隔与上限**：默认 60s / 50 次 / 8s 防抖，是按 pi 版默认值给的；你在意的话用
   `bin/watchdogctl set timeoutMs=... maxChecks=...` 调，不需要改代码。
