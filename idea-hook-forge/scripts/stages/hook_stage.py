from __future__ import annotations

import copy

PLACEHOLDER = "<填: {}>"

REQUIRED_FIELDS = ["problem_hook", "method_hook", "experiment_hook", "writing_hook"]

HOOK_TYPES = [
    ("problem_hook", "问题 Hook", "描述论文核心问题陈述的 Hook"),
    ("method_hook", "方法 Hook", "描述核心方法或技术创新的 Hook"),
    ("variable_hook", "变量 Hook", "描述关键变量/参数设计的 Hook"),
    ("experiment_hook", "实验 Hook", "描述实验设计或亮点结果的 Hook"),
    ("explanation_hook", "解释 Hook", "描述直觉解释或可视化展示的 Hook"),
    ("counterexample_hook", "反例 Hook", "描述反直觉结果或对比实验的 Hook"),
    ("failure_hook", "失败 Hook", "描述方法局限或失败案例的 Hook"),
    ("writing_hook", "写作 Hook", "描述论文写作风格或表达技巧的 Hook"),
]


def _hook_skeleton(description: str) -> dict:
    return {
        "hook_statement": PLACEHOLDER.format(
            f"{description}——写一句有冲击感的核心句，可改写或引用原文。"
            "例：'标准RNN无法并行，Transformer无法处理超长序列——S4一步解决了两者'"
        ),
        "concrete_action": PLACEHOLDER.format(
            f"{description}——基于此 Hook 你能采取的具体行动。"
            "要具体到：在自己的[具体模型/实验]中用[具体方法]实现[具体目标]"
        ),
        "hook_level": PLACEHOLDER.format("Hook 强度等级：高 / 中 / 低"),
        "evidence_from_paper": PLACEHOLDER.format(
            f"{description}——原文引用：[章节] + [关键数据或结论句]。"
            "例：Table 2，Path-X任务准确率从50%提升到88.1%"
        ),
    }


def _hook_template() -> dict:
    return {
        "hook_statement": "",
        "concrete_action": "",
        "hook_level": "",
        "evidence_from_paper": "",
    }


def build_skeleton() -> dict:
    return {key: _hook_skeleton(description) for key, _, description in HOOK_TYPES}


def build_values_template() -> dict:
    return {key: _hook_template() for key, _, _ in HOOK_TYPES}


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    missing = []
    for req in REQUIRED_FIELDS:
        hook = values.get(req, {}) or {}
        if not str(hook.get("hook_statement", "")).strip():
            missing.append(req)
    if missing:
        return None, missing
    result = copy.deepcopy(skeleton)
    for key, _, _ in HOOK_TYPES:
        if key in values and isinstance(values[key], dict):
            h = values[key]
            result[key] = {
                "hook_statement": h.get("hook_statement", "") or "",
                "concrete_action": h.get("concrete_action", "") or "",
                "hook_level": h.get("hook_level", "") or "",
                "evidence_from_paper": h.get("evidence_from_paper", "") or "",
            }
    return result, []


def run_check(filled: dict) -> list[str]:
    issues = []
    for key, label, _ in HOOK_TYPES:
        hook = filled.get(key, {}) or {}
        level = hook.get("hook_level", "")
        if level and level not in ("高", "中", "低"):
            issues.append(f"{label} hook_level 应为：高/中/低，当前值：{level}")
    return issues


def render(filled: dict) -> str:
    LEVEL_MARK = {"高": "🔴 高", "中": "🟡 中", "低": "🟢 低"}
    lines = ["## Hook 提取\n"]
    for key, label, _ in HOOK_TYPES:
        item = filled.get(key, {}) or {}
        stmt = item.get("hook_statement", "—")
        action = item.get("concrete_action", "—")
        level_raw = item.get("hook_level", "—")
        level = LEVEL_MARK.get(level_raw, level_raw)
        evidence = item.get("evidence_from_paper", "—")
        lines.append(
            f"### {label}　{level}\n\n"
            f"**核心句：** {stmt}\n\n"
            f"**可行动作：** {action}\n\n"
            f"**原文证据：** {evidence}\n"
        )
    return "\n".join(lines)
