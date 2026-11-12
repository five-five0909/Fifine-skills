# codebuddy-watchdog

CodeBuddy Code（`cbc`）插件：会话静下来之后**替你发一条「继续」**，但把「要不要继续」交给模型通过一个
工具明确回答，而不是让它从催促文字里猜。行为对照 GreenHatHG 的
[pi-extension-watchdog](https://github.com/GreenHatHG/pi-extension-watchdog)（Pi Coding Agent 扩展）移植。

一句话流程：一轮结束 → 起倒计时（默认 60s）→ 到点发一条带「这不是用户输入」标记的检查 →
模型必须调用 `watchdog_decide(decision, note)` → `wait_user` / `done` 自动停表，`continue` 再发一个工作回合 →
没调用工具就当没答、倒计时重来 → 到达上限（默认 50 次）自动停止。

## 仓库副本与运行实例

此目录保存完整源码及测试，不会自动改变已经安装的插件。安装后实际运行的通常是 CodeBuddy 插件缓存中的副本；修改这里的源码不会自动更新已安装副本。需要切换或更新时，先确认安装影响，再按下述步骤操作。状态、日志和用户配置不随源码复制。

源码包括 `.codebuddy-plugin/` 清单、`hooks/` 插件逻辑、`bin/watchdogctl` 会话外控制器、`config/` 配置、安装与卸载脚本，以及 `tests/` 模拟测试。`codebuddy-watchdog-report.md` 是原始实现及历史测试报告，其中的环境、测试数量和交付物描述不代表本副本的当前状态。

## 安装

```bash
cd codebuddy-watchdog
./install.sh                 # validate → 备份 settings.json → plugin add --yes → 固定 state 目录 → 自检
./install.sh --dry-run       # 只打印命令，不动任何东西
./install.sh --state-dir DIR # 指定状态/日志/config 目录
```

前置：`codebuddy`（`cbc`）在 PATH 上，即 `npm install -g @tencent-ai/codebuddy-code`。
也可以用 `CODEBUDDY_BIN=/path/to/codebuddy ./install.sh`。

安装会修改用户插件配置、缓存和状态目录，不会因源码复制而自动执行。默认状态目录为 `~/.codebuddy/watchdog`；可用 `--state-dir` 指定其他目录。安装脚本会备份已有 settings，但并非所有被修改文件都有自动恢复保证；已有安装应先检查实际配置与备份。

卸载与回滚：

```bash
./uninstall.sh            # 禁用 + 移除缓存 + 清理 installed_plugins.json（保留状态与日志）
./uninstall.sh --purge    # 连状态目录一起删
```

`plugin uninstall` 在 2.176.0 上对本地添加的插件会报 `Marketplace undefined is not found`，
`uninstall.sh` 因此多走一步：直接清 `~/.codebuddy/plugins/cache/*/codebuddy-watchdog` 与
`installed_plugins.json` 里的条目；脚本会备份该索引，但不会备份被删除的缓存。`--purge` 删除的是默认的 `~/.codebuddy/watchdog`，不会自动查找自定义状态目录；其中可能包含配置、状态和日志。卸载或清理前先检查目标并备份需要保留的内容；缓存可通过插件源码重新安装。

## 使用

会话里：`/watchdog status | on | off | reset`。

会话外（不需要登录）：

```bash
bin/watchdogctl where        # 插件目录/状态目录/状态文件/日志文件/配置文件 各在哪
bin/watchdogctl status       # 上次/本次会话的 phase、检查次数、停表原因
bin/watchdogctl logs 40      # 日志尾部
bin/watchdogctl on|off       # 硬开关：写 <stateDir>/config.json 的 enabled
bin/watchdogctl set timeoutMs=45000 maxChecks=20
bin/watchdogctl reset        # 清掉状态与计数
```

`where` 和 `status` 只读；`on`、`off`、`set` 会写配置并备份原配置，`reset` 会删除状态镜像。控制器默认优先读取 `~/.codebuddy/watchdog/pointer.json` 指向的已安装实例，因此从源码目录运行也可能操作当前插件；执行写操作前先运行 `where` 核对路径。

## 配置

`config/watchdog.config.json` 是插件默认配置，`<stateDir>/config.json`（`watchdogctl set` 写的）逐项覆盖。插件会校验配置并报告类型错误、越界和未知键；控制器的 `set` 只检查已知键及基本类型，不检查所有取值边界。修改后应检查插件日志和实际生效配置，不要仅凭写入成功认定生效。

| 键 | 默认 | 含义 |
| --- | --- | --- |
| `enabled` | `true` | 总开关；`false` 时插件仍加载但完全不动 |
| `timeoutMs` | `60000` | 一轮结束后等多久发检查 |
| `minIntervalMs` | `8000` | 两次检查的最小间隔（防抖） |
| `maxChecks` | `50` | 单会话检查次数上限，到点自动停止 |
| `graceMs` | `2000` | 刚有用户动作时改期而不是抢话 |
| `tickMs` | `1000` | 状态栏刷新周期（对应原版的 1s ticker） |
| `requireDecisionTool` | `true` | 要求用 `watchdog_decide` 而不是自由文本 |
| `blockOtherToolsInDecisionRound` | `true` | 决策轮只放行 `watchdog_decide` |
| `postponeOnDraft` | `true` | 输入框里有草稿（人正在打字）时改期 |
| `maxDraftPostpones` | `3` | 草稿连续改期达到该次数后继续检查 |
| `marker` | `[Automated watchdog check` | 自动检查消息的标识 |
| `foldOnCompact` | `false` | 压缩时丢掉 watchdog 往返（见报告「未验证边界」） |
| `logToFile` | `true` | 写 `<stateDir>/watchdog.log` |
| `stateDir` | `default` | `default` = `<插件目录>/state`；也可写绝对路径 |

## 测试

```bash
./tests/run-tests.sh                 # 语法、配置、模拟宿主场景和打包布局
CBC_BIN=codebuddy ./tests/run-tests.sh --with-cli  # 额外运行真实 CLI 探针
```

日志写在 `tests/logs/`；测试会删除并重建该目录下的 `watchdogctl-home` 测试夹。真实 CLI 探针在临时 HOME 里安装插件并运行一次 `-p`，会产生实际 CLI 调用；是否加载成功须检查日志，脚本本身不能保证验证了完整功能。历史报告记录过无登录环境下的加载观察，但未验证模型截断后自动继续。当前环境的真实会话行为也需要单独验证。
