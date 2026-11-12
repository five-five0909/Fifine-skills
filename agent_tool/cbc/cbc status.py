#!/usr/bin/env python3
"""CodeBuddy Code status line.

从 stdin 读取 CodeBuddy 的 statusLine JSON，输出模型、上下文、工作区、
Git、MCP、Skill、token、待办和后台任务状态。所有外部数据均容错处理；
状态栏本身不应因为配置文件、转录或 Git 异常而退出。
"""

import glob
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RESET = "\033[0m"
GRAY = "\033[97m"
CYAN = "\033[38;5;117m"
PURPLE = "\033[1;38;5;183m"
BOLD_CYAN = "\033[1;38;5;117m"
GREEN = "\033[38;5;114m"
YELLOW = "\033[38;5;221m"
RED = "\033[38;5;203m"

BAR_CELLS = 12
TAIL_BYTES = 512 * 1024
USAGE_FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def paint(value, color=CYAN):
    return f"{color}{value}{RESET}"


def nonnegative_int(value):
    return value if type(value) is int and value >= 0 else None


def nonnegative_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if value >= 0 and math.isfinite(value) else None


def compact(value):
    if value is None:
        return "-"
    if value < 1_000:
        return str(value)
    if value < 1_000_000:
        text = f"{value / 1_000:.1f}k"
    else:
        text = f"{value / 1_000_000:.1f}M"
    return text.replace(".0k", "k").replace(".0M", "M")


def duration(seconds):
    if seconds is None:
        return "-"
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m{seconds:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m"


def read_json(file):
    try:
        value = json.loads(Path(file).read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeError, ValueError):
        return {}


# --- Token usage -----------------------------------------------------------

def transcript_lines(transcript_path):
    """只读长转录尾部；尾部没有 usage 时才退回整文件。"""
    if not transcript_path:
        return []
    path = Path(transcript_path)
    try:
        size = path.stat().st_size
        if size <= TAIL_BYTES:
            return path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        with path.open("rb") as handle:
            handle.seek(size - TAIL_BYTES)
            tail = handle.read().decode("utf-8", "replace")
    except OSError:
        return []
    lines = tail.partition("\n")[2].splitlines()
    if any(_line_has_usage(line) for line in lines):
        return lines
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return lines


def _line_has_usage(line):
    try:
        record = json.loads(line)
        return bool(isinstance(record, dict) and (record.get("providerData") or {}).get("usage"))
    except (ValueError, AttributeError):
        return False


def latest_usage(transcript_path):
    """兼容 OpenAI 与 Anthropic 风格的缓存 token 字段。"""
    for line in reversed(transcript_lines(transcript_path)):
        try:
            record = json.loads(line)
            provider = record.get("providerData") or {}
            usage = provider.get("usage") or {}
        except (ValueError, AttributeError):
            continue
        input_tokens = nonnegative_int(usage.get("inputTokens"))
        if input_tokens is None:
            continue
        details = usage.get("inputTokensDetails") or {}
        if isinstance(details, list):
            details = next((item for item in details if isinstance(item, dict)), {})
        if not isinstance(details, dict):
            details = {}
        raw = provider.get("rawUsage") or {}
        if not isinstance(raw, dict):
            raw = {}
        raw_details = raw.get("prompt_tokens_details") or {}
        if not isinstance(raw_details, dict):
            raw_details = {}
        cache_read = next(
            (
                value
                for value in (
                    nonnegative_int(details.get("cached_tokens")),
                    nonnegative_int(raw.get("cache_read_input_tokens")),
                    nonnegative_int(raw.get("prompt_cache_hit_tokens")),
                    nonnegative_int(raw_details.get("cached_tokens")),
                )
                if value is not None
            ),
            0,
        )
        cache_write = next(
            (
                value
                for value in (
                    nonnegative_int(raw.get("cache_creation_input_tokens")),
                    nonnegative_int(raw.get("prompt_cache_write_tokens")),
                )
                if value is not None
            ),
            0,
        )
        # CodeBuddy 的 inputTokens 是总输入；三个展示字段必须互不重叠。
        return {
            "input_tokens": max(0, input_tokens - cache_read - cache_write),
            "cache_creation_input_tokens": cache_write,
            "cache_read_input_tokens": cache_read,
            "output_tokens": nonnegative_int(usage.get("outputTokens")),
        }
    return {}


def model_config(config_dir, settings, model_id):
    candidates = [model_id, settings.get("model")]
    candidates += [item.split(":", 1)[1] for item in candidates if isinstance(item, str) and ":" in item]
    for model in read_json(config_dir / "models.json").get("models") or []:
        if isinstance(model, dict) and model.get("id") in candidates:
            return model
    return {}


# --- Workspace -------------------------------------------------------------

def git_status(cwd):
    """一次无可选锁的 Git 调用获取分支和脏状态。"""
    if not cwd or not Path(cwd).is_dir():
        return None
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "status", "--porcelain=v2", "--branch"],
            capture_output=True,
            text=True,
            timeout=1.5,
            check=False,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = result.stdout or ""
    if result.returncode != 0 or "# branch.head" not in output:
        return None
    branch = "?"
    oid = ""
    dirty = False
    for line in output.splitlines():
        if line.startswith("# branch.head "):
            branch = line.removeprefix("# branch.head ").strip()
        elif line.startswith("# branch.oid "):
            oid = line.removeprefix("# branch.oid ").strip()
        elif line and not line.startswith("#"):
            dirty = True
    if branch == "(detached)":
        branch = "detached@" + (oid[:7] if oid and oid != "(initial)" else "?")
    return branch + ("*" if dirty else "")


