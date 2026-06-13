#!/usr/bin/env python3
"""草稿审计脚本。

读取用户的草稿文件 → 逐部分检查 → 输出审计表。
检查项来自 question_bank.json 的 audit 部分。

用法：
    python audit.py --draft draft.md                  # 审计草稿
    python audit.py --draft draft.md --output audit.md # 输出到文件
    python audit.py --draft draft.md --section title   # 只审计标题
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BANK_PATH = SCRIPT_DIR / "question_bank.json"


def load_bank() -> dict:
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def split_sections(text: str) -> dict[str, str]:
    """把草稿按标题拆成部分。"""
    sections = {}
    current = "preamble"
    buf = []
    for line in text.split("\n"):
        if re.match(r"^#{1,2}\s+", line):
            if buf:
                sections[current] = "\n".join(buf).strip()
            current = line.lstrip("#").strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections[current] = "\n".join(buf).strip()
    return sections


def detect_title(sections: dict) -> str | None:
    for key in sections:
        if key == "preamble" and sections[key]:
            return sections[key].split("\n")[0]
    return None


def check_title(title: str | None) -> list[dict]:
    checks = []
    if not title:
        return [{"check": "标题存在", "pass": False, "note": "未检测到标题"}]
    checks.append({"check": "标题存在", "pass": True, "note": title})
    checks.append({"check": "有具体对象", "pass": len(title) > 5, "note": "标题太短可能缺乏具体性"})
    checks.append({"check": "无空泛词", "pass": not re.search(r"浅谈|论|研究|分析|探讨", title),
                    "note": "检测到空泛词" if re.search(r"浅谈|论|研究|分析|探讨", title) else "没有空泛词"})
    checks.append({"check": "长度合理", "pass": len(title) <= 25, "note": f"{len(title)}字"})
    return checks


def check_section(name: str, content: str, checks_def: list[str]) -> list[dict]:
    results = []
    for check_name in checks_def:
        if "主题句" in check_name:
            has_topic = content.strip() and len(content.strip().split("\n")[0]) < 100
            results.append({"check": check_name, "pass": has_topic,
                          "note": "段首有短句" if has_topic else "段首过长或无主题句"})
        elif "证据" in check_name and "来源" not in check_name:
            has_evidence = bool(re.search(r"\d+%|\d+人|\d+篇|数据|案例|访谈|调查|统计", content))
            results.append({"check": check_name, "pass": has_evidence,
                          "note": "检测到证据词" if has_evidence else "未检测到具体证据"})
        elif "来源" in check_name:
            has_source = bool(re.search(r"\(\d{4}\)|\[\d+\]|据.*报道|根据.*研究|来源", content))
            results.append({"check": check_name, "pass": has_source,
                          "note": "检测到来源标注" if has_source else "未检测到来源标注"})
        elif "过渡" in check_name:
            has_transition = bool(re.search(r"然而|但是|因此|所以|此外|另外|同时|首先|其次|最后|一方面|另一方面", content))
            results.append({"check": check_name, "pass": has_transition,
                          "note": "检测到过渡词" if has_transition else "未检测到过渡词"})
        elif "问题" in check_name and "引言" in name:
            has_question = bool(re.search(r"[？?]|\b为什么\b|\b如何\b|\b是否\b|\b怎样\b", content))
            results.append({"check": check_name, "pass": has_question,
                          "note": "检测到疑问" if has_question else "未检测到疑问句"})
        elif "主张" in check_name:
            has_claim = bool(re.search(r"本文认为|我认为|我主张|核心观点|本文发现|研究表明", content))
            results.append({"check": check_name, "pass": has_claim,
                          "note": "检测到主张" if has_claim else "未检测到明确主张"})
        else:
            results.append({"check": check_name, "pass": bool(content.strip()),
                          "note": "有内容" if content.strip() else "内容为空"})
    return results


def render_audit_report(sections: dict, audit_def: dict) -> str:
    lines = []
    lines.append(f"# 草稿审计报告\n")
    lines.append(f"生成日期：{date.today().isoformat()}\n")

    # 标题检查
    title = detect_title(sections)
    lines.append("## 标题审计\n")
    lines.append("| 检查项 | 通过 | 说明 |")
    lines.append("|---|---|---|")
    for c in check_title(title):
        lines.append(f"| {c['check']} | {'是' if c['pass'] else '否'} | {c['note']} |")
    lines.append("")

    # 逐部分检查
    section_checks = {
        "摘要": audit_def.get("abstract_checks", []),
        "引言": audit_def.get("intro_checks", []),
        "正文": audit_def.get("body_checks", []),
        "结论": audit_def.get("conclusion_checks", []),
        "参考文献": audit_def.get("references_checks", []),
    }

    for section_name, checks_def in section_checks.items():
        matched = None
        for key in sections:
            if section_name in key or key in section_name:
                matched = sections[key]
                break
        if matched is None and section_name == "正文":
            # 正文可能没有明确标题，取最长的部分
            body_candidates = {k: v for k, v in sections.items()
                             if k not in ["preamble", "摘要", "引言", "结论", "参考文献"]
                             and k != "标题"}
            if body_candidates:
                matched = max(body_candidates.values(), key=len)

        lines.append(f"## {section_name}审计\n")
        lines.append("| 检查项 | 通过 | 说明 |")
        lines.append("|---|---|---|")
        if matched:
            for c in check_section(section_name, matched, checks_def):
                lines.append(f"| {c['check']} | {'是' if c['pass'] else '否'} | {c['note']} |")
        else:
            lines.append(f"| 未检测到{section_name} | 否 | 草稿中未找到该部分 |")
        lines.append("")

    # 段落级检查
    lines.append("## 段落级检查\n")
    lines.append("| 段落(前20字) | 长度 | 有主题句 | 有证据 | 有来源 |")
    lines.append("|---|---:|---|---|---|")
    for section_content in sections.values():
        paragraphs = [p.strip() for p in section_content.split("\n\n") if p.strip()]
        for p in paragraphs[:20]:  # 最多检查20段
            preview = p[:20].replace("\n", " ")
            length = len(p)
            has_topic = len(p.split("\n")[0]) < 80
            has_evidence = bool(re.search(r"\d+%|\d+人|\d+篇|数据|案例|访谈", p))
            has_source = bool(re.search(r"\(\d{4}\)|\[\d+\]|据.*报道", p))
            lines.append(f"| {preview}... | {length} | {'是' if has_topic else '否'} | {'是' if has_evidence else '否'} | {'是' if has_source else '否'} |")
    lines.append("")

    lines.append("## AI 需要判断\n")
    lines.append("1. 标题是否足够具体？")
    lines.append("2. 摘要是否包含问题、主张、方法、发现？")
    lines.append("3. 引言是否在3段内提出问题？")
    lines.append("4. 正文每段是否有主题句和证据？")
    lines.append("5. 结论是否回答引言的问题？")
    lines.append("6. 有没有正确废话需要删除？")
    lines.append("7. 有没有学生腔/学术腔/官腔需要改写？")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="草稿审计。")
    parser.add_argument("--draft", required=True, help="草稿文件路径。")
    parser.add_argument("--section", help="只审计指定部分。")
    parser.add_argument("--output", help="输出报告文件路径。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    draft_path = Path(args.draft)
    if not draft_path.exists():
        print(f"错误：找不到文件 {draft_path}")
        return

    text = draft_path.read_text(encoding="utf-8")
    bank = load_bank()
    audit_def = bank.get("audit", {})

    sections = split_sections(text)
    report = render_audit_report(sections, audit_def)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"审计报告已保存到：{out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
