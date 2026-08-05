#!/usr/bin/env python3
"""Interactive LLM research grilling script.

Asks the user questions → collects answers → generates structured grill report.
AI reads the report and gives judgment, scores, and next actions.

Usage:
    python grill.py --mode direction     # Problem/direction triage
    python grill.py --mode dataset       # Dataset interrogation
    python grill.py --mode framework     # PyTorch/LLM framework audit
    python grill.py --mode literature    # Paper/book grilling
    python grill.py --mode experiment    # Experiment design review
    python grill.py --mode defense       # Defense/advisor prep
    python grill.py --mode mixed         # Full research grill
    python grill.py --mode direction --output report.md
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
    """Ask questions one by one, collect answers."""
    answers = []
    for i, item in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"Question {i}/{len(questions)}")
        print(f"{'='*60}")
        print(f"\n{item['q']}")
        print(f"\n(Good answer: {item['good']})")
        print(f"(Bad signal: {item['bad']} → {item['fix']})")
        print()
        try:
            answer = input("Your answer: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nInterrupted. Collected answers saved.")
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


def render_report(mode: str, bank: dict, all_answers: list[dict]) -> str:
    lines = []
    lines.append(f"# Research Grill Report: {mode}\n")
    lines.append(f"Generated: {date.today().isoformat()}\n")

    # Research state snapshot
    lines.append("## Research State Snapshot\n")
    lines.append("| Dimension | Status | Evidence/Gap |")
    lines.append("|---|---|---|")
    for dim in ["problem", "data", "model/framework", "literature", "risk"]:
        lines.append(f"| {dim} | missing/partial/clear | |")
    lines.append("")

    # Answers
    for section in all_answers:
        lines.append(f"## {section['name']}\n")
        for a in section["answers"]:
            lines.append(f"### {a['question']}")
            lines.append(f"**Answer:** {a['answer'] if a['answer'] else '(no answer)'}")
            lines.append(f"**Good example:** {a['good_example']}")
            lines.append(f"**Bad signal:** {a['bad_signal']} → {a['fix_hint']}")
            lines.append("")

    # Scoreboard
    lines.append("## Scoreboard\n")
    lines.append("| Dimension | Score /5 | Reason | Evidence to improve by 1 point |")
    lines.append("|---|---:|---|---|")
    for dim in ["problem clarity", "dataset readiness", "implementation readiness", "literature grounding", "experiment validity", "novelty/contribution", "reproducibility"]:
        lines.append(f"| {dim} | | | |")
    lines.append("")

    # Verdicts from rubrics
    rubrics = bank.get("rubrics", {})
    if rubrics:
        lines.append("## Verdict Guide\n")
        for label, desc in rubrics.get("verdicts", {}).items():
            lines.append(f"- **{label.replace('_', ' ')}**: {desc}")
        lines.append("")

    # Sprint
    lines.append("## 24-Hour Research Sprint\n")
    lines.append("1. Fill the research state snapshot table.")
    lines.append("2. Produce the next artifact from the weakest grill round.")
    lines.append("3. Bring back one concrete piece of evidence: dataset sample, config, paper card, result table, or training log.")
    lines.append("")
    lines.append("## Evidence to Bring Back\n")
    lines.append("- ...")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive LLM research grilling.")
    parser.add_argument("--mode", choices=["direction", "dataset", "framework", "literature", "experiment", "defense", "mixed"], default="mixed")
    parser.add_argument("--output", help="Output report file path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bank = load_bank()

    # Determine which modes to run
    if args.mode == "mixed":
        modes = ["direction", "dataset", "framework", "literature", "experiment"]
    else:
        modes = [args.mode]

    all_answers = []
    for mode in modes:
        section = bank.get(mode)
        if not section:
            print(f"Warning: mode '{mode}' not found in question bank")
            continue
        print(f"\n\n{'#'*60}")
        print(f"# {section['name']}")
        print(f"{'#'*60}")
        answers = ask_questions(section["questions"])
        all_answers.append({"mode": mode, "name": section["name"], "answers": answers})

    report = render_report(args.mode, bank, all_answers)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"\nReport saved to: {out}")
    else:
        print("\n" + "="*60)
        print(report)


if __name__ == "__main__":
    main()
