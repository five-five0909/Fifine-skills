# Runtime Discovery

Read this when entering a new or unfamiliar execution target. Goal: learn what the target
actually is, using cheap short commands, before generating any real command.

---

## 1. The four environments, kept separate

```text
Agent environment        where the agent process/harness runs
User machine             where the human sits
Command execution env    where a single command is executed
Background job env       where a detached job actually keeps running
```

These are frequently different. A WSL session has a Linux side and a Windows host side. An SSH
call executes remotely but may be launched locally. A container exec enters a new filesystem and
process namespace. Always re-probe the environment that will actually run the command.

---

## 2. Target type detection

Cheap signals, in the order worth trying:

| Signal | Suggests |
|--------|----------|
| `/proc/version` or `uname -r` contains `microsoft` / `WSL` | WSL guest |
| `/.dockerenv` exists, or `/proc/1/cgroup` mentions `docker`/`containerd` | container |
| `KUBERNETES_SERVICE_HOST` set, or `/var/run/secrets/kubernetes.io` exists | Kubernetes pod |
| `SLURM_JOB_ID` set, or `sinfo` / `sbatch` on PATH | Slurm node/job |
| `SSH_CONNECTION` / `SSH_CLIENT` set | reached over SSH |
| `systemd-detect-virt` returns non-`none` | VM or container |
| `$env:OS` = `Windows_NT`, or `$PSVersionTable` populated | Windows host |
| `uname -s` = `Darwin` | macOS |

Record the result as `target_type`, and let it drive shell and executor choice — never let the
agent's own platform stand in for it.

---

## 3. POSIX / Unix-like probes

One combined probe is cheaper and more reliable than five calls:

```bash
uname -s; uname -m; printf '%s\n' "${SHELL:-unknown}"; \
command -v bash || true; command -v sh || true; command -v zsh || true; \
cat /etc/os-release 2>/dev/null || true
```

Then, only if backgrounding matters:

```bash
command -v nohup setsid tmux screen systemd-run sbatch srun 2>/dev/null || true
```

Notes:

- `os` from `/etc/os-release` (`ID`), `os_version` from `VERSION_ID`.
- `available_shells` comes from the `command -v` results, not from assumption.
- Missing `/etc/os-release` does not mean failure — fall back to `uname -s`.

---

## 4. Windows / PowerShell probes

```powershell
$PSVersionTable.PSVersion.ToString()
$env:OS
[System.Environment]::OSVersion.VersionString
(Get-Command pwsh -ErrorAction SilentlyContinue).Source
(Get-Command powershell -ErrorAction SilentlyContinue).Source
(Get-Command cmd -ErrorAction SilentlyContinue).Source
```

Then, only if backgrounding matters:

```powershell
(Get-Command schtasks -ErrorAction SilentlyContinue).Source
(Get-Command wsl -ErrorAction SilentlyContinue).Source
```

Detection order for the shell is `pwsh` → `powershell.exe` → `cmd.exe`. Do not prefer `cmd.exe`
for anything beyond trivial invocation — its quoting and error semantics make real automation
fragile.

---

## 5. WSL boundary rules

WSL is one machine with two execution sides. Decide which side owns the task, then probe **that**
side:

| Task involves | Use |
|---------------|-----|
| Linux Python, CUDA, Linux files, Linux tooling | Bash on the Linux side |
| Windows services, registry, Windows networking, Windows processes | `pwsh` / `powershell.exe` on the Windows host |

Record `is_wsl = true` and record `execution_scope` as `wsl-linux` or `wsl-host` so later rounds
do not silently cross the boundary. Crossing sides invalidates the profile — a Linux-side Bash
profile says nothing about the Windows host's PowerShell.

---

## 6. SSH / container boundary rules

OS and shell must be re-probed **inside** the remote host or container that will run the command.
The local host's shells, paths, and timeout are irrelevant there — and frequently different.

- SSH target: probe over the same channel you will use to launch, since the remote shell may be
  non-interactive and skip profile scripts that set `PATH` or `SHELL`.
- Container: enter it, then build a profile scoped to that container. Rebuilding the image,
  restarting the pod, or exec'ing a different container invalidates it.
- Kubernetes pod: treat the pod as the target, not the node. A pod restart produces a new target.
- Custom exec proxy / MCP remote executor: the innermost executor in the chain usually determines
  the real timeout, not the outer tool. Probe at the innermost layer you can reach.

---

## 7. Confirming the target after the fact

Before relying on a profile, one cheap consistency check is enough:

```bash
hostname; uname -s; command -v bash
```

Compare against the cached `hostname`, `os`, and `shell_path`. Any mismatch triggers the
invalidation flow in `profile-schema.md`.
