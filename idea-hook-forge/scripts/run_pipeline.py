from __future__ import annotations

import copy
import importlib
import json
import re
import sys
from pathlib import Path
import argparse

from schema import STAGE_ORDER, REQUIRED_FIELDS
from shared import (
    ensure_dir,
    read_pdf_snapshot,
    write_json,
    build_reference_key,
    normalize_title_lines,
    normalize_authors_from_lines,
    shorten_authors,
    shorten_title_for_key,
    parse_named_pdf_stem,
)
from state_machine import resolve_mode
from render_html_report import render as render_html

STAGE_MODULES = {
    'paper_profile': 'stages.paper_profile_stage',
    'kt_classification': 'stages.kt_stage',
    'aj_component_breakdown': 'stages.aj_stage',
    'u_formula_tags': 'stages.u_stage',
    'hook_extraction': 'stages.hook_stage',
    'reverse_call_map': 'stages.reverse_call_stage',
    'quality_gate': 'stages.quality_gate_stage',
}

STAGE_DIRS = {
    'paper_profile': '01_paper_profile',
    'kt_classification': '02_kt_classification',
    'aj_component_breakdown': '03_aj_component_breakdown',
    'u_formula_tags': '04_u_formula_tags',
    'hook_extraction': '05_hook_extraction',
    'reverse_call_map': '06_reverse_call_map',
    'quality_gate': '07_quality_gate',
}


def _load_module(stage: str):
    return importlib.import_module(STAGE_MODULES[stage])


# ---------- PDF metadata extraction ----------

def extract_title(snapshot: dict, pdf_path: Path) -> str:
    named_year, named_title, _named_authors = parse_named_pdf_stem(pdf_path.stem)
    if named_year and named_title:
        return named_title
    meta = snapshot.get('metadata', {}) or {}
    title = (meta.get('title') or '').strip()
    if title:
        return title
    for page in snapshot.get('pages', [])[:2]:
        lines = [x.strip() for x in page.get('text', '').splitlines() if x.strip()]
        title = normalize_title_lines(lines)
        if title:
            return title
    return pdf_path.stem


def extract_authors(snapshot: dict) -> str:
    meta = snapshot.get('metadata', {}) or {}
    author = (meta.get('author') or '').strip()
    if author:
        return author
    for page in snapshot.get('pages', [])[:2]:
        lines = [x.strip() for x in page.get('text', '').splitlines() if x.strip()]
        author = normalize_authors_from_lines(lines)
        if author:
            return author
    return 'Unknown Author'


def extract_authors_with_filename(snapshot: dict, pdf_path: Path) -> str:
    _named_year, _named_title, named_authors = parse_named_pdf_stem(pdf_path.stem)
    if named_authors:
        return named_authors
    return extract_authors(snapshot)


def extract_year(snapshot: dict) -> str:
    meta = snapshot.get('metadata', {}) or {}
    for key in ['creationDate', 'modDate', 'subject']:
        value = str(meta.get(key) or '')
        m = re.search(r'(19|20)\d{2}', value)
        if m:
            return m.group(0)
    text = '\n'.join(p.get('text', '') for p in snapshot.get('pages', [])[:2])
    m = re.search(r'(19|20)\d{2}', text)
    return m.group(0) if m else '0000'


# ---------- prefill ----------

def prefill(stage: str, data: dict, snapshot: dict, pdf_path: Path) -> dict:
    if stage == 'paper_profile':
        title = extract_title(snapshot, pdf_path)
        authors = extract_authors_with_filename(snapshot, pdf_path)
        year = extract_year(snapshot)
        author_short = shorten_authors(authors)
        title_short = shorten_title_for_key(title)
        data.update({
            'paper_title': title,
            'authors_raw': authors,
            'year': year,
            'venue': '',
            'task': '',
            'modality': '',
            'one_line_problem': '',
            'one_line_method': '',
            'one_line_result': '',
            'reading_priority': '',
            'reference_key': build_reference_key(year, title_short, author_short),
        })
    elif stage == 'u_formula_tags':
        data['formula_thread_summary'] = '请严格按论文原文补充核心公式；公式本体不能改写，解释可额外填写。'
    return data


# ---------- stage operations ----------

