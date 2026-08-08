from __future__ import annotations
import copy

PLACEHOLDER = "<填: {}>"

KT_TAGS = [
    "K-架构创新", "K-训练策略", "K-数据增强", "K-评估基准",
    "T-应用场景", "T-任务适配", "T-系统集成",
]

REQUIRED_FIELDS = ["primary_kt_tag", "classification_reason"]

_TAGS_HINT = " / ".join(KT_TAGS)


def build_skeleton() -> dict:
    return {
        "primary_kt_tag": PLACEHOLDER.format(
            f"从以下标签中选一个（精确匹配）：{_TAGS_HINT}"
        ),
        "secondary_kt_tags": [PLACEHOLDER.format(
            f"次级标签（可多选，从上述列表中选）：{_TAGS_HINT}"
        )],
        "classification_reason": PLACEHOLDER.format(
            "判断理由：[主标签]，因为[论文贡献X]（见 Section Y），"
            "区别于[近似标签Z]的原因是[本质差异]。必须引用论文原句+章节"
        ),
        "evidence_sections": [PLACEHOLDER.format(
            "证据所在章节，如 Abstract / Section 3 / Table 2"
        )],
    }


def build_values_template() -> dict:
    return {
        "primary_kt_tag": "",
        "secondary_kt_tags": [],
        "classification_reason": "",
        "evidence_sections": [],
    }


def fill_values(skeleton: dict, values: dict) -> tuple[dict | None, list[str]]:
    missing = [k for k in REQUIRED_FIELDS if not str(values.get(k, "")).strip()]
    if missing:
        return None, missing
    result = copy.deepcopy(skeleton)
    result["primary_kt_tag"] = values.get("primary_kt_tag", "")
    result["secondary_kt_tags"] = values.get("secondary_kt_tags", [])
    result["classification_reason"] = values.get("classification_reason", "")
    result["evidence_sections"] = values.get("evidence_sections", [])
    return result, []


def run_check(filled: dict) -> list[str]:
    issues = []
    tag = filled.get("primary_kt_tag", "")
    if tag and tag not in KT_TAGS:
        issues.append(
            f"primary_kt_tag 值 '{tag}' 不在标准列表中。"
            f"请从以下选项中精确选择：{_TAGS_HINT}"
        )
    for t in filled.get("secondary_kt_tags", []):
        if t and t not in KT_TAGS:
            issues.append(f"secondary_kt_tag '{t}' 不在标准列表中")
    return issues


def render(filled: dict) -> str:
    primary = filled.get("primary_kt_tag", "—")
    secondary = filled.get("secondary_kt_tags", []) or []
    reason = filled.get("classification_reason", "—")
    evidence = filled.get("evidence_sections", []) or []

    tag_desc = {
        "K-架构创新": "核心贡献是提出新的模型结构或模块设计",
        "K-训练策略": "核心贡献是改进训练方法、损失函数或优化策略",
        "K-数据增强": "核心贡献是数据处理、增强或预处理技术",
        "K-评估基准": "核心贡献是建立新的评测任务或基准数据集",
        "T-应用场景": "把现有技术适配到特定应用场景或领域",
        "T-任务适配": "面向特定任务做结构或流程的针对性调整",
        "T-系统集成": "把多个组件或方法整合成完整系统",
    }
    desc = tag_desc.get(primary, "")

    lines = [
        "## K-T 分类\n",
        f"**主标签：{primary}**" + (f"　　_{desc}_" if desc else ""),
        "",
        f"**次级标签：** {', '.join(secondary) or '无'}",
        "",
        "**分类理由：**",
        f"> {reason}",
        "",
        f"**证据章节：** {', '.join(evidence) or '—'}",
        "",
    ]
    return "\n".join(lines)
