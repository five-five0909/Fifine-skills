from __future__ import annotations

import json
from pathlib import Path

from shared import check_leading_connectors

ASSET_PATH = Path(__file__).resolve().parents[2] / "assets" / "experiments" / "templates.json"
ALLOWED_ABLATION_VERDICTS = ("真贡献", "部分贡献", "可能只是包装", "证据不足以判断")


def load_templates() -> dict:
    return json.loads(ASSET_PATH.read_text(encoding="utf-8"))


def build_skeleton(method_name: str, claim_ids: list[str] | None = None, section_ids: list[str] | None = None, ablations: int = 1, efficiency: bool = True) -> dict:
    claim_ids = claim_ids or ["claim1"]
    section_ids = section_ids or ["4.1"]
    claims = [{"claim_id": cid, "claim_name": "", "claim_origin": "", "claim_statement": ""} for cid in claim_ids]
    sections = [{"section_id": sid, "claim_id": claim_ids[min(i, len(claim_ids) - 1)], "evidence": [{"table_or_fig": "", "comparison_desc": "", "result_desc": ""}], "section_takeaway": ""} for i, sid in enumerate(section_ids)]
    ablation_checks = [{"module_name": "", "has_ablation_evidence": False, "ablation_table_or_section": "", "ablation_result": "", "verdict": "", "scope_note": "", "supported_claim": "", "where_to_look": ""} for _ in range(ablations)]
    data = {
        "method_name": method_name,
        "claims": claims,
        "experiment_sections": sections,
        "ablation_checks": ablation_checks,
        "overall_verdict": "",
        "anti_pattern": "某一张表分数最高",
        "evidence_chain_thesis": "",
    }
    if efficiency:
        data["efficiency_check"] = {"efficiency_evidence": "", "efficiency_verdict": "", "verdict_category": ""}
    return data


def build_values_template(skeleton: dict) -> dict:
    return json.loads(json.dumps(skeleton, ensure_ascii=False))


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    data = json.loads(json.dumps(skeleton, ensure_ascii=False))
    missing = []
    data["method_name"] = values.get("method_name", "")
    if not str(data["method_name"]).strip():
        missing.append("method_name")
    claims = values.get("claims", [])
    if len(claims) != len(data["claims"]):
        missing.append(f"claims.count(需要 {len(data['claims'])}，当前 {len(claims)})")
    else:
        data["claims"] = claims
        for i, claim in enumerate(claims):
            for key in ("claim_id", "claim_name", "claim_origin", "claim_statement"):
                if not str(claim.get(key, "")).strip():
                    missing.append(f"claims[{i}].{key}")
    known_ids = {c.get("claim_id") for c in claims if str(c.get("claim_id", "")).strip()}
    sections = values.get("experiment_sections", [])
    if len(sections) != len(data["experiment_sections"]):
        missing.append(f"experiment_sections.count(需要 {len(data['experiment_sections'])}，当前 {len(sections)})")
    else:
        data["experiment_sections"] = sections
        for i, section in enumerate(sections):
            for key in ("section_id", "claim_id", "section_takeaway"):
                if not str(section.get(key, "")).strip():
                    missing.append(f"experiment_sections[{i}].{key}")
            if section.get("claim_id") not in known_ids:
                missing.append(f"experiment_sections[{i}].claim_id(未定义: {section.get('claim_id')})")
            evidence = section.get("evidence", [])
            if not evidence:
                missing.append(f"experiment_sections[{i}].evidence")
            else:
                for j, ev in enumerate(evidence):
                    for key in ("table_or_fig", "comparison_desc", "result_desc"):
                        if not str(ev.get(key, "")).strip():
                            missing.append(f"experiment_sections[{i}].evidence[{j}].{key}")
                        else:
                            missing.extend(check_leading_connectors(f"experiment_sections[{i}].evidence[{j}].{key}", ev.get(key, "")))
    checks = values.get("ablation_checks", [])
    if len(checks) != len(data["ablation_checks"]):
        missing.append(f"ablation_checks.count(需要 {len(data['ablation_checks'])}，当前 {len(checks)})")
    else:
        data["ablation_checks"] = checks
        for i, item in enumerate(checks):
            if not str(item.get("module_name", "")).strip():
                missing.append(f"ablation_checks[{i}].module_name")
            if item.get("has_ablation_evidence") is True:
                for key in ("ablation_table_or_section", "ablation_result", "verdict"):
                    if not str(item.get(key, "")).strip():
                        missing.append(f"ablation_checks[{i}].{key}")
                verdict = item.get("verdict", "")
                if verdict and verdict not in ALLOWED_ABLATION_VERDICTS:
                    missing.append(f"ablation_checks[{i}].verdict(非法: {verdict})")
            elif item.get("has_ablation_evidence") is False:
                for key in ("scope_note", "supported_claim", "where_to_look"):
                    if not str(item.get(key, "")).strip():
                        missing.append(f"ablation_checks[{i}].{key}")
            else:
                missing.append(f"ablation_checks[{i}].has_ablation_evidence")
    if "efficiency_check" in data:
        eff = values.get("efficiency_check", {})
        data["efficiency_check"] = eff
        for key in ("efficiency_evidence", "efficiency_verdict"):
            if not str(eff.get(key, "")).strip():
                missing.append(f"efficiency_check.{key}")
    for key in ("overall_verdict", "anti_pattern", "evidence_chain_thesis"):
        if not str(values.get(key, "")).strip():
            missing.append(key)
        else:
            data[key] = values[key]
    return (data, []) if not missing else (None, missing)