def prepare_stage(stage: str, stage_dir: Path, snapshot: dict, pdf_path: Path) -> None:
    """生成 skeleton.json 和 values.json（若不存在）。"""
    mod = _load_module(stage)
    skeleton = mod.build_skeleton()
    write_json(stage_dir / 'skeleton.json', skeleton)

    values_path = stage_dir / 'values.json'
    if not values_path.exists():
        template = mod.build_values_template()
        prefilled = prefill(stage, template, snapshot, pdf_path)
        write_json(values_path, prefilled)


def process_stage(stage: str, stage_dir: Path) -> bool:
    """
    读取 values.json，填充并验证，生成 filled.json 和 output.md。
    返回 True 表示通过，False 表示有缺失字段。
    """
    mod = _load_module(stage)
    skeleton = json.loads((stage_dir / 'skeleton.json').read_text(encoding='utf-8'))
    values = json.loads((stage_dir / 'values.json').read_text(encoding='utf-8'))

    filled, missing = mod.fill_values(skeleton, values)
    if missing:
        fail_stage(stage, stage_dir, missing)
        return False

    # 写入 filled.json
    write_json(stage_dir / 'filled.json', filled)

    # 运行质量检查
    issues = mod.run_check(filled)
    if issues:
        print(f'[{stage}] 质量检查警告：')
        for issue in issues:
            print(f'  - {issue}')

    # 渲染 output.md
    md_text = mod.render(filled)
    (stage_dir / 'output.md').write_text(md_text, encoding='utf-8')

    # 清理旧的 missing_fields.json
    mf = stage_dir / 'missing_fields.json'
    if mf.exists():
        mf.unlink()

    return True


def fail_stage(stage: str, stage_dir: Path, missing: list[str]) -> None:
    write_json(stage_dir / 'missing_fields.json', {'stage': stage, 'missing_fields': missing})
    print(f'[{stage}] 缺少必填字段，已阻断：{missing}')


# ---------- main ----------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--mode', default='auto')
    parser.add_argument('--request-text', default='')
    parser.add_argument('--stages', default='')
    parser.add_argument('--output-root', default='')
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f'PDF not found: {pdf_path}', file=sys.stderr)
        return 1

    mode, stages = resolve_mode(args.request_text, args.mode)
    if args.mode == 'custom' and args.stages:
        wanted = [s.strip() for s in args.stages.split(',') if s.strip()]
        stages = [s for s in STAGE_ORDER if s in wanted]

    snapshot = read_pdf_snapshot(pdf_path)
    title = extract_title(snapshot, pdf_path)
    authors = extract_authors_with_filename(snapshot, pdf_path)
    named_year, _named_title, _named_authors = parse_named_pdf_stem(pdf_path.stem)
    year = named_year or extract_year(snapshot)
    reference_key = build_reference_key(year, shorten_title_for_key(title), shorten_authors(authors))

    output_root = Path(args.output_root) if args.output_root else pdf_path.parent / reference_key
    ensure_dir(output_root)
    ensure_dir(output_root / 'stages')
    write_json(output_root / 'manifest.json', {
        'pdf': str(pdf_path),
        'mode': mode,
        'request_text': args.request_text,
        'stages': stages,
        'reference_key': reference_key,
    })
    write_json(output_root / 'source_snapshot.json', snapshot)

    blocked = False
    for stage in stages:
        stage_dir = ensure_dir(output_root / 'stages' / STAGE_DIRS[stage])
        prepare_stage(stage, stage_dir, snapshot, pdf_path)
        ok = process_stage(stage, stage_dir)
        if not ok:
            blocked = True

    full_ready = all(
        (output_root / 'stages' / STAGE_DIRS[s] / 'filled.json').exists()
        for s in STAGE_ORDER
    )
    missing_any = any(
        (output_root / 'stages' / STAGE_DIRS[s] / 'missing_fields.json').exists()
        for s in stages
    )
    if full_ready and not missing_any:
        render_html(output_root)
        (output_root / 'final_report.md').write_text(
            'HTML 主报告已生成，请优先查看 final_report.html\n', encoding='utf-8'
        )
        print(output_root / 'final_report.html')
    else:
        print(output_root)
        print('请补齐各阶段 values.json 中的字段后重新运行。')
        if blocked:
            print('当前有阶段因缺字段被阻断。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
