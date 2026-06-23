from __future__ import annotations

import copy

PLACEHOLDER = "<填: {}>"

REQUIRED_FIELDS = ["main_contribution_summary"]

COMPONENTS = [
    ("input_encoding", "A 输入编码", "输入如何被表示/编码"),
    ("local_features", "B 局部特征", "局部特征提取机制"),
    ("global_interaction", "C 全局交互", "全局上下文交互方式"),
    ("long_range_modeling", "D 长程建模", "长距离依赖建模方法"),
    ("memory_update", "E 记忆更新", "记忆/状态更新机制"),
    ("gating_selection", "F 选择注意力", "门控或选择性注意力"),
    ("feature_fusion", "G 特征融合", "多分支/多模态融合策略"),
    ("training_stability", "H 训练稳定", "训练稳定性技巧（正则化/归一化等）"),
    ("acceleration", "I 计算加速", "计算效率优化（硬件/算法级别）"),
    ("knowledge_constraints", "J 知识约束", "引入领域知识或先验约束"),
]


def _component_skeleton(label: str) -> dict:
    return {
        "whether_present": False,
        "module_name": PLACEHOLDER.format(
            f"{label}：模块/层的实际名称（论文原词），如 HiPPO矩阵、SSM卷积核，不要写通用名"
        ),
        "what_problem_it_solves": PLACEHOLDER.format(
            f"{label}：这个组件具体解决了什么问题？"
            "格式：通过[技术手段]，解决了[具体问题]，效果是[可量化改进]"
        ),
    }


def _component_template() -> dict:
    return {
        "whether_present": False,
        "module_name": "",
        "what_problem_it_solves": "",
    }


def build_skeleton() -> dict:
    result = {}
    for key, label, description in COMPONENTS:
        result[key] = _component_skeleton(label)
    result["main_contribution_summary"] = PLACEHOLDER.format("主创新点总结（1-3句话）")
    return result


def build_values_template() -> dict:
    result = {}
    for key, _, _ in COMPONENTS:
        result[key] = _component_template()
    result["main_contribution_summary"] = ""
    return result


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    missing = [k for k in REQUIRED_FIELDS if not str(values.get(k, "")).strip()]
    if missing:
        return None, missing
    result = copy.deepcopy(skeleton)
    for key, _, _ in COMPONENTS:
        if key in values and isinstance(values[key], dict):
            comp = values[key]
            result[key] = {
                "whether_present": bool(comp.get("whether_present", False)),
                "module_name": comp.get("module_name", "") or "",
                "what_problem_it_solves": comp.get("what_problem_it_solves", "") or "",
            }
    result["main_contribution_summary"] = values.get("main_contribution_summary", "")
    return result, []


def run_check(filled: dict) -> list[str]:
    issues = []
    present_count = sum(
        1 for key, _, _ in COMPONENTS
        if filled.get(key, {}).get("whether_present", False)
    )
    if present_count == 0:
        issues.append("A-J 组件中没有任何一项标记为 whether_present=true，请检查是否漏填")
    return issues


def render(filled: dict) -> str:
    COMPONENT_LABELS = [
        ("input_encoding", "A 输入编码"),
        ("local_features", "B 局部特征"),
        ("global_interaction", "C 全局交互"),
        ("long_range_modeling", "D 长程建模"),
        ("memory_update", "E 记忆更新"),
        ("gating_selection", "F 门控/选择注意力"),
        ("feature_fusion", "G 特征融合"),
        ("training_stability", "H 训练稳定"),
        ("acceleration", "I 计算加速"),
        ("knowledge_constraints", "J 知识约束"),
    ]
    summary = filled.get("main_contribution_summary", "—")
    lines = [
        "## A-J 组件拆解\n",
        f"**主创新总结：** {summary}\n",
        "### 存在的组件\n",
    ]
    present = []
    for key, label in COMPONENT_LABELS:
        item = filled.get(key, {}) or {}
        if item.get("whether_present"):
            name = item.get("module_name", "—")
            problem = item.get("what_problem_it_solves", "—")
            present.append(f"**✓ {label}**\n- 模块：{name}\n- 解决问题：{problem}")
    if present:
        lines.extend(present)
    else:
        lines.append("_（所有组件均标记为不存在，请检查 values.json）_")
    return "\n\n".join(lines) + "\n"
