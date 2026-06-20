#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import mistune


MATH_RE = re.compile(r"\$\$(.*?)\$\$", re.S)
FOCUS_LABEL_RE = re.compile(r":::focus-label::(.*?):::", re.S)
FOCUS_BODY_RE = re.compile(r":::focus-body::(.*?):::", re.S)
SWITCH_RE = re.compile(r":::switch::(.*?)\|\|(.*?)\|\|(.*?):::", re.S)

SECTION_ORDER = [
    ("abstract", "1. Abstract"),
    ("introduction", "2. Introduction / GAP"),
    ("related_work", "3. Related Work"),
    ("method_overview", "4. Method Overview"),
    ("formula_thread", "5. Formula Thread"),
    ("experiments", "6. Experiments"),
]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="paper-weaver HTML 报告渲染器")
    ap.add_argument("--workspace", required=True, help="paper-weaver 工作目录")
    ap.add_argument("--out", default="", help="输出 HTML 路径；不填则默认 workspace/final_report.html")
    return ap.parse_args()


def load_manifest(workspace: Path) -> dict:
    manifest_path = workspace / "manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def make_markdown():
    return mistune.create_markdown(plugins=["table", "url", "strikethrough"])


def render_section(md, text: str) -> str:
    math_blocks: list[str] = []

    def sub_math(m: re.Match[str]) -> str:
        idx = len(math_blocks)
        math_blocks.append(m.group(1).strip())
        return f"@@MATH{idx}@@"

    text = MATH_RE.sub(sub_math, text)
    text = FOCUS_LABEL_RE.sub(lambda m: f"@@FLABEL[{m.group(1).strip()}]@@", text)
    text = FOCUS_BODY_RE.sub(lambda m: f"@@FBODY[{m.group(1).strip()}]@@", text)
    text = SWITCH_RE.sub(lambda m: f"@@FSWITCH[{m.group(1).strip()}||{m.group(2).strip()}||{m.group(3).strip()}]@@", text)

    html = md(text)

    for i, block in enumerate(math_blocks):
        repl = f'<div class="math-block">$$\n{block}\n$$</div>'
        html = html.replace(f"<p>@@MATH{i}@@</p>", repl)
        html = html.replace(f"@@MATH{i}@@", repl)

    html = re.sub(r"<p>@@FLABEL\[(.*?)\]@@</p>", lambda m: f'<div class="formula-focus-label">{m.group(1)}</div>', html)
    html = re.sub(r"<p>@@FBODY\[(.*?)\]@@</p>", lambda m: f'<div class="formula-focus-body">{m.group(1)}</div>', html, flags=re.S)

    def repl_switch(m: re.Match[str]) -> str:
        whole, a, b = m.group(1), m.group(2), m.group(3)
        return (
            '<div class="formula-switch-card">'
            f'<div class="formula-switch-title">{whole}</div>'
            '<div class="formula-switch-arrow">⟹</div>'
            '<div class="formula-switch-grid">'
            f'<div class="formula-switch-item">{a}</div>'
            f'<div class="formula-switch-item">{b}</div>'
            "</div></div>"
        )

    html = re.sub(r"<p>@@FSWITCH\[(.*?)\|\|(.*?)\|\|(.*?)\]@@</p>", repl_switch, html, flags=re.S)
    return html


