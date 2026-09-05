# Polling Playbook

Read this while a job is running. It carries the formulas, the full algorithm with numeric
factors, stall diagnosis, the decision-log format, and copy-ready probes.

---

## 1. Duration limit `L`

`L` = hard per-call duration limit of the current executor.

Derive it in this order:

1. Current tool schema / explicit timeout parameter
2. Current tool capability description
3. Explicit timeout information already present in this session
4. Environment configuration
5. Conservative estimate

Never reuse a fixed cross-environment value (`60 / 120 / 240 / 600`). **Never run a near-limit
sleep just to measure `L`** — the cost of tripping the limit is losing the call and possibly the
job handle.

If `L` cannot be determined: enter `unknown-timeout mode` and use short conservative intervals.

## 2. Wait window

```text
G     = max(5s, min(30s, L × 0.15))     # margin: shell, SSH, network, stat, tail, API return
I_cap = L - G                           # max safe single-round wait
I0    = min(max(10s, L × 0.20), 60s, I_cap)     # no ETA available
I0   ≈ 15–30s                                   # L unknown
```

Hard requirement: **`sleep I < I_cap`**, always. A sleep sitting flush against `L` turns a slow
network round-trip into a lost call.

`I_min` — the lower clamp used by the algorithm below — is the shortest interval worth using.
Take it as `I0` unless the user explicitly asked for a tighter floor; polling faster than `G` is
pointless anyway, since `G` is the cost of the status query itself.

---

## 3. Baseline (round 0), before any long sleep

Capture in one shot: Job ID / PID, state, log bytes, log mtime, result artifacts, structured
progress, timestamp, and CPU/GPU activity when relevant.

Track log change by **bytes + mtime**, never `wc -l` alone. tqdm progress bars, stdout buffering,
and long epochs all keep line counts flat while the job is perfectly healthy.

---

## 4. One round, one call

Do not fan out into `ps`, `tail`, `stat`, `wc`, `test` as separate calls. Collect everything in a
single command and emit `KEY=VALUE` so the next round parses cleanly.

POSIX template — adapt to the selected shell and the real log/artifact paths:

```bash
DIR="logs/jobs/<task_id>"
PID=$(cat "$DIR/pid" 2>/dev/null || echo none)
LOG="$DIR/task.log"
GLOB='<result-glob>'          # e.g. 'results/*.bin' — must be quoted, never `<...>` inline
NOW=$(date +%s)

echo "JOB_ID=$PID"
if [ -f "$DIR/exit_code" ]; then echo "EXIT_CODE=$(cat "$DIR/exit_code")"; else echo "EXIT_CODE=none"; fi
if [ -f "$DIR/done" ]; then echo "DONE_MARKER=yes"; else echo "DONE_MARKER=no"; fi
kill -0 "$PID" 2>/dev/null && echo "ALIVE=yes" || echo "ALIVE=no"
STAT=$(stat -c '%s %Y' "$LOG" 2>/dev/null || echo "0 0")
echo "LOG_BYTES=$(echo "$STAT" | cut -d' ' -f1)"
echo "LOG_MTIME=$(echo "$STAT" | cut -d' ' -f2)"
echo "NOW=$NOW"
echo "AGE_SEC=$(( NOW - $(echo "$STAT" | cut -d' ' -f2) ))"
echo "TAIL_BEGIN"
tail -n 5 "$LOG" 2>/dev/null
echo "TAIL_END"
echo "ARTIFACT_COUNT=$(ls -1 $GLOB 2>/dev/null | wc -l)"
command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | sed 's/^/GPU=/'
```

Notes on the parts that silently bite:

- `GLOB` must be a quoted variable. Writing `ls -1 <result-glob>` literally is a **shell syntax
  error** (`<` is a redirect operator), and it aborts the whole probe round.
- `stat -c` is GNU. On BSD/macOS use `stat -f '%z %m'`; do not assume one form everywhere.
- `AGE_SEC` is `now - log_mtime`, so it is "seconds since the log last changed", not job age.

PowerShell template:

```powershell
$dir  = "logs/jobs/<task_id>"
$glob = '<result-glob>'          # e.g. 'results\*.bin' — replace the placeholder, brackets included
$log  = Join-Path $dir "task.log"
$now  = [int64](Get-Date -UtcNow -UnixTimeSeconds)

"JOB_ID=" + (Get-Content (Join-Path $dir "pid") -ErrorAction SilentlyContinue)
"EXIT_CODE=" + (Get-Content (Join-Path $dir "exit_code") -ErrorAction SilentlyContinue)
"DONE_MARKER=" + [int](Test-Path (Join-Path $dir "done"))
if (Test-Path $log) {
  $item = Get-Item $log
  "LOG_BYTES=" + $item.Length
  "LOG_MTIME=" + [int64]($item.LastWriteTimeUtc - (Get-Date "1970-01-01Z")).TotalSeconds
  "AGE_SEC=" + ($now - [int64]($item.LastWriteTimeUtc - (Get-Date "1970-01-01Z")).TotalSeconds)
  "TAIL_BEGIN"
  Get-Content $log -Tail 5
  "TAIL_END"
}
"ARTIFACT_COUNT=" + (Get-ChildItem -Path $glob -ErrorAction SilentlyContinue).Count
$p = Get-Process -Id (Get-Content (Join-Path $dir "pid") -ErrorAction SilentlyContinue) -ErrorAction SilentlyContinue
"ALIVE=" + [int][bool]$p
if ($p) { "CPU_SEC=" + $p.CPU }
```

PowerShell-specific gotchas:

