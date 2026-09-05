---
name: fifine-adaptive-runtime-orchestrator
description: "Use this skill when a command, build, training run, download, or remote job may outlive one tool call, or when the agent must decide which shell, executor, host, or wait strategy to use without asking. Trigger: /fifine-adaptive-runtime-orchestrator, long-running task, background job, poll, sleep, nohup, timeout, SSH long task, SSH 长任务, 后台任务, 长任务, 轮询, 卡死检测, wait for job, Slurm, tmux, Start-Process. Produces a discovered Runtime Profile, an executor/shell choice, a launched job with a real Job ID, and an adaptive polling loop that stops on DONE/FAILED. Not for short one-shot commands that return in seconds — just run those directly."
---

# Adaptive Runtime Orchestrator

## Trigger check

This skill applies when the work may exceed a single tool call, or when the correct executor,
shell, host, or wait strategy is not already known — long builds, model training, large
downloads, batch conversions, SSH/container/scheduler jobs, or any task where the agent would
otherwise be tempted to guess `sleep 300`.

Stop and just run the command directly when it is a short one-shot that returns in seconds and
needs no backgrounding. Stop and use `fifine-parallel-executor-with-trellis` when the real need
is splitting a large task into parallel workstreams, not waiting on one job.

---

## Core loop

```text
Discover → Decide → Execute → Baseline → Observe → Estimate → Wait Safely → Poll → Adapt → Remember
```

Never degrade into:

```text
Launch → guess a sleep → guess another sleep → guess another sleep
```

---

## Step 0 — Separate the four environments

Before anything else, keep these distinct. Conflating them is the root cause of most
"it worked locally" runtime failures:

```text
Agent environment        ≠ user's machine
                         ≠ command execution environment
                         ≠ where the background job actually runs
```

One session can hold several targets at once — `local-windows`, `wsl-ubuntu`,
`remote-gpu-server`, `docker-training-container`, `slurm-cluster`. Each gets its own profile.

---

## Step 1 — Capability Discovery (do this, do not guess the product)

Inspect the tools actually exposed in this session. Look for anything offering: shell / bash /
terminal / exec / command runner, PowerShell / pwsh, SSH / remote exec, container exec,
background or async task, job handle / process handle, incremental output, wait / poll / task
status, scheduler.

Do **not** hard-code behavior from a product name:

```text
Linux → Bash            ✗
Windows → PowerShell    ✗
Claude Code → fixed Bash tool and timeout   ✗
Codex → fixed timeout   ✗
SSH → nohup is reliable ✗
```

Real targets include: Windows host, Linux host, macOS host, WSL, Docker/Podman container, SSH
remote, Kubernetes pod/job, Slurm node/job, MCP remote executor, agent sandbox, cloud VM,
tmux/screen/systemd, custom exec proxy.

Build a candidate set and score it — `native_async_job`, `native_exec`, `shell_exec`,
`powershell_exec`, `ssh_exec`, `container_exec`, `scheduler_exec`. Scoring inputs: provides a Job
Handle, independently queryable status, incremental output, reliable timeout, survives the
parent call, returns a real exit code, actually targets the right host, quoting/cross-platform
complexity, and reuses a runner the project already has. Details:
`references/executor-selection.md`.

---

## Step 2 — Load or build the Runtime Capability Profile

Per execution target. If a profile exists for this target, do a **light consistency check**
(hostname, OS, shell path, one cheap command) and reuse it. Do not re-probe from scratch every
round; do not blindly trust a stale cache either.

Minimum fields — `target_id`, `target_type`, `hostname`, `os`, `os_version`, `architecture`,
`executor`, `executor_type`, `preferred_executor`, `shell`, `shell_path`, `shell_version`,
`available_shells`, `preferred_shell`, `supports_background`, `supports_async_job`,
`supports_job_handle`, `supports_incremental_output`, `supports_independent_poll`,
`supports_timeout`, `supports_scheduler`, `timeout_limit_sec`, `safe_timeout_limit_sec`,
`is_remote`, `is_container`, `is_wsl`, `execution_scope`, `last_verified`, `profile_version`.

