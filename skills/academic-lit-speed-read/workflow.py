#!/usr/bin/env python3
"""
workflow.py — lit-speed-read HTML 生成器与阅读记录存档
用法：python workflow.py --data-file <json路径> --output-dir <输出目录>
"""

import sys, os, re, json, argparse
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# --- HTML 转义 ---
def h(text):
    return str(text).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

# --- 文件名生成 ---
def make_filename(title, author, year):
    first_author = author.split()[0] if author else "Unknown"
    words = re.findall(r'[A-Za-z]+', title)[:6]
    slug = "-".join(words)
    raw = f"{first_author}-{year}-{slug}"
    cleaned = re.sub(r"[^A-Za-z0-9\-]", "", raw)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    return cleaned + ".html"

# --- 构建摘要解析表 ---
def build_abstract_rows(sentences):
    rows = []
    for s in sentences:
        origin = h(s.get("origin", ""))
        trans = h(s.get("trans", ""))
        insight = s.get("insight", "").strip()
        row = f'''        <tr>
          <td class="col-origin">{origin}</td>
          <td class="col-trans">{trans}</td>
        </tr>'''
        if insight:
            row += f'''
        <tr>
          <td colspan="2" class="col-insight"><span class="insight-prefix">注：</span>{h(insight)}</td>
        </tr>'''
        rows.append(row)
    return "\n".join(rows)

# --- 构建方法数据流 ---
def build_method_flow(deep):
    if not deep:
        return ""
    steps = deep.get("method_flow", [])
    if not steps:
        return ""
    parts = []
    for i, step in enumerate(steps):
        parts.append(f'<div class="var-box">{h(step)}</div>')
        if i < len(steps) - 1:
            parts.append('<div class="var-arrow">→</div>')
    return "\n        ".join(parts)

# --- 构建变量流向 ---
def build_var_flow(deep):
    if not deep:
        return ""
    indep = deep.get("indep_vars", [])
    dep = deep.get("dep_var", "")
    direction = deep.get("var_direction", "")
    parts = []
    for v in indep:
        parts.append(f'<div class="var-box">{h(v)}</div>')
        parts.append('<div class="var-arrow">→</div>')
    parts.append(f'<div class="var-outcome">{h(dep)}</div>')
    if direction:
        parts.append(f'<div class="var-dir">（{h(direction)}）</div>')
    return "\n        ".join(parts)

# --- 构建 metrics ---
def build_metrics(metrics_list):
    return "\n        ".join(
        f'<div class="metric">{h(m)}</div>' for m in metrics_list if m.strip()
    )

# --- 构建 tags（支持多选高亮）---
def build_tags(items, primary=None, primaries=None):
    primary_set = set()
    if primary:
        primary_set.add(primary)
    if primaries:
        primary_set.update(primaries)
    parts = []
    for item in (items or []):
        cls = "tag primary" if item in primary_set else "tag"
        parts.append(f'<span class="{cls}">{h(item)}</span>')
    return " ".join(parts)

# --- 构建思考问题 ---
def build_questions(questions):
    items = []
    for i, q in enumerate(questions, 1):
        num = str(i).zfill(2)
        items.append(f'''        <li>
          <span class="q-num">{num}</span>
          <div class="q-inner">
            <div class="q-type">{h(q["type"])}</div>
            {h(q["text"])}
          </div>
        </li>''')
    return "\n".join(items)