- `Get-Date "1970-01-01"` parses as **local** midnight. Subtracting it from a UTC `LastWriteTime`
  skews the epoch by the machine's UTC offset (e.g. +8h on UTC+8), so `LOG_MTIME` and `AGE_SEC`
  come out wrong. Use the `Z` suffix (`"1970-01-01Z"`) to force a UTC instant.
- `-UnixTimeSeconds` and `-UtcNow` need **PowerShell 7+** (`pwsh`). On Windows PowerShell 5.1,
  compute the epoch as `[int64]((Get-Date).ToUniversalTime() - (Get-Date "1970-01-01Z")).TotalSeconds`.
- `Get-ChildItem <result-glob>` is a parse error — pass the pattern as a variable.
- `(...).Count` returns `0` when the collection is empty and `$null` when nothing matched at all;
  treat `$null` as "no match", not as zero.

Scheduler equivalents are usually cheaper and more authoritative than file probes — prefer
`squeue -j <id>`, `kubectl get job <id>`, `systemctl is-active <unit>`, or the harness's own job
status call when one exists.

---

## 5. Progress signal reliability

Highest to lowest:

1. **Structured progress** — step/total, epoch/total, percentage, ETA
2. **Official job status / result artifacts** — done marker, checkpoint, result file, scheduler
   progress
3. **Log change** — bytes, mtime, tail
4. **Resource activity** — CPU, GPU, VRAM, disk IO, network IO
5. **Process liveness** — PID / process handle, supporting signal only

Signal 5 alone proves almost nothing: a live PID can be wedged, and a dead wrapper PID can mean
the work finished under a scheduler.

---

## 6. State machine

```text
STARTING → RUNNING → PROGRESSING | QUIET → SUSPECTED_STALL
                                          → DONE | FAILED | UNKNOWN_EXIT
```

- **DONE** — done marker, scheduler success, `exit_code=0`, or official success. **Stop polling
  immediately.**
- **FAILED** — `exit_code≠0`, scheduler `FAILED`, or failed marker. **Stop normal polling**, read
  the last log, diagnose.
- **UNKNOWN_EXIT** — job/PID gone with no clear success or failure. Run one final diagnostic:
  exit marker, result artifact, scheduler history, log tail. If success still cannot be proven,
  report "process disappeared with no reliable completion marker" and stop normal polling.

---

## 7. Dynamic algorithm

State: `I` (current interval), `I0` (initial), `I_cap` (ceiling), `stale` (consecutive
no-progress rounds).

| Case | Rule |
|------|------|
| **A. DONE** | stop polling |
| **B. FAILED** | stop normal polling; diagnose |
| **C. Quantified progress + ETA** | From ≥2 observations: `rate = Δprogress / Δtime`, `ETA = remaining / rate`, `I_next ≈ ETA × 0.20–0.33`, clamped to `[I_min, I_cap]`. Poll more often as completion approaches. |
| **D. Clear progress, no reliable ETA** | `stale = 0`; `I_next = min(I × 1.2, I_cap)` |
| **E. One round no visible progress** | `stale += 1`; `I_next = min(I × 1.5, I_cap)`. One round is **not** a stall. |
| **F. `stale >= 2`** | `I_next = min(I × 2, I_cap)`. If resources are still clearly busy, keep treating it as running. |
| **G. Progress resumes after backoff** | `stale = 0`; `I_next = max(I0, I / 2)`; return to ETA mode if an ETA reappears |
| **H. Ceiling** | `I_max = I_cap`, or `min(I_cap, I_user_cap)` if the user capped it. **Never `I_max = I0`.** |

Case G matters: having backed off once is no reason to keep a long interval while a job is
closing in on completion.

If the job provides its own ETA, use it from the start rather than deriving one.

---

## 8. Stall diagnosis

Silence is normal for: CUDA kernels, large epochs, compile and link, large-file compression,
database operations, network downloads, model evaluation.

A log unchanged for 5 minutes with `GPU util = 98%` is a healthy job — do not call it stalled.

At `stale >= 3`, **do not auto-kill**. Diagnose first:

```text
process state        child processes
CPU                  GPU / VRAM
RAM                  disk IO
network IO           scheduler state
```

Resources still active → keep waiting. Mark `SUSPECTED_STALL` only when, sustained over several
rounds, all of the following hold: no progress, CPU≈0, GPU≈0, IO≈0, network≈0, outputs unchanged.
Then **report** it. Never kill an important training, build, or remote job without user
authorization.

---

## 9. Exec timeout ≠ job failure

When the *status call* times out, the job is usually fine. Do:

1. Re-check that the background job still exists
2. Shorten the per-round wait
3. Correct `L` / `I_cap`
4. Update the Runtime Profile
5. Continue checking the job

Never announce a training or build failure because the status call timed out.

---

## 10. Deadline

If the user set a total wait cap, define `T_deadline`; when reached, stop actively waiting and
report current status. If the user set none, do not invent a short total timeout for a
legitimately long job.

---

## 11. Decision log

One short block per round. Auditable, not spammy:

```text
round=3 interval=45s state=RUNNING progress=epoch 18/50 log_bytes=381229 gpu_util=97% eta≈11m next_interval=60s reason=progressing
```

```text
round=6 interval=90s state=QUIET log_unchanged=2 rounds process_alive=yes gpu_util=95% next_interval=135s reason=job active but log quiet
```

```text
round=9 interval=135s state=SUSPECTED_STALL cpu=0% gpu=0% io=0 log_unchanged=4 rounds next_interval=action reason=reporting to user, not killing
```

Never overwrite logs, checkpoints, results, or raw data while polling, and never let the polling
mechanism alter the task's own behavior or correctness.
