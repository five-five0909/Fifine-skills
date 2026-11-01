#!/usr/bin/env python3
"""Render local-font specimens as 16:9 PDF/PNG or an editable PowerPoint slide.

The font root is read-only.  Fonts are opened as binary streams, so Pillow can
never fall back to its operating-system font search when a face cannot open.
"""
from __future__ import annotations

import argparse
import bisect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from font_index import load_index
from recommend_typography import recommend_styles

WIDTH, HEIGHT = 1920, 1080
# 13.333... x 7.5 inches at 144 dpi: one point is two image pixels.
PX_PER_PT = HEIGHT / 540
SCALE = WIDTH / 1600
SAMPLE_CN = "智控卫士"
SAMPLE_SUBTITLE = "矿山重金属污染智能治理系统"
SAMPLE_EN = "INTELLIGENT ENVIRONMENTAL CONTROL"
SAMPLE_EN_SHORT = "AI-DRIVEN SOLUTIONS"
SAMPLE_DATA = "97.98%"
SAMPLE_RANGE = "01—08"

# Background and accent originate from PPT最终字体配置.md.  The other colours
# are deliberately selected for contrast; historical font paths are not used.
STYLES = {
    "01": ("典藏黑金", "#101016", "#D5B46A", "#F4F0E7", "#ACA69A", "ELEVATED VISION"),
    "02": ("瑞士秩序", "#F4F5F7", "#20252C", "#20252C", "#606974", "CLARITY IN DATA"),
    "03": ("深海未来", "#081827", "#3BE1E8", "#E8F5F7", "#8AACB8", "FUTURE SYSTEMS"),
    "04": ("杂志新奢", "#171315", "#C9A36A", "#F3EAE1", "#B1A19B", "THE EDITORIAL ISSUE"),
    "05": ("自然人文", "#F4F1E9", "#657E58", "#293528", "#697466", "NATURE AND PEOPLE"),
    "06": ("当代东方", "#EFE9DD", "#A04432", "#352C27", "#786E64", "A MODERN HERITAGE"),
    "07": ("先锋海报", "#131313", "#F8DE39", "#F8F5E8", "#AAA99F", "MAKE AN IMPACT"),
    "08": ("圆润创意", "#F4EFFF", "#7656CB", "#302849", "#776F8D", "CURIOUS BY DESIGN"),
}


@dataclass(frozen=True)
class TextBox:
    # Design coordinates on a 1600 x 900 artboard.
    x: int
    y: int
    width: int
    height: int
    text: str
    role: str
    pt: float
    color: str
    tracking: float = 0
    align: str = "left"
    mixed: bool = False


@dataclass(frozen=True)
class Segment:
    text: str
    record: dict[str, Any] | None
    axes: tuple[tuple[str, float], ...] = ()
    replacement: bool = False


@dataclass
class PreparedBox:
    box: TextBox
    segments: list[Segment]


def _px(value: float) -> int:
    return round(value * SCALE)


def _weight(record: dict[str, Any]) -> float:
    try:
        return float(record.get("weight") or 400)
    except (TypeError, ValueError):
        return 400


