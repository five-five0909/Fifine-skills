from __future__ import annotations

import copy

PLACEHOLDER = "<填: {}>"

REQUIRED_FIELDS = ["u_tags"]


def build_skeleton() -> dict:
    return {
        "u_tags": [PLACEHOLDER.format(
            "U 标签：每个核心公式的角色标注，从以下选择："
            "输入/状态/参数/输出/中间变量。格式：'公式编号: 角色'，如 'Eq.1: 状态'"
        )],
        "formula_blocks": [{
            "latex_source": PLACEHOLDER.format("LaTeX 公式源码（严格对照论文原文，不得改写）"),
            "equation_id": PLACEHOLDER.format("公式编号，如 Eq. (1) 或 (3.2)"),
            "explanation": PLACEHOLDER.format(
                "解释格式（三层）：\n"
                "①符号含义：逐符号说明每个变量代表什么\n"
                "②推导作用：这步公式在整个推导链中干了什么\n"
                "③设计动机：为什么要这样设计，解决了什么问题\n"
                "要求：不少于 3 句，具体到数学含义"
            ),
        }],
        "formula_thread_summary": PLACEHOLDER.format(
            "公式主线叙述：用 3-5 句话串起核心公式链，每句对应一个关键推导步骤。"
            "例：先定义连续SSM(Eq.1)→离散化零阶保持(Eq.3)→DPLR降秩参数化(Eq.5)→卷积核高效计算(Eq.7)"
        ),
    }


def build_values_template() -> dict:
    return {
        "u_tags": [],
        "formula_blocks": [],
        "formula_thread_summary": "",
    }


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    missing = []
    u_tags = values.get("u_tags", [])
    if not u_tags:
        missing.append("u_tags")
    if missing:
        return None, missing
    result = copy.deepcopy(skeleton)
    result["u_tags"] = u_tags
    blocks = values.get("formula_blocks", []) or []
    result["formula_blocks"] = [
        {
            "latex_source": b.get("latex_source", "") or "",
            "equation_id": b.get("equation_id", "") or "Unnumbered",
            "explanation": b.get("explanation", "") or "",
        }
        for b in blocks
        if isinstance(b, dict)
    ]
    result["formula_thread_summary"] = values.get("formula_thread_summary", "") or ""
    return result, []


def run_check(filled: dict) -> list[str]:
    issues = []
    blocks = filled.get("formula_blocks", []) or []
    for i, block in enumerate(blocks):
        if not block.get("latex_source", "").strip():
            issues.append(f"formula_blocks[{i}] latex_source 为空，请填入论文原始公式")
    return issues


def render(filled: dict) -> str:
    tags = filled.get("u_tags", []) or []
    blocks = filled.get("formula_blocks", []) or []
    summary = filled.get("formula_thread_summary", "") or "—"

    lines = [
        "## U 公式标签\n",
        f"**U 标签：** {', '.join(tags) or '—'}\n",
        f"**公式主线：** {summary}\n",
        "### 公式块列表\n",
    ]
    for i, block in enumerate(blocks, 1):
        eq_id = block.get("equation_id", "Unnumbered")
        latex = block.get("latex_source", "")
        explain = block.get("explanation", "—")
        lines.append(f"**[{i}] {eq_id}**\n")
        lines.append(f"$$\n{latex}\n$$\n")
        lines.append(f"> {explain}\n")
    return "\n".join(lines)
