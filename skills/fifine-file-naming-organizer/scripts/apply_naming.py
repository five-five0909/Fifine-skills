#!/usr/bin/env python3
"""
apply_naming.py — Execute a rename/move plan produced from an audit report.

Usage:
    python apply_naming.py <plan.json> --dry-run
    python apply_naming.py <plan.json> [--mapping-log PATH] [--no-log]
    python apply_naming.py --undo <mapping-log.json>

Plan JSON format (new_dir optional; defaults to the current directory):
[
  {
    "old_path": "/abs/or/rel/path/报价.docx",
    "new_name": "20260910_秋季活动-报价单_V1.docx",
    "new_dir":  "/abs/or/rel/path/20260910_秋季活动/交付物"
  }
]

Rename, move, and rename+move are derived, not declared: omit new_dir to stay in
place, and a directory entry is detected from the filesystem, never from the
name. The version number is part of new_name and must already reflect the agreed
major/minor bump: whatever the user confirmed at the plan table is exactly what
gets written, so the executor never recomputes a version.

Guards: grammar validation, 定稿/归档 lock refusal, conflict refusal (never
auto-suffixes), case-insensitive collision detection, two-phase temp hops for
rename cycles, full-path budget check. Every executed move lands in a mapping
log so the batch can be reversed with --undo.
Dependencies: Python 3.7+ standard library only.
"""

import argparse
import datetime as _dt
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import naming_lib as L  # noqa: E402

TEMP_PREFIX = ".naming-tmp"
CREATED_DIRS = []


def load_plan(path):
    with open(path, "r", encoding="utf-8") as handle:
        plan = json.load(handle)
    if not isinstance(plan, list):
        raise ValueError("plan must be a JSON array of objects")
    return plan


def stem_of(name):
    return L.split_ext(name)[0]


def slot(path_pair):
    return (os.path.dirname(path_pair), os.path.basename(path_pair).casefold())


def resolve_items(plan, mode):
    """Turn plan entries into executable items or pre-flight rejections."""
    items, rejected = [], []
    for index, raw in enumerate(plan):
        src = raw.get("old_path") or raw.get("path")
        new_name = (raw.get("new_name") or "").strip()
        if not src or not new_name:
            rejected.append({"index": index, "old_path": src or "", "new_name": new_name,
                             "status": "MISSING_FIELD",
                             "reason": "条目缺少 old_path 或 new_name"})
            continue

        src = os.path.abspath(os.path.expanduser(src))
        dst_dir = (os.path.abspath(os.path.expanduser(raw["new_dir"]))
                   if raw.get("new_dir") else os.path.dirname(src))
        kind = "dir" if os.path.isdir(src) else "file"

        if not os.path.lexists(src):
            rejected.append({"index": index, "old_path": src, "new_name": new_name,
                             "status": "MISSING", "reason": "源文件不存在"})
            continue

        check = L.validate(new_name, kind=kind, mode=mode, dir_path=dst_dir)
        if not check["ok"]:
            rejected.append({"index": index, "old_path": src, "new_name": new_name,
                             "status": "INVALID_NAME", "reason": "; ".join(check["errors"])})
            continue

        old_name = os.path.basename(src)
        old_parse = L.validate(old_name, kind=kind, mode="solo")
        tag = old_parse["parsed"]["tag"]
        if tag in L.LOCKED_TAGS and stem_of(new_name) != stem_of(old_name):
            rejected.append({"index": index, "old_path": src, "new_name": new_name,
                             "status": "LOCKED-REFUSE",
                             "reason": "「%s」已锁定，禁止改动主名；需要继续迭代请另存【待改】新副本" % tag})
            continue

        dst = os.path.join(dst_dir, new_name)
        if dst == src:
            rejected.append({"index": index, "old_path": src, "new_name": new_name,
                             "status": "SKIP-SAME", "reason": "已在目标位置且名称合规"})
            continue

        items.append({"index": index, "src": src, "dst": dst, "kind": kind,
                      "src_key": slot(src), "dst_key": slot(dst), "intermediate": False})
    return items, rejected


