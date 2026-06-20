from __future__ import annotations

import html
from pathlib import Path

from shared import read_json

MATHJAX = """
<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
  },
  svg: {fontCache: 'global'}
};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
"""


def _yes_no(flag) -> str:
    return "是" if flag else "否"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def render_formula_blocks(blocks):
    if not blocks:
        return '<div class="callout orange"><b>公式区：</b>当前还没有填入公式，请在 values.json 中补齐公式原文、编号和解释。</div>'
    parts = []
    for item in blocks:
        eq = item.get("latex_source", "").strip()
        meta = item.get("equation_id", "Unnumbered")
        explain = item.get("explanation", "")
        parts.append(
            f'<div class="formula-block">'
            f'<div class="formula-meta">{html.escape(meta)}</div>'
            f'<div class="formula-math">\\[{eq}\\]</div>'
            f'<div class="formula-explain">{html.escape(explain)}</div>'
            f'</div>'
        )
    return "\n".join(parts)


def render_component_table(aj: dict) -> str:
    rows = []
    mapping = [
        ("A 输入编码", "input_encoding"),
        ("B 局部特征", "local_features"),
        ("C 全局交互", "global_interaction"),
        ("D 长程建模", "long_range_modeling"),
        ("E 记忆更新", "memory_update"),
        ("F 选择注意力", "gating_selection"),
        ("G 特征融合", "feature_fusion"),
        ("H 训练稳定", "training_stability"),
        ("I 计算加速", "acceleration"),
        ("J 知识约束", "knowledge_constraints"),
    ]
    for label, key in mapping:
        item = aj.get(key, {}) or {}
        rows.append([
            html.escape(label),
            _yes_no(item.get("whether_present", False)),
            html.escape(item.get("module_name", "") or "—"),
            html.escape(item.get("what_problem_it_solves", "") or "—"),
        ])
    return _table(["组件类", "是否出现", "模块名", "解决问题"], rows)


def render_hooks_table(hooks: dict) -> str:
    rows = []
    mapping = [
        ("问题 Hook", "problem_hook"),
        ("方法 Hook", "method_hook"),
        ("变量 Hook", "variable_hook"),
        ("实验 Hook", "experiment_hook"),
        ("解释 Hook", "explanation_hook"),
        ("反例 Hook", "counterexample_hook"),
        ("失败 Hook", "failure_hook"),
        ("写作 Hook", "writing_hook"),
    ]
    for label, key in mapping:
        item = hooks.get(key, {}) or {}
        rows.append([
            html.escape(label),
            html.escape(item.get("hook_statement", "") or "—"),
            html.escape(item.get("concrete_action", "") or "—"),
            html.escape(item.get("hook_level", "") or "—"),
            html.escape(item.get("evidence_from_paper", "") or "—"),
        ])
    return _table(["Hook 类型", "核心句", "可行动作", "等级", "证据"], rows)


def render_reverse(reverse: dict) -> str:
    rows = []
    order = [
        ("Introduction", "introduction"),
        ("Related Work", "related_work"),
        ("Method", "method"),
        ("Experiment", "experiment"),
        ("Discussion", "discussion"),
        ("Limitation", "limitation"),
        ("Future Work", "future_work"),
    ]
    for label, key in order:
        value = reverse.get(key, []) or []
        rows.append([html.escape(label), "<br/>".join(html.escape(str(x)) for x in value) or "—"])
    return _table(["写作位置", "可回调内容"], rows)


def render_profile_cards(profile: dict, kt: dict, quality: dict) -> str:
    badges = [
        f'<span class="badge">Reference Key：{html.escape(profile.get("reference_key", ""))}</span>',
        f'<span class="badge">年份：{html.escape(profile.get("year", ""))}</span>',
        f'<span class="badge">Venue：{html.escape(profile.get("venue", "") or "待补齐")}</span>',
        f'<span class="badge">K-T：{html.escape(kt.get("primary_kt_tag", "") or "待分类")}</span>',
        f'<span class="badge">Hook Level：{html.escape(quality.get("overall_hook_level", "") or "待评估")}</span>',
    ]
    return (
        '<div class="badges">' + "".join(badges) + "</div>"
        + '<div class="summary-grid">'
        + f'<div class="summary-card"><div class="label">任务</div><div class="value">{html.escape(profile.get("task", "") or "待补齐")}</div></div>'
        + f'<div class="summary-card"><div class="label">模态</div><div class="value">{html.escape(profile.get("modality", "") or "待补齐")}</div></div>'
        + f'<div class="summary-card"><div class="label">一句话问题</div><div class="value">{html.escape(profile.get("one_line_problem", "") or "待补齐")}</div></div>'
        + f'<div class="summary-card"><div class="label">一句话方法</div><div class="value">{html.escape(profile.get("one_line_method", "") or "待补齐")}</div></div>'
        + "</div>"
    )