# --- 主渲染函数 ---
def render_html(data):
    mode = data.get("mode", "fast")
    mode_cn = "速读模式" if mode == "fast" else "精读模式"
    mode_en = "Fast Review" if mode == "fast" else "Deep Review"
    today = datetime.now().strftime("%Y-%m-%d")

    deep = data.get("deep") if mode == "deep" else None

    # 新增字段
    limitations = data.get("limitations", [])
    theory_framework = data.get("theory_framework", "")
    related_papers = data.get("related_papers", "")
    deep_read_suggestion = data.get("deep_read_suggestion", "")

    # 深度 sections（仅 deep 模式）
    deep_html = ""
    if deep:
        var_flow = build_var_flow(deep)
        method_flow_html = build_method_flow(deep)
        metrics_html = build_metrics(deep.get("metrics", []))
        methods = deep.get("methods", [])
        methods_html = " ".join(f'<span class="tag">{h(m)}</span>' for m in methods)
        method_flow_section = ""
        if method_flow_html:
            method_flow_section = f"""
    <div class="section">
      <div class="section-label">方法数据流</div>
      <div class="var-flow">
        {method_flow_html}
      </div>
    </div>"""
        deep_html = f"""
    <div class="section">
      <div class="section-label">变量关系</div>
      <div class="var-flow">
        {var_flow}
      </div>
    </div>
{method_flow_section}
    <div class="section">
      <div class="section-label">关键数字</div>
      <div class="metrics">
        {metrics_html}
      </div>
    </div>

    <div class="section">
      <div class="section-label">研究方法</div>
      <div>{methods_html}</div>
    </div>"""

    four_q = data.get("four_q", {})
    usage = data.get("usage", [])
    lit_type = data.get("lit_type", "")
    relation = data.get("relation", "")
    chapter = data.get("chapter", "").strip() or "未填写"

    # 文献定位 tags
    lit_types_all = ["理论", "方法", "背景", "原创", "衍生"]
    relation_all = ["继承", "修正", "挑战"]
    usage_all = ["方法参照", "观点支撑", "概念来源", "对比案例"]

    lit_type_html = build_tags(lit_types_all, primary=lit_type)
    relation_html = build_tags(relation_all, primary=relation)
    usage_html = build_tags(usage_all, primaries=set(usage) if usage else set())

    abstract_rows = build_abstract_rows(data.get("sentences", []))
    questions_html = build_questions(data.get("questions", []))
    title_short = " ".join(data.get("title","").split()[:8])

    # 局限性 section
    limitations_html = ""
    if limitations:
        items_html = "\n".join(
            f'        <li>{h(lim)}</li>' for lim in limitations if lim.strip()
        )
        limitations_html = f"""
    <div class="section">
      <div class="section-label">局限性</div>
      <ul class="lim-list">
{items_html}
      </ul>
    </div>"""

    # Fast 模式精读建议
    suggestion_html = ""
    if mode == "fast" and deep_read_suggestion:
        suggestion_html = f'<div class="suggestion">精读建议：{h(deep_read_suggestion)}</div>'

    # 我的思考 — 3个子区域
    theory_val = h(theory_framework) if theory_framework else ""
    theory_placeholder = "" if theory_framework else "这篇用了什么理论框架或分析视角？与你熟悉的理论有什么关联？"
    related_val = h(related_papers) if related_papers else ""
    related_placeholder = "" if related_papers else "这篇让你联想到哪些文章？有没有观点一致、矛盾或互补的文献？"

    if theory_val:
        theory_content = theory_val
        theory_note_cls = "my-note"
    else:
        theory_content = theory_placeholder
        theory_note_cls = "my-note placeholder"

    if related_val:
        related_content = related_val
        related_note_cls = "my-note"
    else:
        related_content = related_placeholder
        related_note_cls = "my-note placeholder"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{h(data.get("author",""))} {h(data.get("year",""))} · {h(title_short)}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Georgia", "Times New Roman", serif;
    font-size: 15px; line-height: 1.75;
    color: #1a1a1a; background: #f4f4f0;
    padding: 40px 16px 80px;
  }}
  .page {{ max-width: 820px; margin: 0 auto; background: #fff; border: 1px solid #ccc; }}
  .header {{ border-bottom: 3px solid #1a1a1a; padding: 36px 48px 28px; }}
  .header .mode {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #666; margin-bottom: 14px; }}
  .header h1 {{ font-size: 19px; font-weight: 700; font-style: italic; line-height: 1.45; margin-bottom: 16px; }}
  .header .meta {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 13px; color: #444; display: flex; gap: 24px; flex-wrap: wrap; }}
  .header .meta .label {{ color: #999; margin-right: 4px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .suggestion {{ margin-top: 12px; font-family: "Helvetica Neue", Arial, sans-serif; font-size: 13px; color: #444; background: #f6f8fa; border-left: 3px solid #1a1a1a; padding: 8px 14px; }}
  .content {{ padding: 40px 48px; }}
  .section {{ margin-bottom: 40px; }}
  .section-label {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 2.5px; text-transform: uppercase; color: #999; border-bottom: 1px solid #ddd; padding-bottom: 6px; margin-bottom: 18px; }}
  .abstract-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  .abstract-table td {{ padding: 10px 14px; border: 1px solid #ddd; vertical-align: top; }}
  .col-origin {{ width: 48%; color: #555; font-style: italic; background: #fafafa; }}
  .col-trans {{ width: 52%; color: #1a1a1a; }}
  .col-insight {{ background: #f9f7ed; border-top: none; font-family: "Helvetica Neue", Arial, sans-serif; font-size: 13px; color: #3a3a2a; }}
  .insight-prefix {{ font-weight: 700; margin-right: 6px; font-style: normal; }}
  .four-q {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1px; border: 1px solid #ddd; background: #ddd; }}
  .q-block {{ background: #fff; padding: 16px 18px; }}
  .q-key {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #888; margin-bottom: 6px; }}
  .q-val {{ font-size: 14px; color: #1a1a1a; line-height: 1.6; }}
  .var-flow {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 16px 20px; background: #fafafa; border: 1px solid #ddd; font-family: "Helvetica Neue", Arial, sans-serif; font-size: 13px; }}
  .var-box {{ border: 1px solid #999; padding: 5px 14px; background: #fff; }}
  .var-arrow {{ color: #666; font-size: 16px; padding: 0 4px; }}
  .var-outcome {{ border: 2px solid #1a1a1a; padding: 5px 14px; background: #fff; font-weight: 700; }}
  .var-dir {{ margin-left: 8px; font-size: 12px; color: #666; font-style: italic; }}
  .metrics {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .metric {{ border: 1px solid #bbb; padding: 4px 14px; font-family: "Courier New", monospace; font-size: 13px; font-weight: 700; background: #fafafa; color: #1a1a1a; }}
  .attr-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1px; border: 1px solid #ddd; background: #ddd; }}
  .attr-block {{ background: #fff; padding: 14px 18px; }}
  .attr-key {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #888; margin-bottom: 8px; }}
  .tag {{ display: inline-block; border: 1px solid #bbb; padding: 2px 10px; font-family: "Helvetica Neue", Arial, sans-serif; font-size: 12px; margin: 2px 2px 2px 0; background: #f5f5f5; color: #333; }}
  .tag.primary {{ background: #1a1a1a; color: #fff; border-color: #1a1a1a; }}
  .lim-list {{ list-style: none; padding: 0; }}
  .lim-list li {{ padding: 8px 0; border-bottom: 1px solid #eee; font-size: 14px; line-height: 1.6; padding-left: 12px; border-left: 2px solid #bbb; margin-bottom: 6px; }}
  .lim-list li:last-child {{ border-bottom: none; }}
  .q-list {{ list-style: none; }}
  .q-list li {{ display: flex; gap: 16px; padding: 14px 0; border-bottom: 1px solid #eee; font-size: 14px; line-height: 1.65; }}
  .q-list li:last-child {{ border-bottom: none; }}
  .q-num {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 11px; font-weight: 700; color: #999; min-width: 20px; padding-top: 2px; }}
  .q-inner .q-type {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #666; margin-bottom: 4px; }}
  .my-note-label {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #aaa; margin-bottom: 6px; }}
  .my-note {{ border: 1px dashed #bbb; padding: 20px; min-height: 100px; font-size: 14px; color: #1a1a1a; background: #fdfdfd; }}
  .my-note.placeholder {{ color: #aaa; font-style: italic; }}
  .footer {{ border-top: 1px solid #ddd; padding: 16px 48px; font-family: "Helvetica Neue", Arial, sans-serif; font-size: 11px; color: #aaa; display: flex; justify-content: space-between; }}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="mode">{h(mode_cn)} / {h(mode_en)}</div>
    <h1>{h(data.get("title",""))}</h1>
    <div class="meta">
      <span><span class="label">Author</span>{h(data.get("author",""))}</span>
      <span><span class="label">Year</span>{h(data.get("year",""))}</span>
      <span><span class="label">Journal</span>{h(data.get("journal",""))}</span>
      <span><span class="label">Read</span>{h(today)}</span>
    </div>
    {suggestion_html}
  </div>
  <div class="content">
    <div class="section">
      <div class="section-label">Abstract — 逐句解析</div>
      <table class="abstract-table">
{abstract_rows}
      </table>
    </div>
    <div class="section">
      <div class="section-label">核心定位</div>
      <div class="four-q">
        <div class="q-block"><div class="q-key">动机 / 研究空白</div><div class="q-val">{h(four_q.get("motivation",""))}</div></div>
        <div class="q-block"><div class="q-key">研究对象</div><div class="q-val">{h(four_q.get("subject",""))}</div></div>
        <div class="q-block"><div class="q-key">核心做法</div><div class="q-val">{h(four_q.get("method",""))}</div></div>
        <div class="q-block"><div class="q-key">结论方向</div><div class="q-val">{h(four_q.get("conclusion",""))}</div></div>
      </div>
    </div>
{deep_html}
    <div class="section">
      <div class="section-label">文献定位</div>
      <div class="attr-grid">
        <div class="attr-block"><div class="attr-key">文献类型</div>{lit_type_html}</div>
        <div class="attr-block"><div class="attr-key">与本研究关系</div>{relation_html}</div>
        <div class="attr-block"><div class="attr-key">引用用途</div>{usage_html}</div>
        <div class="attr-block"><div class="attr-key">拟放入章节</div><span class="tag">{h(chapter)}</span></div>
      </div>
    </div>
{limitations_html}
    <div class="section">
      <div class="section-label">思考问题</div>
      <ul class="q-list">
{questions_html}
      </ul>
    </div>
    <div class="section">
      <div class="section-label">我的思考</div>

      <div class="my-note-label">理论框架 / 分析视角</div>
      <div class="my-note {('placeholder' if not theory_framework else '')}" contenteditable="true">{theory_content}</div>

      <div class="my-note-label" style="margin-top:16px;">关联文献</div>
      <div class="my-note {('placeholder' if not related_papers else '')}" contenteditable="true">{related_content}</div>

      <div class="my-note-label" style="margin-top:16px;">自由思考</div>
      <div class="my-note" contenteditable="true">在此记录读完后的想法、与自己研究的连接点、后续需要追查的问题……</div>
    </div>
  </div>
  <div class="footer">
    <span>生成于 {today} · lit-speed-read skill</span>
    <span>基于《做研究是有趣的》· 《写作是门手艺》</span>
  </div>
</div>
</body>
</html>"""

# --- 存档记录 ---
def save_record(data, html_path, output_dir):
    record_dir = Path(output_dir) / ".lit-reads"
    record_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H-%M-%S")
    record_file = record_dir / f"{today}_{time_str}.md"
    author = data.get("author", "Unknown")
    year = data.get("year", "")
    title = data.get("title", "")
    mode = data.get("mode", "fast")
    relation = data.get("relation", "")
    record_file.write_text(
        f"# 阅读记录\n\n"
        f"- **时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- **文献**：{author} ({year}) {title}\n"
        f"- **模式**：{mode}\n"
        f"- **与本研究关系**：{relation}\n"
        f"- **HTML 文件**：{html_path}\n",
        encoding="utf-8"
    )

# --- 主入口 ---
def main():
    parser = argparse.ArgumentParser(description="lit-speed-read HTML 生成器")
    parser.add_argument("--data-file", required=True, help="JSON 数据文件路径")
    parser.add_argument("--output-dir", default=".", help="HTML 输出目录")
    args = parser.parse_args()

    with open(args.data_file, encoding="utf-8") as f:
        data = json.load(f)

    html_content = render_html(data)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = make_filename(
        data.get("title", "untitled"),
        data.get("author", "unknown"),
        data.get("year", "0000")
    )
    out_path = out_dir / filename
    out_path.write_text(html_content, encoding="utf-8")

    save_record(data, str(out_path), args.output_dir)

    print(f"HTML 已生成：{out_path}")

if __name__ == "__main__":
    main()
