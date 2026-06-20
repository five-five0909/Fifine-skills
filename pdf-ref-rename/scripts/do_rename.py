#!/usr/bin/env python3
"""
do_rename.py — Execute PDF renames from a JSON plan file.

Usage:
    python do_rename.py <plan.json>            # Execute renames
    python do_rename.py <plan.json> --dry-run  # Preview only, no changes

Plan JSON format:
[
  {
    "old_path": "/absolute/path/to/file.pdf",
    "new_name": "2024_Paper Title_Author et al.pdf"
  },
  ...
]

Dependencies: Python 3.7+ (no external packages)
"""

import sys
import os
import json
import re
import argparse

# ---------------------------------------------------------------------------
# Windows filename sanitization (same rules as scan_refs.py)
# ---------------------------------------------------------------------------
ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Windows MAX_PATH = 260. Use 255 as safe limit to leave margin.
WINDOWS_MAX_PATH = 255


def sanitize_filename(name: str) -> str:
    """Replace Windows-illegal characters with safe alternatives."""
    name = name.replace(":", " -")
    name = name.replace("/", "-")
    name = name.replace("\\", "-")
    name = ILLEGAL_CHARS.sub("", name)
    name = re.sub(r"  +", " ", name).strip()
    if len(name) > 200:
        name = name[:197] + "..."
    return name


def ensure_path_length(dir_path: str, new_name: str) -> str:
    """Ensure full path stays within Windows MAX_PATH limit.
    
    If the path is too long, truncates the title portion of the filename
    (format: YYYY_Title_Author.pdf). Returns the (possibly shortened) new_name.
    """
    full_path = os.path.join(dir_path, new_name)
    if len(full_path) <= WINDOWS_MAX_PATH:
        return new_name

    # Parse: YYYY_<title>_<author>.pdf
    # Use rfind to find the LAST underscore before .pdf (separates author from title)
    if not new_name.lower().endswith(".pdf"):
        # Not a PDF, just truncate the whole name
        max_name_len = WINDOWS_MAX_PATH - len(dir_path) - 1
        if len(new_name) > max_name_len:
            return new_name[:max_name_len - 3] + "..."
        return new_name

    name_without_ext = new_name[:-4]  # remove .pdf
    
    # Find year prefix: first 4 chars should be digits, followed by _
    year_match = re.match(r'^(\d{4})_(.*)', name_without_ext)
    if not year_match:
        # Not in YYYY_... format, truncate whole name
        max_name_len = WINDOWS_MAX_PATH - len(dir_path) - 1
        if len(new_name) > max_name_len:
            return new_name[:max_name_len - 3] + "..."
        return new_name

    year = year_match.group(1)
    rest = year_match.group(2)  # Title_Author

    # Find the last underscore (separates title from author)
    last_us = rest.rfind('_')
    if last_us < 0:
        # No underscore in rest, can't separate title/author
        max_name_len = WINDOWS_MAX_PATH - len(dir_path) - 1
        if len(new_name) > max_name_len:
            return new_name[:max_name_len - 3] + "..."
        return new_name

    title = rest[:last_us]
    author = rest[last_us + 1:]  # Everything after the last underscore

    # Calculate max title length
    # Format: dir_path/YYYY_<title>_<author>.pdf
    fixed_overhead = len(dir_path) + 1 + len(year) + 1 + 1 + len(author) + 4  # dir/ + year_ + _ + author + .pdf
    max_title_len = WINDOWS_MAX_PATH - fixed_overhead

    if max_title_len < 20:
        max_title_len = 20
    
    if len(title) > max_title_len:
        title = title[:max_title_len - 3] + "..."

    return f"{year}_{title}_{author}.pdf"


# ---------------------------------------------------------------------------
# Rename execution
# ---------------------------------------------------------------------------
def execute_plan(plan: list, dry_run: bool = False) -> dict:
    """Execute rename plan. Returns summary stats."""
    stats = {"total": len(plan), "renamed": 0, "skipped": 0, "errors": 0}
    results = []

    for item in plan:
        old_path = item.get("old_path", "")
        new_name = item.get("new_name", "")

        if not old_path or not new_name:
            results.append({"status": "ERROR", "msg": f"Missing old_path or new_name: {item}"})
            stats["errors"] += 1
            continue

        # Sanitize new name
        new_name = sanitize_filename(new_name)
        if not new_name.lower().endswith(".pdf"):
            new_name += ".pdf"

        dir_path = os.path.dirname(old_path)

        # Ensure full path stays within Windows MAX_PATH limit
        original_new_name = new_name
        new_name = ensure_path_length(dir_path, new_name)
        if new_name != original_new_name:
            truncation_note = f" (path truncated: {len(os.path.join(dir_path, original_new_name))} -> {len(os.path.join(dir_path, new_name))} chars)"
        else:
            truncation_note = ""

        new_path = os.path.join(dir_path, new_name)

        # Validation checks
        if not os.path.exists(old_path):
            results.append({"status": "SKIP", "old": os.path.basename(old_path),
                           "msg": f"Source not found: {old_path}"})
            stats["skipped"] += 1
            continue

        if old_path == new_path:
            results.append({"status": "SKIP", "old": os.path.basename(old_path),
                           "msg": "Same path, no rename needed"})
            stats["skipped"] += 1
            continue

        if os.path.exists(new_path):
            results.append({"status": "SKIP", "old": os.path.basename(old_path),
                           "msg": f"Target already exists: {new_name}"})
            stats["skipped"] += 1
            continue

        # Execute or preview
        if dry_run:
            results.append({"status": "DRY-RUN", "old": os.path.basename(old_path),
                           "new": new_name, "note": truncation_note})
            stats["renamed"] += 1
        else:
            try:
                os.rename(old_path, new_path)
                results.append({"status": "OK", "old": os.path.basename(old_path),
                               "new": new_name, "note": truncation_note})
                stats["renamed"] += 1
            except Exception as e:
                results.append({"status": "ERROR", "old": os.path.basename(old_path),
                               "msg": str(e)})
                stats["errors"] += 1

    return {"stats": stats, "details": results}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Execute PDF renames from a JSON plan")
    parser.add_argument("plan", help="Path to JSON plan file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview renames without making changes")
    args = parser.parse_args()

    if not os.path.exists(args.plan):
        print(f"ERROR: Plan file not found: {args.plan}", file=sys.stderr)
        sys.exit(1)

    with open(args.plan, "r", encoding="utf-8") as f:
        plan = json.load(f)

    if not isinstance(plan, list):
        print("ERROR: Plan must be a JSON array of objects", file=sys.stderr)
        sys.exit(1)

    mode = "[DRY-RUN] " if args.dry_run else ""
    print(f"{mode}Executing rename plan: {len(plan)} file(s)\n")

    result = execute_plan(plan, dry_run=args.dry_run)

    # Print results
    for r in result["details"]:
        status = r["status"]
        if status in ("OK", "DRY-RUN"):
            note = r.get("note", "")
            print(f"  [{status}] {r['old']}")
            print(f"       -> {r['new']}{note}")
        else:
            print(f"  [{status}] {r.get('old', '?')}: {r.get('msg', 'unknown')}")

    # Summary
    s = result["stats"]
    print(f"\n{mode}Done: {s['renamed']} renamed, {s['skipped']} skipped, {s['errors']} errors (of {s['total']} total)")

    if args.dry_run:
        print("\nRe-run without --dry-run to execute.")


if __name__ == "__main__":
    main()
