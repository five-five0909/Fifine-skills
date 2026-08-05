from __future__ import annotations

import copy
import json
from pathlib import Path

from schema import ABSTRACT_REQUIRED
from shared import find_unfilled, validate_no_braces

ASSET_PATH = Path(__file__).resolve().parents[2] / "assets" / "abstract" / "formula_templates.json"
PLACEHOLDER = "<填: {}>"
WHY_FIELDS = {
    "task": "XXX任务（论文研究的具体任务/场景，不要带“任务”二字，模板已经加了）",
    "methods": "现有方法（A/B/C，列出被比较的旧方法）",
    "capability": "现有方法欠缺的关键能力",
    "scenario": "表现受限的具体场景（如长序列/高复杂度/大规模数据）",
}
HOW_FIELDS = {
    "method_name": "本文提出的方法名称",
    "mechanism": "核心机制（关键技术/结构变换/优化方式）",
    "capability_achieved": "该机制实现的能力",
    "effect": "由此带来的效果，写成完整短句",
}
SO_WHAT_FIELDS = {
    "benchmark": "实验验证用的数据集/基准",
    "improvement": "取得的具体改进，写成名词短语",
}
CHECK_MARKERS = [
    ("问题 (Why)", 0, ["不足", "受限", "局限"]),
    ("方法 (How)", 1, ["提出", "通过"]),
    ("证据 (So what)", 2, ["实验表明", "优于", "改进", "实现", "验证"]),
]


def load_templates() -> dict:
    return json.loads(ASSET_PATH.read_text(encoding="utf-8"))


def build_skeleton() -> dict:
    return {
        "why": {k: PLACEHOLDER.format(v) for k, v in WHY_FIELDS.items()},
        "how": {k: PLACEHOLDER.format(v) for k, v in HOW_FIELDS.items()},
        "so_what": {k: PLACEHOLDER.format(v) for k, v in SO_WHAT_FIELDS.items()},
    }


def build_values_template() -> dict:
    return {
        "why": {k: "" for k in WHY_FIELDS},
        "how": {k: "" for k in HOW_FIELDS},
        "so_what": {k: "" for k in SO_WHAT_FIELDS},
    }


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    result = copy.deepcopy(skeleton)
    missing = []
    why = values.get("why", {})
    how = values.get("how", {})
    so_what = values.get("so_what", {})
    for group, required, source in [
        ("why", ABSTRACT_REQUIRED["why"], why),
        ("how", ABSTRACT_REQUIRED["how"], how),
        ("so_what", ABSTRACT_REQUIRED["so_what"], so_what),
    ]:
        for key in required:
            if not str(source.get(key, "")).strip():
                missing.append(f"{group}.{key}")
    if missing:
        return None, missing
    result["why"].update(why)
    result["how"].update(how)
    result["so_what"].update(so_what)
    brace_issues = validate_no_braces(result)
    if brace_issues:
        raise ValueError("\n".join(brace_issues))
    return result, []


def render(filled: dict) -> str:
    templates = load_templates()
    why_data = filled["why"]
    if why_data.get("methods2", "").strip():
        why = templates["why_contrast"].format(**why_data)
    else:
        why = templates["why_single"].format(**why_data)
    how = templates["how"].format(**filled["how"])
    so_what = templates["so_what"].format(**filled["so_what"])
    return "\n".join([why, how, so_what]).strip() + "\n"


def run_check(filled: dict) -> list[str]:
    sentences = render(filled).strip().splitlines()
    issues = []
    for label, idx, markers in CHECK_MARKERS:
        if not any(m in sentences[idx] for m in markers):
            issues.append(f"{label} 对应的第{idx + 1}句未命中判定关键词")
    issues.extend(find_unfilled(filled))
    return issues