def make_temp(dst_dir, ext):
    for seq in range(1, 1000):
        candidate = "%s%d%s" % (TEMP_PREFIX, seq, ext)
        if not os.path.lexists(os.path.join(dst_dir, candidate)):
            return candidate
    return "%s-%s%s" % (TEMP_PREFIX, os.urandom(4).hex(), ext)


def order_moves(items):
    """
    Sequence the moves so every target slot is free when it is used, inserting
    a temp hop whenever two entries swap names or form a longer cycle.
    """
    pending = list(items)
    order = []
    hops = 0
    ceiling = len(items) + 2

    while pending:
        held = {item["src_key"] for item in pending}
        for item in list(pending):
            if item["dst_key"] in held:
                continue
            order.append(item)
            pending.remove(item)
            break
        else:
            if hops >= ceiling:
                order.extend(pending)
                pending = []
                break
            hops += 1
            stuck = pending[0]
            _, ext = L.split_ext(os.path.basename(stuck["dst"]))
            temp_dir = stuck["dst_key"][0]
            temp_name = make_temp(temp_dir, ext)

            hop_out = dict(stuck)
            hop_out["dst"] = os.path.join(temp_dir, temp_name)
            hop_out["dst_key"] = (temp_dir, temp_name.casefold())
            hop_out["intermediate"] = True
            order.append(hop_out)

            hop_back = dict(stuck)
            hop_back["src"] = hop_out["dst"]
            hop_back["src_key"] = hop_out["dst_key"]
            hop_back["intermediate"] = True

            pending.remove(stuck)
            pending.insert(0, hop_back)
    return order


def prepare_dirs(order, dry_run):
    for item in order:
        target = item["dst_key"][0]
        if os.path.isdir(target) or target in CREATED_DIRS:
            continue
        missing = []
        probe = target
        while probe and not os.path.isdir(probe) and probe not in CREATED_DIRS:
            missing.append(probe)
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent
        if not dry_run:
            try:
                os.makedirs(target)
            except OSError as exc:
                return "无法创建目标目录 %s (%s)" % (target, exc)
        CREATED_DIRS.extend(reversed(missing))
    return None


def upfront_conflicts(order, items):
    """Targets occupied by something outside the plan, or claimed twice."""
    vacating = {item["src_key"] for item in items}
    problems, claimed = {}, set()
    for item in order:
        key = item["dst_key"]
        if key in claimed:
            problems[id(item)] = "计划内两条条目指向同一目标名: %s" % item["dst"]
            continue
        claimed.add(key)
        if key in vacating:
            continue
        if os.path.lexists(item["dst"]):
            problems[id(item)] = "目标已存在: %s" % item["dst"]
    return problems


def execute(order, problems, dry_run):
    results = []
    stats = {"moved": 0, "skipped": 0, "errors": 0}
    for item in order:
        base = {"old_path": item["src"], "new_path": item["dst"],
                "intermediate": item["intermediate"]}

        reason = problems.get(id(item))
        if reason is None and not dry_run and os.path.lexists(item["dst"]):
            reason = "执行时目标已存在: %s" % item["dst"]
        if reason:
            results.append(dict(base, status="CONFLICT", reason=reason))
            stats["skipped"] += 1
            continue

        if dry_run:
            results.append(dict(base, status="DRY-RUN", reason=""))
            stats["moved"] += 1
            continue

        if not os.path.isdir(item["dst_key"][0]):
            results.append(dict(base, status="ERROR", reason="目标目录不存在: %s" % item["dst_key"][0]))
            stats["errors"] += 1
            continue
        try:
            shutil.move(item["src"], item["dst"])
        except Exception as exc:
            results.append(dict(base, status="ERROR", reason=str(exc)))
            stats["errors"] += 1
            continue
        results.append(dict(base, status="OK", reason=""))
        stats["moved"] += 1
    return results, stats


