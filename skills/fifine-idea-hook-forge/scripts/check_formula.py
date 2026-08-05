"""check_formula.py — 从 HTML 报告中提取 MathJax 公式，生成 formula_manifest.json。

职责：仅提取公式，生成 manifest。不判断质量，不修改 HTML。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# 匹配 render_html_report.py 输出的公式容器：
#   <div class="formula-math">\[FORMULA_CONTENT\]</div>
_FORMULA_RE = re.compile(
    r'<div class="formula-math">\\\\\[(.*?)\\\\\]</div>',
    re.S,
)

# 用于推断 source 字段：找最近的 <section id="...">
_SECTION_RE = re.compile(r'<section[^>]+id="([^"]+)"', re.S)


def _extract_formulas(html_text: str) -> list[dict]:
    """从 HTML 文本中提取全部公式，返回 formula 对象列表。"""
    formulas: list[dict] = []

    for idx, m in enumerate(_FORMULA_RE.finditer(html_text)):
        raw = m.group(1).strip()
        start = m.start()
        end = m.end()

        # context
        context_before = html_text[max(0, start - 50):start]
        context_after = html_text[end:end + 50]

        # source：往前扫描，找最近的 <section id="...">
        preceding = html_text[:start]
        section_matches = list(_SECTION_RE.finditer(preceding))
        source = section_matches[-1].group(1) if section_matches else "unknown"

        formulas.append({
            "id": idx,
            "source": source,
            "type": "display",
            "raw": raw,
            "context_before": context_before,
            "context_after": context_after,
            "status": "pending",
            "note": "",
        })

    return formulas


def run_check(html_path: "str | Path", engine: str = "mathjax") -> dict:
    """提取公式并写出 formula_manifest.json。

    供 run_pipeline.py 直接 import 调用（不走 subprocess）。
    返回 manifest dict。
    """
    html_path = Path(html_path).resolve()
    if not html_path.exists():
        print(f"[formula-check] 错误：HTML 文件不存在 → {html_path}", file=sys.stderr)
        return {}

    html_text = html_path.read_text(encoding="utf-8")
    formulas = _extract_formulas(html_text)

    manifest = {
        "html_path": str(html_path),
        "engine": engine,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(formulas),
        "formulas": formulas,
    }

    output_path = html_path.parent / "formula_manifest.json"
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[formula-check] 已提取 {len(formulas)} 条公式 → {output_path.name}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从 HTML 报告中提取 MathJax 公式，生成 formula_manifest.json"
    )
    parser.add_argument("--html", required=True, help="HTML 报告路径")
    parser.add_argument("--engine", default="mathjax", help="公式渲染引擎（默认 mathjax）")
    parser.add_argument("--output", default="", help="输出路径（默认同 HTML 目录下的 formula_manifest.json）")
    args = parser.parse_args()

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        print(f"错误：HTML 文件不存在 → {html_path}", file=sys.stderr)
        return 1

    manifest = run_check(html_path, engine=args.engine)
    if not manifest:
        return 1

    if args.output:
        out = Path(args.output).resolve()
        out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[formula-check] manifest 已写入 → {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
