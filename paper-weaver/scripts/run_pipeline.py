#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from shared import ensure_pdf, read_json, slugify_path, write_json, write_text
from state_machine import resolve_auto_plan, resolve_stage_sequence

STAGE_MODULES = {
    "abstract": "stages.abstract_stage",
    "introduction": "stages.introduction_stage",
    "related_work": "stages.related_work_stage",
    "method_overview": "stages.method_overview_stage",
    "formula_thread": "stages.formula_thread_stage",
    "experiments": "stages.experiments_stage",
}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="paper-weaver 主控脚本：硬编码论文阅读主流程")
    ap.add_argument("--pdf", required=True, help="主论文 PDF 路径（唯一入口）")
    ap.add_argument("--mode", default="auto", choices=["auto", "first-pass", "second-pass", "full", "custom"], help="阅读模式；默认 auto")
    ap.add_argument("--modules", default="", help="custom 模式下的模块列表，逗号分隔")
    ap.add_argument("--request-text", default="", help="用户原始请求文本；auto 模式用它做硬编码模式判定")
    ap.add_argument("--workspace", default="", help="工作目录；不提供则自动生成")
    ap.add_argument("--method-name", default="", help="方法名；不提供则使用 PDF 文件名")
    ap.add_argument("--transitions", type=int, default=1, help="Related Work 转折段数")
    ap.add_argument("--cycles", type=int, default=3, help="Formula Thread 的问题-工具-解决循环数")
    ap.add_argument("--symbols", type=int, default=8, help="Formula Thread 的符号表行数")
    ap.add_argument("--concepts", type=int, default=3, help="Formula Thread 的概念卡数量")
    ap.add_argument("--splits", type=int, default=1, help="Formula Thread 的 split 节点数")
    ap.add_argument("--claims", default="claim1", help="Experiments 的 claim id 列表，逗号分隔")
    ap.add_argument("--sections", default="4.1", help="Experiments 的 section id 列表，逗号分隔")
    ap.add_argument("--ablations", type=int, default=1, help="Experiments 的消融检查数量")
    ap.add_argument("--no-efficiency", action="store_true", help="Experiments 阶段跳过效率检查")
    return ap.parse_args()


def get_workspace(args: argparse.Namespace, pdf_path: Path) -> Path:
    if args.workspace:
        return Path(args.workspace)
    return pdf_path.parent / f"{slugify_path(pdf_path)}-paper-weaver"


def build_manifest(args: argparse.Namespace, pdf_path: Path, workspace: Path, stages: list[str]) -> dict:
    method_name = args.method_name or pdf_path.stem
    return {
        "pdf": str(pdf_path),
        "mode": args.mode,
        "request_text": args.request_text,
        "workspace": str(workspace),
        "method_name": method_name,
        "stages": stages,
        "planning": {
            "transitions": args.transitions,
            "cycles": args.cycles,
            "symbols": args.symbols,
            "concepts": args.concepts,
            "splits": args.splits,
            "claim_ids": [x.strip() for x in args.claims.split(",") if x.strip()],
            "section_ids": [x.strip() for x in args.sections.split(",") if x.strip()],
            "ablations": args.ablations,
            "efficiency": not args.no_efficiency,
        },
    }


def import_stage(name: str):
    return importlib.import_module(STAGE_MODULES[name])


