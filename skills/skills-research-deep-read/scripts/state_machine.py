from __future__ import annotations

STAGE_ORDER = [
    "abstract",
    "introduction",
    "related_work",
    "method_overview",
    "formula_thread",
    "experiments",
]

MODE_TO_STAGES = {
    "first-pass": ["abstract", "introduction", "related_work"],
    "second-pass": ["method_overview", "formula_thread", "experiments"],
    "full": STAGE_ORDER,
}


MODULE_KEYWORDS = {
    "abstract": ["abstract", "摘要"],
    "introduction": ["introduction", "intro", "引言", "前言", "gap", "故事线"],
    "related_work": ["related work", "related", "相关工作", "文献综述"],
    "method_overview": ["method", "方法", "方法主线"],
    "formula_thread": ["formula", "公式", "推导", "符号表"],
    "experiments": ["experiment", "experiments", "实验", "消融", "效率"],
}


def resolve_auto_plan(request_text: str | None) -> tuple[str, list[str] | None]:
    text = (request_text or "").lower()

    explicit_modules = [
        module
        for module, keywords in MODULE_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]

    only_markers = ["只看", "只读", "只做", "仅看", "仅做", "单看", "单独看"]
    if explicit_modules:
        unique_modules = []
        for module in STAGE_ORDER:
            if module in explicit_modules:
                unique_modules.append(module)
        if len(unique_modules) == 1 and any(marker in text for marker in only_markers):
            return "custom", unique_modules
        if len(unique_modules) >= 2:
            return "custom", unique_modules
        if unique_modules == ["experiments"] and any(marker in text for marker in only_markers):
            return "custom", unique_modules
        if unique_modules == ["formula_thread"] and any(marker in text for marker in only_markers):
            return "custom", unique_modules
        if unique_modules == ["method_overview"] and any(marker in text for marker in only_markers):
            return "custom", unique_modules
        if unique_modules == ["abstract"] and any(marker in text for marker in only_markers):
            return "custom", unique_modules
        if unique_modules == ["introduction"] and any(marker in text for marker in only_markers):
            return "custom", unique_modules
        if unique_modules == ["related_work"] and any(marker in text for marker in only_markers):
            return "custom", unique_modules

    if any(k in text for k in ["全部", "完整", "全面", "full", "all"]):
        return "full", None
    if any(k in text for k in ["精读", "深读", "方法", "公式", "实验", "method", "formula", "experiment"]):
        return "second-pass", None
    if any(k in text for k in ["abstract", "introduction", "related", "摘要", "引言", "相关工作"]):
        return "first-pass", None
    return "first-pass", None


def resolve_stage_sequence(mode: str, modules: list[str] | None = None) -> list[str]:
    if mode != "custom":
        return MODE_TO_STAGES[mode]
    if not modules:
        raise ValueError("custom 模式必须通过 --modules 提供至少一个模块")
    selected = set(modules)
    unknown = selected - set(STAGE_ORDER)
    if unknown:
        raise ValueError(f"未知模块: {sorted(unknown)}")
    return [stage for stage in STAGE_ORDER if stage in selected]