def write_log(path, results, rejected, note):
    payload = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "note": note,
        "created_dirs": list(CREATED_DIRS),
        "moves": results,
        "rejected": rejected,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def undo(log_path):
    with open(log_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    reverted = failed = 0
    for move in reversed([m for m in payload.get("moves", []) if m.get("status") == "OK"]):
        current, original = move["new_path"], move["old_path"]
        if not os.path.lexists(current):
            print("  [SKIP] 找不到当前文件: %s" % current)
            failed += 1
            continue
        if os.path.lexists(original):
            print("  [SKIP] 还原目标已被占用: %s" % original)
            failed += 1
            continue
        try:
            shutil.move(current, original)
            print("  [OK] %s -> %s" % (os.path.basename(current), original))
            reverted += 1
        except Exception as exc:
            print("  [ERROR] %s: %s" % (current, exc))
            failed += 1

    for directory in reversed(payload.get("created_dirs", [])):
        if not os.path.isdir(directory):
            continue
        try:
            os.rmdir(directory)
            print("  [OK] 删除空目录: %s" % directory)
        except OSError:
            print("  [SKIP] 目录非空，保留: %s" % directory)

    print("\nUndo done: %d reverted, %d skipped/failed" % (reverted, failed))
    return 1 if failed else 0


def report(results, rejected, stats, dry_run):
    mode = "[DRY-RUN] " if dry_run else ""
    print("%sApplying naming plan: %d move(s), %d pre-flight reject(s)\n" % (
        mode, len(results), len(rejected)))

    for item in rejected:
        print("  [%s] %s" % (item["status"], item["old_path"] or "(缺字段)"))
        print("       目标名: %s" % (item["new_name"] or "(空)"))
        print("       原因: %s" % item["reason"])
    for move in results:
        tag = " (改名环中转步)" if move["intermediate"] else ""
        if move["status"] in ("OK", "DRY-RUN"):
            print("  [%s]%s %s" % (move["status"], tag, move["old_path"]))
            print("       -> %s" % move["new_path"])
        else:
            print("  [%s]%s %s: %s" % (move["status"], tag, move["old_path"], move["reason"]))

    print("\n%sDone: %d moved, %d conflict/skip, %d error, %d pre-flight reject" % (
        mode, stats["moved"], stats["skipped"], stats["errors"], len(rejected)))
    if dry_run:
        print("\n去掉 --dry-run 才会真正执行。")


def main():
    parser = argparse.ArgumentParser(description="Execute or preview a file/folder naming plan")
    parser.add_argument("plan", nargs="?", help="path to plan.json")
    parser.add_argument("--dry-run", action="store_true", help="preview without touching the disk")
    parser.add_argument("--mode", choices=L.MODES, default="solo",
                        help="grammar mode used to validate new names")
    parser.add_argument("--mapping-log", dest="log", help="where to write the mapping log")
    parser.add_argument("--no-log", action="store_true", help="do not write a mapping log")
    parser.add_argument("--undo", dest="undo_log", help="reverse a previous mapping log")
    args = parser.parse_args()

    L.utf8_streams()

    if args.undo_log:
        sys.exit(undo(os.path.abspath(os.path.expanduser(args.undo_log))))

    if not args.plan:
        parser.error("plan.json is required unless --undo is used")

    plan_path = os.path.abspath(os.path.expanduser(args.plan))
    if not os.path.exists(plan_path):
        print("ERROR: plan file not found: %s" % plan_path, file=sys.stderr)
        sys.exit(1)
    try:
        plan = load_plan(plan_path)
    except (ValueError, json.JSONDecodeError) as exc:
        print("ERROR: bad plan JSON: %s" % exc, file=sys.stderr)
        sys.exit(1)

    items, rejected = resolve_items(plan, args.mode)
    order = order_moves(items)

    mkdir_error = prepare_dirs(order, args.dry_run)
    if mkdir_error:
        rejected.append({"index": -1, "old_path": "", "new_name": "",
                         "status": "MKDIR-FAIL", "reason": mkdir_error})
        order = []
        items = []

    problems = upfront_conflicts(order, items)
    results, stats = execute(order, problems, args.dry_run)
    report(results, rejected, stats, args.dry_run)

    blocked = stats["skipped"] + stats["errors"] + len(rejected)
    if not args.dry_run and not args.no_log and (results or blocked):
        log_path = os.path.abspath(args.log) if args.log else os.path.join(
            os.path.dirname(plan_path),
            "naming-map-%s.json" % _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        write_log(log_path, results, rejected, plan_path)
        print("\n映射日志: %s" % log_path)
        print("回滚命令: python %s --undo \"%s\"" % (
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "apply_naming.py"), log_path))

    if stats["errors"] or stats["skipped"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
