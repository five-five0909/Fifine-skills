#!/usr/bin/env python3
"""Render merged Multiple Translation JSON as selectable HTML and/or Markdown."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

LANG_LABELS = {
    "zh-CN": "中文",
    "zh-TW": "繁體中文",
    "en": "English",
    "en-US": "English",
    "ja-JP": "日本語",
    "ko-KR": "한국어",
    "fr-FR": "Français",
    "de-DE": "Deutsch",
    "es-ES": "Español",
}


def load_data(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    validate(data)
    return data


def validate(data: dict[str, Any]) -> None:
    blocks = data.get("blocks")
    targets = data.get("target_languages")
    if not isinstance(blocks, list) or not blocks:
        raise ValueError("blocks must be a non-empty list")
    if not isinstance(targets, list) or not targets or not all(isinstance(t, str) and t.strip() for t in targets):
        raise ValueError("target_languages must be a non-empty list of strings")
    if len(set(targets)) != len(targets):
        raise ValueError("target_languages contains duplicates")
    ids: set[str] = set()
    for i, block in enumerate(blocks, 1):
        if not isinstance(block, dict):
            raise ValueError(f"block {i} must be an object")
        for key in ("id", "type", "order", "source", "translations"):
            if key not in block:
                raise ValueError(f"block {i} missing {key}")
        if block["id"] in ids:
            raise ValueError(f"duplicate block id: {block['id']}")
        ids.add(block["id"])
        if not isinstance(block["id"], str) or not block["id"].strip():
            raise ValueError(f"block {i} id must be a non-empty string")
        if not isinstance(block["order"], int):
            raise ValueError(f"block {block['id']} order must be an integer")
        if not isinstance(block["source"], str):
            raise ValueError(f"block {block['id']} source must be a string")
        if not isinstance(block["translations"], dict):
            raise ValueError(f"block {block['id']} translations must be an object")
        for target in targets:
            value = block["translations"].get(target)
            if not isinstance(value, str):
                raise ValueError(f"block {block['id']} missing translation for {target}")


def label(lang: str) -> str:
    return LANG_LABELS.get(lang, lang)


def safe_basename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
    return value or "translation"


def md_text(text: str, block_type: str) -> str:
    if block_type == "code":
        return f"```\n{text}\n```"
    return text


def render_md(data: dict[str, Any], layout: str) -> str:
    title = data.get("title") or data.get("source_name") or "Translation"
    lines = [f"# {title}", ""]
    if data.get("job_id"):
        lines.extend([f"> JobID: `{data['job_id']}`", ""])
    targets = data["target_languages"]
    for block in sorted(data["blocks"], key=lambda b: b["order"]):
        btype = block.get("type", "paragraph")
        if btype == "heading":
            lines.extend(["---", ""])
        lines.append(f"<!-- {block['id']} | {btype} -->")
        if layout != "target-only":
            lines.extend(["**Source**", "", md_text(block["source"], btype), ""])
        if layout != "source-only":
            for target in targets:
                lines.extend([f"**{label(target)}**", "", md_text(block["translations"][target], btype), ""])
    notes = data.get("notes")
    if isinstance(notes, list) and notes:
        lines.extend(["## Notes", ""])
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def esc_multiline(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def render_html(data: dict[str, Any], layout: str) -> str:
    title = html.escape(data.get("title") or data.get("source_name") or "Translation")
    job_id = html.escape(str(data.get("job_id", "")))
    targets = data["target_languages"]

    target_buttons = "\n".join(
        f'<button type="button" onclick="setMode(\'target-{html.escape(t)}\')">仅{html.escape(label(t))}</button>'
        for t in targets
    )

    block_html: list[str] = []
    for block in sorted(data["blocks"], key=lambda b: b["order"]):
        btype = html.escape(str(block.get("type", "paragraph")))
        source_html = ""
        if layout != "target-only":
            source_html = (
                '<div class="lang source"><div class="lang-label">Source</div>'
                f'<div class="text">{esc_multiline(block["source"])}</div></div>'
            )
        translations = []
        if layout != "source-only":
            for t in targets:
                translations.append(
                    f'<div class="lang target" data-lang="{html.escape(t)}">'
                    f'<div class="lang-label">{html.escape(label(t))}</div>'
                    f'<div class="text">{esc_multiline(block["translations"][t])}</div></div>'
                )
        block_html.append(
            f'<section class="block block-{btype}" data-block-id="{html.escape(block["id"])}">'
            f'<div class="block-meta">{html.escape(block["id"])} · {btype}</div>'
            f'{source_html}{"".join(translations)}</section>'
        )

    notes_html = ""
    notes = data.get("notes")
    if isinstance(notes, list) and notes:
        lis = "".join(f"<li>{html.escape(str(n))}</li>" for n in notes)
        notes_html = f'<section class="notes"><h2>Notes</h2><ul>{lis}</ul></section>'

    initial_class = ""
    if layout == "target-only":
        initial_class = " target-only-default"
    elif layout == "source-only":
        initial_class = " source-only-default"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#1f1f1f;--panel:#272727;--fg:#ededed;--muted:#999;--line:#414141;--accent:#f0c2c7;--target:#dcebd7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font-family:"Segoe UI","Microsoft YaHei",Arial,sans-serif;line-height:1.8}}
.toolbar{{position:sticky;top:0;z-index:5;display:flex;gap:8px;flex-wrap:wrap;padding:10px 18px;background:#181818;border-bottom:1px solid #333}}
button{{background:#2b2b2b;color:#eee;border:1px solid #555;border-radius:8px;padding:7px 11px;cursor:pointer;font:inherit}} button:hover{{background:#373737}}
main{{max-width:1100px;margin:0 auto;padding:36px 34px 72px}} h1{{font-size:28px;line-height:1.45;margin:0 0 5px}} .job{{font-size:13px;color:var(--muted);margin-bottom:28px}}
.block{{padding:18px 0 23px;border-bottom:1px solid var(--line)}} .block-meta{{font-size:12px;color:#777;margin-bottom:8px}} .lang{{margin:8px 0 14px}} .lang-label{{font-size:13px;color:var(--muted)}} .text{{font-size:18px;text-align:justify;white-space:normal}} .target .text{{color:var(--target)}}
.block-heading .text{{font-weight:700;font-size:20px}} .block-code .text{{font-family:Consolas,monospace;white-space:pre-wrap;background:#181818;padding:12px;border-radius:8px}}
.notes{{margin-top:34px}} .notes h2{{font-size:20px;color:var(--accent)}}
body.mode-source .target{{display:none}} body.mode-target .source{{display:none}} body.mode-target .target{{display:none}} body.mode-target .target.active-target{{display:block}}
body.source-only-default .target{{display:none}} body.target-only-default .source{{display:none}}
@media print{{.toolbar{{display:none}}body{{background:#fff;color:#111}}main{{max-width:none;padding:10mm}}.target .text,.text{{color:#111}}.block{{border-color:#ccc;break-inside:avoid}}.block-meta,.lang-label,.job{{color:#555}}}}
</style>
</head>
<body class="{initial_class.strip()}">
<div class="toolbar">
  <button type="button" onclick="setMode('all')">全部</button>
  <button type="button" onclick="setMode('source')">仅原文</button>
  {target_buttons}
  <button type="button" onclick="selectAllText()">全选全文</button>
  <button type="button" onclick="copyAllText()">复制全文</button>
</div>
<main id="content">
<h1>{title}</h1>
<div class="job">{('JobID: ' + job_id) if job_id else ''}</div>
{''.join(block_html)}
{notes_html}
</main>
<script>
function clearModes(){{document.body.classList.remove('mode-source','mode-target','source-only-default','target-only-default');for(const el of document.querySelectorAll('.target.active-target'))el.classList.remove('active-target')}}
function setMode(mode){{clearModes();if(mode==='source'){{document.body.classList.add('mode-source');return}}if(mode.startsWith('target-')){{const lang=mode.slice(7);document.body.classList.add('mode-target');for(const el of document.querySelectorAll('.target')){{if(el.dataset.lang===lang)el.classList.add('active-target')}}return}}}}
function selectAllText(){{const node=document.getElementById('content');const range=document.createRange();range.selectNodeContents(node);const sel=window.getSelection();sel.removeAllRanges();sel.addRange(range)}}
async function copyAllText(){{const text=document.getElementById('content').innerText;try{{await navigator.clipboard.writeText(text)}}catch(e){{selectAllText();document.execCommand('copy')}}}}
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    parser.add_argument("--format", choices=["html", "md", "both"], default="both")
    parser.add_argument("--layout", choices=["parallel", "target-only", "source-only"], default="parallel")
    parser.add_argument("--basename", default="translation")
    args = parser.parse_args()

    data = load_data(args.input_json)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    base = safe_basename(args.basename)
    created: list[Path] = []
    if args.format in {"html", "both"}:
        path = args.out_dir / f"{base}_translated.html"
        path.write_text(render_html(data, args.layout), encoding="utf-8")
        created.append(path)
    if args.format in {"md", "both"}:
        path = args.out_dir / f"{base}_translated.md"
        path.write_text(render_md(data, args.layout), encoding="utf-8")
        created.append(path)
    for path in created:
        print(path)


if __name__ == "__main__":
    main()
