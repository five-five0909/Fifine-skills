from __future__ import annotations

import copy
import re

PLACEHOLDER = "<填: {}>"

FIELDS = {
    "paper_title": "论文完整标题（从 PDF 自动提取，请核实）",
    "authors_raw": "作者列表（原文格式，如 Gu, Albert et al.）",
    "year": "发表年份（4 位数字，如 2022）",
    "venue": "发表会议/期刊（如 ICLR 2022），查不到填 Unknown",
    "task": "研究任务，写法：动词+宾语，如「高效建模超长序列」，不要带「任务」二字",
    "modality": "数据模态，如 序列数据（文本/音频/时间序列）或 多模态",
    "one_line_problem": (
        "一句话说清核心矛盾：现有方法X在Y场景下有Z不足。"
        "例：Transformer在超长序列上二次复杂度导致速度和显存瓶颈"
    ),
    "one_line_method": (
        "一句话说清本文方案：提出X，用Y机制实现Z。"
        "例：提出S4，用结构化SSM参数化+高效卷积核把长程依赖从O(n²)降到近线性"
    ),
    "one_line_result": (
        "一句话量化结果：在X基准上超过Y，实现Z。"
        "例：LRA上超越所有Transformer基线，Path-X路径长度8192时效率提升60x"
    ),
    "reading_priority": "阅读优先级：高/中/低 + 一句理由，如 高——SSM奠基性工作，必读",
    "reference_key": "引用 key（自动生成），格式：年份_标题缩写_作者",
}

REQUIRED_FIELDS = ["paper_title", "year", "task", "one_line_problem", "one_line_method", "reference_key"]


def build_skeleton() -> dict:
    return {k: PLACEHOLDER.format(v) for k, v in FIELDS.items()}


def build_values_template() -> dict:
    return {k: "" for k in FIELDS}


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    missing = [k for k in REQUIRED_FIELDS if not str(values.get(k, "")).strip()]
    if missing:
        return None, missing
    result = copy.deepcopy(skeleton)
    result.update({k: v for k, v in values.items() if k in FIELDS})
    return result, []


def run_check(filled: dict) -> list[str]:
    issues = []
    key = filled.get("reference_key", "")
    if key:
        if not re.search(r"\d{4}", key):
            issues.append("reference_key 应包含年份（4位数字）")
        if "_" not in key:
            issues.append("reference_key 格式应为：年份_标题_作者")
    return issues


def render(filled: dict) -> str:
    rows = [
        ("paper_title", "论文标题"),
        ("authors_raw", "作者"),
        ("year", "年份"),
        ("venue", "会议/期刊"),
        ("task", "研究任务"),
        ("modality", "数据模态"),
        ("one_line_problem", "一句话问题"),
        ("one_line_method", "一句话方法"),
        ("one_line_result", "一句话结果"),
        ("reading_priority", "阅读优先级"),
        ("reference_key", "Reference Key"),
    ]
    lines = ["## 论文画像\n", "| 字段 | 内容 |", "| --- | --- |"]
    for key, label in rows:
        val = str(filled.get(key, "") or "—")
        lines.append(f"| {label} | {val} |")
    return "\n".join(lines) + "\n"
