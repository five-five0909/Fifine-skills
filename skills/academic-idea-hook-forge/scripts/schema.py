from __future__ import annotations

STAGE_ORDER = [
    'paper_profile',
    'kt_classification',
    'aj_component_breakdown',
    'u_formula_tags',
    'hook_extraction',
    'reverse_call_map',
    'quality_gate',
]

# 各 stage 的必填字段由各自的 stage 模块自维护。
# 此处保留 REQUIRED_FIELDS 供外部（如测试、文档工具）向后兼容访问。
REQUIRED_FIELDS = {
    'paper_profile': ['paper_title', 'year', 'task', 'one_line_problem', 'one_line_method', 'reference_key'],
    'kt_classification': ['primary_kt_tag', 'classification_reason'],
    'aj_component_breakdown': ['main_contribution_summary'],
    'u_formula_tags': ['u_tags'],
    'hook_extraction': ['problem_hook', 'method_hook', 'experiment_hook', 'writing_hook'],
    'reverse_call_map': ['introduction', 'method', 'discussion'],
    'quality_gate': ['overall_hook_level', 'quality_summary'],
}