def render(output_dir: Path) -> Path:
    stage_map = {
        "profile": "01_paper_profile",
        "kt": "02_kt_classification",
        "aj": "03_aj_component_breakdown",
        "u": "04_u_formula_tags",
        "hooks": "05_hook_extraction",
        "reverse": "06_reverse_call_map",
        "quality": "07_quality_gate",
    }
    profile = read_json(output_dir / "stages" / stage_map["profile"] / "filled.json")
    kt = read_json(output_dir / "stages" / stage_map["kt"] / "filled.json")
    aj = read_json(output_dir / "stages" / stage_map["aj"] / "filled.json")
    uf = read_json(output_dir / "stages" / stage_map["u"] / "filled.json")
    hooks = read_json(output_dir / "stages" / stage_map["hooks"] / "filled.json")
    reverse = read_json(output_dir / "stages" / stage_map["reverse"] / "filled.json")
    quality = read_json(output_dir / "stages" / stage_map["quality"] / "filled.json")

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(profile.get('paper_title', 'Idea Hook Forge Report'))}</title>
  {MATHJAX}
  <style>
    :root {{
      --bg:#f6f8fa; --panel:#fff; --border:#d0d7de; --muted:#57606a; --text:#24292f;
      --accent:#0969da; --accent-soft:#ddf4ff; --warning:#9a6700; --warning-bg:#fff8c5;
      --orange-bg:#fff4e8; --orange-border:#ffdfbd; --shadow:0 8px 24px rgba(140,149,159,.18);
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--text); background:radial-gradient(circle at top right, rgba(9,105,218,.08), transparent 25%), linear-gradient(180deg, #f8fbff 0%, var(--bg) 280px); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,"PingFang SC","Microsoft YaHei",sans-serif; }}
    .page {{ width:min(1280px, calc(100vw - 32px)); margin:24px auto 64px; }}
    .hero {{ background:linear-gradient(135deg, #fff 0%, #f6faff 100%); border:1px solid var(--border); border-radius:20px; padding:28px; box-shadow:var(--shadow); margin-bottom:20px; }}
    .hero h1 {{ margin:0 0 10px; font-size:34px; line-height:1.2; }}
    .hero .subtitle {{ color:var(--muted); margin:0 0 18px; font-size:15px; }}
    .badges {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:18px; }}
    .badge {{ border:1px solid var(--border); background:#fff; border-radius:999px; padding:6px 12px; font-size:13px; color:var(--muted); }}
    .summary-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-top:18px; }}
    .summary-card {{ background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:16px; }}
    .summary-card .label {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.06em; margin-bottom:8px; }}
    .summary-card .value {{ font-size:15px; line-height:1.6; font-weight:600; }}
    .layout {{ display:grid; grid-template-columns:260px minmax(0,1fr); gap:20px; align-items:start; }}
    .toc {{ position:sticky; top:20px; background:var(--panel); border:1px solid var(--border); border-radius:18px; padding:18px; box-shadow:var(--shadow); }}
    .toc h2 {{ margin:0 0 12px; font-size:16px; }}
    .toc a {{ display:block; color:var(--accent); text-decoration:none; padding:7px 0; font-size:14px; }}
    .toc a:hover {{ text-decoration:underline; }}
    .content-shell {{ background:var(--panel); border:1px solid var(--border); border-radius:20px; box-shadow:var(--shadow); overflow:hidden; }}
    .report-body {{ max-width:none; background:transparent; padding:28px; font-size:16px; line-height:1.78; }}
    .report-section {{ scroll-margin-top:24px; margin-bottom:28px; }}
    .section-header {{ margin:0 0 16px; padding-bottom:10px; border-bottom:1px solid var(--border); }}
    .callout {{ border-left:4px solid var(--accent); background:var(--accent-soft); padding:14px 16px; border-radius:10px; margin:18px 0; }}
    .callout.orange {{ border-left-color:var(--warning); background:var(--warning-bg); }}
    table {{ width:100%; border-collapse:separate; border-spacing:0; margin:14px 0 20px; border:1px solid var(--border); border-radius:12px; overflow:hidden; background:#fff; font-size:14px; }}
    th,td {{ border-bottom:1px solid var(--border); border-right:1px solid var(--border); padding:10px 12px; vertical-align:top; text-align:left; }}
    th:last-child,td:last-child {{ border-right:0; }}
    tr:last-child td {{ border-bottom:0; }}
    th {{ background:#fbfaf8; color:#4b5563; font-weight:650; }}
    .mini-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin:18px 0; }}
    .mini-card {{ border:1px solid var(--border); border-radius:14px; padding:14px 16px; background:#fff; }}
    .mini-card h3 {{ margin:0 0 10px; font-size:16px; }}
    .formula-block {{ background:#fff; border:1px solid var(--border); border-radius:14px; padding:16px; margin:14px 0; }}
    .formula-meta {{ font-size:13px; color:var(--muted); margin-bottom:8px; }}
    .formula-explain {{ background:var(--orange-bg); border:1px solid var(--orange-border); border-radius:10px; padding:10px 12px; margin-top:10px; }}
    .footer-note {{ margin-top:32px; padding-top:20px; border-top:1px solid var(--border); color:var(--muted); font-size:14px; }}
    @media (max-width:960px) {{ .summary-grid,.layout,.mini-grid {{ grid-template-columns:1fr; }} .toc {{ position:static; }} .hero h1 {{ font-size:28px; }} }}
  </style>
</head>
<body>
  <div class="page">
    <header class="hero">
      <div class="badges">
        <span class="badge">idea-hook-forge / HTML report</span>
        <span class="badge">公式保真渲染</span>
        <span class="badge">组件拆解 × Hook × Idea 闭环</span>
      </div>
      <h1>{html.escape(profile.get('paper_title', ''))}</h1>
      <p class="subtitle">{html.escape(profile.get('one_line_method', '') or '论文组件化 × Hook 闭环分析报告')}</p>
      {render_profile_cards(profile, kt, quality)}
    </header>
    <div class="layout">
      <aside class="toc">
        <h2>目录</h2>
        <a href="#profile">1. 论文画像</a>
        <a href="#kt">2. K-T 分类</a>
        <a href="#aj">3. A-J 组件拆解</a>
        <a href="#u">4. U 公式标签</a>
        <a href="#hooks">5. Hook 提取</a>
        <a href="#reverse">6. 反向调用</a>
        <a href="#quality">7. 质量门控</a>
      </aside>
      <main class="content-shell">
        <article class="report-body">
          <section id="profile" class="report-section">
            <h2 class="section-header">1. 论文画像</h2>
            <div class="callout"><strong>一句话问题</strong>{html.escape(profile.get('one_line_problem', '') or '待补齐')}</div>
            <div class="callout"><strong>一句话结果</strong>{html.escape(profile.get('one_line_result', '') or '待补齐')}</div>
            {_table(["字段", "内容"], [
                ["Paper", html.escape(profile.get("paper_title", "") or "—")],
                ["Authors", html.escape(profile.get("authors_raw", "") or "—")],
                ["Year", html.escape(profile.get("year", "") or "—")],
                ["Venue", html.escape(profile.get("venue", "") or "—")],
                ["Task", html.escape(profile.get("task", "") or "—")],
                ["Modality", html.escape(profile.get("modality", "") or "—")],
                ["Reference Key", html.escape(profile.get("reference_key", "") or "—")],
            ])}
          </section>

          <section id="kt" class="report-section">
            <h2 class="section-header">2. K-T 分类</h2>
            <div class="callout"><strong>主分类判断</strong>{html.escape(kt.get('classification_reason', '') or '待补齐')}</div>
            {_table(["字段", "内容"], [
                ["Primary K-T Tag", html.escape(kt.get("primary_kt_tag", "") or "—")],
                ["Secondary Tags", html.escape(", ".join(kt.get("secondary_kt_tags", []) or []) or "—")],
                ["Evidence Sections", html.escape(", ".join(kt.get("evidence_sections", []) or []) or "—")],
            ])}
          </section>

          <section id="aj" class="report-section">
            <h2 class="section-header">3. A-J 组件拆解</h2>
            <div class="callout"><strong>主创新总结</strong>{html.escape(aj.get('main_contribution_summary', '') or '待补齐')}</div>
            {render_component_table(aj)}
          </section>

          <section id="u" class="report-section">
            <h2 class="section-header">4. U 公式标签</h2>
            <div class="callout orange"><strong>公式主线</strong>{html.escape(uf.get('formula_thread_summary', '') or '待补齐')}</div>
            <div class="callout"><strong>U 标签</strong>{html.escape(', '.join(uf.get('u_tags', [])) or '—')}</div>
            {render_formula_blocks(uf.get('formula_blocks', []))}
          </section>

          <section id="hooks" class="report-section">
            <h2 class="section-header">5. Hook 提取</h2>
            {render_hooks_table(hooks)}
          </section>

          <section id="reverse" class="report-section">
            <h2 class="section-header">6. 反向调用</h2>
            {render_reverse(reverse)}
          </section>

          <section id="quality" class="report-section">
            <h2 class="section-header">7. 质量门控</h2>
            <div class="callout"><strong>质量总结</strong>{html.escape(quality.get('quality_summary', '') or '待补齐')}</div>
            {_table(["字段", "内容"], [
                ["Overall Hook Level", html.escape(quality.get("overall_hook_level", "") or "—")],
                ["Should Enter Project Plan", _yes_no(quality.get("should_enter_project_plan", False))],
                ["Manual Review Needed", _yes_no(quality.get("manual_review_needed", False))],
                ["Unresolved Fields", "<br/>".join(html.escape(str(x)) for x in (quality.get("unresolved_fields", []) or [])) or "—"],
            ])}
            <div class="footer-note">这份 HTML 不是原始 JSON 调试输出，而是按 idea-hook-forge 的组件化 × Hook × Idea 闭环模板渲染出的正式阅读报告。公式本体必须继续严格对照原论文校验。</div>
          </section>
        </article>
      </main>
    </div>
  </div>
</body>
</html>"""

    out = output_dir / "final_report.html"
    out.write_text(html_doc, encoding="utf-8")
    return out