def count_mcp(project_dir, config_dir):
    names = set()
    files = [config_dir / "mcp.json"]
    if project_dir:
        files += [project_dir / ".mcp.json", project_dir / ".codebuddy" / "mcp.json"]
    for file in files:
        servers = read_json(file).get("mcpServers")
        if isinstance(servers, dict):
            names.update(servers)
    return len(names)


def skill_files(root):
    if not root or not root.is_dir():
        return set()
    found = set()
    try:
        for dirpath, _, filenames in os.walk(root, followlinks=True):
            if "SKILL.md" in filenames:
                found.add(os.path.realpath(os.path.join(dirpath, "SKILL.md")).casefold())
    except OSError:
        pass
    return found


def count_skills(project_dir, config_dir, settings):
    found = skill_files(config_dir / "skills")
    if project_dir:
        for folder in (".codebuddy", ".claude", ".codex", ".agents"):
            found |= skill_files(project_dir / folder / "skills")
    plugins = settings.get("enabledPlugins") or {}
    if isinstance(plugins, dict):
        for plugin_id, enabled in plugins.items():
            if not enabled or not isinstance(plugin_id, str) or "@" not in plugin_id:
                continue
            plugin, publisher = plugin_id.rsplit("@", 1)
            found |= skill_files(config_dir / "plugins" / "cache" / publisher / plugin)
    return len(found)


def todo_progress(config_dir, session_id):
    session_dir = config_dir / "tasks" / str(session_id or "")
    if not session_id or not session_dir.is_dir():
        return 0, 0
    done = total = 0
    try:
        files = session_dir.glob("*.json")
        for file in files:
            item = read_json(file)
            if "status" not in item:
                continue
            total += 1
            done += item.get("status") == "completed"
    except OSError:
        pass
    return done, total


# --- Background tasks ------------------------------------------------------

def proc_elapsed(pid, uptime):
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        fields = stat[stat.rindex(")") + 2 :].split()
        started = int(fields[19]) / os.sysconf("SC_CLK_TCK")
        return max(0.0, uptime - started)
    except (OSError, ValueError, IndexError):
        return None


def background_tasks(session_id):
    if not session_id or not os.path.isdir("/proc"):
        return 0, None
    root = os.path.join(tempfile.gettempdir(), f"codebuddy-{os.getuid()}")
    logs = set()
    for folder in glob.glob(os.path.join(root, "*", str(session_id), "bg-tasks")):
        try:
            logs.update(
                os.path.realpath(os.path.join(folder, name))
                for name in os.listdir(folder)
                if name.endswith(".stdout.log")
            )
        except OSError:
            continue
    if not logs:
        return 0, None
    try:
        uptime = float(Path("/proc/uptime").read_text().split()[0])
        proc_entries = os.listdir("/proc")
    except (OSError, ValueError, IndexError):
        return 0, None
    running = {}
    for pid in (entry for entry in proc_entries if entry.isdigit()):
        fd_dir = f"/proc/{pid}/fd"
        try:
            fds = os.listdir(fd_dir)
        except OSError:
            continue
        for fd in fds:
            try:
                target = os.path.realpath(os.readlink(f"{fd_dir}/{fd}"))
            except OSError:
                continue
            if target not in logs:
                continue
            task = os.path.basename(target).removesuffix(".stdout.log")
            elapsed = proc_elapsed(pid, uptime) or 0
            running[task] = max(running.get(task, 0), elapsed)
    return (len(running), max(running.values()) or None) if running else (0, None)


# --- Rendering -------------------------------------------------------------

