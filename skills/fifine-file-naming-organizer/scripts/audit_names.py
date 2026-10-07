#!/usr/bin/env python3
"""
audit_names.py — Read-only compliance check for the naming convention.

Usage:
    python audit_names.py "<root>" [options]

Options:
    --mode solo|collab     solo (default) treats 【状态标签】 as optional;
                           collab expects files to carry one
    --targets files|dirs|all   what to inspect (default: files)
    --depth N              inspect at most N levels below root (default: 3)
    --problems-only        hide clean entries
    --limit N              cap printed entries (default: 200)
    --json PATH            also write the machine-readable report to PATH

Only reads directory metadata and file mtimes; never mutates anything.
Dependencies: Python 3.7+ standard library only.
"""

import argparse
import datetime as _dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import naming_lib as L  # noqa: E402


def walk(root, max_depth, targets):
    """Yield (path, rel_parts, kind) for files and/or folders under root."""
    found = []
    stack = [(root, ())]
    while stack:
        current, rel = stack.pop()
        depth = len(rel)
        try:
            entries = sorted(os.scandir(current), key=lambda e: e.name)
        except OSError as exc:
            print("WARN: cannot read %s: %s" % (current, exc), file=sys.stderr)
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            child_rel = rel + (entry.name,)
            if entry.is_dir(follow_symlinks=False):
                if entry.name in L.EXCLUDED_DIRS:
                    continue
                if targets in ("dirs", "all") and depth + 1 <= max_depth:
                    found.append((entry.path, child_rel, "dir"))
                if depth + 1 < max_depth:
                    stack.append((entry.path, child_rel))
            elif entry.is_file() and targets in ("files", "all") and depth + 1 <= max_depth:
                found.append((entry.path, child_rel, "file"))
    return found


def mtime_date(path):
    try:
        return _dt.date.fromtimestamp(os.path.getmtime(path)).strftime("%Y%m%d")
    except OSError:
        return None


def ancestor_context(rel_parts):
    """
    Walk upward for a 项目 keyword and a date prefix.

    The root's own name is never a project (it is usually a temp or drop box),
    and generic role folders carry no project information.
    """
    project = date = None
    for part in reversed(rel_parts[:-1]):
        if not part or part in L.EXCLUDED_DIRS:
            continue
        match = L.DIR_RE.match(part)
        core = (match.group("core") if match else L.clean_keyword(part)) or ""
        if match and match.group("date") and not date:
            date = match.group("date")
        head = core.split("-")[0]
        if head and head not in L.STRUCTURAL_DIRS and not project:
            project = head
        if project and date:
            break
    return project, date


def gather_hints(path, name, kind, rel_parts, depth):
    stem, ext = L.split_ext(name)
    project, ancestor_date = ancestor_context(rel_parts)
    hints = {
        "depth": depth,
        "ext": ext,
        "mtime_date": mtime_date(path),
        "ancestor_date": ancestor_date if kind == "file" else None,
        "project_from_dir": project,
        "keyword_candidates": L.core_candidates(stem)[:6],
    }
    return {k: v for k, v in hints.items() if v}


def suggest(name, kind, parsed, hints):
    """Best-effort canonical name; None when the core must be decided by AI."""
    salvaged = L.salvage(name, kind)

    if kind == "dir":
        core = parsed.get("core") or L.clean_keyword("-".join(salvaged["keywords"]))
        if not core:
            return None
        date = parsed.get("date") or salvaged["date"] or hints.get("mtime_date")
        return L.build_name(date=date, core=core)

    date = parsed.get("date") or salvaged["date"] or hints.get("ancestor_date") \
        or hints.get("mtime_date")
    raw = parsed["core"].split("-") if parsed.get("core") else list(salvaged["keywords"])
    project = hints.get("project_from_dir")
    if project and (not raw or L.clean_keyword(project) != L.clean_keyword(raw[0])):
        raw.insert(0, project)

    keywords = []
    for item in raw:
        kw = L.clean_keyword(item or "")
        if kw and kw not in keywords:
            keywords.append(kw)
    if len(keywords) < 2 or not date:
        return None
    return L.build_name(tag=parsed.get("tag") or salvaged["tag"], date=date,
                        core="-".join(keywords[:5]), ver=parsed.get("ver") or salvaged["ver"],
                        ext=parsed.get("ext") or salvaged["ext"])


