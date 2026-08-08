from __future__ import annotations

import copy

PLACEHOLDER = "<填: {}>"

REQUIRED_FIELDS = ["introduction", "method", "discussion"]

SECTIONS = [
    ("introduction", "Introduction", "Introduction 章节中可回调的内容（如动机、问题陈述）"),
    ("related_work", "Related Work", "Related Work 中引用本论文时可使用的角度"),
    ("method", "Method", "Method 章节中可回调的模块/公式/设计决策"),
    ("experiment", "Experiment", "Experiment 中可回调的设置、基线、指标"),
    ("discussion", "Discussion", "Discussion 中可回调的分析视角或对比结论"),
    ("limitation", "Limitation", "Limitation 章节中提到的局限性"),
    ("future_work", "Future Work", "Future Work 中可延伸的研究方向"),
]

_SECTION_HINTS = {
    "introduction": "写 Introduction 时可以引用这篇的[具体内容]来支撑[哪个论点]。例：引用 S4 在 LRA 的结果(Table 2)说明 SSM 在长程任务的有效性",
    "related_work": "写 Related Work 时可以把这篇放在[哪条演化线]上，对比点是[什么]。例：放在 SSM 发展线，对比 HiPPO→S4→Mamba 的参数化进化",
    "method": "写 Method 时可以借用这篇的[哪个技术组件]，复用点是[什么]。例：借用 DPLR 参数化思路，用于自己模型的结构化约束设计",
    "experiment": "写 Experiment 时可以用这篇的[哪个基准/结果]做对比基线。例：用 LRA 基准的 S4 结果作为长序列任务的强基线",
    "discussion": "写 Discussion 时可以引用这篇讨论[哪类局限/未来方向]。例：引用 S4 在非均匀采样场景的局限性讨论",
    "limitation": "这篇论文的[哪个局限]与你的工作相关，可以在你的 Limitation 中对照说明",
    "future_work": "这篇论文指出的[哪个方向]可以成为你的 Future Work，具体是[什么]",
}


def build_skeleton() -> dict:
    return {
        key: [PLACEHOLDER.format(_SECTION_HINTS[key])]
        for key, _, _ in SECTIONS
    }


def build_values_template() -> dict:
    return {key: [] for key, _, _ in SECTIONS}


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    missing = [k for k in REQUIRED_FIELDS if not values.get(k)]
    if missing:
        return None, missing
    result = copy.deepcopy(skeleton)
    for key, _, _ in SECTIONS:
        val = values.get(key, [])
        if isinstance(val, list):
            result[key] = [str(x) for x in val if str(x).strip()]
    return result, []


def run_check(filled: dict) -> list[str]:
    issues = []
    for key, label, _ in SECTIONS:
        val = filled.get(key, []) or []
        if key in REQUIRED_FIELDS and not val:
            issues.append(f"{label} 反向调用列表为空，请至少填写一条可回调内容")
    return issues


def render(filled: dict) -> str:
    ORDER = [
        ("introduction", "Introduction"),
        ("related_work", "Related Work"),
        ("method", "Method"),
        ("experiment", "Experiment"),
        ("discussion", "Discussion"),
        ("limitation", "Limitation"),
        ("future_work", "Future Work"),
    ]
    lines = ["## 反向调用映射\n"]
    for key, label in ORDER:
        items = filled.get(key, []) or []
        if items:
            lines.append(f"**{label}**")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")
    if len(lines) == 1:
        lines.append("_（所有章节均为空，请补充 values.json）_")
    return "\n".join(lines)
