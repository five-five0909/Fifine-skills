#!/usr/bin/env python3
"""
scan_pdfs.py — 扫描参考文献目录，列出未分类 PDF

用法：python scan_pdfs.py "<目录路径>"
输出：JSON 列表，每项含 filename / already_classified / abs_path
"""
import sys
import json
from pathlib import Path

PANEL_DIRS = {
    "A-Mamba-SSM", "B-Physics-Prior-ML", "C-Transfer-Learning",
    "D-Soil-Spectral-DL", "E-Soil-Science-Basics", "F-Traditional-Baseline",
}


def scan(root: Path) -> list[dict]:
    results = []
    for pdf in sorted(root.rglob("*.pdf")):
        parts = pdf.relative_to(root).parts
        in_panel = len(parts) > 1 and parts[0] in PANEL_DIRS
        results.append({
            "filename": pdf.name,
            "abs_path": str(pdf),
            "already_classified": in_panel,
            "current_panel": parts[0] if in_panel else None,
        })
    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python scan_pdfs.py <目录路径>", file=sys.stderr)
        sys.exit(1)

    root = Path(sys.argv[1])
    if not root.exists():
        print(f"[ERROR] 目录不存在: {root}", file=sys.stderr)
        sys.exit(1)

    data = scan(root)
    unclassified = [d for d in data if not d["already_classified"]]

    if not unclassified:
        print("All files already classified. Nothing to do.")
        sys.exit(0)

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
