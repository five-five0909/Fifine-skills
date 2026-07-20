from __future__ import annotations

import copy
import json
from pathlib import Path

from shared import find_unfilled, validate_no_braces

ASSET_PATH = Path(__file__).resolve().parents[2] / "assets" / "introduction" / "formula_templates.json"
PLACEHOLDER = "<填: {}>"
STAGE1_FIELDS = {
    "X": "研究领域",
    "Y": "（可选）核心问题/研究对象或现象",
    "goal_verb": "研究目标的动词（解释/预测/改善）",
    "Z": "目标能力",
    "A": "已有研究路径或方法集合",
}
STAGE2_FIELDS = {
    "B": "关键情境/条件/范围",
    "core_problem": "GAP 所在的核心问题描述",
    "req1": "现有方法无法同时满足的关键要求1",
    "req2": "现有方法无法同时满足的关键要求2",
}
STAGE3_FIELDS = {
    "M": "本文提出的新方法/新理论/新框架/新模型",
    "mechanism": "关键机制/核心思想/方法路径",
    "old_structure": "（可选）原有问题结构",
    "new_form": "（可选）转化后的新形式",
}


def load_templates() -> dict:
    return json.loads(ASSET_PATH.read_text(encoding="utf-8"))


def build_skeleton() -> dict:
    return {
        "stage1": {k: PLACEHOLDER.format(v) for k, v in STAGE1_FIELDS.items()},
        "stage2": {
            **{k: PLACEHOLDER.format(v) for k, v in STAGE2_FIELDS.items()},
            "limitations": [PLACEHOLDER.format("局限1"), PLACEHOLDER.format("局限2")],
        },
        "stage3": {k: PLACEHOLDER.format(v) for k, v in STAGE3_FIELDS.items()},
    }


def build_values_template() -> dict:
    return {
        "stage1": {"X": "", "Y": "", "goal_verb": "", "Z": "", "A": ""},
        "stage2": {"B": "", "limitations": ["", ""], "core_problem": "", "req1": "", "req2": ""},
        "stage3": {"M": "", "mechanism": "", "old_structure": "", "new_form": ""},
    }


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    result = copy.deepcopy(skeleton)
    missing = []
    s1, s2, s3 = values.get("stage1", {}), values.get("stage2", {}), values.get("stage3", {})
    for key in ("X", "goal_verb", "Z", "A"):
        if not str(s1.get(key, "")).strip():
            missing.append(f"stage1.{key}")
    for key in ("B", "core_problem", "req1", "req2"):
        if not str(s2.get(key, "")).strip():
            missing.append(f"stage2.{key}")
    limitations = s2.get("limitations", [])
    if not isinstance(limitations, list) or not any(str(x).strip() for x in limitations):
        missing.append("stage2.limitations")
    for key in ("M", "mechanism"):
        if not str(s3.get(key, "")).strip():
            missing.append(f"stage3.{key}")
    paired = [bool(str(s3.get(k, "")).strip()) for k in ("old_structure", "new_form")]
    if any(paired) and not all(paired):
        missing.append("stage3.old_structure+new_form")
    if missing:
        return None, missing
    result["stage1"].update(s1)
    result["stage2"].update({**s2, "limitations": [x for x in limitations if str(x).strip()]})
    result["stage3"].update(s3)
    if not paired:
        result["stage3"]["old_structure"] = ""
        result["stage3"]["new_form"] = ""
    brace_issues = validate_no_braces(result)
    if brace_issues:
        raise ValueError("\n".join(brace_issues))
    return result, []


def render_paragraphs(filled: dict) -> list[str]:
    templates = load_templates()
    s1, s2, s3 = filled["stage1"], filled["stage2"], filled["stage3"]
    p1 = templates["stage1_sentence1_full"].format(**s1) if s1.get("Y", "").strip() else templates["stage1_sentence1_short"].format(**s1)
    p1 += templates["stage1_sentence2"].format(**s1)
    s2_render = dict(s2)
    s2_render["limitations"] = "、".join(s2["limitations"])
    p2 = templates["stage2_sentence1"].format(**s2_render) + templates["stage2_sentence2"].format(**s2_render)
    if s3.get("old_structure", "").strip() and s3.get("new_form", "").strip():
        p3 = templates["stage3_sentence1_full"].format(Z=s1["Z"], **s3)
    else:
        p3 = templates["stage3_sentence1_short"].format(Z=s1["Z"], **s3)
    return [f"①{p1}", f"②{p2}", f"③{p3}"]


def render_gap_table(filled: dict) -> str:
    s1, s2, s3 = filled["stage1"], filled["stage2"], filled["stage3"]
    rows = [
        ("关键情境/范围 B", s2["B"]),
        ("现有局限", "、".join(s2["limitations"])),
        ("核心问题/GAP 描述", s2["core_problem"]),
        ("无法同时满足的要求", f"{s2['req1']} vs {s2['req2']}"),
        ("本文方法 M", s3["M"]),
        ("核心机制", s3["mechanism"]),
        ("目标能力 Z（呼应①）", s1["Z"]),
    ]
    lines = ["| 项目 | 内容 |", "|---|---|"]
    lines.extend([f"| {k} | {v} |" for k, v in rows])
    return "\n".join(lines)


def render(filled: dict) -> str:
    paragraphs = render_paragraphs(filled)
    gap_table = render_gap_table(filled)
    return "\n\n".join(paragraphs) + "\n\n## GAP 表\n\n" + gap_table + "\n"


def run_check(filled: dict) -> list[str]:
    issues = find_unfilled(filled)
    s1, s2, s3 = filled["stage1"], filled["stage2"], filled["stage3"]
    answer = (
        f"作者插入的研究缝隙是：现有方法无法同时满足「{s2['req1']}」与「{s2['req2']}」；"
        f"本文通过「{s3['mechanism']}」提出「{s3['M']}」，弥合了这一缝隙，使「{s1['Z']}」得以改进。"
    )
    if not answer.strip():
        issues.append("判定句生成异常")
    return issues
