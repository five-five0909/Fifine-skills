#!/usr/bin/env python3
"""Merge a curated memory proposal and update a managed global-agent block."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

BEGIN = "<!-- FIFINE_SESSION_MEMORY_BEGIN -->"
END = "<!-- FIFINE_SESSION_MEMORY_END -->"
ALLOWED_CATEGORY = {"preference", "correction", "pitfall", "workflow", "constraint"}
ALLOWED_SCOPE = {"global", "project", "session"}
ALLOWED_GROUNDING = {
    "explicit_user",
    "user_correction",
    "repeated_observation",
    "verified_external",
    "assistant_inference",
}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_STATUS = {"active", "candidate", "rejected", "superseded", "deleted"}
STRONG_GROUNDING = {"explicit_user", "user_correction", "verified_external"}
KEY_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
SECRET_PATTERNS = (
    re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*[^\s]{8,}"),
    re.compile(r"\b(?:sk|ghp|github_pat|xox[baprs])[-_][A-Za-z0-9_-]{16,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def follow_symlink(path: Path) -> Path:
    return path.resolve() if path.is_symlink() else path


def resolve_target(value: str) -> Path:
    if value == "auto":
        if os.environ.get("CLAUDE_CONFIG_DIR") or os.environ.get("CLAUDECODE"):
            value = "claude"
        else:
            value = "codex"
    if value == "codex":
        home = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
        override = home / "AGENTS.override.md"
        if override.exists() and override.read_text(encoding="utf-8").strip():
            return follow_symlink(override)
        return follow_symlink(home / "AGENTS.md")
    if value == "claude":
        return follow_symlink(Path(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")).expanduser() / "CLAUDE.md")
    if value == "agents":
        return follow_symlink(Path(os.environ.get("AGENTS_HOME", "~/.agents")).expanduser() / "AGENTS.md")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError("target must be codex, claude, agents, auto, or an absolute path")
    return follow_symlink(path)


def contains_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"top-level JSON value must be an object: {path}")
    return data


def validate_entry(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"entries[{index}] must be an object")
    required = {
        "key",
        "instruction",
        "category",
        "scope",
        "grounding",
        "confidence",
        "status",
        "evidence",
    }
    missing = sorted(required - raw.keys())
    if missing:
        raise ValueError(f"entries[{index}] missing fields: {', '.join(missing)}")

    entry = dict(raw)
    for field in required:
        if not isinstance(entry[field], str) or not entry[field].strip():
            raise ValueError(f"entries[{index}].{field} must be a non-empty string")
        entry[field] = entry[field].strip()

    if not KEY_RE.fullmatch(entry["key"]):
        raise ValueError(f"entries[{index}].key must be a stable lowercase semantic key")
    if entry["category"] not in ALLOWED_CATEGORY:
        raise ValueError(f"entries[{index}].category is unsupported")
    if entry["scope"] not in ALLOWED_SCOPE:
        raise ValueError(f"entries[{index}].scope is unsupported")
    if entry["grounding"] not in ALLOWED_GROUNDING:
        raise ValueError(f"entries[{index}].grounding is unsupported")
    if entry["confidence"] not in ALLOWED_CONFIDENCE:
        raise ValueError(f"entries[{index}].confidence is unsupported")
    if entry["status"] not in ALLOWED_STATUS:
        raise ValueError(f"entries[{index}].status is unsupported")
    if not isinstance(entry.get("confirmed", False), bool):
        raise ValueError(f"entries[{index}].confirmed must be boolean")
    if "reason" in entry and not isinstance(entry["reason"], str):
        raise ValueError(f"entries[{index}].reason must be a string")
    if len(entry["instruction"]) > 500:
        raise ValueError(f"entries[{index}].instruction is too long")
    if len(entry["evidence"]) > 1000:
        raise ValueError(f"entries[{index}].evidence is too long")
    if contains_secret(entry["instruction"]) or contains_secret(entry["evidence"]):
        raise ValueError(f"entries[{index}] appears to contain a secret")

    confirmed = entry.get("confirmed", False)
    if entry["status"] == "active" and entry["grounding"] not in STRONG_GROUNDING and not confirmed:
        entry["status"] = "candidate"
        entry["reason"] = (
            entry.get("reason", "").strip()
            or "Automatically retained as candidate because grounding is not strong and the user did not confirm it."
        )
    if entry["status"] == "active" and entry["scope"] != "global":
        entry["status"] = "candidate"
        entry["reason"] = (
            entry.get("reason", "").strip()
            or "Retained as candidate because only global entries belong in the global agent block."
        )
    if entry["status"] == "active" and entry["confidence"] == "low" and not confirmed:
        entry["status"] = "candidate"
        entry["reason"] = (
            entry.get("reason", "").strip()
            or "Automatically retained as candidate because confidence is low and the user did not confirm it."
        )
    if entry["status"] == "deleted" and entry["grounding"] not in STRONG_GROUNDING and not confirmed:
        entry["status"] = "candidate"
        entry["reason"] = (
            entry.get("reason", "").strip()
            or "A memory can be erased only from a grounded user request or explicit confirmation."
        )

    entry["confirmed"] = confirmed
    entry["updated_at"] = datetime.now(timezone.utc).isoformat()
    return entry


def validate_proposal(data: dict[str, Any]) -> list[dict[str, Any]]:
    if data.get("version") != 1:
        raise ValueError("proposal version must be 1")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("proposal entries must be a non-empty array")
    validated = [validate_entry(raw, index) for index, raw in enumerate(entries)]
    keys = [entry["key"] for entry in validated]
    if len(keys) != len(set(keys)):
        raise ValueError("proposal contains duplicate entry keys")
    return validated


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "entries": {}, "history": [], "pending": []}
    ledger = load_json(path)
    if ledger.get("version") != 1 or not isinstance(ledger.get("entries"), dict):
        raise ValueError(f"unsupported ledger format: {path}")
    if not isinstance(ledger.get("history", []), list):
        raise ValueError(f"ledger history must be an array: {path}")
    if not isinstance(ledger.get("pending", []), list):
        raise ValueError(f"ledger pending must be an array: {path}")
    ledger.setdefault("history", [])
    ledger.setdefault("pending", [])
    return ledger


def merge_ledger(ledger: dict[str, Any], incoming: list[dict[str, Any]]) -> dict[str, Any]:
    entries = dict(ledger["entries"])
    history = list(ledger["history"])
    pending = list(ledger["pending"])
    now = datetime.now(timezone.utc).isoformat()
    for entry in incoming:
        key = entry["key"]
        previous = entries.get(key)
        weak_revision = (
            previous
            and previous.get("status") == "active"
            and entry.get("status") != "active"
            and entry.get("grounding") not in STRONG_GROUNDING
            and not entry.get("confirmed", False)
        )
        if weak_revision:
            proposal = dict(entry)
            proposal["proposed_against"] = key
            proposal["retained_at"] = now
            duplicate = any(
                item.get("key") == proposal["key"]
                and item.get("instruction") == proposal.get("instruction")
                and item.get("status") == proposal.get("status")
                for item in pending
            )
            if not duplicate:
                pending.append(proposal)
            continue
        pending = [
            item
            for item in pending
            if item.get("key") != key and item.get("proposed_against") != key
        ]
        if entry.get("status") == "deleted":
            entries[key] = {
                "key": key,
                "status": "deleted",
                "reason": "Removed from active memory at the user's grounded request.",
                "updated_at": now,
            }
            history = [item for item in history if item.get("key") != key]
            continue
        if previous and previous != entry:
            historical = dict(previous)
            historical["archived_at"] = now
            history.append(historical)
        entries[key] = entry
    return {
        "version": 1,
        "updated_at": now,
        "entries": entries,
        "history": history,
        "pending": pending,
    }


def render_block(ledger: dict[str, Any], max_active: int, ledger_path: Path, newline: str) -> str:
    active = [
        entry
        for entry in ledger["entries"].values()
        if entry.get("status") == "active" and entry.get("scope") == "global"
    ]
    active.sort(key=lambda item: (item["category"], item["key"]))
    if len(active) > max_active:
        raise ValueError(
            f"ledger has {len(active)} active global entries; curate to at most {max_active} instead of truncating"
        )

    lines = [
        BEGIN,
        "## Curated session memory",
        "",
        f"Last updated: {date.today().isoformat()}",
        "",
        "> These are correctable user-scoped defaults, not unquestionable facts. Current explicit",
        "> instructions and verified live evidence take precedence. If a rule appears stale,",
        "> contradictory, or out of scope, clarify it and update the memory instead of obeying blindly.",
        f"> Provenance ledger: `{ledger_path}`. Use `fifine-session-memory-curator` to inspect or revise it.",
        "",
    ]
    if active:
        labels = {
            "preference": "Preference",
            "correction": "Correction",
            "pitfall": "Pitfall",
            "workflow": "Workflow",
            "constraint": "Constraint",
        }
        lines.extend(
            f"- **{labels[item['category']]}** (`{item['key']}`): {item['instruction']}"
            for item in active
        )
    else:
        lines.append("- No active global memories have been promoted yet.")
    lines.append(END)
    return newline.join(lines) + newline


def replace_managed_block(existing: str, block: str, newline: str) -> str:
    begin_count = existing.count(BEGIN)
    end_count = existing.count(END)
    if begin_count > 1 or end_count > 1:
        raise ValueError("target contains multiple managed blocks; consolidate them manually before updating")
    start = existing.find(BEGIN)
    end = existing.find(END)
    if (start == -1) != (end == -1):
        raise ValueError("target contains an incomplete managed block; repair it manually before updating")
    if start != -1:
        if end < start:
            raise ValueError("target managed block markers are out of order")
        end += len(END)
        before = existing[:start].rstrip()
        after = existing[end:].lstrip("\r\n")
        parts = [part for part in (before, block.rstrip(), after.rstrip()) if part]
        return (newline * 2).join(parts) + newline
    if existing.strip():
        return block.rstrip("\r\n") + (newline * 2) + existing.lstrip("\r\n")
    return block


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="auto", help="codex, claude, agents, auto, or absolute path")
    parser.add_argument("--proposal-file", required=True, help="JSON proposal created by the curating agent")
    parser.add_argument("--ledger", help="absolute ledger path; defaults beside the target config")
    parser.add_argument("--max-active", type=int, default=12, help="maximum active global instructions")
    parser.add_argument("--dry-run", action="store_true", help="validate and print the resulting config without writing")
    parser.add_argument("--no-backup", action="store_true", help="do not keep a one-generation target backup")
    args = parser.parse_args()

    try:
        target = resolve_target(args.target)
        ledger_path = (
            Path(args.ledger).expanduser()
            if args.ledger
            else target.parent / "fifine-session-memory-ledger.json"
        )
        if not ledger_path.is_absolute():
            raise ValueError("ledger path must be absolute")
        if args.max_active < 1:
            raise ValueError("max-active must be positive")

        proposal = load_json(Path(args.proposal_file).expanduser())
        incoming = validate_proposal(proposal)
        merged = merge_ledger(load_ledger(ledger_path), incoming)
        if target.exists():
            with target.open("r", encoding="utf-8", newline="") as handle:
                existing = handle.read()
        else:
            existing = ""
        newline = "\r\n" if "\r\n" in existing else "\n"
        block = render_block(merged, args.max_active, ledger_path, newline)
        updated = replace_managed_block(existing, block, newline)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.dry_run:
        print(updated, end="")
        return 0

    if target.exists() and not args.no_backup and updated != existing:
        backup = target.with_name(f"{target.name}.fifine-session-memory.bak")
        shutil.copy2(target, backup)
    atomic_write(ledger_path, json.dumps(merged, ensure_ascii=False, indent=2) + "\n")
    atomic_write(target, updated)

    active_count = sum(
        1
        for entry in merged["entries"].values()
        if entry.get("status") == "active" and entry.get("scope") == "global"
    )
    candidate_count = (
        sum(1 for entry in merged["entries"].values() if entry.get("status") == "candidate")
        + len(merged["pending"])
    )
    print(json.dumps({
        "target": str(target),
        "ledger": str(ledger_path),
        "active_global": active_count,
        "candidates_retained": candidate_count,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
