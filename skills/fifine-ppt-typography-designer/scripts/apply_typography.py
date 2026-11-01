#!/usr/bin/env python3
"""Apply a library typography style to an existing PowerPoint without overwriting it.

Only regular slide runs are edited. Layouts, masters, notes, charts, SmartArt,
fields and other complex objects are intentionally left untouched and reported.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata
from zipfile import ZipFile

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.text.text import Font
from pptx.util import Pt

if __package__:
    from .font_index import resolve_root
    from .recommend_typography import recommend_style
else:
    from font_index import resolve_root
    from recommend_typography import recommend_style


ROLE_LABELS = {
    "cover": "封面标题",
    "title": "页面标题",
    "subtitle": "模块小标题",
    "body": "正文",
    "data": "核心数据",
    "english": "英文标题",
    "chart": "图表标签",
    "caption": "图注/来源",
}
PPTX_LIMITATION = (
    "仅写入 family、字号和布尔 Bold；不更改原颜色、字间距、行距或其他格式。"
    "PPTX 不嵌入或安装字体；Semibold/Heavy 和可变轴不能精确控制，"
    "PowerPoint 可能选择其他字重、字体回退或重排；最终显示未经验证。"
)
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
EMU_PER_PT = 12700.0


def parse_slides(value: str | None, count: int) -> set[int]:
    """Parse a one-based selection and reject malformed or out-of-range entries."""
    if value is None:
        return set(range(1, count + 1))
    selected: set[int] = set()
    for token in value.split(","):
        token = token.strip()
        match = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", token)
        if not match:
            raise ValueError(f"无效的 --slides 项 {token!r}；例如 1,3-5")
        first = int(match.group(1))
        last = int(match.group(2) or first)
        if first < 1 or last < first or last > count:
            raise ValueError(f"幻灯片范围 {token!r} 超出 1–{count} 或顺序错误")
        selected.update(range(first, last + 1))
    return selected


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_font(record: dict | None, root: Path, cache: dict) -> tuple[dict | None, str | None]:
    """Revalidate the exact indexed file and only expose its actually covered glyphs."""
    if not record:
        return None, "推荐角色缺少字体"
    relative = record.get("path")
    digest = record.get("sha256")
    if not isinstance(relative, str) or not relative or not isinstance(digest, str) or not digest:
        return None, "字体索引缺少相对路径或 SHA256，请重建索引"
    relpath = Path(relative)
    if relpath.is_absolute() or ".." in relpath.parts:
        return None, f"拒绝越界字体路径：{relative}"
    path = (root / relpath).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None, f"拒绝越界字体路径：{relative}"
    key = (str(path), digest)
    if key not in cache:
        try:
            if not path.is_file():
                raise FileNotFoundError(path)
            if file_sha256(path).lower() != digest.lower():
                raise ValueError("SHA256 与索引不一致")
            cache[key] = None
        except (OSError, ValueError) as exc:
            cache[key] = f"字体文件不可用或已更改：{relative}（{exc}）；请重建索引"
    if cache[key] is not None:
        return None, cache[key]
    family = record.get("family")
    coverage = record.get("coverage")
    if not isinstance(family, str) or not family or not isinstance(coverage, list):
        return None, f"字体元数据不完整：{relative}；请重建索引"
    return {"record": record, "path": str(path), "coverage": set(coverage)}, None


def is_cjk(char: str) -> bool:
    code = ord(char)
    return (
        0x2E80 <= code <= 0xA4CF
        or 0xAC00 <= code <= 0xD7AF
        or 0xF900 <= code <= 0xFAFF
        or 0xFE30 <= code <= 0xFE4F
        or 0xFF00 <= code <= 0xFFEF
        or 0x20000 <= code <= 0x323AF
        or 0x3000 <= code <= 0x303F
    )

def has_complex_shaping(text: str) -> bool:
    """Avoid splitting grapheme clusters, bidirectional or complex-script runs."""
    complex_bidi = {"R", "AL", "AN", "RLE", "RLO", "LRE", "LRO", "PDF", "RLI", "LRI", "FSI", "PDI"}
    for char in text:
        category = unicodedata.category(char)
        name = unicodedata.name(char, "")
        if (category.startswith("M") or category == "Cf" or
                unicodedata.bidirectional(char) in complex_bidi or
                any(script in name for script in (
                    "ARABIC", "HEBREW", "DEVANAGARI", "BENGALI", "GURMUKHI", "GUJARATI",
                    "ORIYA", "TAMIL", "TELUGU", "KANNADA", "MALAYALAM", "SINHALA",
                    "THAI", "LAO", "TIBETAN", "MYANMAR", "KHMER", "SYRIAC", "THAANA",
                ))):
            return True
    return False


def split_scripts(text: str) -> list[tuple[str, str]]:
    """Keep neutral marks with their neighboring script and never reorder text."""
    groups: list[tuple[str, str]] = []
    pending = ""
    for char in text:
        if is_cjk(char):
            kind = "cjk"
        elif char.isspace() or unicodedata.category(char)[0] in "PMZC":
            kind = None
        else:
            kind = "other"
        if kind is None:
            if groups:
                old_kind, old_text = groups[-1]
                groups[-1] = (old_kind, old_text + char)
            else:
                pending += char
        elif groups and groups[-1][0] == kind:
            old_kind, old_text = groups[-1]
            groups[-1] = (old_kind, old_text + pending + char)
            pending = ""
        else:
            groups.append((kind, pending + char))
            pending = ""
    if pending:
        groups.append(("other", pending))
    return groups


def missing_characters(text: str, coverage: set[int]) -> list[str]:
    """Whitespace controls have layout semantics; all visible characters require cmap coverage."""
    return list(dict.fromkeys(char for char in text if not char.isspace() and ord(char) not in coverage))


def old_font(run, paragraph=None) -> dict:
    # Access existing XML directly: the public font properties can create rPr.
    rpr = run._r.rPr
    ppr = paragraph._p.pPr if paragraph is not None else None
    default_rpr = ppr.find(qn("a:defRPr")) if ppr is not None else None

    def read_properties(node):
        if node is None:
            return None
        font = Font(node)
        ea = node.find(qn("a:ea"))
        size = font.size
        return {"family": font.name,
                "east_asian_family": ea.get("typeface") if ea is not None else None,
                "size_pt": round(size.pt, 2) if size is not None else None,
                "bold": font.bold}

    explicit = read_properties(rpr) or {"family": None, "east_asian_family": None,
                                       "size_pt": None, "bold": None}
    explicit["paragraph_default"] = read_properties(default_rpr)
    explicit["note"] = "空值继续从段落/版式/母版/主题继承，未解析最终显示字体"
    return explicit


def describe_font(font: dict, role: dict) -> dict:
    record = font["record"]
    return {
        "family": record["family"],
        "subfamily": record.get("subfamily"),
        "names": record.get("names", {}),
        "path": record["path"],
        "resolved_path": font["path"],
        "face_index": record.get("face_index", 0),
        "sha256": record.get("sha256"),
        "indexed_weight": record.get("weight"),
        "recommended_role_weight": role.get("weight"),
        "available_axes": record.get("axes", []),
        "recommended_role_axis_values_not_applied": role.get("axis_values", {}),
        "identity_note": "该文件/集合面用于推荐与覆盖检查；PPTX 只写家族名，无法绑定具体文件或 face_index，PowerPoint 实际选面未经验证。",
        "installed": record.get("installed", {"status": "未确认"}),
        "license": record.get("license", {"status": "待核实"}),
    }


def existing_file_pair(input_path: Path, output_path: Path, report_path: Path, root: Path) -> None:
    if not input_path.is_file():
        raise FileNotFoundError(f"输入文件不存在：{input_path}")
    if input_path.suffix.lower() not in {".ppt", ".pptx"}:
        raise ValueError("输入仅支持 .ppt 或 .pptx")
    try:
        input_path.resolve().relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("拒绝读取或转换只读字体库中的非字体文件")
    if output_path.suffix.lower() != ".pptx":
        raise ValueError("输出必须为新的 .pptx 文件")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("拒绝输入与输出为同一路径；原文件不会被覆盖")
    for path in (output_path, report_path):
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            pass
        else:
            raise ValueError(f"拒绝写入只读字体目录：{path}")
        if os.path.lexists(path):
            raise FileExistsError(f"拒绝覆盖已有输出或报告：{path}")
        if not path.parent.is_dir():
            raise FileNotFoundError(f"输出目录不存在：{path.parent}")


def convert_ppt_to_pptx(source: Path, directory: Path) -> Path:
    """Convert an isolated copy using a dedicated PowerPoint COM application."""
    if sys.platform != "win32":
        raise RuntimeError("旧式 .ppt 需要 Windows PowerPoint COM；请在 Windows 本机转换后重试")
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise RuntimeError("旧式 .ppt 需要 Windows PowerPoint 和可选依赖 pywin32") from exc

    copy_path = directory / "input-copy.ppt"
    converted_path = directory / "converted.pptx"
    shutil.copy2(source, copy_path)
    app = presentation = None
    initialized = False
    try:
        pythoncom.CoInitialize()
        initialized = True
        app = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            # msoAutomationSecurityForceDisable: never run macros from the source.
            app.AutomationSecurity = 3
        except Exception as exc:
            raise RuntimeError("无法强制禁用宏，拒绝自动转换") from exc
        # ReadOnly=True, Untitled=False, WithWindow=False. The user file is never opened.
        presentation = app.Presentations.Open(str(copy_path), True, False, False)
        presentation.SaveAs(str(converted_path), 24)  # ppSaveAsOpenXMLPresentation
        presentation.Close()
        presentation = None
        if not converted_path.is_file():
            raise RuntimeError("PowerPoint 未生成 PPTX 文件")
        return converted_path
    except Exception as exc:
        raise RuntimeError(f"PowerPoint COM 无法启动或转换 .ppt：{exc}；原稿保持不变") from exc
    finally:
        if presentation is not None:
            try:
                presentation.Close()
            except Exception:
                pass
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
        if initialized:
            pythoncom.CoUninitialize()


def group_scale(shape, current: tuple[float, float] | None) -> tuple[float, float] | None:
    """Propagate child-coordinate scale; rotation/reflection makes geometry uncertain."""
    if current is None:
        return None
    xfrm = shape._element.xfrm
    if xfrm is None or xfrm.chExt is None or xfrm.ext is None:
        return None
    if xfrm.rot or xfrm.flipH or xfrm.flipV:
        return None
    try:
        child_x = int(xfrm.chExt.get("cx"))
        child_y = int(xfrm.chExt.get("cy"))
        parent_x = int(xfrm.ext.get("cx"))
        parent_y = int(xfrm.ext.get("cy"))
        if min(child_x, child_y, parent_x, parent_y) <= 0:
            return None
        return current[0] * parent_x / child_x, current[1] * parent_y / child_y
    except (TypeError, ValueError):
        return None


def shape_geometry(shape, scale: tuple[float, float] | None) -> tuple[float, float] | None:
    if scale is None:
        return None
    try:
        if shape.rotation:
            return None
        if shape.width is None or shape.height is None:
            return None
        return shape.width / EMU_PER_PT * scale[0], shape.height / EMU_PER_PT * scale[1]
    except (TypeError, ValueError, AttributeError):
        return None


def classify(shape, text: str, slide_number: int, slide_size: tuple[float, float],
             geometry: tuple[float, float] | None, table_cell: bool = False) -> tuple[str | None, str]:
    compact = " ".join(text.split())
    if not compact:
        return None, "空文本"
    if table_cell:
        return "chart", "表格单元格，使用高密度图表标签角色"
    if shape.is_placeholder:
        kind = shape.placeholder_format.type
        if kind == PP_PLACEHOLDER.CENTER_TITLE:
            return ("cover" if slide_number == 1 else "title"), "居中标题占位符"
        if kind == PP_PLACEHOLDER.VERTICAL_TITLE:
            return None, "竖排标题占位符无法可靠估计溢出，保持原样"
        if kind == PP_PLACEHOLDER.TITLE:
            return ("cover" if slide_number == 1 else "title"), "标题占位符"
        if kind == PP_PLACEHOLDER.SUBTITLE:
            return "subtitle", "副标题占位符"
        if kind == PP_PLACEHOLDER.VERTICAL_BODY:
            return None, "竖排正文占位符无法可靠估计溢出，保持原样"
        if kind in (PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.OBJECT):
            return "body", "正文/内容占位符"
        if kind in (PP_PLACEHOLDER.DATE, PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.SLIDE_NUMBER,
                    PP_PLACEHOLDER.HEADER):
            return "caption", "页眉、页脚或页码占位符"
        return None, f"无法安全判断占位符角色：{kind}"
    if geometry is None:
        return None, "形状尺寸或组合缩放无法可靠判断"
    width, height = geometry
    slide_width, slide_height = slide_size
    if width <= 0 or height <= 0:
        return None, "形状尺寸无效"
    # A short, mostly numeric textbox is recognizable without imposing semantic guessing on arbitrary labels.
    numeric = sum(char.isdigit() for char in compact)
    if numeric and len(compact) <= 18 and numeric / len(compact) >= 0.35 and height >= 30:
        return "data", "短且以数字为主的独立文本框"
    if len(compact) >= 80 or len(text.splitlines()) >= 3:
        return "body", "较长或多段文本框"
    if len(compact) <= 32 and width >= slide_width * 0.50 and height >= 38:
        return ("cover" if slide_number == 1 else "title"), "宽幅短标题形状"
    if len(compact) <= 48 and width >= slide_width * 0.22 and 26 <= height <= slide_height * 0.28:
        return "subtitle", "中等宽度短文本形状"
    if len(compact) > 48 and width >= slide_width * 0.25 and height >= 40:
        return "body", "较宽的正文文本框"
    return None, "普通短标签或形状语义不明确，保留原样"


def estimated_overflow(text: str, geometry: tuple[float, float] | None,
                       margins: tuple[float, float, float, float], size: float,
                       vertical_scale: float = 1.0) -> str | None:
    """Conservative estimate only, not a claim of actual PowerPoint rendering."""
    if geometry is None:
        return "无法可靠计算尺寸/组合缩放，存在未评估的溢出风险"
    width = geometry[0] - margins[0] - margins[1]
    height = geometry[1] - margins[2] - margins[3]
    if width <= 0 or height <= 0 or size <= 0:
        return "文本区域尺寸无效或过小，存在溢出风险"
    units = []
    for line in text.replace("\v", "\n").split("\n"):
        units.append(sum(1.0 if is_cjk(ch) or unicodedata.east_asian_width(ch) in "WF" else 0.65
                         for ch in line if not unicodedata.combining(ch)))
    lines = sum(max(1, math.ceil(amount * size / width)) for amount in units)
    if size > width or lines * size * vertical_scale * 1.2 > height:
        return f"按字符宽度粗估可能溢出（约 {lines} 行；不是 PowerPoint 实际排版测量）"
    return None


def margins_pt(frame, scale: tuple[float, float] | None, cell=None) -> tuple[float, float, float, float]:
    sx, sy = scale or (1.0, 1.0)
    source = cell if cell is not None else frame
    return (source.margin_left / EMU_PER_PT * sx, source.margin_right / EMU_PER_PT * sx,
            source.margin_top / EMU_PER_PT * sy, source.margin_bottom / EMU_PER_PT * sy)


def cell_geometry(shape, table, row: int, column: int, cell,
                  scale: tuple[float, float] | None) -> tuple[float, float] | None:
    base = shape_geometry(shape, scale)
    if base is None:
        return None
    try:
        span_w = cell.span_width if cell.is_merge_origin else 1
        span_h = cell.span_height if cell.is_merge_origin else 1
        width = sum(table.columns[c].width for c in range(column, column + span_w))
        height = sum(table.rows[r].height for r in range(row, row + span_h))
        return width / EMU_PER_PT * scale[0], height / EMU_PER_PT * scale[1]
    except (IndexError, TypeError, ValueError):
        return None


def unsupported_entry(slide: int, location: str, reason: str) -> dict:
    return {"slide": slide, "location": location, "reason": reason}


def plan_frame(frame, shape, slide_number: int, location: str, role_name: str, role_reason: str,
               geometry: tuple[float, float] | None, scale: tuple[float, float] | None,
               roles: dict, fonts: dict, cell=None) -> tuple[list[dict], list[dict], list[tuple]]:
    body_props = frame._txBody.bodyPr
    if body_props is not None and body_props.get("vert", "horz") != "horz":
        return [], [unsupported_entry(slide_number, location, "竖排或特殊方向文字保持原样")], []
    if body_props is not None:
        if body_props.find(qn("a:prstTxWarp")) is not None or body_props.get("rot", "0") != "0":
            return [], [unsupported_entry(slide_number, location, "旋转或变形文字无法可靠估计溢出，保持原样")], []
    role = roles.get(role_name) or {}
    size = role.get("size")
    if not isinstance(size, (int, float)) or size <= 0:
        return [], [unsupported_entry(slide_number, location, "推荐角色缺少有效字号，原样保留")], []
    primary, primary_error = fonts.get(role_name, (None, "推荐角色缺失"))
    english, english_error = fonts.get("english", (None, "英文角色缺失"))
    text = frame.text
    margin = margins_pt(frame, scale, cell)
    sx, sy = scale or (1.0, 1.0)
    risk = estimated_overflow(text, geometry, margin, float(size) * sx, sy / sx)
    if risk is None and ("\t" in text or any(
            paragraph._p.pPr is not None and
            (paragraph._p.pPr.find(qn("a:lnSpc")) is not None or
             paragraph._p.pPr.find(qn("a:spcBef")) is not None or
             paragraph._p.pPr.find(qn("a:spcAft")) is not None)
            for paragraph in frame.paragraphs)):
        risk = "制表符或显式段落间距无法可靠估计溢出，保持原样"
    entries: list[dict] = []
    skipped: list[dict] = []
    operations: list[tuple] = []
    field_tag = qn("a:fld")
    for paragraph_number, paragraph in enumerate(frame.paragraphs, 1):
        field_count = sum(child.tag == field_tag for child in paragraph._p)
        if field_count:
            skipped.append(unsupported_entry(slide_number, f"{location} 段落 {paragraph_number}",
                                             f"{field_count} 个动态字段保持原样"))
        for run_number, run in enumerate(paragraph.runs, 1):
            text_run = run.text
            if not text_run or not text_run.strip():
                continue
            run_location = f"{location} 段落 {paragraph_number} run {run_number}"
            groups = split_scripts(text_run)
            if not groups:
                continue
            segments: list[tuple[str, dict, dict, str]] = []
            error = None
            if primary is None:
                error = f"该文字角色的字体不可用：{primary_error}"
            if has_complex_shaping(text_run):
                error = "涉及组合字符、双向或复杂文字塑形，无法安全拆分/换字，保持原样"
            if len(groups) > 1 and run._r.rPr is not None:
                rpr = run._r.rPr
                if (rpr.find(qn("a:extLst")) is not None or
                        rpr.find(qn("a:hlinkClick")) is not None or
                        rpr.find(qn("a:hlinkMouseOver")) is not None):
                    error = "带扩展元数据或超链接的混排 run 无法安全拆分，保持原样"
            for kind, content in groups:
                if error:
                    break
                candidates = []
                if kind == "cjk":
                    if primary is not None:
                        candidates.append((primary, role))
                else:
                    contains_letters = any(char.isalpha() for char in content)
                    english_first = contains_letters and role_name not in ("data", "chart", "caption")
                    if english_first and english is not None:
                        candidates.append((english, roles.get("english") or {}))
                    if primary is not None:
                        candidates.append((primary, role))
                    if not english_first and english is not None:
                        candidates.append((english, roles.get("english") or {}))
                if not candidates:
                    error = f"该文字角色的字体不可用：{primary_error}; 英文字体：{english_error}"
                    break
                choices = [(font, font_role) for font, font_role in candidates
                           if not missing_characters(content, font["coverage"])]
                if not choices:
                    missing_sets = [set(missing_characters(content, candidate[0]["coverage"]))
                                    for candidate in candidates]
                    missing = [char for char in dict.fromkeys(content)
                               if all(char in values for values in missing_sets)]
                    codepoints = " ".join(f"U+{ord(char):04X}" for char in missing)
                    detail = f" {' '.join(missing)!r}（{codepoints}）" if missing else "（不同候选各缺部分字符）"
                    error = f"所选库内字体不能完整覆盖该段{detail}，此 run 保持原样"
                    break
                font, font_role = choices[0]
                if font is not candidates[0][0]:
                    selection_note = (f"首选 {candidates[0][0]['record']['family']} 缺少该段字符；"
                                      f"改用受限库中的 {font['record']['family']}，覆盖已检查")
                elif font is english:
                    selection_note = "使用推荐英文字体，字符覆盖已检查"
                else:
                    selection_note = "使用本角色字体，字符覆盖已检查"
                segments.append((content, font, font_role, selection_note))
            if error:
                unchanged = unsupported_entry(slide_number, run_location, error)
                unchanged.update({"shape_id": shape.shape_id, "shape_name": shape.name,
                                  "role": role_name, "role_label": ROLE_LABELS[role_name],
                                  "proposed_size_pt": size, "original_text": text_run,
                                  "original_font": old_font(run, paragraph)})
                skipped.append(unchanged)
                continue
            # The size is determined by the semantic role, not the English role.
            mapped = []
            for content, font, font_role, selection_note in segments:
                requested_weight = font_role.get("weight")
                if not isinstance(requested_weight, (int, float)):
                    requested_weight = font["record"].get("weight", 400)
                bold = bool(requested_weight >= 700)
                mapped.append({
                    "text": content,
                    "font": describe_font(font, font_role),
                    "size_pt": size,
                    "bold": bold,
                    "recommended_spacing_not_applied": font_role.get("spacing"),
                    "recommended_line_height_not_applied": role.get("line_height"),
                    "recommended_color_not_applied": font_role.get("color"),
                    "selection_note": selection_note,
                })
            entry = {
                "slide": slide_number,
                "location": run_location,
                "shape_id": shape.shape_id,
                "shape_name": shape.name,
                "role": role_name,
                "role_label": ROLE_LABELS[role_name],
                "role_reason": role_reason,
                "original_text": text_run,
                "original_font": old_font(run, paragraph),
                "planned_segments": mapped,
                "overflow_risk": risk,
                "status": "拟修改" if not risk else "保留原样：存在溢出风险",
            }
            entries.append(entry)
            if risk:
                skipped.append(unsupported_entry(slide_number, run_location, risk + "；原样保留"))
            else:
                operations.append((run, mapped))
    return entries, skipped, operations


def collect_slide(slide, slide_number: int, slide_size: tuple[float, float], roles: dict,
                  fonts: dict) -> tuple[list[dict], list[dict], list[tuple]]:
    entries: list[dict] = []
    skipped: list[dict] = []
    operations: list[tuple] = []

    def visit(shapes, scale: tuple[float, float] | None, prefix: str = "") -> None:
        ignored_tags = {qn("p:nvGrpSpPr"), qn("p:grpSpPr"), qn("p:extLst")}
        supported_tags = {qn("p:sp"), qn("p:grpSp"), qn("p:graphicFrame"),
                          qn("p:cxnSp"), qn("p:pic")}
        for ordinal, element in enumerate(shapes._spTree, 1):
            if element.tag in ignored_tags:
                continue
            if element.tag not in supported_tags:
                names = element.xpath(".//p:cNvPr")
                identity = (f"id {names[0].get('id')} [{names[0].get('name')}]"
                            if names else f"XML 子项 {ordinal}")
                skipped.append(unsupported_entry(slide_number, prefix + identity,
                                                 f"不支持的特殊对象 {element.tag} 保持原样"))
                continue
            shape = shapes._shape_factory(element)
            location = f"{prefix}shape {shape.shape_id} [{shape.name}]"
            if element.tag == qn("p:grpSp"):
                child_scale = group_scale(shape, scale)
                if child_scale is None:
                    skipped.append(unsupported_entry(slide_number, location,
                                                     "组合存在旋转、翻转或不明缩放，子文本保持原样"))
                visit(shape.shapes, child_scale, location + " / ")
                continue
            if shape.has_chart:
                skipped.append(unsupported_entry(slide_number, location, "图表及其内部标签不作修改"))
                continue
            if shape.has_table:
                table = shape.table
                for row_index, row in enumerate(table.rows):
                    for column_index, cell in enumerate(row.cells):
                        cell_location = f"{location} 表格 R{row_index + 1}C{column_index + 1}"
                        if cell._tc.txBody is None:
                            continue
                        frame = cell.text_frame
                        if cell.is_spanned:
                            if frame.text.strip():
                                skipped.append(unsupported_entry(slide_number, cell_location,
                                                                 "合并表格的被覆盖单元格，保持原样"))
                            continue
                        if not frame.text.strip():
                            continue
                        geometry = cell_geometry(shape, table, row_index, column_index, cell, scale)
                        role_name, reason = classify(shape, frame.text, slide_number,
                                                     slide_size, geometry, table_cell=True)
                        result = plan_frame(frame, shape, slide_number, cell_location,
                                            role_name, reason, geometry, scale, roles, fonts, cell)
                        entries.extend(result[0])
                        skipped.extend(result[1])
                        operations.extend(result[2])
                continue
            if shape.has_text_frame:
                # Most autoshapes have no text body; accessing .text_frame would create one.
                if shape._element.txBody is None:
                    continue
                if shape._element.xpath("./p:txBody/a:bodyPr/a:prstTxWarp"):
                    skipped.append(unsupported_entry(slide_number, location,
                                                     "艺术字/变形文字保持原样"))
                    continue
                frame = shape.text_frame
                if not frame.text.strip():
                    continue
                geometry = shape_geometry(shape, scale)
                role_name, reason = classify(shape, frame.text, slide_number, slide_size, geometry)
                if role_name is None:
                    skipped.append(unsupported_entry(slide_number, location, reason))
                    continue
                result = plan_frame(frame, shape, slide_number, location, role_name, reason,
                                    geometry, scale, roles, fonts)
                entries.extend(result[0])
                skipped.extend(result[1])
                operations.extend(result[2])
                continue
            element_tag = shape._element.tag
            if element_tag == qn("p:graphicFrame"):
                skipped.append(unsupported_entry(slide_number, location,
                                                 "SmartArt、OLE 或其他图形对象保持原样"))
            elif element_tag not in {qn("p:pic"), qn("p:cxnSp")}:
                skipped.append(unsupported_entry(slide_number, location,
                                                 "特殊或未知对象保持原样，未处理其中的文字"))

    visit(slide.shapes, (1.0, 1.0))
    return entries, skipped, operations


def set_typeface(rpr, family: str) -> None:
    """Set both DrawingML Latin and East Asian slots, retaining all other run properties."""
    Font(rpr).name = family
    ea = rpr.find(qn("a:ea"))
    if ea is None:
        ea = OxmlElement("a:ea")
        rpr.insert_element_before(ea, "a:cs", "a:sym", "a:hlinkClick", "a:hlinkMouseOver",
                                  "a:rtl", "a:extLst")
    ea.set("typeface", family)


def apply_operation(run, mapped: list[dict]) -> None:
    """Clone only run XML; hyperlink, fields, paragraph and all non-font attributes survive."""
    original = run._r
    for segment in mapped:
        new_run = deepcopy(original)
        text_element = new_run.t
        text_element.text = segment["text"]
        if segment["text"][:1].isspace() or segment["text"][-1:].isspace():
            text_element.set(XML_SPACE, "preserve")
        rpr = new_run.get_or_add_rPr()
        font = Font(rpr)
        set_typeface(rpr, segment["font"]["family"])
        font.size = Pt(segment["size_pt"])
        font.bold = segment["bold"]
        original.addprevious(new_run)
    original.getparent().remove(original)


def print_preview(report: dict) -> None:
    print(f"只读修改预览：{report['input']} → {report['output']}，风格 {report['style']}", flush=True)
    print(PPTX_LIMITATION, flush=True)
    for item in report["slides"]:
        print(f"\n第 {item['slide']} 页：", flush=True)
        for entry in item["changes"]:
            original = entry["original_font"]
            details = "; ".join(
                f"{part['text']!r}: {part['font']['family']} "
                f"[{part['font']['path']}#{part['font']['face_index']}] "
                f"{part['size_pt']}pt Bold={part['bold']}；"
                f"安装={part['font']['installed'].get('status', '未确认')} "
                f"许可={part['font']['license'].get('status', '待核实')}；{part['selection_note']}"
                for part in entry["planned_segments"]
            )
            paragraph_default = original["paragraph_default"] or {}
            original_family = original["family"] or paragraph_default.get("family") or "继承主题/母版"
            original_size = original["size_pt"] or paragraph_default.get("size_pt") or "继承"
            print(f"  {entry['location']} 原={original_family}/{original_size}pt "
                  f"→ {entry['role_label']}: {details} [{entry['status']}]", flush=True)
        for skipped in item["unprocessed"]:
            extra = ""
            if "original_font" in skipped:
                original = skipped["original_font"]
                defaults = original["paragraph_default"] or {}
                family = original["family"] or defaults.get("family") or "继承主题/母版"
                size = original["size_pt"] or defaults.get("size_pt") or "继承"
                extra = f" 原={family}/{size}pt，拟定={skipped['role_label']} {skipped['proposed_size_pt']}pt；"
            print(f"  未处理 {skipped['location']}:{extra} {skipped['reason']}", flush=True)
        if not item["changes"] and not item["unprocessed"]:
            print("  无可处理文字或特殊对象", flush=True)
    for warning in report["warnings"]:
        print(f"警告：{warning}", flush=True)


def write_new_output(source: Path, changed_parts: dict[str, object], output: Path,
                     report_path: Path, report: dict) -> None:
    """Copy original ZIP parts; serialize only edited slide XML with python-pptx."""
    written: list[Path] = []
    try:
        with ZipFile(source, "r") as original:
            original_infos = original.infolist()
            original_names = {info.filename for info in original_infos}
            if len(original_names) != len(original_infos):
                raise ValueError("输入文件含重复 ZIP 条目，无法安全保真编辑")
            if not changed_parts.keys() <= original_names:
                raise ValueError("无法定位待修改的原始幻灯片 XML，拒绝保存")
            if changed_parts and any(name.startswith("_xmlsignatures/") for name in original_names):
                raise ValueError("输入包含数字签名；修改会破坏签名，拒绝保存")
            with output.open("xb") as stream:
                written.append(output)
                with ZipFile(stream, "w") as result:
                    result.comment = original.comment
                    for info in original_infos:
                        if info.filename in changed_parts:
                            result.writestr(info, changed_parts[info.filename].blob)
                        else:
                            with original.open(info, "r") as source_part, result.open(info, "w") as target_part:
                                shutil.copyfileobj(source_part, target_part, length=1024 * 1024)
        for page in report["slides"]:
            for entry in page["changes"]:
                if entry["status"] == "拟修改":
                    entry["status"] = "已修改"
        with report_path.open("x", encoding="utf-8", newline="\n") as stream:
            written.append(report_path)
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except Exception:
        for path in reversed(written):
            try:
                path.unlink()
            except OSError:
                pass
        raise


def apply_typography(input_path: str | Path, output_path: str | Path, style: str,
                     root: str | Path | None = None, slides: str | None = None) -> dict:
    """Analyze then save a new PPTX and a UTF-8 JSON operation report."""
    if style not in {f"{number:02}" for number in range(1, 9)}:
        raise ValueError("风格必须是 01 至 08")
    input_path = Path(input_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().absolute()
    report_path = output_path.with_name(output_path.name + ".typography-report.json")
    font_root = Path(resolve_root(root)).resolve()
    existing_file_pair(input_path, output_path, report_path, font_root)
    recommendation = recommend_style(style, root=font_root)
    if not isinstance(recommendation, dict) or not isinstance(recommendation.get("roles"), dict):
        raise ValueError(f"风格 {style} 的推荐不可用")
    roles = recommendation["roles"]
    cache: dict = {}
    fonts = {name: safe_font((roles.get(name) or {}).get("font"), font_root, cache)
             for name in ROLE_LABELS}
    input_hash = file_sha256(input_path)
    with tempfile.TemporaryDirectory(prefix=".ppt-typography-", dir=output_path.parent) as tmp:
        source = input_path
        conversion_note = None
        if input_path.suffix.lower() == ".ppt":
            source = convert_ppt_to_pptx(input_path, Path(tmp))
            conversion_note = "旧式 PPT 的副本经 PowerPoint COM 转为 PPTX；转换可能改变布局或特殊对象。"
        presentation = Presentation(str(source))
        selected = parse_slides(slides, len(presentation.slides))
        slide_width = presentation.slide_width / EMU_PER_PT
        slide_height = presentation.slide_height / EMU_PER_PT
        if slide_width <= 0 or slide_height <= 0:
            raise ValueError("演示文稿页面尺寸无效")
        warnings = [PPTX_LIMITATION,
                    "原颜色、段落布局、图片、图表、备注、母版、动态字段和不支持对象不会被本工具主动更改。",
                    "仅依据字体索引逐字符 cmap 判断覆盖；组合字符、复杂排版和最终视觉效果仍需 PowerPoint 检查。",
                    "原有字体颜色保持不变；换字后可能改变对比度，需人工检查。",
                    "授权与安装状态来自实时检查，不代表已获商业使用许可或已验证实际显示。"]
        warnings.extend(recommendation.get("warnings") or [])
        warnings.extend(f"{ROLE_LABELS[name]}：{error}" for name, (_, error) in fonts.items() if error)
        if abs(slide_width / slide_height - 16 / 9) > 0.01:
            warnings.append(f"页面并非 16:9（{slide_width:.1f}×{slide_height:.1f} pt）；"
                            "统一保留原样，不应用为 16:9 制定的字号。")
        if conversion_note:
            warnings.append(conversion_note)
        all_operations: list[tuple] = []
        changed_parts: dict[str, object] = {}
        slide_reports: list[dict] = []
        non_widescreen = abs(slide_width / slide_height - 16 / 9) > 0.01
        for slide_number, slide in enumerate(presentation.slides, 1):
            if slide_number not in selected:
                continue
            entries, skipped, operations = collect_slide(slide, slide_number, (slide_width, slide_height),
                                                         roles, fonts)
            if non_widescreen:
                for entry in entries:
                    if entry["status"] == "拟修改":
                        entry["status"] = "保留原样：页面并非 16:9"
                        skipped.append(unsupported_entry(slide_number, entry["location"],
                                                         "页面并非 16:9，保持原样"))
                operations = []
            slide_xml = slide._element
            if operations and (slide_xml.xpath(".//p:timing") or
                               slide_xml.xpath(".//p:extLst | .//a:extLst") or
                               slide_xml.xpath(".//*[namespace-uri()='http://schemas.openxmlformats.org/markup-compatibility/2006']")):
                reason = "页面包含动画、扩展或兼容性替代内容，修改/拆分 run 可能影响特殊对象，整页保持原样"
                for entry in entries:
                    if entry["status"] == "拟修改":
                        entry["status"] = "保留原样：页面含动画、扩展或兼容性替代内容"
                        skipped.append(unsupported_entry(slide_number, entry["location"], reason))
                operations = []
            all_operations.extend(operations)
            if operations:
                changed_parts[str(slide.part.partname).lstrip("/")] = slide.part
            slide_reports.append({"slide": slide_number, "changes": entries, "unprocessed": skipped})
        if not all_operations:
            warnings.append("没有满足安全条件的可修改 run；将输出未改写字体的副本及原因报告。")
        report = {
            "input": str(input_path),
            "input_sha256": input_hash,
            "output": str(output_path),
            "report": str(report_path),
            "style": style,
            "font_root": str(font_root),
            "selected_slides": sorted(selected),
            "slide_size_pt": [round(slide_width, 2), round(slide_height, 2)],
            "conversion": conversion_note,
            "changed_run_count": len(all_operations),
            "changed_slide_parts": sorted(changed_parts),
            "warnings": warnings,
            "unprocessed_global": ["幻灯片母版、版式与备注保持原样", "图表内部标签、SmartArt、动态字段与其他特殊对象不处理"],
            "slides": slide_reports,
        }
        print_preview(report)
        for run, mapped in all_operations:
            apply_operation(run, mapped)
        # Abort if an external process changed the user's input while it was being analyzed.
        if file_sha256(input_path) != input_hash:
            raise RuntimeError("输入文件在处理期间发生变化；未写入输出")
        write_new_output(source, changed_parts, output_path, report_path, report)
        if file_sha256(input_path) != input_hash:
            for created in (output_path, report_path):
                try:
                    created.unlink()
                except OSError:
                    pass
            raise RuntimeError("输入文件在输出期间发生变化；已尝试移除不一致的输出")
    print(f"\n已保存新 PPTX：{output_path}\n操作报告：{report_path}", flush=True)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="安全复制并应用 PPT 字体方案，不修改原稿")
    parser.add_argument("--input", required=True, help="输入 .pptx 或 Windows PowerPoint 可转换的 .ppt")
    parser.add_argument("--output", required=True, help="不存在的新 .pptx；同时生成 JSON 侧车报告")
    parser.add_argument("--style", required=True, choices=[f"{number:02}" for number in range(1, 9)])
    parser.add_argument("--root", help="限定字体库根目录；也可通过 PPT_TYPOGRAPHY_FONT_ROOT 指定")
    parser.add_argument("--slides", help="仅处理指定页，1 起计，例如 1,3-5")
    args = parser.parse_args(argv)
    try:
        apply_typography(args.input, args.output, args.style, args.root, args.slides)
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
