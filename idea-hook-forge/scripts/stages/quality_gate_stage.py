from __future__ import annotations

import copy

PLACEHOLDER = "<填: {}>"

REQUIRED_FIELDS = ["overall_hook_level", "quality_summary"]

HOOK_LEVELS = ("高", "中", "低")


def build_skeleton() -> dict:
    return {
        "overall_hook_level": PLACEHOLDER.format("整体 Hook 等级：高 / 中 / 低"),
        "should_enter_project_plan": PLACEHOLDER.format("true/false，是否应纳入项目计划"),
        "manual_review_needed": PLACEHOLDER.format("true/false，是否需要人工复核"),
        "unresolved_fields": [PLACEHOLDER.format("未解决的字段名列表（可为空列表）")],
        "quality_summary": PLACEHOLDER.format(
            "总结格式：这篇论文的核心钩子是[X]，"
            "读完后最值得做的1件事是[Y]（具体到可执行的实验/写作动作），"
            "最危险的过度解读是[Z]"
        ),
    }


def build_values_template() -> dict:
    return {
        "overall_hook_level": "",
        "should_enter_project_plan": False,
        "manual_review_needed": False,
        "unresolved_fields": [],
        "quality_summary": "",
    }


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    missing = [k for k in REQUIRED_FIELDS if not str(values.get(k, "")).strip()]
    if missing:
        return None, missing
    result = copy.deepcopy(skeleton)
    result["overall_hook_level"] = values.get("overall_hook_level", "")
    result["should_enter_project_plan"] = bool(values.get("should_enter_project_plan", False))
    result["manual_review_needed"] = bool(values.get("manual_review_needed", False))
    result["unresolved_fields"] = list(values.get("unresolved_fields", []) or [])
    result["quality_summary"] = values.get("quality_summary", "")
    return result, []


def run_check(filled: dict) -> list[str]:
    issues = []
    level = filled.get("overall_hook_level", "")
    if level and level not in HOOK_LEVELS:
        issues.append(f"overall_hook_level 应为：高/中/低，当前值：{level}")
    return issues


def render(filled: dict) -> str:
    def yes_no(flag) -> str:
        return "是" if flag else "否"

    level = filled.get("overall_hook_level", "—")
    summary = filled.get("quality_summary", "—")
    enter_plan = yes_no(filled.get("should_enter_project_plan", False))
    manual = yes_no(filled.get("manual_review_needed", False))
    unresolved = filled.get("unresolved_fields", []) or []

    lines = [
        "## 质量门控\n",
        f"**质量总结：** {summary}\n",
        "| 字段 | 内容 |",
        "| --- | --- |",
        f"| 整体 Hook 等级 | {level} |",
        f"| 纳入项目计划 | {enter_plan} |",
        f"| 需要人工复核 | {manual} |",
        f"| 未解决字段 | {', '.join(unresolved) or '无'} |",
    ]
    return "\n".join(lines) + "\n"
