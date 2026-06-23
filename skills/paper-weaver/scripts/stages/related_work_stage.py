from __future__ import annotations

import copy
import json
from pathlib import Path

from shared import find_unfilled, validate_no_braces

ASSET_PATH = Path(__file__).resolve().parents[2] / "assets" / "related_work" / "formula_templates.json"
PLACEHOLDER = "<填: {}>"
CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩", "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑳"]
STAGE1_FIELDS = {
    "O": "起源驱动", "X": "核心问题", "Y": "模型框架类型", "A": "早期作者", "yA": "早期作者年份",
    "mA": "A提出的方法", "opt": "A阶段的优化手段", "B": "扩展作者", "yB": "扩展作者年份",
    "ext": "B的扩展形式", "struct": "B引入的关键结构设计", "limA": "阶段①遗留限制",
}
TRANSITION_FIELDS = {"author": "该阶段作者", "year": "发表年份", "tform": "提出的模型形式", "param": "核心参数", "cost": "新增代价", "lim": "阶段遗留限制"}
FINAL_FIELDS = {"M": "本文方法", "design": "参数化设计/算法结构", "gen": "推广到的模型类别", "role": "本文在该脉络中的作用"}


def load_templates() -> dict:
    return json.loads(ASSET_PATH.read_text(encoding="utf-8"))


def build_skeleton(transitions: int = 1) -> dict:
    return {
        "stage1": {k: PLACEHOLDER.format(v) for k, v in STAGE1_FIELDS.items()},
        "transitions": [{k: PLACEHOLDER.format(v) for k, v in TRANSITION_FIELDS.items()} for _ in range(transitions)],
        "final": {k: PLACEHOLDER.format(v) for k, v in FINAL_FIELDS.items()},
    }


def build_values_template(transitions: int = 1) -> dict:
    return {
        "stage1": {k: "" for k in STAGE1_FIELDS},
        "transitions": [{k: "" for k in TRANSITION_FIELDS} for _ in range(transitions)],
        "final": {k: "" for k in FINAL_FIELDS},
    }


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    result = copy.deepcopy(skeleton)
    missing = []
    s1 = values.get("stage1", {})
    for key in STAGE1_FIELDS:
        if not str(s1.get(key, "")).strip():
            missing.append(f"stage1.{key}")
    transitions = values.get("transitions", [])
    if len(transitions) != len(skeleton["transitions"]):
        missing.append(f"transitions.count(需要 {len(skeleton['transitions'])}，当前 {len(transitions)})")
    else:
        for i, item in enumerate(transitions):
            for key in TRANSITION_FIELDS:
                if not str(item.get(key, "")).strip():
                    missing.append(f"transitions[{i}].{key}")
    final = values.get("final", {})
    for key in FINAL_FIELDS:
        if not str(final.get(key, "")).strip():
            missing.append(f"final.{key}")
    if missing:
        return None, missing
    result["stage1"].update(s1)
    for i, item in enumerate(transitions):
        result["transitions"][i].update(item)
    result["final"].update(final)
    brace_issues = validate_no_braces(result)
    if brace_issues:
        raise ValueError("\n".join(brace_issues))
    return result, []


def render(filled: dict) -> str:
    templates = load_templates()
    paragraphs = []
    stage1 = filled["stage1"]
    paragraphs.append(f"{CIRCLED[0]}{templates['stage_origin'].format(**stage1)}")
    prev_form = stage1["ext"]
    for i, t in enumerate(filled["transitions"]):
        paragraphs.append(f"{CIRCLED[i + 1]}{templates['stage_transition'].format(prev_form=prev_form, **t)}")
        prev_form = t["tform"]
    paragraphs.append(f"{CIRCLED[len(filled['transitions']) + 1]}{templates['stage_final'].format(limA=stage1['limA'], tform=prev_form, **filled['final'])}")
    return "\n\n".join(paragraphs).strip() + "\n"


def run_check(filled: dict) -> list[str]:
    return find_unfilled(filled)