def render_workspace_html(workspace: Path, out: Path | None = None) -> Path:
    manifest = load_manifest(workspace)
    md = make_markdown()

    section_html_parts: list[str] = []
    for stage, title in SECTION_ORDER:
        stage_path = workspace / "stages" / stage / "output.md"
        if not stage_path.exists():
            continue
        section_html = render_section(md, stage_path.read_text(encoding="utf-8"))
        section_html_parts.append(
            f'<section id="{stage}" class="report-section"><h2 class="section-header">{title}</h2>{section_html}</section>'
        )

    workspace_text = str(workspace)
    code_block = (
        "```bash\n"
        f'python paper-weaver/scripts/run_pipeline.py --pdf "{manifest.get("pdf", "<paper.pdf>")}" --mode {manifest.get("mode", "auto")}\n'
        "```\n\n"
        f"- Workspace：`{workspace_text}`\n"
        f"- 最终 Markdown：`{workspace / 'final_report.md'}`\n"
        f"- 最终 HTML：`{workspace / 'final_report.html'}`\n"
    )
    code_html = render_section(md, code_block)

    method_name = manifest.get("method_name", workspace.name)
    mode = manifest.get("mode", "auto")
    stages = manifest.get("stages", [])
    stages_text = " / ".join(stages) if stages else "未记录"

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{method_name} - paper-weaver 最终报告</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5.8.1/github-markdown-light.min.css" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build/styles/github.min.css" />
<style>
:root {{ --bg:#f6f8fa; --panel:#fff; --border:#d0d7de; --muted:#57606a; --text:#24292f; --accent:#0969da; --accent-soft:#ddf4ff; --shadow:0 8px 24px rgba(140,149,159,.18); }}
* {{ box-sizing:border-box; }}
body {{ margin:0; color:var(--text); background:radial-gradient(circle at top right, rgba(9,105,218,.08), transparent 25%), linear-gradient(180deg, #f8fbff 0%, var(--bg) 280px); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,"PingFang SC","Microsoft YaHei",sans-serif; }}
.page {{ width:min(1280px, calc(100vw - 32px)); margin:24px auto 64px; }}
.hero {{ background:linear-gradient(135deg, #fff 0%, #f6faff 100%); border:1px solid var(--border); border-radius:20px; padding:28px; box-shadow:var(--shadow); margin-bottom:20px; }}
.hero h1 {{ margin:0 0 10px; font-size:34px; line-height:1.2; }}
.hero .subtitle {{ color:var(--muted); margin:0 0 18px; font-size:15px; }}
.badges {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:18px; }}
.badge {{ border:1px solid var(--border); background:#fff; border-radius:999px; padding:6px 12px; font-size:13px; color:var(--muted); }}
.summary-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }}
.summary-card {{ background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:16px; }}
.summary-card .label {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.06em; margin-bottom:8px; }}
.summary-card .value {{ font-size:15px; line-height:1.6; font-weight:600; }}
.layout {{ display:grid; grid-template-columns:260px minmax(0,1fr); gap:20px; align-items:start; }}
.toc {{ position:sticky; top:20px; background:var(--panel); border:1px solid var(--border); border-radius:18px; padding:18px; box-shadow:var(--shadow); }}
.toc h2 {{ margin:0 0 12px; font-size:16px; }}
.toc a {{ display:block; color:var(--accent); text-decoration:none; padding:7px 0; font-size:14px; }}
.toc a:hover {{ text-decoration:underline; }}
.content-shell {{ background:var(--panel); border:1px solid var(--border); border-radius:20px; box-shadow:var(--shadow); overflow:hidden; }}
.markdown-body {{ max-width:none; background:transparent; padding:28px; font-size:16px; line-height:1.78; }}
.report-section {{ scroll-margin-top:24px; margin-bottom:28px; }}
.section-header {{ margin:0 0 16px; padding-bottom:10px; border-bottom:1px solid var(--border); }}
.callout {{ border-left:4px solid var(--accent); background:var(--accent-soft); padding:14px 16px; border-radius:10px; margin:18px 0; }}
.callout strong {{ display:block; margin-bottom:6px; }}
pre {{ overflow-x:auto; border-radius:12px; border:1px solid var(--border); }}
code {{ font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",Menlo,monospace; }}
.footer-note {{ margin-top:32px; padding-top:20px; border-top:1px solid var(--border); color:var(--muted); font-size:14px; }}
.formula-focus-label {{ margin:20px auto 10px; width:fit-content; padding:4px 0; color:#9a6700; font-size:13px; font-weight:700; letter-spacing:.08em; text-align:center; }}
.formula-focus-body {{ margin:0 auto 14px; max-width:92%; text-align:center; color:#1f2328; line-height:1.9; background:#fff8c5; border-left:4px solid #d4a72c; padding:12px 16px; border-radius:8px; }}
.formula-switch-card {{ margin:18px auto 22px; padding:18px 20px; border:1px dashed #8c959f; border-radius:16px; background:#fbfdff; text-align:center; }}
.formula-switch-title {{ font-size:14px; color:var(--muted); margin-bottom:8px; }}
.formula-switch-arrow {{ font-size:22px; font-weight:700; color:var(--accent); margin:8px 0 12px; }}
.formula-switch-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }}
.formula-switch-item {{ border:1px solid var(--border); background:#fff; border-radius:12px; padding:12px 14px; font-weight:600; }}
.math-block {{ margin:14px 0; }}
@media (max-width:960px) {{ .summary-grid,.layout,.formula-switch-grid {{ grid-template-columns:1fr; }} .toc {{ position:static; }} .hero h1 {{ font-size:28px; }} }}
</style></head><body>
<div class="page"><header class="hero"><div class="badges"><span class="badge">paper-weaver / HTML report</span><span class="badge">公式主线已同步为默认样式</span><span class="badge">支持 KaTeX 与 GitHub 代码高亮</span></div><h1>{method_name}</h1><p class="subtitle">由 paper-weaver 自动生成的结构化论文阅读报告。当前版本已固化公式主线、提示块和视角切换样式。</p><div class="summary-grid"><div class="summary-card"><div class="label">Method</div><div class="value">{method_name}</div></div><div class="summary-card"><div class="label">Mode</div><div class="value">{mode}</div></div><div class="summary-card"><div class="label">Stages</div><div class="value">{stages_text}</div></div><div class="summary-card"><div class="label">Workspace</div><div class="value">{workspace_text}</div></div></div></header><div class="layout"><aside class="toc"><h2>目录</h2><a href="#abstract">1. Abstract</a><a href="#introduction">2. Introduction / GAP</a><a href="#related_work">3. Related Work</a><a href="#method_overview">4. Method Overview</a><a href="#formula_thread">5. Formula Thread</a><a href="#experiments">6. Experiments</a><a href="#reproduce">7. Reproduce / Notes</a></aside><main class="content-shell"><article class="markdown-body">
{''.join(section_html_parts)}
<section id="reproduce" class="report-section"><h2 class="section-header">7. Reproduce / Notes</h2><div class="callout"><strong>说明</strong>这份 HTML 不是手写摘要，而是先按 paper-weaver 的结构化阶段产出 Markdown，再由 skill 内正式渲染器生成的可视化成品。</div>{code_html}<div class="footer-note">当前版本使用 CDN 加载 GitHub Markdown CSS、KaTeX 与 highlight.js。若后续要做完全离线的正式交付版，可以继续把依赖改成项目内本地 assets。</div></section>
</article></main></div></div>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script><script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script><script defer src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build/highlight.min.js"></script><script>window.addEventListener('DOMContentLoaded', () => {{ if (window.hljs) window.hljs.highlightAll(); if (window.renderMathInElement) {{ window.renderMathInElement(document.body, {{ delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'\\\\(',right:'\\\\)',display:false}},{{left:'$',right:'$',display:false}}], ignoredTags:['script','noscript','style','textarea','pre','code'] }}); }} }});</script>
</body></html>"""

    out_path = out or (workspace / "final_report.html")
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).expanduser().resolve()
    out = Path(args.out).expanduser().resolve() if args.out else None
    out_path = render_workspace_html(workspace, out)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
