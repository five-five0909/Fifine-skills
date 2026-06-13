#!/usr/bin/env python3
"""交互式写前审问脚本。

问用户问题 → 收集回答 → 生成结构化审问报告。
AI 读取报告后给出判断、评分和下一步动作。

用法：
    python grill.py --mode topic        # 选题审问
    python grill.py --mode material     # 素材审计
    python grill.py --mode structure    # 结构预审
    python grill.py --mode argument     # 论证压力测试
    python grill.py --mode full         # 综合审问
    python grill.py --mode topic --output report.md  # 输出到文件
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BANK_PATH = SCRIPT_DIR / "question_bank.json"


def load_bank() -> dict:
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def ask_questions(questions: list[dict]) -> list[dict]:
    """逐个问问题，收集用户回答。"""
    answers = []
    for i, item in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"问题 {i}/{len(questions)}")
        print(f"{'='*60}")
        print(f"\n{item['q']}")
        print(f"\n（好答案示例：{item['good']}）")
        print(f"（烂答案说明：{item['bad']} → {item['fix']}）")
        print()
        try:
            answer = input("你的回答：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n中断。已收集的回答已保存。")
            break
        answers.append({
            "id": item["id"],
            "question": item["q"],
            "answer": answer,
            "good_example": item["good"],
            "bad_signal": item["bad"],
            "fix_hint": item["fix"],
        })
    return answers


def render_topic_report(answers: list[dict]) -> str:
    lines = []
    lines.append(f"# 选题审问报告\n")
    lines.append(f"生成日期：{date.today().isoformat()}\n")
    lines.append("## 写前状态快照\n")
    lines.append("| 维度 | 状态 | 证据/缺口 |")
    lines.append("|---|---|---|")
    lines.append("| 问题 | 待AI判断 | |")
    lines.append("| 读者 | 待AI判断 | |")
    lines.append("| 素材 | 待AI判断 | |")
    lines.append("| 结构 | 待AI判断 | |")
    lines.append("| 风险 | 待AI判断 | |")
    lines.append("")
    lines.append("## 用户回答\n")
    for a in answers:
        lines.append(f"### {a['question']}")
        lines.append(f"**回答：** {a['answer'] if a['answer'] else '（未回答）'}")
        lines.append(f"**好答案参考：** {a['good_example']}")
        lines.append(f"**烂答案信号：** {a['bad_signal']} → {a['fix_hint']}")
        lines.append("")
    lines.append("## AI 需要判断\n")
    lines.append("对每个回答判断：答得好 / 答得烂 / 没回答。")
    lines.append("对答得烂的追问，对没回答的标记风险。")
    lines.append("")
    lines.append("## 评分\n")
    lines.append("| 维度 | 分数/5 | 原因 | 下一步 |")
    lines.append("|---|---:|---|---|")
    lines.append("| 问题清晰度 | | | |")
    lines.append("| 读者定位 | | | |")
    lines.append("| 素材充分度 | | | |")
    lines.append("| 论证强度 | | | |")
    lines.append("| 结构完整度 | | | |")
    lines.append("| 表达信心 | | | |")
    lines.append("")
    lines.append("## 写前冲刺\n")
    lines.append("- 今天：")
    lines.append("- 本周：")
    lines.append("- 下次带回：")
    return "\n".join(lines)


def render_material_report(answers: list[dict]) -> str:
    lines = []
    lines.append(f"# 素材审计报告\n")
    lines.append(f"生成日期：{date.today().isoformat()}\n")
    lines.append("## 素材清单\n")
    lines.append("| 类型 | 来源 | 支撑什么 | 可靠性 |")
    lines.append("|---|---|---|---|")
    lines.append("| 待整理 | | | |")
    lines.append("")
    lines.append("## 用户回答\n")
    for a in answers:
        lines.append(f"### {a['question']}")
        lines.append(f"**回答：** {a['answer'] if a['answer'] else '（未回答）'}")
        lines.append(f"**好答案参考：** {a['good_example']}")
        lines.append(f"**烂答案信号：** {a['bad_signal']} → {a['fix_hint']}")
        lines.append("")
    lines.append("## 缺口清单\n")
    lines.append("| 缺什么 | 去哪找 | 关键词 |")
    lines.append("|---|---|---|")
    lines.append("| 待整理 | | |")
    lines.append("")
    lines.append("## AI 需要判断\n")
    lines.append("1. 素材是否够写？不够的话缺什么？")
    lines.append("2. 核心文献和背景分清了吗？")
    lines.append("3. They say / I say 位置清楚吗？")
    return "\n".join(lines)


def render_structure_report(answers: list[dict]) -> str:
    lines = []
    lines.append(f"# 结构预审报告\n")
    lines.append(f"生成日期：{date.today().isoformat()}\n")
    lines.append("## 大纲矩阵\n")
    lines.append("| 部分 | 回答什么问题 | 关系 |")
    lines.append("|---|---|---|")
    lines.append("| 引言 | | |")
    lines.append("| 正文1 | | |")
    lines.append("| 正文2 | | |")
    lines.append("| 正文3 | | |")
    lines.append("| 结论 | | |")
    lines.append("")
    lines.append("## 用户回答\n")
    for a in answers:
        lines.append(f"### {a['question']}")
        lines.append(f"**回答：** {a['answer'] if a['answer'] else '（未回答）'}")
        lines.append(f"**好答案参考：** {a['good_example']}")
        lines.append(f"**烂答案信号：** {a['bad_signal']} → {a['fix_hint']}")
        lines.append("")
    lines.append("## AI 需要判断\n")
    lines.append("1. 大纲每部分是否回答一个子问题？")
    lines.append("2. 各部分之间关系是否清楚？")
    lines.append("3. 引言是否在3段内提出问题？")
    lines.append("4. 结论是否回答引言的问题？")
    return "\n".join(lines)


def render_argument_report(answers: list[dict]) -> str:
    lines = []
    lines.append(f"# 论证压力测试报告\n")
    lines.append(f"生成日期：{date.today().isoformat()}\n")
    lines.append("## 论证树\n")
    lines.append("```")
    lines.append("问题：[待填写]")
    lines.append("├── 观点：[待填写]")
    lines.append("│   ├── 理由1 → 证据（来源？）")
    lines.append("│   ├── 理由2 → 证据（来源？）")
    lines.append("│   └── 理由3 → 证据（来源？）")
    lines.append("├── 反对意见 → 回应")
    lines.append("└── 限定条件")
    lines.append("```")
    lines.append("")
    lines.append("## 用户回答\n")
    for a in answers:
        lines.append(f"### {a['question']}")
        lines.append(f"**回答：** {a['answer'] if a['answer'] else '（未回答）'}")
        lines.append(f"**好答案参考：** {a['good_example']}")
        lines.append(f"**烂答案信号：** {a['bad_signal']} → {a['fix_hint']}")
        lines.append("")
    lines.append("## AI 需要判断\n")
    lines.append("1. 论证类型是什么？（事实/价值/政策/概念/解释）")
    lines.append("2. 每个理由有证据吗？证据有来源吗？")
    lines.append("3. 有反对意见和回应吗？")
    lines.append("4. 有限定条件吗？")
    return "\n".join(lines)


def render_full_report(bank: dict) -> str:
    lines = []
    lines.append(f"# 综合写前审问报告\n")
    lines.append(f"生成日期：{date.today().isoformat()}\n")
    all_answers = []
    for mode in ["topic", "material", "structure", "argument"]:
        section = bank[mode]
        print(f"\n\n{'#'*60}")
        print(f"# {section['name']}")
        print(f"{'#'*60}")
        answers = ask_questions(section["questions"])
        all_answers.append({"mode": mode, "name": section["name"], "answers": answers})

    lines.append("## 写前状态快照\n")
    lines.append("| 维度 | 状态 | 证据/缺口 |")
    lines.append("|---|---|---|")
    lines.append("| 问题 | 待AI判断 | |")
    lines.append("| 读者 | 待AI判断 | |")
    lines.append("| 素材 | 待AI判断 | |")
    lines.append("| 结构 | 待AI判断 | |")
    lines.append("| 风险 | 待AI判断 | |")
    lines.append("")

    for section in all_answers:
        lines.append(f"## {section['name']}\n")
        for a in section["answers"]:
            lines.append(f"### {a['question']}")
            lines.append(f"**回答：** {a['answer'] if a['answer'] else '（未回答）'}")
            lines.append(f"**好答案参考：** {a['good_example']}")
            lines.append(f"**烂答案信号：** {a['bad_signal']} → {a['fix_hint']}")
            lines.append("")

    lines.append("## 评分\n")
    lines.append("| 维度 | 分数/5 | 原因 | 下一步 |")
    lines.append("|---|---:|---|---|")
    lines.append("| 问题清晰度 | | | |")
    lines.append("| 读者定位 | | | |")
    lines.append("| 素材充分度 | | | |")
    lines.append("| 论证强度 | | | |")
    lines.append("| 结构完整度 | | | |")
    lines.append("| 表达信心 | | | |")
    lines.append("")
    lines.append("## 写前冲刺\n")
    lines.append("- 今天：")
    lines.append("- 本周：")
    lines.append("- 下次带回：")
    return "\n".join(lines)


RENDERERS = {
    "topic": lambda bank: render_topic_report(ask_questions(bank["topic"]["questions"])),
    "material": lambda bank: render_material_report(ask_questions(bank["material"]["questions"])),
    "structure": lambda bank: render_structure_report(ask_questions(bank["structure"]["questions"])),
    "argument": lambda bank: render_argument_report(ask_questions(bank["argument"]["questions"])),
    "full": render_full_report,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="交互式写前审问。")
    parser.add_argument("--mode", choices=sorted(RENDERERS.keys()), default="full")
    parser.add_argument("--output", help="输出报告文件路径。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bank = load_bank()
    report = RENDERERS[args.mode](bank)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"\n报告已保存到：{out}")
    else:
        print("\n" + "="*60)
        print(report)


if __name__ == "__main__":
    main()