def render(filled: dict) -> str:
    templates = load_templates()
    claims = filled["claims"]
    claims_by_id = {c["claim_id"]: c for c in claims}
    claims_list = "、".join(c["claim_name"] for c in claims)
    paragraphs = [templates["opening"].format(method_name=filled["method_name"], n_claims=len(claims), claims_list=claims_list)]
    for section in filled["experiment_sections"]:
        claim = claims_by_id[section["claim_id"]]
        pieces = []
        for i, ev in enumerate(section["evidence"]):
            sentence = templates["evidence_sentence_single"].format(**ev)
            if i < len(section["evidence"]) - 1 and sentence.endswith("。"):
                sentence = sentence[:-1] + "；"
            pieces.append(sentence)
        body = templates["section_block"].format(section_id=section["section_id"], claim_name=claim["claim_name"], evidence_sentences="".join(pieces), section_takeaway=section["section_takeaway"])
        support = templates["section_support_line"].format(section_id=section["section_id"], target_claim_origin=claim["claim_origin"], claim_name=claim["claim_name"])
        paragraphs.append(body + " " + support)
    if filled.get("ablation_checks"):
        ablation_parts = []
        for item in filled["ablation_checks"]:
            if item["has_ablation_evidence"]:
                ablation_parts.append(templates["ablation_present"].format(**item))
            else:
                ablation_parts.append(templates["ablation_absent"].format(scope_note=item["scope_note"], module_list=item["module_name"], supported_claim=item["supported_claim"], where_to_look=item["where_to_look"]))
        paragraphs.append(" ".join(ablation_parts))
    if filled.get("efficiency_check"):
        paragraphs.append(templates["efficiency_block"].format(**filled["efficiency_check"]))
    recap = "；".join([f"通过{s['section_id']}节说明{claims_by_id[s['claim_id']]['claim_name']}方面的{s['section_takeaway']}" for s in filled["experiment_sections"]])
    paragraphs.append(templates["closing"].format(method_name=filled["method_name"], overall_verdict=filled["overall_verdict"], claim_to_evidence_recap=recap, anti_pattern=filled["anti_pattern"], evidence_chain_thesis=filled["evidence_chain_thesis"]))
    return "\n\n".join(paragraphs).strip() + "\n"


def run_check(filled: dict) -> list[str]:
    return []