def _fmt(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


def _path(root: Path, record: dict[str, Any]) -> Path:
    """Resolve only a real file under the indexed root, including symlinks."""
    raw = record.get("path")
    if not isinstance(raw, str) or not raw:
        raise ValueError("索引字体缺少相对路径；请重新 build 索引")
    relative = Path(raw.replace("\\", "/"))
    if relative.is_absolute() or relative.drive or ".." in relative.parts or ":" in raw:
        raise ValueError(f"索引字体路径不是安全相对路径: {raw}")
    resolved = (root / relative).resolve(strict=True)
    try:
        resolved.relative_to(root.resolve(strict=True))
    except ValueError as exc:
        raise ValueError(f"索引字体越过字体根目录: {raw}") from exc
    if not resolved.is_file():
        raise ValueError(f"索引字体不是文件: {raw}")
    stat = resolved.stat()
    if record.get("size") is not None and stat.st_size != record["size"]:
        raise ValueError(f"字体已变更，请重新 build 索引: {raw}")
    if record.get("mtime_ns") is not None and stat.st_mtime_ns != record["mtime_ns"]:
        raise ValueError(f"字体已变更，请重新 build 索引: {raw}")
    return resolved


def _supports(record: dict[str, Any] | None, text: str) -> bool:
    if not record:
        return False
    coverage = record.get("coverage") or []  # index guarantees ascending unique values
    for char in set(text):
        if char in "\n\r\t":
            continue
        codepoint = ord(char)
        i = bisect.bisect_left(coverage, codepoint)
        if i == len(coverage) or coverage[i] != codepoint:
            return False
    return True


def _axes(record: dict[str, Any], requested: dict[str, Any] | None) -> tuple[tuple[str, float], ...]:
    requested = requested or {}
    values = []
    for axis in record.get("axes") or []:
        default = float(axis["default"])
        value = float(requested.get(axis["tag"], default))
        value = max(float(axis["min"]), min(float(axis["max"]), value))
        values.append((str(axis["tag"]), value))
    return tuple(values)


def _character_script(char: str) -> str:
    codepoint = ord(char)
    if (0x3400 <= codepoint <= 0x9FFF or 0xF900 <= codepoint <= 0xFAFF
            or 0x20000 <= codepoint <= 0x323AF):
        return "cn"
    return "latin"


def _chunks(text: str, mixed: bool) -> list[tuple[str, str | None]]:
    if not mixed:
        return [(text, None)]
    chunks: list[tuple[str, str | None]] = []
    for char in text:
        script = _character_script(char)
        if chunks and chunks[-1][1] == script:
            chunks[-1] = (chunks[-1][0] + char, script)
        else:
            chunks.append((char, script))
    return chunks


def _roles(style: dict[str, Any], role: str) -> dict[str, Any]:
    return style.get("roles", {}).get(role) or {}


def _display_face(record: dict[str, Any]) -> bool:
    names = record.get("names") or {}
    values = [record.get("family", ""), names.get("family", ""),
              names.get("typographic_family", ""), names.get("full", ""),
              *(names.get("aliases") or [])]
    normalized = " ".join("".join(c for c in str(value).casefold() if c.isalnum()) for value in values)
    return any(name in normalized for name in ("youshebiaotihei", "优设标题黑", "優設標題黑"))


def _resolve_chunk(text: str, role: str, style: dict[str, Any], records: list[dict[str, Any]]) -> Segment:
    spec = _roles(style, role)
    original = spec.get("font")
    if _supports(original, text) and not (role in ("body", "chart", "caption") and _display_face(original)):
        return Segment(text, original, _axes(original, spec.get("axis_values")))

    # Prefer another explicitly recommended role, then the same style folder,
    # then any face inside the selected root. Never interpret folder names as
    # family metadata, and never choose an italic face just for its filename.
    target = float(spec.get("weight") or 400)
    style_id = str(style["style"])
    candidates: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    seen: set[tuple[str, int]] = set()
    preferred = [entry.get("font") for entry in style.get("roles", {}).values()]
    for priority, pool in ((0, preferred), (1, records)):
        for record in pool:
            if not record:
                continue
            key = (str(record.get("path", "")), int(record.get("face_index") or 0))
            if key in seen:
                continue
            seen.add(key)
            if role in ("body", "chart", "caption") and _display_face(record):
                continue
            if not _supports(record, text):
                continue
            italic = any(s in str(record.get("subfamily", "")).casefold()
                         for s in ("italic", "oblique"))
            in_style = str(record.get("path", "")).replace("\\", "/").split("/", 1)[0].startswith(style_id + "_")
            rank = (italic, priority, not in_style, abs(_weight(record) - target), key)
            candidates.append((rank, record))
    if candidates:
        record = min(candidates, key=lambda entry: entry[0])[1]
        # A fallback is reported at its actual axis defaults, not the primary's
        # requested axis values, which might not exist on the replacement.
        return Segment(text, record, _axes(record, None), True)
    return Segment(text, None, (), True)


def _resolve_text(text: str, role: str, style: dict[str, Any],
                  records: list[dict[str, Any]]) -> list[Segment]:
    whole = _resolve_chunk(text, role, style, records)
    if whole.record or len(text) <= 1:
        return [whole]
    # If no single face covers the whole paragraph, retain supported glyphs
    # in individually verified runs instead of dropping the whole paragraph.
    result: list[Segment] = []
    for char in text:
        segment = _resolve_chunk(char, role, style, records)
        if result and (result[-1].record, result[-1].axes, result[-1].replacement) == (
                segment.record, segment.axes, segment.replacement):
            previous = result[-1]
            result[-1] = Segment(previous.text + char, previous.record, previous.axes,
                                 previous.replacement)
        else:
            result.append(segment)
    return result


def _prepare_boxes(boxes: list[TextBox], style: dict[str, Any], records: list[dict[str, Any]]) -> list[PreparedBox]:
    prepared = []
    for box in boxes:
        segments = []
        for chunk, script in _chunks(box.text, box.mixed):
            role = "english" if script == "latin" else box.role
            segments.extend(_resolve_text(chunk, role, style, records))
        prepared.append(PreparedBox(box, segments))
    return prepared


def _artwork(style_id: str) -> tuple[list[tuple[Any, ...]], list[TextBox]]:
    """Eight deliberately different art directions on a common 16:9 canvas."""
    name, bg, accent, ink, muted, kicker = STYLES[style_id]
    G: list[tuple[Any, ...]] = []
    B: list[TextBox] = []

    def rect(x: int, y: int, w: int, h: int, color: str, radius: int = 0) -> None:
        G.append(("rect", x, y, w, h, color, radius))

    def line(x1: int, y1: int, x2: int, y2: int, color: str, weight: int = 1) -> None:
        G.append(("line", x1, y1, x2, y2, color, weight))

    def ellipse(x: int, y: int, w: int, h: int, color: str) -> None:
        G.append(("ellipse", x, y, w, h, color))

    def text(x: int, y: int, w: int, h: int, value: str, role: str,
             pt: float, color: str, tracking: float = 0, align: str = "left", mixed: bool = False) -> None:
        B.append(TextBox(x, y, w, h, value, role, pt, color, tracking, align, mixed))

    # Footer band is reserved for exact, traceable face and coverage labels.
    line(70, 680, 1530, 680, muted)
    text(70, 28, 850, 31, f"{style_id}  /  {name}", "caption", 14, ink)
    text(1130, 28, 400, 31, "TYPOGRAPHY SPECIMEN", "english", 11, muted, .02, "right")

    if style_id == "01":
        rect(75, 104, 5, 490, accent)
        line(110, 114, 1490, 114, accent, 2)
        text(115, 143, 850, 42, kicker, "english", 16, accent, .08)
        text(110, 213, 780, 125, SAMPLE_CN, "cover", 64, ink, .05)
        text(115, 354, 895, 58, SAMPLE_SUBTITLE, "subtitle", 27, ink)
        line(116, 440, 765, 440, accent, 2)
        text(115, 467, 860, 34, SAMPLE_EN, "english", 18, accent, .02)
        text(115, 521, 760, 35, SAMPLE_EN_SHORT, "english", 17, muted, .02)
        rect(1075, 190, 370, 330, "#1A1A22", 5)
        line(1105, 235, 1415, 235, accent, 2)
        text(1108, 260, 300, 40, "PERFORMANCE", "english", 13, accent, .04)
        text(1105, 318, 315, 86, SAMPLE_DATA, "data", 37, ink)
        text(1108, 438, 300, 32, "2026  /  01—08", "chart", 14, muted)
        text(115, 628, 1080, 38, "智能治理  AI-DRIVEN SOLUTIONS", "body", 18, ink, mixed=True)
    elif style_id == "02":
        rect(70, 95, 1460, 3, accent)
        line(800, 112, 800, 675, "#C8CDD2")
        text(70, 132, 610, 45, kicker, "english", 16, muted, .06)
        text(70, 206, 680, 105, SAMPLE_CN, "cover", 52, ink)
        text(72, 337, 680, 55, SAMPLE_SUBTITLE, "subtitle", 24, ink)
        text(72, 431, 680, 42, SAMPLE_EN_SHORT, "english", 18, muted)
        text(72, 560, 680, 34, "智能治理  AI-DRIVEN SOLUTIONS", "body", 18, ink, mixed=True)
        text(855, 138, 600, 35, "01 / SYSTEM OVERVIEW", "english", 14, ink)
        line(855, 185, 1510, 185, accent, 2)
        text(855, 225, 560, 83, SAMPLE_DATA, "data", 48, ink)
        text(855, 342, 655, 45, SAMPLE_EN, "english", 17, ink)
        line(855, 410, 1510, 410, "#C8CDD2")
        text(855, 446, 555, 35, "2026   /   01—08", "chart", 16, muted)
        rect(855, 520, 180, 10, accent)
        rect(1045, 520, 180, 10, "#8E9BA8")
        rect(1235, 520, 180, 10, "#CFD5DC")
    elif style_id == "03":
        rect(1010, 100, 485, 550, "#0C2333", 12)
        for gx in range(1040, 1480, 75):
            line(gx, 125, gx, 620, "#173C4B")
        for gy in range(135, 620, 75):
            line(1035, gy, 1465, gy, "#173C4B")
        ellipse(1080, 183, 280, 280, "#103240")
        ellipse(1145, 248, 150, 150, "#164956")
        rect(70, 134, 105, 5, accent)
        text(70, 168, 800, 35, kicker, "english", 15, accent, .08)
        text(70, 236, 800, 115, SAMPLE_CN, "cover", 58, ink, .025)
        text(70, 378, 870, 50, SAMPLE_SUBTITLE, "subtitle", 25, ink)
        text(70, 469, 870, 38, SAMPLE_EN, "english", 17, accent, .01)
        text(70, 522, 760, 35, SAMPLE_EN_SHORT, "english", 16, muted, .03)
        text(70, 621, 830, 35, "智能治理  AI-DRIVEN SOLUTIONS", "body", 18, ink, mixed=True)
        text(1060, 485, 390, 74, SAMPLE_DATA, "data", 42, accent, 0, "center")
        text(1060, 570, 390, 30, "2026  /  01—08", "chart", 14, ink, 0, "center")
    elif style_id == "04":
        line(70, 98, 1530, 98, accent, 2)
        text(75, 130, 1000, 38, kicker, "english", 17, accent, .08)
        text(75, 216, 850, 135, SAMPLE_CN, "cover", 65, ink, .06)
        line(77, 377, 700, 377, accent)
        text(75, 402, 900, 54, SAMPLE_SUBTITLE, "subtitle", 26, ink)
        text(75, 505, 870, 42, SAMPLE_EN, "english", 18, accent, .025)
        text(75, 572, 870, 35, "智能治理  AI-DRIVEN SOLUTIONS", "body", 18, ink, mixed=True)
        rect(1050, 135, 405, 465, "#282020")
        line(1080, 175, 1425, 175, accent)
        text(1080, 206, 330, 40, "THE NEW", "english", 16, accent, .08)
        text(1080, 263, 345, 50, "PERSPECTIVE", "english", 25, ink, .02)
        text(1080, 354, 345, 80, SAMPLE_DATA, "data", 42, ink)
        text(1080, 493, 345, 35, "2026  /  01—08", "chart", 14, muted)
        line(1080, 546, 1425, 546, accent)
    elif style_id == "05":
        ellipse(1045, 112, 430, 430, "#E1E8D9")
        ellipse(1135, 202, 250, 250, "#CDDCC5")
        rect(70, 120, 58, 5, accent)
        text(70, 164, 800, 38, kicker, "english", 15, accent, .06)
        text(70, 245, 830, 110, SAMPLE_CN, "cover", 55, ink, .04)
        text(72, 380, 920, 55, SAMPLE_SUBTITLE, "subtitle", 25, ink)
        text(72, 470, 850, 38, SAMPLE_EN, "english", 16, accent)
        text(72, 527, 820, 35, "智能治理  AI-DRIVEN SOLUTIONS", "body", 18, ink, mixed=True)
        line(72, 610, 940, 610, "#C7D0C1")
        text(1040, 262, 440, 88, SAMPLE_DATA, "data", 42, accent, 0, "center")
        text(1040, 357, 440, 35, "2026  /  01—08", "chart", 14, ink, 0, "center")
        text(72, 641, 700, 30, SAMPLE_EN_SHORT, "english", 14, muted)
    elif style_id == "06":
        rect(70, 102, 250, 508, "#E2D9CB")
        rect(104, 135, 8, 420, accent)
        text(150, 150, 140, 42, "东方", "title", 26, accent)
        text(150, 230, 140, 42, "智控", "title", 26, accent)
        text(150, 310, 140, 42, "未来", "title", 26, accent)
        text(150, 468, 130, 40, "2026", "chart", 16, accent)
        line(390, 123, 1500, 123, accent, 2)
        text(390, 162, 1000, 38, kicker, "english", 15, accent, .05)
        text(390, 242, 850, 115, SAMPLE_CN, "cover", 56, ink, .06)
        text(390, 383, 1040, 55, SAMPLE_SUBTITLE, "subtitle", 25, ink)
        text(390, 473, 1000, 35, SAMPLE_EN, "english", 17, muted)
        text(390, 540, 900, 38, "智能治理  AI-DRIVEN SOLUTIONS", "body", 18, ink, mixed=True)
        text(1110, 590, 360, 64, SAMPLE_DATA, "data", 34, accent, 0, "right")
        text(390, 635, 500, 30, "01—08  /  2026", "chart", 14, muted)
    elif style_id == "07":
        rect(70, 100, 1460, 8, accent)
        rect(1050, 125, 440, 465, accent)
        text(70, 139, 850, 38, kicker, "english", 17, accent, .06)
        text(70, 215, 900, 130, SAMPLE_CN, "cover", 64, ink, .02)
        text(70, 367, 930, 53, SAMPLE_SUBTITLE, "subtitle", 25, ink)
        text(70, 465, 900, 37, SAMPLE_EN, "english", 17, accent)
        text(70, 526, 840, 37, "智能治理  AI-DRIVEN SOLUTIONS", "body", 18, ink, mixed=True)
        text(70, 626, 840, 36, SAMPLE_EN_SHORT, "english", 16, muted, .02)
        text(1090, 163, 360, 45, "SYSTEM / 01", "english", 18, bg)
        text(1085, 255, 370, 100, SAMPLE_DATA, "data", 47, bg)
        line(1090, 390, 1450, 390, bg, 3)
        text(1090, 440, 350, 45, "2026", "data", 23, bg)
        text(1090, 510, 350, 37, SAMPLE_RANGE, "chart", 16, bg)
    else:
        rect(67, 104, 883, 510, "#FFFFFF", 35)
        rect(1010, 104, 480, 235, "#E4D9FF", 36)
        rect(1010, 360, 480, 254, "#D8CEF6", 36)
        ellipse(1245, 126, 194, 194, "#C7B4F5")
        text(105, 146, 760, 38, kicker, "english", 15, accent, .04)
        text(105, 218, 740, 112, SAMPLE_CN, "cover", 53, ink, .02)
        text(105, 350, 770, 52, SAMPLE_SUBTITLE, "subtitle", 23, ink)
        text(105, 430, 760, 37, SAMPLE_EN, "english", 16, accent)
        text(105, 505, 760, 36, "智能治理  AI-DRIVEN SOLUTIONS", "body", 18, ink, mixed=True)
        text(1045, 163, 390, 78, SAMPLE_DATA, "data", 38, accent)
        text(1045, 267, 390, 34, "2026  /  01—08", "chart", 14, ink)
        text(1045, 407, 390, 35, SAMPLE_EN_SHORT, "english", 15, accent)
        text(1045, 480, 390, 35, "2026  /  01—08", "chart", 15, ink)
        text(105, 649, 760, 30, "TYPOGRAPHY WITH PERSONALITY", "english", 13, muted, .03)
    return G, B


def _describe(record: dict[str, Any], axes: tuple[tuple[str, float], ...], axis_failure: bool = False) -> str:
    family = record.get("family") or "(unknown family)"
    subfamily = record.get("subfamily") or "Regular"
    if axes:
        axis_label = ", ".join(f"{tag}={_fmt(value)}" for tag, value in axes)
        if axis_failure:
            axis_label += " default; requested axis unavailable"
        weight = next((value for tag, value in axes if tag == "wght"), _weight(record))
        detail = f"{subfamily}; weight {_fmt(weight)}; {axis_label}"
    else:
        detail = f"{subfamily}; weight {_fmt(_weight(record))}"
    return f"{family} / {detail} / face {int(record.get('face_index') or 0)} / {record.get('path', '')}"


class _RasterFonts:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.cache: dict[tuple[Any, ...], tuple[Any, tuple[tuple[str, float], ...], bool]] = {}

    def get(self, segment: Segment, pt: float) -> tuple[Any, tuple[tuple[str, float], ...], bool]:
        if not segment.record:
            raise ValueError("缺少字体不能绘制文本")
        rec = segment.record
        size = max(1, round(pt * PX_PER_PT))
        key = (rec["path"], rec.get("face_index", 0), size, segment.axes)
        if key in self.cache:
            return self.cache[key]
        path = _path(self.root, rec)
        # Supplying a stream is critical: ImageFont.truetype(path) itself may
        # otherwise search OS font directories after a FreeType error.
        with path.open("rb") as source:
            font = ImageFont.truetype(source, size=size, index=int(rec.get("face_index") or 0))
        actual, failed = segment.axes, False
        if segment.axes:
            axes_meta = rec.get("axes") or []
            defaults = tuple((str(a["tag"]), float(a["default"])) for a in axes_meta)
            if segment.axes != defaults:
                try:
                    reported = font.get_variation_axes()
                    if len(reported) != len(segment.axes):
                        raise ValueError("FreeType axis count differs from index")
                    font.set_variation_by_axes([value for _, value in segment.axes])
                except (OSError, ValueError, TypeError, AttributeError):
                    # Reopen to guarantee a clean default instance after a
                    # failed FreeType change; never claim the target weight.
                    with path.open("rb") as source:
                        font = ImageFont.truetype(source, size=size, index=int(rec.get("face_index") or 0))
                    actual, failed = defaults, True
        result = (font, actual, failed)
        self.cache[key] = result
        return result


def _add_warnings(prepared: list[PreparedBox], style: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    seen: set[tuple[Any, ...]] = set()
    for item in prepared:
        for segment in item.segments:
            if not segment.replacement:
                continue
            if segment.record:
                key = ("fallback", item.box.role, segment.record["path"], segment.record.get("face_index", 0))
                msg = f"{item.box.role} 替代: {_describe(segment.record, segment.axes)}"
            else:
                missing = " ".join(f"U+{ord(c):04X}({c})" for c in sorted(set(segment.text)))
                key = ("missing", item.box.role, missing)
                msg = f"{item.box.role} 缺字，无法使用库内字体绘制: {missing}"
            if key not in seen:
                warnings.append(msg)
                seen.add(key)
    for warning in style.get("warnings") or []:
        # Primary style recommendations can describe additional availability
        # issues; retain them in the execution report, not as invented facts.
        line = str(warning)
        if line and line not in warnings:
            warnings.append(line)
    return warnings


def _draw_artwork(draw: Any, graphics: list[tuple[Any, ...]]) -> None:
    for shape in graphics:
        kind = shape[0]
        if kind == "line":
            _, x1, y1, x2, y2, color, width = shape
            draw.line((_px(x1), _px(y1), _px(x2), _px(y2)), fill=color, width=max(1, _px(width)))
        else:
            _, x, y, w, h, color, *rest = shape
            bounds = (_px(x), _px(y), _px(x + w), _px(y + h))
            if kind == "ellipse":
                draw.ellipse(bounds, fill=color)
            elif rest and rest[0]:
                draw.rounded_rectangle(bounds, radius=_px(rest[0]), fill=color)
            else:
                draw.rectangle(bounds, fill=color)


def _measure(font: Any, text: str, spacing: float) -> float:
    if not text:
        return 0
    width = (sum(float(font.getlength(char)) for char in text)
             if spacing else float(font.getlength(text)))
    return width + max(0, len(text) - 1) * spacing


def _draw_box(draw: Any, item: PreparedBox, fonts: _RasterFonts,
              used: dict[tuple[str, int, tuple[tuple[str, float], ...]], tuple[dict[str, Any], bool]],
              warnings: list[str]) -> None:
    box = item.box
    x, y, width, height = map(_px, (box.x, box.y, box.width, box.height))
    spacing = box.tracking * box.pt * PX_PER_PT
    rendered = []
    total = 0.0
    for segment in item.segments:
        if segment.record is None:
            advance = box.pt * PX_PER_PT * max(1, len(segment.text))
            rendered.append((segment, None, (), False, advance))
        else:
            font, actual, failed = fonts.get(segment, box.pt)
            advance = _measure(font, segment.text, spacing)
            rendered.append((segment, font, actual, failed, advance))
            key = (segment.record["path"], int(segment.record.get("face_index") or 0), actual)
            prior = used.get(key)
            used[key] = (segment.record, failed or bool(prior and prior[1]))
            if failed:
                msg = f"变量轴设置失败，使用实际默认值: {_describe(segment.record, actual, True)}"
                if msg not in warnings:
                    warnings.append(msg)
        total += advance
    if total > width + 1:
        warnings.append(f"文字宽度超出预留区域，未缩小字号: {box.text!r} ({total / SCALE:.0f}>{box.width})")
    if box.align == "center":
        x += max(0, int((width - total) / 2))
    elif box.align == "right":
        x += max(0, int(width - total))
    cursor = float(x)
    # Share a baseline across Chinese/Latin runs, positioned from actual
    # ink extents instead of using each face's inconsistent ascender metrics.
    extents = [draw.textbbox((0, 0), segment.text, font=font, anchor="ls")
               for segment, font, _, _, _ in rendered if font is not None and segment.text]
    top = min((extent[1] for extent in extents), default=0)
    bottom = max((extent[3] for extent in extents), default=height)
    baseline = y + max(0, (height - (bottom - top)) / 2) - top
    for segment, font, actual, failed, advance in rendered:
        if font is None:
            # A visible vector cross is not an invented glyph or system fallback.
            side = max(12, min(int(box.pt * PX_PER_PT * .75), height - 2))
            for _ in segment.text:
                draw.rectangle((cursor, y, cursor + side, y + side), outline=box.color, width=2)
                draw.line((cursor, y, cursor + side, y + side), fill=box.color, width=2)
                draw.line((cursor + side, y, cursor, y + side), fill=box.color, width=2)
                cursor += box.pt * PX_PER_PT
            continue
        if spacing:
            for char in segment.text:
                bbox = draw.textbbox((cursor, baseline), char, font=font, anchor="ls")
                if bbox[1] < y or bbox[3] > y + height:
                    warnings.append(f"文字高度超出预留区域，未缩小字号: {box.text!r}")
                draw.text((cursor, baseline), char, font=font, fill=box.color, anchor="ls")
                cursor += float(font.getlength(char)) + spacing
            cursor -= spacing
        else:
            bbox = draw.textbbox((cursor, baseline), segment.text, font=font, anchor="ls")
            if bbox[1] < y or bbox[3] > y + height:
                warnings.append(f"文字高度超出预留区域，未缩小字号: {box.text!r}")
            draw.text((cursor, baseline), segment.text, font=font, fill=box.color, anchor="ls")
            cursor += advance


def _raster_labels(draw: Any, root: Path, style: dict[str, Any],
                   records: list[dict[str, Any]], fonts: _RasterFonts,
                   used: dict[tuple[str, int, tuple[tuple[str, float], ...]], tuple[dict[str, Any], bool]],
                   warnings: list[str], prepared: list[PreparedBox]) -> None:
    # Labels are themselves rendered only with a fully covering indexed font.
    # Their strings describe the actual specimen fonts, never a fabricated face.
    fallback_keys = {(s.record["path"], int(s.record.get("face_index") or 0))
                     for item in prepared for s in item.segments if s.replacement and s.record}
    # The recommender also marks library-internal replacements relative to the
    # intended design, even when no additional coverage fallback was needed.
    fallback_keys.update((spec["font"]["path"], int(spec["font"].get("face_index") or 0))
                         for spec in style.get("roles", {}).values()
                         if spec.get("font") and any("原设计意向" in str(note) or "其他方案" in str(note)
                                                     for note in spec.get("notes", [])))
    lines = []
    for i, (key, (rec, failed)) in enumerate(used.items()):
        marker = "替代 " if key[:2] in fallback_keys else ""
        lines.append(f"{i + 1:02d}. {marker}{_describe(rec, key[2], failed)}")
    lines.extend(warning for warning in warnings if "无法使用库内字体绘制" in warning)
    x, y = _px(70), _px(695)
    column_width, gap, line_gap = _px(710), _px(30), _px(17)
    rows_per_column = 11
    color = STYLES[str(style["style"])][4]
    position = 0
    truncated = False
    for label in lines:
        segments = _resolve_text(label, "caption", style, records)
        for segment in segments:
            if not segment.record:
                warnings.append("来源标签缺字，完整来源见命令行报告: " + label)
                truncated = True
                continue
            font, _, _ = fonts.get(segment, 7)
            for char in segment.text:
                advance = float(font.getlength(char))
                if position + advance > column_width:
                    position = 0
                    y += line_gap
                row = (y - _px(695)) // line_gap
                if row >= rows_per_column:
                    x += column_width + gap
                    y = _px(695)
                    position = 0
                if x + column_width > _px(1530):
                    truncated = True
                    break
                draw.text((x + position, y), char, font=font, fill=color, anchor="lt")
                position += advance
            if truncated:
                break
        if truncated:
            break
        position = 0
        y += line_gap
        if (y - _px(695)) // line_gap >= rows_per_column:
            x += column_width + gap
            y = _px(695)
    if truncated:
        warnings.append("页面来源标签空间不足或缺字；完整来源见命令行报告")
    # A persistent visible marker accompanies any missing sample character.
    if any("无法使用库内字体绘制" in warning for warning in warnings):
        notice = "缺字：完整字符及原因见命令行"
        segments = _resolve_text(notice, "caption", style, records)
        if all(segment.record for segment in segments):
            cursor = _px(70)
            for segment in segments:
                font, _, _ = fonts.get(segment, 8)
                draw.text((cursor, _px(885)), segment.text, font=font, fill=color, anchor="lt")
                cursor += font.getlength(segment.text)


def _render_page(root: Path, style: dict[str, Any], records: list[dict[str, Any]]) -> tuple[Image.Image, list[str]]:
    style_id = str(style["style"])
    graphics, boxes = _artwork(style_id)
    prepared = _prepare_boxes(boxes, style, records)
    warnings = _add_warnings(prepared, style)
    image = Image.new("RGB", (WIDTH, HEIGHT), STYLES[style_id][1])
    draw = ImageDraw.Draw(image)
    fonts = _RasterFonts(root)
    used: dict[tuple[str, int, tuple[tuple[str, float], ...]], tuple[dict[str, Any], bool]] = {}
    _draw_artwork(draw, graphics)
    for item in prepared:
        _draw_box(draw, item, fonts, used, warnings)
    for key, (record, failed) in used.items():
        installed = (record.get("installed") or {}).get("status", "未确认")
        print(f"  USED: {_describe(record, key[2], failed)} / 安装 {installed} / 授权待核实")
    _raster_labels(draw, root, style, records, fonts, used, warnings, prepared)
    return image, warnings


def _pptx_graphics(slide: Any, graphics: list[tuple[Any, ...]], px_to_emu: float) -> None:
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Emu

    def E(v: float) -> Any:
        return Emu(round(v * px_to_emu))

    for shape in graphics:
        kind = shape[0]
        if kind == "line":
            _, x1, y1, x2, y2, color, width = shape
            # Thin rectangles avoid connector endpoints and remain editable.
            if x1 == x2:
                left, top, w, h = x1, min(y1, y2), max(width, 1), abs(y2 - y1)
            elif y1 == y2:
                left, top, w, h = min(x1, x2), y1, abs(x2 - x1), max(width, 1)
            else:
                continue
            item = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, E(left), E(top), E(w), E(h))
        else:
            _, x, y, w, h, color, *rest = shape
            shape_type = MSO_SHAPE.OVAL if kind == "ellipse" else (
                MSO_SHAPE.ROUNDED_RECTANGLE if rest and rest[0] else MSO_SHAPE.RECTANGLE)
            item = slide.shapes.add_shape(shape_type, E(x), E(y), E(w), E(h))
        item.fill.solid()
        item.fill.fore_color.rgb = RGBColor.from_string(color.lstrip("#"))
        item.line.fill.background()


def _set_east_asian_font(run: Any, family: str) -> None:
    """python-pptx's .name sets a:latin; PowerPoint needs a:ea for CJK."""
    from pptx.oxml.ns import qn
    from pptx.oxml.xmlchemy import OxmlElement

    props = run._r.get_or_add_rPr()
    ea = props.find(qn("a:ea"))
    if ea is None:
        ea = OxmlElement("a:ea")
        # CT_TextCharacterProperties ordering is latin, ea, cs, sym, links.
        following = next((child for child in props if child.tag in {
            qn("a:cs"), qn("a:sym"), qn("a:hlinkClick"), qn("a:hlinkMouseOver"),
            qn("a:rtl"), qn("a:extLst")}), None)
        if following is not None:
            following.addprevious(ea)
        else:
            props.append(ea)
    ea.set("typeface", family)


def _pptx_box(slide: Any, item: PreparedBox, px_to_emu: float) -> None:
    from pptx.dml.color import RGBColor
    from pptx.enum.text import MSO_AUTO_SIZE, MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Pt

    box = item.box
    shape = slide.shapes.add_textbox(*(Emu(round(v * px_to_emu)) for v in (box.x, box.y, box.width, box.height)))
    frame = shape.text_frame
    frame.clear()
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.word_wrap = False
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.vertical_anchor = MSO_ANCHOR.TOP
    paragraph = frame.paragraphs[0]
    paragraph.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[box.align]
    for segment in item.segments:
        if not segment.record:
            # Preserve original Unicode in an editable run even when coverage
            # is absent. Mark it as missing; PowerPoint may display fallback.
            run = paragraph.add_run()
            run.text = segment.text
            run.font.size = Pt(box.pt)
            run.font.color.rgb = RGBColor.from_string("FF4444")
            continue
        record = segment.record
        run = paragraph.add_run()
        run.text = segment.text
        names = record.get("names") or {}
        # PowerPoint's typeface selector understands legacy family names;
        # unlike typographic-family names these may retain static weight names.
        family = str(names.get("family") or record.get("family") or "")
        if not family:
            raise ValueError(f"索引缺少字体家族名: {record.get('path')}")
        run.font.name = family
        _set_east_asian_font(run, family)
        run.font.size = Pt(box.pt)
        # PowerPoint has a Boolean bold flag, not an exact numeric weight.
        # The slide reports this limitation, including for variable fonts.
        ppt_family = family.casefold()
        full = str(names.get("full") or "").casefold()
        # For a family-scoped static Bold face, request real Bold; for an
        # individually named Bold family do not ask PowerPoint to synthesize
        # a second boldening. Variable weight remains application-dependent.
        run.font.bold = not segment.axes and _weight(record) >= 700 and ppt_family != full
        run.font.color.rgb = RGBColor.from_string(box.color.lstrip("#"))


def _pptx_page(root: Path, style: dict[str, Any], records: list[dict[str, Any]], output: Path) -> list[str]:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches

    style_id = str(style["style"])
    graphics, boxes = _artwork(style_id)
    prepared = _prepare_boxes(boxes, style, records)
    warnings = _add_warnings(prepared, style)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333333), Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = RGBColor.from_string(STYLES[style_id][1].lstrip("#"))
    ratio = prs.slide_width / 1600
    _pptx_graphics(slide, graphics, ratio)
    for item in prepared:
        _pptx_box(slide, item, ratio)

    used: dict[tuple[str, int, tuple[tuple[str, float], ...]], dict[str, Any]] = {}
    for item in prepared:
        for segment in item.segments:
            if not segment.record:
                warnings.append(f"PPTX 将保留缺字原文 {segment.text!r}；PowerPoint 可能自行回退。")
                continue
            _path(root, segment.record)
            used[(segment.record["path"], int(segment.record.get("face_index") or 0), segment.axes)] = segment.record
    for key, record in used.items():
        # The face and requested axes are provenance, not proof of PPT display.
        installed = (record.get("installed") or {}).get("status", "未确认")
        print(f"  REQUESTED: {_describe(record, key[2])} / 安装 {installed} / 授权待核实")
    # Keep provenance as editable text; source lines are also printed in full.
    lines = [f"{i + 1:02d}. 请求 {_describe(rec, key[2])}"
             for i, (key, rec) in enumerate(used.items())]
    # Two narrow editable columns keep source paths readable on the slide.
    max_lines = 10
    if len(lines) > max_lines:
        warnings.append("PPTX 来源标签空间不足；完整来源见命令行报告")
    for i, line in enumerate(lines[:max_lines]):
        segments = _resolve_text(line, "caption", style, records)
        x, y = 70 + (i // 5) * 740, 697 + (i % 5) * 30
        item = PreparedBox(TextBox(x, y, 700, 29, line, "caption", 6.5, STYLES[style_id][4]), segments)
        if any(not segment.record for segment in segments):
            warnings.append("PPTX 来源标签缺字，完整来源见命令行报告: " + line)
        _pptx_box(slide, item, ratio)
    notice = "字体未嵌入，须自行确认安装；变量轴及字面由 PowerPoint 决定"
    notice_box = PreparedBox(TextBox(70, 856, 1460, 25, notice, "caption", 8, STYLES[style_id][4]),
                             _resolve_text(notice, "caption", style, records))
    _pptx_box(slide, notice_box, ratio)
    warnings.append("PPTX 不嵌入或安装字体，PowerPoint 实际显示和回退未验证；目标设备须自行确认字体可用。")
    warnings.append("PPTX 仅表达字体家族、字号、布尔粗体及颜色；字间距、精确字重/字面与变量轴不受控。")
    with output.open("xb") as stream:
        prs.save(stream)
    return warnings


def _print_warnings(style_id: str, warnings: list[str]) -> None:
    seen = set()
    for warning in warnings:
        if warning not in seen:
            print(f"  [{style_id}] {warning}", file=sys.stderr)
            seen.add(warning)


def _check_output(output: Path, root: Path) -> None:
    if output.absolute() == (Path(__file__).resolve().parent.parent / "references" / "local-font-index.json").absolute():
        raise ValueError("输出不得覆盖字体索引")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"输出文件已存在，拒绝覆盖: {output}")
    parent = output.parent.resolve(strict=True)
    try:
        parent.relative_to(root.resolve(strict=True))
    except ValueError:
        pass
    else:
        raise ValueError("字体根目录只读，输出不能位于字体目录中")
    if not parent.is_dir():
        raise ValueError(f"输出父目录不存在: {parent}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="使用受限字体库渲染八种 PPT 字体样张")
    parser.add_argument("--output", required=True, type=Path, help="输出文件；已存在时拒绝覆盖")
    parser.add_argument("--root", type=Path, help="精选字体根目录")
    parser.add_argument("--style", choices=sorted(STYLES), help="只生成指定风格（01–08）")
    parser.add_argument("--format", choices=("pdf", "png", "pptx"), default="pdf")
    args = parser.parse_args(argv)
    try:
        if args.output.suffix.lower() != "." + args.format:
            raise ValueError(f"输出扩展名必须为 .{args.format}")
        root, records = load_index(args.root)
        style_ids = [args.style] if args.style else (["01"] if args.format == "pptx" else list(STYLES))
        output_paths = [args.output]
        if args.format == "png" and len(style_ids) > 1:
            output_paths.extend(args.output.with_name(f"{args.output.stem}-{style_id}.png")
                                for style_id in style_ids[1:])
        for output in output_paths:
            _check_output(output, root)
        # Reuse the already loaded index: coverage lists can be large.
        candidates = recommend_styles(root=root, records=records)
        by_style = {str(candidate["style"]): candidate for candidate in candidates}
        missing = [style_id for style_id in style_ids if style_id not in by_style]
        if missing:
            raise ValueError("推荐模块未返回风格: " + ", ".join(missing))
        if args.format == "pptx":
            style = by_style[style_ids[0]]
            print(f"{style_ids[0]} / {STYLES[style_ids[0]][0]}")
            warnings = _pptx_page(root, style, records, args.output)
            _print_warnings(style_ids[0], warnings)
        else:
            pages = []
            for style_id in style_ids:
                print(f"{style_id} / {STYLES[style_id][0]}")
                page, warnings = _render_page(root, by_style[style_id], records)
                pages.append(page)
                _print_warnings(style_id, warnings)
            if args.format == "pdf":
                with args.output.open("xb") as stream:
                    pages[0].save(stream, "PDF", resolution=144.0,
                                  save_all=True, append_images=pages[1:])
            else:
                for page, output in zip(pages, output_paths):
                    with output.open("xb") as stream:
                        page.save(stream, "PNG", dpi=(144, 144))
                    if output != args.output:
                        print(f"已生成: {output}")
            for page in pages:
                page.close()
        print(f"已生成: {args.output}")
        print("预览仅供本机使用；公开分发前需核实所用字体及衍生物授权。")
        return 0
    except (OSError, ValueError, KeyError, ImportError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