def audit(root, max_depth, targets, mode):
    entries = []
    for path, rel_parts, kind in walk(root, max_depth, targets):
        name = os.path.basename(path)
        depth = len(rel_parts)
        parent = os.path.dirname(path)
        result = L.validate(name, kind=kind, mode=mode, dir_path=parent, depth=depth)

        if result["status"] == "SKIP-EXCLUDED":
            entries.append({
                "path": os.path.abspath(path), "rel_path": os.path.join(*rel_parts),
                "name": name, "kind": kind, "depth": depth, "status": result["status"],
                "ok": False, "locked": False, "parsed": result["parsed"],
                "issues": result["errors"], "warnings": [], "hints": {},
                "suggested_name": None,
            })
            continue

        hints = gather_hints(path, name, kind, rel_parts, depth)
        proposal = None if result["ok"] else suggest(name, kind, result["parsed"], hints)
        if proposal and not L.validate(proposal, kind=kind, mode=mode,
                                       dir_path=parent, depth=depth)["ok"]:
            proposal = None
        entries.append({
            "path": os.path.abspath(path),
            "rel_path": os.path.join(*rel_parts),
            "name": name,
            "kind": kind,
            "depth": depth,
            "status": result["status"],
            "ok": result["ok"],
            "locked": result["locked"],
            "parsed": result["parsed"],
            "issues": result["errors"],
            "warnings": result["warnings"],
            "hints": hints,
            "suggested_name": proposal,
        })
    return entries


def print_report(entries, root, mode, problems_only, limit):
    compliant = sum(1 for e in entries if e["status"] == "COMPLIANT")
    canonical_bad = sum(1 for e in entries if e["status"] == "NON_CANONICAL")
    excluded = sum(1 for e in entries if e["status"] == "SKIP-EXCLUDED")
    warn_only = sum(1 for e in entries if e["status"] == "COMPLIANT" and e["warnings"])

    print("root : %s" % root)
    print("mode : %s   targets as requested" % mode)
    print("total: %d  compliant=%d  non-canonical=%d  warn-only=%d  excluded=%d\n" % (
        len(entries), compliant, canonical_bad, warn_only, excluded))

    shown = 0
    for entry in entries:
        dirty = entry["status"] != "COMPLIANT" or entry["warnings"]
        if problems_only and not dirty:
            continue
        if shown >= limit:
            print("... 其余 %d 条见 JSON 报告" % (len(entries) - shown))
            break
        flag = entry["status"] + ("/LOCKED" if entry["locked"] else "")
        print("[%s] (%s) %s" % (flag, "dir" if entry["kind"] == "dir" else "file",
                                entry["rel_path"]))
        for issue in entry["issues"]:
            print("    问题: %s" % issue)
        for note in entry["warnings"]:
            print("    提示: %s" % note)
        if entry["status"] not in ("COMPLIANT", "SKIP-EXCLUDED"):
            hints = entry["hints"]
            bits = []
            if hints.get("mtime_date"):
                bits.append("mtime=%s" % hints["mtime_date"])
            if hints.get("ancestor_date"):
                bits.append("上级目录日期=%s" % hints["ancestor_date"])
            if hints.get("project_from_dir"):
                bits.append("上级目录=%s" % hints["project_from_dir"])
            if hints.get("keyword_candidates"):
                bits.append("候选关键词=%s" % " / ".join(hints["keyword_candidates"]))
            if bits:
                print("    线索: %s" % " | ".join(bits))
            print("    建议: %s" % (entry["suggested_name"] or "(核心信息线索不足，需 AI 判定)"))
        shown += 1

    if shown == 0:
        print("全部符合规范，无需整理。")


def main():
    parser = argparse.ArgumentParser(
        description="Audit file/folder names against the naming convention (read-only)")
    parser.add_argument("root", help="directory to inspect")
    parser.add_argument("--mode", choices=L.MODES, default="solo")
    parser.add_argument("--targets", choices=("files", "dirs", "all"), default="files")
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--problems-only", action="store_true")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--json", dest="json_out", help="write machine-readable report")
    args = parser.parse_args()

    L.utf8_streams()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("ERROR: not a directory: %s" % root, file=sys.stderr)
        sys.exit(1)

    entries = audit(root, args.depth, args.targets, args.mode)

    if args.json_out:
        payload = {
            "root": root,
            "mode": args.mode,
            "targets": args.targets,
            "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "summary": {
                "total": len(entries),
                "compliant": sum(1 for e in entries if e["status"] == "COMPLIANT"),
                "non_canonical": sum(1 for e in entries if e["status"] == "NON_CANONICAL"),
                "locked": sum(1 for e in entries if e["locked"]),
            },
            "entries": entries,
        }
        out_path = os.path.abspath(args.json_out)
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        print("JSON report: %s\n" % out_path)

    print_report(entries, root, args.mode, args.problems_only, args.limit)


if __name__ == "__main__":
    main()
