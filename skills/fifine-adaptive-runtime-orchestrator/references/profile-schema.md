# Runtime Capability Profile Schema

Read this when creating, persisting, or invalidating a profile.

---

## 1. Fields

This is a logical model. Keep only the fields the current agent can actually determine; unknown
values stay `null` rather than being guessed.

| Field | Meaning |
|-------|---------|
| `target_id` | Stable short identifier for this execution target (`local`, `remote-gpu-01`, `training-pod`) |
| `target_type` | `local-linux` / `local-windows` / `local-macos` / `wsl` / `container` / `ssh-remote` / `k8s-pod` / `slurm-node` / `sandbox` / `vm` / `unknown` |
| `hostname` | Non-sensitive host name, used as the cheap consistency check |
| `os` | `ubuntu` / `debian` / `windows` / `darwin` / … |
| `os_version` | Version string, when cheap to obtain |
| `architecture` | `x86_64` / `arm64` / … |
| `executor` | Concrete executor actually chosen (`ssh-exec`, `native-bash`, `pwsh`, …) |
| `executor_type` | Class of that executor (`native_async_job` / `shell_exec` / `ssh_exec` / `container_exec` / `scheduler_exec` / …) |
| `preferred_executor` | Best-scoring candidate for this target |
| `shell` | Selected shell (`bash` / `sh` / `zsh` / `pwsh` / `powershell` / `cmd`) |
| `shell_path` | Absolute path to the selected shell |
| `shell_version` | Version string, when cheap to obtain |
| `available_shells` | Shells actually found by probing |
| `preferred_shell` | Best shell by the selection order, if different from `shell` |
| `supports_background` | Process can be launched and outlive the call |
| `supports_async_job` | Executor has a native async/background job API |
| `supports_job_handle` | Executor returns a handle/ID usable in later calls |
| `supports_incremental_output` | Partial output is retrievable while running |
| `supports_independent_poll` | Status can be queried from a separate call |
| `supports_timeout` | Caller can set or observe a per-call timeout |
| `supports_scheduler` | A scheduler is reachable (`sbatch`, `kubectl`, `systemd-run`, `schtasks`) |
| `timeout_limit_sec` | Observed/derived hard per-call limit `L` |
| `safe_timeout_limit_sec` | Working limit after margin (`I_cap`) |
| `is_remote` | Commands run somewhere other than the agent |
| `is_container` | Target is a container or pod |
| `is_wsl` | Target is a WSL guest |
| `execution_scope` | Which side/scope owns execution (`wsl-linux`, `wsl-host`, `container:<name>`, …) |
| `last_verified` | When the profile was last confirmed |
| `profile_version` | Schema version, so old caches can be discarded on shape change |

---

## 2. Worked example

```json
{
  "target_id": "remote-gpu-01",
  "target_type": "ssh-remote",
  "hostname": "gpu01",
  "os": "ubuntu",
  "os_version": "22.04",
  "architecture": "x86_64",
  "executor": "ssh-exec",
  "executor_type": "ssh_exec",
  "preferred_executor": "ssh-exec",
  "shell": "bash",
  "shell_path": "/usr/bin/bash",
  "shell_version": "5.1.16",
  "available_shells": ["bash", "sh"],
  "preferred_shell": "bash",
  "supports_background": true,
  "supports_async_job": false,
  "supports_job_handle": false,
  "supports_incremental_output": true,
  "supports_independent_poll": true,
  "supports_timeout": true,
  "supports_scheduler": true,
  "timeout_limit_sec": 240,
  "safe_timeout_limit_sec": 200,
  "is_remote": true,
  "is_container": false,
  "is_wsl": false,
  "execution_scope": "ssh-remote",
  "last_verified": "2026-09-05T10:12:00Z",
  "profile_version": 1
}
```

---

## 3. Per-target isolation

A single session may hold several profiles simultaneously. Key them by `target_id` and keep them
independent:

```text
local-windows
wsl-ubuntu
remote-gpu-server
docker-training-container
slurm-cluster
```

Never carry capabilities across targets:

- local Windows PowerShell capabilities → remote Ubuntu
- host Bash capabilities → container inside that host
- one SSH target's timeout → another SSH target
- WSL Linux-side profile → Windows host side

Each of these is a separate profile even when the physical machine is shared. Reusing across them
is the single most common source of "the same command worked before" failures.

---

## 4. Session Memory storage

Priority order:

1. **Native session / working / task memory** — if the current agent exposes one, use it.
2. **Current conversation context** — when there is no separate memory API, keep the profile in
   the conversation.
3. **Temporary session state file** — only when context may be compacted, truncated, or
   restarted, and writing a temp file is acceptable:

   POSIX: `${XDG_RUNTIME_DIR:-/tmp}/adaptive-runtime-orchestrator/<session-id>.json`
   Windows: `$env:TEMP\adaptive-runtime-orchestrator\<session-id>.json`

This is a **session cache**, not project configuration. Do not commit it, do not write it into
the repository, and do not treat it as durable truth.

---

## 5. Cache semantics

Everything below can change mid-session: shell, executor, timeout, SSH target, container/pod,
tool capability, job backend, hostname, OS.

Therefore:

- Reuse the profile for subsequent tasks on the same target.
- Run a **light consistency check** before reuse (hostname, OS, shell path, one cheap command).
- Do not re-run full discovery every round — that wastes calls and latency.
- Do not trust a stale cache indefinitely — the light check is what makes reuse safe.

---

## 6. Invalidation

Invalidate immediately on any of:

- `command not found`
- shell syntax error
- executor unavailable
- timeout behavior visibly inconsistent with the cache
- SSH target or hostname changed
- container / pod changed
- OS changed
- current tool list changed
- job backend changed
- background mechanism failed
- agent judgment that the profile is no longer trustworthy

Flow:

```text
invalidate profile
  → Runtime Discovery
  → update Session Memory
```

---

## 7. Sensitive data

**Allowed to persist:**

- OS, OS version, architecture
- shell, shell path, shell version, available shells
- executor type and capabilities
- timeout values
- target type, target id, execution scope
- non-sensitive hostname
- job and tool capability flags

**Never persist:**

- passwords
- API keys
- access tokens
- cookies
- SSH private keys
- credentials of any kind
- full values of secret environment variables

If a probe output contains a secret, do not write it to Session Memory. Record only the
non-sensitive conclusion the probe was meant to establish (for example, "credential present and
accepted"), never the credential itself. Truncate log tails before persisting when there is any
chance they echo secrets.