def build(data):
    config_dir = Path(os.environ.get("CODEBUDDY_CONFIG_DIR") or Path.home() / ".codebuddy")
    settings = read_json(config_dir / "settings.json")
    workspace = data.get("workspace") if isinstance(data.get("workspace"), dict) else {}
    cwd = data.get("cwd") or workspace.get("current_dir") or os.getcwd()
    project_value = workspace.get("project_dir") or cwd
    project_dir = Path(project_value) if project_value else None
    model_data = data.get("model") if isinstance(data.get("model"), dict) else {}
    model = model_data.get("display_name") or model_data.get("id") or "Unknown"
    effort = str(settings.get("reasoningEffort") or "").upper()
    permissions = settings.get("permissions") if isinstance(settings.get("permissions"), dict) else {}
    permission = data.get("permission_mode") or permissions.get("defaultMode") or "-"

    context = data.get("context_window") if isinstance(data.get("context_window"), dict) else {}
    current_usage = context.get("current_usage")
    usage = dict(current_usage) if isinstance(current_usage, dict) else {}
    fallback = latest_usage(data.get("transcript_path"))
    for key in USAGE_FIELDS + ("output_tokens",):
        if nonnegative_int(usage.get(key)) is None and nonnegative_int(fallback.get(key)) is not None:
            usage[key] = fallback[key]
    values = {key: nonnegative_int(usage.get(key)) for key in USAGE_FIELDS}
    have_usage = all(value is not None for value in values.values())
    total_input = sum(values.values()) if have_usage else None
    output_tokens = nonnegative_int(usage.get("output_tokens"))

    size = nonnegative_int(context.get("context_window_size"))
    if not size:
        size = nonnegative_int(model_config(config_dir, settings, model_data.get("id")).get("maxInputTokens"))
    remaining = nonnegative_number(context.get("remaining_percentage"))
    if remaining is None:
        used = nonnegative_number(context.get("used_percentage"))
        remaining = 100 - used if used is not None else None
    if remaining is None and total_input is not None and size:
        remaining = 100 * max(0, size - total_input) / size
    remaining = min(100, max(0, remaining)) if remaining is not None else None
    if remaining is None:
        context_text = paint("[" + "-" * BAR_CELLS + "]", GRAY) + paint(
            " n/a" + (f" /{compact(size)}" if size else ""), GRAY
        )
    else:
        filled = min(BAR_CELLS, max(0, round(remaining * BAR_CELLS / 100)))
        color = GREEN if remaining >= 50 else YELLOW if remaining >= 20 else RED
        context_text = paint("[" + "#" * filled + "-" * (BAR_CELLS - filled) + "]", color)
        context_text += paint(f" {remaining:.0f}%" + (f" /{compact(size)}" if size else ""), GRAY)

    separator = paint(" | ", GRAY)
    head = paint("MODEL", GRAY) + " " + paint(model, PURPLE)
    if effort:
        head += paint(" - ", GRAY) + paint(effort, BOLD_CYAN)
    head += separator + context_text

    local = [paint(project_dir.name or str(project_dir), BOLD_CYAN) if project_dir else paint("Unknown", BOLD_CYAN)]
    branch = git_status(cwd)
    if branch:
        local.append(paint(branch, PURPLE))
    local += [
        paint("cfg ", GRAY) + paint(permission),
        paint(str(cwd)),
        paint("MCP ", GRAY) + paint(count_mcp(project_dir, config_dir)),
        paint("Skill ", GRAY) + paint(count_skills(project_dir, config_dir, settings)),
    ]
    local_line = paint("LOCAL", GRAY) + " " + separator.join(local)

    stats = []
    if have_usage:
        stats.append(paint("IN ", GRAY) + paint(compact(values["input_tokens"])))
        cache_read = values["cache_read_input_tokens"]
        if cache_read == 0:
            stats.append(paint("CACHE ", GRAY) + paint("cold", YELLOW))
        elif total_input:
            rate = cache_read * 100 / total_input
            color = GREEN if rate >= 80 else CYAN if rate >= 40 else YELLOW
            stats.append(paint("CACHE ", GRAY) + paint(f"{compact(cache_read)} {rate:.0f}%", color))
        if values["cache_creation_input_tokens"]:
            stats.append(paint("WRITE ", GRAY) + paint(compact(values["cache_creation_input_tokens"])))
    if output_tokens is not None:
        stats.append(paint("OUT ", GRAY) + paint(compact(output_tokens)))
    done, total = todo_progress(config_dir, data.get("session_id"))
    if total:
        stats.append(paint("TODO ", GRAY) + paint(f"{done}/{total}", GREEN if done == total else PURPLE))
    running, longest = background_tasks(data.get("session_id"))
    if running:
        label = str(running) + (f" {duration(longest)}" if longest and longest >= 1 else "")
        stats.append(paint("BG ", GRAY) + paint(label, YELLOW))
    team = data.get("team") if isinstance(data.get("team"), dict) else {}
    if nonnegative_int(team.get("total_members")):
        stats.append(paint("TEAM ", GRAY) + paint(f"{team.get('active_members', 0)}/{team['total_members']}", PURPLE))
    cost = data.get("cost") if isinstance(data.get("cost"), dict) else {}
    elapsed = nonnegative_int(cost.get("total_duration_ms"))
    if elapsed is not None:
        stats.append(paint("RUN ", GRAY) + paint(duration(elapsed / 1000)))

    stat_line = paint("STAT", GRAY) + " " + separator.join(stats) if stats else ""
    return "\n".join(line for line in (head, local_line, stat_line) if line)


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, UnicodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    try:
        output = build(data)
    except Exception:
        model_data = data.get("model") if isinstance(data.get("model"), dict) else {}
        model = model_data.get("display_name") or model_data.get("id") or "?"
        output = paint("MODEL", GRAY) + " " + paint(model, PURPLE) + paint(" | status unavailable", RED)
    print(output)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    main()
