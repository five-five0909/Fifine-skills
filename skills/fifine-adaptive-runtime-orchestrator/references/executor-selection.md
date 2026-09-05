# Executor Selection

Read this when deciding how to launch a job. The shell choice comes *after* the executor choice —
picking a shell first is how agents end up with `nohup` inside a pod that reaps process groups.

---

## 1. Discover executors, do not guess from the product name

Inspect the tools actually exposed in this session and look for these capabilities:

```text
shell / bash / terminal / exec / command runner
PowerShell / pwsh
SSH / remote exec
container exec
background task / async task
job handle / process handle
incremental output
wait / poll / task status
scheduler
```

Never derive capabilities from a product name. The same harness name can expose a background job
API in one version and not in another, and a call chain through SSH, MCP, a remote executor, or a
custom proxy means the **innermost** executor determines the real behavior and timeout. Re-verify
capabilities at each new execution target.

Also remember the four environments stay separate: agent environment ≠ user's machine ≠ command
execution environment ≠ where the background job actually runs.

---

## 2. Candidate set

```text
native_async_job    harness-native background job with a handle
native_exec         harness-native synchronous exec
shell_exec          bash / sh / zsh
powershell_exec     pwsh / powershell
ssh_exec            remote exec over SSH
container_exec      docker / podman / kubectl exec
scheduler_exec      slurm / k8s job / systemd / scheduled task
```

Several can coexist on one target. Score them; do not take the first one found.

---

## 3. Scoring inputs

Weight by what actually matters for a long job:

| Factor | Why it matters |
|--------|----------------|
| Provides a Job Handle | Enables independent status queries and clean stop |
| Status independently queryable | Lets polling survive across calls |
| Incremental output | Cheap progress without polling files |
| Reliable timeout | Needed to derive `L`, `G`, `I_cap` |
| Job survives the parent call | Otherwise the "background" job dies with the call |
| Reliable exit code | Needed to distinguish DONE from FAILED |
| Actually matches the target | A local shell cannot run a pod's work |
| Quoting / cross-platform complexity | Fewer escape layers means fewer silent corruptions |
| Reuses an existing project runner | Less new machinery, more likely to be supported |

---

## 4. Preference order

```text
1. Native async/background Job + Job Handle
2. Native exec + independent poll / incremental output
3. Scheduler Job (Slurm / K8s / systemd / Scheduled Task)
4. SSH/Remote Job + independent status query
5. Shell background + independent status query
6. nohup + PID + status file
7. sleep + check            ← fallback only, never a default
```

`sleep + check` at tier 7 exists for when nothing else is available. Reaching for it first
because it is familiar is the failure mode this skill exists to prevent.

---

## 5. Reuse before inventing

Before launching anything, check whether the target already owns a mechanism:

- harness-native Job
- scheduler (`sbatch`, `kubectl`, `systemd-run`, `schtasks`)
- project experiment runner or launch script already in the repo
- tmux / screen
- Slurm / Kubernetes
- Docker / Podman

Only fall back to shell backgrounding when none of these exist **and** a background process can
stably survive the parent call.

---

## 6. Launch patterns

### POSIX shell background (tier 5–6)

```bash
TASK_DIR="logs/jobs/<task_id>"
mkdir -p "$TASK_DIR"
export TASK_DIR          # the child shell expands it, so it must be exported

nohup bash -lc '<REAL_COMMAND>; rc=$?; echo "$rc" > "$TASK_DIR/exit_code"; exit "$rc"' \
  > "$TASK_DIR/task.log" 2>&1 < /dev/null &

echo $! > "$TASK_DIR/pid"
```

This is a **shape, not a literal** — regenerate it for the selected shell. Rules:

- `<REAL_COMMAND>` and `<task_id>` are placeholders; substitute real text, angle brackets
  included. The command string is single-quoted, so `$TASK_DIR` is expanded by the child shell —
  which is why it is exported. Writing `$TASK_DIR` inside the single quotes without exporting it
  makes the exit-code redirect fail with `No such file or directory`.

- Do not rely on `disown`; it is not portable and not sufficient.
- Redirect stdin from `/dev/null` so the job never blocks on a read.
- Write the exit code to a file; a PID alone cannot tell you success from failure.
- Verify immediately that the job survives the parent call returning.
- If the job dies with the exec/session, move up a tier — a real job manager, not a longer `nohup`.

### Windows / PowerShell

Do not mechanically translate Unix commands. Choose by what must survive:

| Need | Mechanism |
|------|-----------|
| Job handle, pollable | harness-native Job, or PowerShell Job |
| Detached process | `Start-Process` |
| Survives logoff/reboot | Scheduled Task, or Windows Service |
| Linux-side work under WSL | a WSL-side task on the Linux side |

Ask first: **after the parent PowerShell exits, must the task still run?** If yes, pick a
mechanism that genuinely detaches — otherwise choose a WSL-side task or the platform scheduler.

### SSH

Distinguish the SSH session lifecycle from the remote process lifecycle. After launching,
confirm the remote job still exists once the SSH call has returned. If the remote side reaps the
process group or cgroup, `nohup … &` is not enough; use tmux, screen, `systemd-run`, Slurm,
Docker, Kubernetes, or the platform scheduler.

### Scheduler

When a scheduler exists, prefer it over shell backgrounding even if backgrounding works — it
gives you a durable Job ID, its own status query, and usually its own log capture.

---

## 7. Job identity mapping

Record the identifier the system actually provides, in preference order:

```text
Agent native → Task ID / Job Handle
Slurm        → Job ID
Kubernetes   → Pod / Job name
Docker       → Container ID
systemd      → Unit name
Linux        → PID
Windows      → Process ID / Job object
```

When a higher-level Job ID exists, do not depend on the PID alone. A wrapper PID can exit while
the real work continues under the scheduler, which reads as `UNKNOWN_EXIT` if only the PID was
tracked.

---

## 8. Shell binding, after the executor is chosen

| Target | Shell order |
|--------|-------------|
| Linux / Unix | `bash` → `sh`; `zsh`/`fish` only when the task needs their features |
| Windows | `pwsh` → `powershell.exe` → `cmd.exe` |
| SSH | the remote host's shells, probed remotely |
| Container | shells probed inside the container |

Bind syntax to the selected shell — never mix:

```bash
VAR=value command > file 2>&1 &
```

```powershell
$env:VAR = "value"
Start-Process ...
```

Get right per shell: quoting, environment variables, path separator, redirection, backgrounding,
PID / process handle, signal and stop semantics, command chaining.
