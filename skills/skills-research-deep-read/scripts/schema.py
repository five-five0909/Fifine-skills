from __future__ import annotations

ABSTRACT_REQUIRED = {
    "why": ["task", "methods", "capability", "scenario"],
    "how": ["method_name", "mechanism", "capability_achieved", "effect"],
    "so_what": ["benchmark", "improvement"],
}

INTRO_REQUIRED = {
    "stage1": ["X", "goal_verb", "Z", "A"],
    "stage2": ["B", "limitations", "core_problem", "req1", "req2"],
    "stage3": ["M", "mechanism"],
}

RELATED_REQUIRED = {
    "stage1": ["O", "X", "Y", "A", "yA", "mA", "opt", "B", "yB", "ext", "struct", "limA"],
    "transition": ["author", "year", "tform", "param", "cost", "lim"],
    "final": ["M", "design", "gen", "role"],
}

FORMULA_ALLOWED_ROLES = {"输入", "状态", "参数", "输出", "中间变量"}
FORMULA_REQUIRED_FIELDS_BY_STAGE = {
    "intro": ["lead_in", "formula", "gloss"],
    "problem": ["stage_name", "capability", "limitation", "problem_statement", "goal_statement"],
    "tool": ["tool_purpose", "tool_name", "tool_statement_label", "tool_formula", "tool_gloss"],
    "resolution": ["unit_label", "problem_recap", "solution_recap"],
    "split": ["whole_label", "part_a_label", "part_b_label"],
}