Probe commands per platform, and the WSL / container / SSH boundary rules:
`references/runtime-discovery.md`. Full schema, the worked JSON example, per-target isolation,
invalidation triggers, and the sensitive-data allow/deny list: `references/profile-schema.md`.

---

## Step 3 — Pick the executor, then the shell

Preference order for **executors** (higher is better; `sleep + check` is last-resort, not a
default):

```text
1. Native async/background Job + Job Handle
2. Native exec + independent poll / incremental output
3. Scheduler Job (Slurm / K8s / systemd / Scheduled Task)
4. SSH/Remote Job + independent status query
5. Shell background + independent status query
6. nohup + PID + status file
7. sleep + check            ← fallback only
```

Preference for **shells**, conditional on the discovered OS:

| Target | Order |
|--------|-------|
| Linux / Unix | `bash` → `sh`; use `zsh`/`fish` only when the task needs their features |
| Windows | `pwsh` → `powershell.exe` → `cmd.exe` (never prefer `cmd` for real automation) |
| SSH | the **remote host's** shell capability, not the local host's assumption |
| Container | probe inside the container, build its own profile, then choose |

Then bind syntax to the selected shell — no mixing:

```bash
# bash
VAR=value command > file 2>&1 &
```

```powershell
# PowerShell
$env:VAR = "value"
Start-Process ...
```

Get these right per shell: quoting, environment variables, path separator, redirection,
backgrounding, PID / process handle, signal & stop semantics, command chaining.

---

## Step 4 — Launch, then verify survival

Reuse an existing mechanism first: native agent Job, scheduler, experiment runner, tmux/screen,
systemd, Slurm, Kubernetes, Docker/Podman. Only fall back to shell backgrounding when none of
those exist **and** a background process can stably survive.

POSIX pattern (adapt it to the selected shell — it is a shape, not a literal):

```bash
TASK_DIR="logs/jobs/<task_id>"
mkdir -p "$TASK_DIR"
export TASK_DIR          # so the child shell can see it

nohup bash -lc '<REAL_COMMAND>; rc=$?; echo "$rc" > "$TASK_DIR/exit_code"; exit "$rc"' \
  > "$TASK_DIR/task.log" 2>&1 < /dev/null &

echo $! > "$TASK_DIR/pid"
```

Quoting rules for this shape — both halves are load-bearing:

- `<REAL_COMMAND>` and `<TASK_DIR>/exit_code` are **placeholders**. Replace the whole
  `<...>` token with real text; never leave the angle brackets in.
- The command string is single-quoted, so `$TASK_DIR` inside it is expanded by the **child**
  shell, not the parent. Exporting `TASK_DIR` is what makes it resolvable there.
- Writing `$TASK_DIR` literally inside the single quotes fails: the child has no such variable.

Rules: do not rely on `disown`; verify immediately after launch that the job survives the
parent call returning; on Windows use the PowerShell equivalent (`Start-Process`, PowerShell
Job, Scheduled Task, or a job the platform owns); if the job dies with the exec/session, switch
to a real job manager. On SSH, confirm the remote process outlives the SSH call — if the remote
side reaps the process group or cgroup, `nohup … &` is not enough and you need tmux/screen,
systemd-run, Slurm, Docker, Kubernetes, or the platform scheduler.

---

## Step 5 — Record the real Job ID

Prefer the identifier the system actually gives you:

```text
Agent native → Task ID / Job Handle
Slurm        → Job ID
Kubernetes   → Pod / Job
Docker       → Container ID
systemd      → Unit
Linux        → PID
Windows      → Process ID / Job object
```

If a higher-level Job ID exists, do not depend on the PID alone.

---

## Step 6 — Baseline (round 0), before any long sleep

Capture: Job ID / PID, state, log bytes, log mtime, result artifacts, structured progress,
timestamp, and CPU/GPU activity when relevant.

Track log change by **bytes + mtime**, not `wc -l` — tqdm, stdout buffering, and long epochs
keep line counts flat while the job is healthy.

---

## Step 7 — Derive the wait window

