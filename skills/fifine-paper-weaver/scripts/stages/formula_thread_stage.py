from __future__ import annotations

import json
from pathlib import Path

from schema import FORMULA_ALLOWED_ROLES, FORMULA_REQUIRED_FIELDS_BY_STAGE
from shared import check_leading_connectors

ASSET_PATH = Path(__file__).resolve().parents[2] / "assets" / "formula" / "templates.json"


def load_templates() -> dict:
    return json.loads(ASSET_PATH.read_text(encoding="utf-8"))


def build_skeleton(method_name: str, cycles: int = 3, symbols: int = 8, concepts: int = 3, intro: bool = True, splits: int = 1) -> dict:
    def empty_fields(kind: str) -> dict:
        return {k: "" for k in FORMULA_REQUIRED_FIELDS_BY_STAGE[kind]}

    nodes = []
    if intro:
        nodes.append({"kind": "intro", "formula_type": "", "fields": empty_fields("intro")})
    split_count = 0
    for i in range(1, cycles + 1):
        nodes.append({"kind": "problem", "formula_type": "", "fields": {**empty_fields("problem"), "stage_name": f"第{i}步"}})
        nodes.append({"kind": "tool", "formula_type": "", "fields": empty_fields("tool")})
        if split_count < splits:
            nodes.append({"kind": "split", "formula_type": "", "fields": empty_fields("split")})
            split_count += 1
        nodes.append({"kind": "resolution", "formula_type": "", "fields": empty_fields("resolution")})
    while split_count < splits:
        nodes.append({"kind": "split", "formula_type": "", "fields": empty_fields("split")})
        split_count += 1
    return {
        "method_name": method_name,
        "thesis_one_liner": "",
        "nodes": nodes,
        "symbol_table": [{"symbol": "", "meaning": "", "role": "", "shape": ""} for _ in range(symbols)],
        "concept_cards": [{"concept_name": "", "why_needed": "", "what_it_simplifies": "", "tradeoff": "", "plain_translation": ""} for _ in range(concepts)],
        "closing": {
            "opening_form_label": "",
            "opening_formula": "",
            "transformation_chain": "",
            "closing_formula": "",
            "thesis_method": method_name,
            "one_line_thesis": "",
        },
    }


def build_values_template(skeleton: dict) -> dict:
    return json.loads(json.dumps(skeleton, ensure_ascii=False))


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    result = json.loads(json.dumps(skeleton, ensure_ascii=False))
    missing = []
    result["method_name"] = values.get("method_name", "")
    result["thesis_one_liner"] = values.get("thesis_one_liner", "")
    if not str(result["method_name"]).strip():
        missing.append("method_name")
    if not str(result["thesis_one_liner"]).strip():
        missing.append("thesis_one_liner")
    nodes = values.get("nodes", [])
    if len(nodes) != len(result["nodes"]):
        missing.append(f"nodes.count(需要 {len(result['nodes'])}，当前 {len(nodes)})")
    else:
        for i, node in enumerate(nodes):
            kind = node.get("kind", result["nodes"][i]["kind"])
            result["nodes"][i]["kind"] = kind
            result["nodes"][i]["formula_type"] = node.get("formula_type", "")
            fields = node.get("fields", {})
            for key in FORMULA_REQUIRED_FIELDS_BY_STAGE[kind]:
                value = str(fields.get(key, "")).strip()
                if not value:
                    missing.append(f"nodes[{i}].fields.{key}")
                else:
                    result["nodes"][i]["fields"][key] = value
                    missing.extend(check_leading_connectors(f"nodes[{i}].fields.{key}", value))
    table = values.get("symbol_table", [])
    if not table:
        missing.append("symbol_table")
    else:
        result["symbol_table"] = table
        for i, row in enumerate(table):
            for key in ("symbol", "meaning", "role", "shape"):
                if not str(row.get(key, "")).strip():
                    missing.append(f"symbol_table[{i}].{key}")
            role = str(row.get("role", "")).strip()
            if role and role not in FORMULA_ALLOWED_ROLES:
                missing.append(f"symbol_table[{i}].role(非法: {role})")
    cards = values.get("concept_cards", [])
    if not cards:
        missing.append("concept_cards")
    else:
        result["concept_cards"] = cards
        for i, card in enumerate(cards):
            for key in ("concept_name", "why_needed", "what_it_simplifies", "tradeoff", "plain_translation"):
                if not str(card.get(key, "")).strip():
                    missing.append(f"concept_cards[{i}].{key}")
    closing = values.get("closing", {})
    for key in ("opening_form_label", "opening_formula", "transformation_chain", "closing_formula", "thesis_method", "one_line_thesis"):
        if not str(closing.get(key, "")).strip():
            missing.append(f"closing.{key}")
        else:
            result["closing"][key] = closing[key]
    return (result, []) if not missing else (None, missing)


def render(filled: dict) -> str:
    templates = load_templates()

    def render_node(node: dict) -> str:
        kind = node["kind"]
        fields = node["fields"]
        if kind == "intro":
            return templates["node_intro"].format(**fields)
        if kind == "problem":
            return templates["node_problem"].format(**fields)
        if kind == "tool":
            return templates["node_tool_intro"].format(**fields)
        if kind == "resolution":
            return templates["node_resolution"].format(**fields)
        if kind == "split":
            return templates["node_transition_split"].format(**fields)
        raise ValueError(f"未知节点类型: {kind}")

    parts = [f"# Method：{filled['method_name']} 的公式主线", "", filled["thesis_one_liner"], ""]
    for node in filled.get("nodes", []):
        parts.append(render_node(node))
        parts.append("")
    if filled.get("symbol_table"):
        header = "| 符号 | 含义 | 角色 | shape |\n|---|---|---|---|"
        body = "\n".join(templates["symbol_row"].format(**row) for row in filled["symbol_table"])
        parts.extend(["## 符号表", "", header, body, ""])
    if filled.get("concept_cards"):
        cards = "\n\n".join(templates["concept_card"].format(**c) for c in filled["concept_cards"])
        parts.extend(["## 概念功能卡", "", cards, ""])
    if filled.get("closing"):
        parts.extend(["## 总结", "", templates["closing_chain"].format(**filled["closing"])])
    return "\n".join(parts).strip() + "\n"


def run_check(filled: dict) -> list[str]:
    return []
