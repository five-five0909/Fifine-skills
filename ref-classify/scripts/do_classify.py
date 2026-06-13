#!/usr/bin/env python3
"""
do_classify.py — 按计划 JSON 移动 PDF 到 A-F 子目录

用法：
  python do_classify.py <plan.json> [--dry-run]

plan.json 格式：
  [{"abs_path": "...", "target_panel": "A-Mamba-SSM"}, ...]
"""
import sys
import json
import shutil
import argparse
from pathlib import Path

PANEL_DIRS = {
    "A-Mamba-SSM", "B-Physics-Prior-ML", "C-Transfer-Learning",
    "D-Soil-Spectral-DL", "E-Soil-Science-Basics", "F-Traditional-Baseline",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", help="plan JSON 路径")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(args.plan, encoding="utf-8") as f:
        plan = json.load(f)

    moved, skipped, errors = 0, 0, 0

    for item in plan:
        src = Path(item["abs_path"])
        panel = item["target_panel"]

        if panel not in PANEL_DIRS:
            print(f"[ERROR] 未知板块: {panel}  ← {src.name}")
            errors += 1
            continue

        if not src.exists():
            print(f"[SKIP]  源文件不存在: {src.name}")
            skipped += 1
            continue

        dest_dir = src.parent / panel
        dest = dest_dir / src.name

        if dest.exists():
            print(f"[SKIP]  目标已存在（不覆盖）: {panel}/{src.name}")
            skipped += 1
            continue

        if not args.dry_run:
            dest_dir.mkdir(exist_ok=True)
            shutil.move(str(src), str(dest))

        tag = "DRY" if args.dry_run else "MOVE"
        print(f"[{tag}]  {src.name} → {panel}/")
        moved += 1

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}完成：移动 {moved}，跳过 {skipped}，错误 {errors}")


if __name__ == "__main__":
    main()
