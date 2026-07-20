#!/usr/bin/env python3
"""Mark a stage as done/skipped and refresh the TODO block in active.md.

AI calls this at the end of each stage:

    python <skill_dir>/scripts/update_stage.py --root <project_root> --stage <name> --status done
    python <skill_dir>/scripts/update_stage.py --root <project_root> --stage <name> --status skipped --reason "<why>"

Statuses:
  pending     — not yet started
  in_progress — currently active (set automatically when moving to next stage)
  done        — completed
  skipped     — optional stage intentionally skipped or merged
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List


def render_todo_block(stages: List[dict]) -> str:
    lines = []
    for s in stages:
        status = s["status"]
        name = s["name"]
        req_tag = "" if s["required"] else " _(optional)_"
        if status == "done":
            marker = "- [x]"
        elif status == "skipped":
            marker = "- [~]"
        elif status == "in_progress":
            marker = "- [▶]"
        else:
            marker = "- [ ]"
        lines.append(f"{marker} **{name}**{req_tag}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mark a dev-done-flow stage complete and refresh TODO.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--stage", required=True, help="Stage name to update.")
    parser.add_argument(
        "--status", required=True,
        choices=["pending", "in_progress", "done", "skipped"],
        help="New status for the stage.",
    )
    parser.add_argument("--reason", default="", help="Reason (required when status=skipped).")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    flow_dir = root / ".dev-done-flow"
    manifest_path = flow_dir / "manifest.json"

    if not manifest_path.exists():
        print("ERROR: manifest.json not found. Run plan_flow.py first.")
        raise SystemExit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stages = manifest["stages"]

    # Validate stage name
    names = [s["name"] for s in stages]
    if args.stage not in names:
        print(f"ERROR: unknown stage '{args.stage}'. Known: {', '.join(names)}")
        raise SystemExit(1)

    # Validate: required stages cannot be skipped
    target = next(s for s in stages if s["name"] == args.stage)
    if args.status == "skipped" and target["required"]:
        print(f"ERROR: stage '{args.stage}' is required and cannot be skipped.")
        raise SystemExit(1)

    # Validate: skip reason must be provided
    if args.status == "skipped" and not args.reason.strip():
        print("ERROR: --reason is required when status=skipped.")
        raise SystemExit(1)

    # Only advance the pointer when the stage being completed was in_progress.
    # Preemptively skipping a future pending stage must NOT move the current pointer.
    was_active = target["status"] == "in_progress"
    target["status"] = args.status

    if was_active and args.status in ("done", "skipped"):
        advanced = False
        for s in stages:
            if s["status"] == "pending":
                s["status"] = "in_progress"
                manifest["current_stage"] = s["name"]
                advanced = True
                break
        if not advanced:
            manifest["current_stage"] = stages[-1]["name"]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest["updated_at"] = now
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Append skip reason to skipped.md
    if args.status == "skipped":
        skipped_file = flow_dir / "stages" / "skipped.md"
        if skipped_file.exists():
            text = skipped_file.read_text(encoding="utf-8")
        else:
            text = "# Skipped / Merged Stages\n\n| Stage | Action | Reason |\n|-------|--------|--------|\n"
        req_label = "required" if target["required"] else "optional"
        text = text.rstrip() + f"\n| {args.stage} ({req_label}) | skipped | {args.reason} |\n"
        skipped_file.write_text(text, encoding="utf-8")

    # Refresh TODO block in active.md
    active = flow_dir / "active.md"
    if active.exists():
        todo_block = render_todo_block(stages)
        text = active.read_text(encoding="utf-8")
        text = re.sub(r"(- Updated At: ).+", rf"\g<1>{now}", text, count=1)
        text = re.sub(
            r"(<!-- updated by update_stage\.py.*?-->\n).*?(\n\n## Stage Summaries)",
            rf"\g<1>{todo_block}\g<2>",
            text,
            flags=re.DOTALL,
        )
        active.write_text(text, encoding="utf-8")

    # Update stage file status line
    stage_file = flow_dir / "stages" / f"{args.stage}.md"
    if stage_file.exists():
        content = stage_file.read_text(encoding="utf-8")
        content = re.sub(r"## Status: .+", f"## Status: {args.status}", content, count=1)
        stage_file.write_text(content, encoding="utf-8")

    print(f"updated stage={args.stage} status={args.status}")
    print(f"current_stage={manifest['current_stage']}")
    print()
    print(render_todo_block(stages))


if __name__ == "__main__":
    main()