`L` = hard per-call duration limit of the current executor. Never across environments reuse a
magic `60 / 120 / 240 / 600`. Derive it in this order: tool schema timeout parameter → tool
capability docs → explicit timeout info already in this session → environment config →
conservative estimate. **Never run a near-limit sleep to measure `L`.** If it cannot be
determined, enter `unknown-timeout mode` and use short conservative intervals.

```text
G     = max(5s, min(30s, L × 0.15))    # margin for shell, SSH, network, stat, tail, API
I_cap = L - G                          # max safe single wait
I0    = min(max(10s, L × 0.20), 60s, I_cap)     # no ETA
I0   ≈ 15–30s                                   # L unknown
```

Hard requirement: `sleep I < I_cap`. Never let a sleep sit flush against `L`.

`I_min` (the lower clamp in the table below) is `I0` unless the user set a tighter floor.

---

## Step 8 — Poll adaptively

State machine: `STARTING`, `RUNNING`, `PROGRESSING`, `QUIET`, `SUSPECTED_STALL`, `DONE`,
`FAILED`, `UNKNOWN_EXIT`.

Maintain `I` (current interval), `I0`, `I_cap`, `stale` (consecutive no-progress rounds).

| Condition | Action |
|-----------|--------|
| DONE (done marker, scheduler succeeded, `exit_code=0`, official success) | **stop polling** |
| FAILED (`exit_code≠0`, scheduler FAILED, failed marker) | **stop normal polling**, read last log, diagnose |
| Quantified progress + ETA | `rate = Δprogress/Δtime`; `ETA = remaining/rate`; `I_next ≈ ETA × 0.20–0.33`, clamped to `[I_min, I_cap]` |
| Clear progress, no reliable ETA | `stale = 0`; `I_next = min(I × 1.2, I_cap)` |
| One round no visible progress | `stale += 1`; `I_next = min(I × 1.5, I_cap)` — one round is **not** a stall |
| `stale >= 2` | `I_next = min(I × 2, I_cap)`; if resources are still busy, keep treating it as running |
| Progress resumes after backoff | `stale = 0`; `I_next = max(I0, I / 2)`; switch back to ETA mode if ETA returns |
| Ceiling | `I_max = I_cap`, or `min(I_cap, I_user_cap)` if the user capped it — **never** `I_max = I0` |

Progress signals, most to least reliable: structured progress (step/total, epoch/total, %, ETA)
→ official job status or result artifacts (done marker, checkpoint, result file) → log change
(bytes, mtime, tail) → resource activity (CPU, GPU, VRAM, disk IO, network IO) → process
liveness (PID/handle) as a supporting signal only.

Collect everything in **one round** — state, exit code, progress, log bytes, log mtime, log
tail, CPU/GPU activity, key artifacts — and emit `KEY=VALUE` lines so the next round parses
cleanly. Copy-ready probes: `references/polling-playbook.md`.

### Silence is not death

Long quiet stretches are normal for CUDA kernels, big epochs, compile/link, compression,
database work, network downloads, and model evaluation. A log unchanged for 5 minutes while
GPU util is 98% is a healthy job.

At `stale >= 3`, **diagnose before killing**: process state, CPU, GPU/VRAM, RAM, disk IO,
network, child processes, scheduler state. Resources still active → keep waiting. Mark
`SUSPECTED_STALL` only when, over a sustained window, there is no progress **and** CPU≈0, GPU≈0,
IO≈0, network≈0, and outputs are unchanged — then report it. **Never auto-kill an important
training, build, or remote job without user authorization.**

### Three confusions to avoid

- **PID gone ≠ failure.** Run one final diagnostic (exit marker, result artifact, scheduler
  history, log tail). If success cannot be proven, report "process disappeared with no reliable
  completion marker" as `UNKNOWN_EXIT` and stop normal polling.
- **Exec timeout ≠ job failure.** On a status-call timeout: re-check that the job still exists,
  shorten the per-round wait, correct `L`/`I_cap`, update the profile, continue. Never declare a
  training or build failed because the *status call* timed out.
- **Log unchanged ≠ stalled.** See above.

### Deadline

If the user set a total wait cap, honor `T_deadline` and report status when it is reached. If
they did not, do not impose a short total timeout on a legitimately long job.

---

