from __future__ import annotations

import json
from pathlib import Path

from shared import validate_no_braces

ASSET_PATH = Path(__file__).resolve().parents[2] / "assets" / "method_overview" / "templates.json"
FIELDS = [
    "method_name", "problem_statement", "task_scope", "bottleneck",
    "pipeline_overview", "key_mechanisms", "target_capability",
    "base_object", "new_form", "preserved_advantage", "improved_aspect",
]


def load_templates() -> dict:
    return json.loads(ASSET_PATH.read_text(encoding="utf-8"))


def build_skeleton(method_name: str) -> dict:
    return {
        "method_name": method_name,
        "problem_statement": "<填: 方法真正要解决的问题>",
        "task_scope": "<填: 任务/数据/场景>",
        "bottleneck": "<填: 旧方法的计算或建模瓶颈>",
        "pipeline_overview": "<填: 方法总路径，用箭头串起来>",
        "key_mechanisms": "<填: 关键机制列表，用顿号分隔>",
        "target_capability": "<填: 方法服务的目标能力>",
        "base_object": "<填: 被改写/重构的原对象>",
        "new_form": "<填: 改写后的新形式>",
        "preserved_advantage": "<填: 保留的优势>",
        "improved_aspect": "<填: 改善的方面>",
    }


def build_values_template(method_name: str) -> dict:
    return {k: (method_name if k == "method_name" else "") for k in FIELDS}


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    missing = [k for k in FIELDS if not str(values.get(k, skeleton.get(k, ""))).strip()]
    if missing:
        return None, missing
    result = {k: values.get(k, skeleton.get(k, "")) for k in FIELDS}
    brace_issues = validate_no_braces(result)
    if brace_issues:
        raise ValueError("\n".join(brace_issues))
    return result, []


def render(filled: dict) -> str:
    templates = load_templates()
    return "\n\n".join([
        templates["paragraph_1"].format(**filled),
        templates["paragraph_2"].format(**filled),
        templates["paragraph_3"].format(**filled),
    ]).strip() + "\n"


def run_check(filled: dict) -> list[str]:
    return []
