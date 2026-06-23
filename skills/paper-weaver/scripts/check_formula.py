#!/usr/bin/env python3
"""check_formula.py — 从 HTML 报告中提取公式清单，生成 formula_manifest.json。

职责：仅提取公式，生成 manifest。不判断质量，不修改 HTML。
引擎：katex
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


# 匹配 render_html_report.py 生成的 math-block 结构
_MATH_BLOCK_RE = re.compile(r'<div class="math-block">\$\$(.*?)\$\$</div>', re.S)

# 用于推断 source 字段：找最近的 <section id="..."> 或 <h2>
_SECTION_ID_RE = re.compile(r'<section[^>]+id=["\']([^"\']+)["\']', re.I)
_H2_TEXT_RE = re.compile(r'<h2[^>]*>(.*?)</h2>', re.I | re.S)


def _strip_tags(text: str) -> str:
    """去除 HTML 标签，仅保留文字内容。"""
    return re.sub(r'<[^>]+>', '', text).strip()


def _infer_source(html: str, match_start: int) -> str:
    """在公式节点前扫描，找最近的 <section id="..."> 或 <h2> 标签。"""
    fragment = html[:match_start]

    # 找所有 section id
    section_matches = list(_SECTION_ID_RE.finditer(fragment))
    # 找所有 h2
    h2_matches = list(_H2_TEXT_RE.finditer(fragment))

    candidates: list[tuple[int, str]] = []
    if section_matches:
        m = section_matches[-1]
        candidates.append((m.start(), m.group(1)))
    if h2_matches:
        m = h2_matches[-1]
        candidates.append((m.start(), _strip_tags(m.group(1))))

    if not candidates:
        return "unknown"

    # 取位置最靠近公式的那个（最大 start）
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1] or "unknown"


def extract_formulas(html: str) -> list[dict]:
    """从 HTML 字符串中提取所有 display 公式，返回公式列表。"""
    formulas = []
    for idx, m in enumerate(_MATH_BLOCK_RE.finditer(html)):
        raw = m.group(1).strip()
        start = m.start()
        end = m.end()

        context_before = html[max(0, start - 50):start]
        context_after = html[end:end + 50]

        # 去除上下文中的 HTML 标签，保留纯文字
        context_before = _strip_tags(context_before)
        context_after = _strip_tags(context_after)

        source = _infer_source(html, start)

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


def run_check(html_path: str | Path, engine: str = "katex") -> dict:
    """提取公式清单并写入 formula_manifest.json。

    供 run_pipeline.py 直接 import 调用。

    Args:
        html_path: HTML 文件路径（str 或 Path）
        engine: 公式渲染引擎标识，默认 "katex"

    Returns:
        manifest dict
    """
    html_path = Path(html_path).resolve()
    html_content = html_path.read_text(encoding="utf-8")

    formulas = extract_formulas(html_content)

    output_path = html_path.parent / "formula_manifest.json"

    manifest = {
        "html_path": str(html_path),
        "engine": engine,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "total": len(formulas),
        "formulas": formulas,
    }

    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[formula-check] 已提取 {len(formulas)} 条公式 → {output_path}")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description="从 HTML 报告提取公式清单")
    ap.add_argument("--html", required=True, help="HTML 报告路径")
    ap.add_argument("--engine", default="katex", help="公式引擎标识（默认 katex）")
    ap.add_argument("--output", default="", help="输出路径；默认与 HTML 同目录的 formula_manifest.json")
    args = ap.parse_args()

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        print(f"[formula-check] 错误：HTML 文件不存在：{html_path}")
        return 1

    manifest = run_check(html_path, engine=args.engine)

    # 若指定了自定义输出路径，则额外写一份
    if args.output:
        custom_out = Path(args.output).resolve()
        custom_out.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[formula-check] 已额外写出到：{custom_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