## Step 9 — Log one short decision line per round

Keep it to one block so the strategy stays auditable without spamming:

```text
round=3 interval=45s state=RUNNING progress=epoch 18/50 log_bytes=381229 gpu_util=97% eta≈11m next_interval=60s reason=progressing
```

```text
round=6 interval=90s state=QUIET log_unchanged=2 rounds process_alive=yes gpu_util=95% next_interval=135s reason=job active but log quiet
```

---

## Step 10 — Remember, per session

Store the verified profile in, in priority order: native session/working/task memory → current
conversation context → a temp session state file
(`${XDG_RUNTIME_DIR:-/tmp}/adaptive-runtime-orchestrator/<session-id>.json`, or
`$env:TEMP\adaptive-runtime-orchestrator\<session-id>.json` on Windows) when context may be
compacted or truncated and temp writes are allowed. It is a **session cache, not project config**.

Invalidate and re-probe on: `command not found`, shell syntax error, executor unavailable,
timeout behavior visibly inconsistent with the cache, SSH target/hostname change, container/pod
change, OS change, tool list change, job backend change, background mechanism failure, or a
judgment that the profile is no longer trustworthy. Flow: `invalidate → Runtime Discovery →
update Session Memory`.

---

## Autonomy rule

If it can be safely discovered with the current tools, do **not** ask the user: Bash or
PowerShell, current OS, available shells, which exec tool fits, how big the timeout is, whether
to `nohup`, whether to use native background, whether to query over SSH, whether to use a
scheduler. `Detect → Decide → Execute → Remember`.

Ask only when: several genuinely different target hosts exist and the intent is ambiguous,
credentials are needed, the operation is irreversible, two options yield materially different
business/research outcomes, or the current tools cannot obtain the needed information.

Avoid: `Ask → Ask → Ask → Execute`.

---

## Hard rules

1. Never preset the shell — probe the environment and tool capabilities first.
2. Never pull `sleep 300/600/1800` out of thin air.
3. Prefer native async Job / Job Handle.
4. One Runtime Profile per execution target.
5. Reuse a verified profile within the session; don't fully re-probe every round.
6. Auto-invalidate and rebuild on environment change, tool error, or inconsistent behavior.
7. Session Memory caches capability only — never passwords, tokens, API keys, cookies, SSH
   private keys, credentials, or full secret env values. If probe output contains a secret, do
   not persist it.
8. Know or conservatively estimate the current executor's per-call limit.
9. `sleep` must be significantly below the tool's hard limit.
10. Reserve margin for shell, SSH, network, and status queries.
11. DONE → stop polling immediately.
12. FAILED → stop normal polling and diagnose.
13. PID gone ≠ failure.
14. Exec timeout ≠ background job failure.
15. Log unchanged ≠ stalled.
16. Active resources → treat silence as normal computation.
17. At sustained silence, diagnose before back off further; never back off unboundedly.
18. No unbounded interval growth.
19. No unbounded high-frequency polling.
20. With ETA, use ETA; without ETA, use multiplicative backoff.
21. On resumed progress, actively shrink the interval.
22. Never auto-kill an important long task without authorization.
23. Never overwrite logs, checkpoints, results, or raw data.
24. Never let the polling mechanism change the task's correctness.
25. Re-confirm the target-level Runtime Profile on every new execution target.

---

## Reference files (read ONLY what you need)

- `references/runtime-discovery.md` — per-platform probe commands, target-type detection, and
  the WSL / container / SSH boundary rules. Read when entering a new or unfamiliar target.
- `references/profile-schema.md` — the full profile field set, worked JSON example, per-target
  isolation, invalidation triggers, and the sensitive-data allow/deny list. Read when creating,
  persisting, or invalidating a profile.
- `references/executor-selection.md` — executor candidate scoring, the 7-tier preference order,
  Windows/PowerShell mechanisms, scheduler and Job-ID mapping. Read when choosing how to launch.
- `references/polling-playbook.md` — timeout derivation, the dynamic algorithm with all numeric
  factors, stall diagnosis, decision-log format, and copy-ready one-shot `KEY=VALUE` probes.
  Read while the job is running.