def prepare_stage(stage: str, stage_dir: Path, manifest: dict) -> dict:
    mod = import_stage(stage)
    method_name = manifest["method_name"]
    planning = manifest["planning"]
    if stage == "abstract":
        skeleton = mod.build_skeleton()
        values_template = mod.build_values_template()
    elif stage == "introduction":
        skeleton = mod.build_skeleton()
        values_template = mod.build_values_template()
    elif stage == "related_work":
        skeleton = mod.build_skeleton(transitions=planning["transitions"])
        values_template = mod.build_values_template(transitions=planning["transitions"])
    elif stage == "method_overview":
        skeleton = mod.build_skeleton(method_name)
        values_template = mod.build_values_template(method_name)
    elif stage == "formula_thread":
        skeleton = mod.build_skeleton(method_name, cycles=planning["cycles"], symbols=planning["symbols"], concepts=planning["concepts"], splits=planning["splits"])
        values_template = mod.build_values_template(skeleton)
    elif stage == "experiments":
        skeleton = mod.build_skeleton(method_name, claim_ids=planning["claim_ids"], section_ids=planning["section_ids"], ablations=planning["ablations"], efficiency=planning["efficiency"])
        values_template = mod.build_values_template(skeleton)
    else:
        raise ValueError(stage)
    write_json(stage_dir / "skeleton.json", skeleton)
    values_path = stage_dir / "values.json"
    if not values_path.exists():
        write_json(values_path, values_template)
    return skeleton


def fail_stage(stage: str, stage_dir: Path, missing: list[str], reason: str) -> int:
    report = {
        "stage": stage,
        "reason": reason,
        "missing_fields": missing,
        "next_action": f"先补齐 stages/{stage}/values.json 中的缺失字段，再重新运行 run_pipeline.py",
    }
    write_json(stage_dir / "missing_fields.json", report)
    print(f"[BLOCKED] 阶段 {stage} 未完成：{reason}")
    for item in missing:
        print(f"  - {item}")
    print(f"已写入缺字段报告：{stage_dir / 'missing_fields.json'}")
    return 2


def process_stage(stage: str, stage_dir: Path, manifest: dict) -> int:
    skeleton = prepare_stage(stage, stage_dir, manifest)
    values = read_json(stage_dir / "values.json")
    mod = import_stage(stage)
    try:
        filled, missing = mod.fill_values(skeleton, values)
    except Exception as exc:  # noqa: BLE001
        return fail_stage(stage, stage_dir, [str(exc)], "字段内容非法")
    if missing:
        return fail_stage(stage, stage_dir, missing, "存在必填字段缺失或结构不合法")
    write_json(stage_dir / "filled.json", filled)
    extra_issues = mod.run_check(filled)
    if extra_issues:
        return fail_stage(stage, stage_dir, extra_issues, "判定自检未通过")
    output = mod.render(filled)
    write_text(stage_dir / "output.md", output)
    missing_path = stage_dir / "missing_fields.json"
    if missing_path.exists():
        missing_path.unlink()
    print(f"[DONE] 阶段完成：{stage} -> {stage_dir / 'output.md'}")
    return 0


def assemble_report(workspace: Path, stages: list[str], manifest: dict) -> None:
    parts = [f"# {manifest['method_name']} 论文阅读结果", "", f"- PDF: {manifest['pdf']}", f"- 模式: {manifest['mode']}", ""]
    for stage in stages:
        output_path = workspace / "stages" / stage / "output.md"
        if output_path.exists():
            parts.extend([f"## {stage}", "", output_path.read_text(encoding="utf-8").strip(), ""])
    write_text(workspace / "final_report.md", "\n".join(parts).strip() + "\n")


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf).expanduser().resolve()
    ensure_pdf(pdf_path)
    if args.mode == "auto":
        args.mode, auto_modules = resolve_auto_plan(args.request_text)
        if auto_modules:
            args.modules = ",".join(auto_modules)
    modules = [x.strip() for x in args.modules.split(",") if x.strip()] if args.modules else None
    stages = resolve_stage_sequence(args.mode, modules)
    workspace = get_workspace(args, pdf_path)
    workspace.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(args, pdf_path, workspace, stages)
    write_json(workspace / "manifest.json", manifest)
    print("=== paper-weaver ===")
    print(f"PDF: {pdf_path}")
    print(f"工作目录: {workspace}")
    print(f"阶段顺序: {stages}")
    for stage in stages:
        code = process_stage(stage, workspace / "stages" / stage, manifest)
        if code != 0:
            return code
    assemble_report(workspace, stages, manifest)
    print(f"[COMPLETE] 全部阶段完成，已生成总报告：{workspace / 'final_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
