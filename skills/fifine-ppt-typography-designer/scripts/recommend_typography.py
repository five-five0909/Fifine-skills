#!/usr/bin/env python3
"""Recommend traceable PPT typography using only the curated font index.

The font record in each role is the original index record.  The selected
variable-axis coordinates, when applicable, are in the role's axis_values;
a consumer must actually apply them before claiming that weight was rendered.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
import json
from pathlib import Path, PureWindowsPath
import re
import sys
from typing import Any

if __package__:
    from .font_index import load_index, resolve_root
else:
    from font_index import load_index, resolve_root


# The phrases are design intents, not evidence that any font file exists.
STYLES: dict[str, dict[str, Any]] = {
    "01": {
        "title": "典藏黑金", "keywords": ("黑金", "高端", "典藏", "奢华", "投资路演", "商务路演", "luxury"),
        "description": "黑金科技、高端路演；衬线标题、无衬线正文与克制留白。",
        "title_families": ("serif", "sans"), "body_families": ("sans", "misans", "alibaba"),
        "english_families": ("serif", "sans"), "data_families": ("serif", "sans"),
        "palette": {"background": "#101016", "text": "#F5EFE2", "accent": "#D5B46A", "muted": "#C9C2B3"},
        "alternatives": ("03", "04", "02", "06", "05", "08", "07"),
    },
    "02": {
        "title": "瑞士秩序", "keywords": ("高密度", "信息密度", "密集", "数据汇报", "数据分析", "图表", "报表", "财务", "咨询", "瑞士", "理性", "dashboard", "data"),
        "description": "瑞士网格与理性层级，适合密集图表和研究汇报。",
        "title_families": ("sans", "misans", "alibaba"), "body_families": ("misans", "sans", "alibaba"),
        "english_families": ("misans", "sans", "alibaba"), "data_families": ("misans", "sans", "alibaba"),
        "palette": {"background": "#F4F5F7", "text": "#20252C", "accent": "#20252C", "muted": "#50565F"},
        "alternatives": ("03", "08", "01", "04", "05", "06", "07"),
    },
    "03": {
        "title": "深海未来", "keywords": ("深海", "科技", "竞赛", "人工智能", "智能", "数字化", "创新", "创业", "技术路演", "ai", "technology", "future"),
        "description": "深色科技底与亮青重点，适合竞赛、创新与产品路演。",
        "title_families": ("sans", "misans", "alibaba"), "body_families": ("alibaba", "sans", "misans"),
        "english_families": ("space", "ibm", "sans", "alibaba"), "data_families": ("space", "ibm", "sans", "alibaba"),
        "palette": {"background": "#081827", "text": "#EAF8FC", "accent": "#3BE1E8", "muted": "#A3C3D1"},
        "alternatives": ("02", "01", "08", "07", "04", "05", "06"),
    },
    "04": {
        "title": "杂志新奢", "keywords": ("杂志", "时尚", "编辑", "品牌故事", "精品", "高级感", "新奢", "magazine", "editorial", "fashion"),
        "description": "编辑式大标题与细致留白，适合品牌故事和精品发布。",
        "title_families": ("serif", "sans"), "body_families": ("serif", "sans", "kai"),
        "english_families": ("serif", "sans"), "data_families": ("serif", "sans"),
        "palette": {"background": "#171315", "text": "#F7EFE6", "accent": "#C9A36A", "muted": "#D7C5B8"},
        "alternatives": ("06", "01", "05", "02", "08", "03", "07"),
    },
    "05": {
        "title": "自然人文", "keywords": ("自然", "人文", "公益", "生态", "环保", "森林", "生活方式", "乡村", "自然教育", "nature", "humanities"),
        "description": "自然色调、舒缓留白与温和字形，适合人文和生态叙事。",
        "title_families": ("serif", "kai", "sans"), "body_families": ("kai", "serif", "sans"),
        "english_families": ("serif", "kai", "sans"), "data_families": ("serif", "kai", "sans"),
        "palette": {"background": "#F4F1E9", "text": "#263326", "accent": "#657E58", "muted": "#4B5A49"},
        "alternatives": ("06", "04", "08", "02", "01", "03", "07"),
    },
    "06": {
        "title": "当代东方", "keywords": ("东方", "国风", "中国文化", "传统文化", "展览", "文化", "书法", "博物馆", "oriental", "heritage"),
        "description": "具有笔意的标题与平稳宋体正文相对照，适合文化展示。",
        "title_families": ("kai", "serif", "sans"), "body_families": ("serif", "sans", "kai"),
        "english_families": ("serif", "sans", "kai"), "data_families": ("serif", "sans", "kai"),
        "palette": {"background": "#EFE9DD", "text": "#342B26", "accent": "#A04432", "muted": "#665A52"},
        "alternatives": ("05", "04", "01", "08", "02", "03", "07"),
    },
    "07": {
        "title": "先锋海报", "keywords": ("先锋", "海报", "潮流", "活动发布", "活动", "发布会", "展演", "festival", "poster"),
        "description": "海报式大字和强反差用于短标题；正文保持安静清晰。",
        "title_families": ("youshe", "sans", "misans"), "body_families": ("sans", "misans", "alibaba"),
        "english_families": ("youshe", "sans", "misans"), "data_families": ("youshe", "sans", "misans"),
        "palette": {"background": "#131313", "text": "#F9F9F5", "accent": "#F8DE39", "muted": "#D1D1CA"},
        "alternatives": ("03", "08", "02", "01", "04", "05", "06"),
    },
    "08": {
        "title": "圆润创意", "keywords": ("圆润", "亲和", "创意", "教育", "儿童", "校园", "教学", "轻产品", "用户体验", "education", "playful"),
        "description": "圆润、轻快且有序，适合教育内容和亲和型产品。",
        "title_families": ("misans", "alibaba", "sans"), "body_families": ("alibaba", "misans", "sans"),
        "english_families": ("nunito", "quicksand", "misans", "alibaba"), "data_families": ("nunito", "quicksand", "misans", "alibaba"),
        "palette": {"background": "#F4EFFF", "text": "#2F2650", "accent": "#7656CB", "muted": "#5C5270"},
        "alternatives": ("02", "03", "05", "07", "06", "04", "01"),
    },
}

FAMILY_ALIASES: dict[str, tuple[str, ...]] = {
    "serif": ("sourcehanserif", "思源宋体", "思源宋體"),
    "sans": ("sourcehansans", "思源黑体", "思源黑體"),
    "misans": ("misans",),
    "alibaba": ("alibabapuhuiti", "阿里巴巴普惠体", "阿里巴巴普惠體"),
    "kai": ("xiawuwenkai", "lxgwwenkai", "霞鹜文楷", "霞鶩文楷"),
    "youshe": ("youshebiaotihei", "优设标题黑", "優設標題黑"),
    "space": ("spacegrotesk",), "ibm": ("ibmplexmono",),
    "nunito": ("nunito",), "quicksand": ("quicksand",),
}
FAMILY_LABELS = {
    "serif": "思源宋体", "sans": "思源黑体", "misans": "MiSans", "alibaba": "阿里巴巴普惠体",
    "kai": "霞鹜文楷", "youshe": "优设标题黑", "space": "Space Grotesk", "ibm": "IBM Plex Mono",
    "nunito": "Nunito", "quicksand": "Quicksand",
}
ROLE_LABELS = {
    "cover": "封面标题", "title": "页面主标题", "subtitle": "模块小标题", "body": "正文",
    "data": "核心数据", "english": "英文标题", "chart": "图表标签", "caption": "图注与来源",
}
ROLE_WEIGHTS = {"cover": 700, "title": 700, "subtitle": 600, "body": 400,
                "data": 700, "english": 700, "chart": 400, "caption": 400}
DEFAULT_ZH = "智控卫士矿山重金属污染智能治理系统"
DEFAULT_EN = "INTELLIGENT ENVIRONMENTAL CONTROL AI-DRIVEN SOLUTIONS"
DEFAULT_DATA = "2026 / 97.98% / 01—08"
DENSE_WORDS = ("高密度", "信息密度", "密集", "大量数据", "数据表", "高信息量", "dense", "high-density")


def _normalized(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


def _name_values(font: dict[str, Any]) -> list[str]:
    names = font.get("names") or {}
    return [str(value) for value in (
        font.get("family", ""), names.get("family", ""), names.get("typographic_family", ""),
        names.get("full", ""), names.get("postscript", ""), *(names.get("aliases") or []),
    ) if value]


def _family_code(font: dict[str, Any]) -> str:
    values = [_normalized(value) for value in _name_values(font)]
    for code, aliases in FAMILY_ALIASES.items():
        if any(_normalized(alias) in name for alias in aliases for name in values):
            return code
    return ""


def _region_rank(font: dict[str, Any], code: str) -> int:
    if code not in ("serif", "sans", "kai"):
        return 0
    names = [_normalized(value) for value in _name_values(font)]
    if any(re.search(r"(?:sourcehan(?:serif|sans)|思源(?:宋体|宋體|黑体|黑體))cn", n) for n in names):
        return 0
    if any(re.search(r"(?:sourcehan(?:serif|sans)|思源(?:宋体|宋體|黑体|黑體)|xiawuwenkai|lxgwwenkai|霞鹜文楷|霞鶩文楷)(?:tc|hk|jp|kr)", n) for n in names):
        return 2
    return 1


def _italic(font: dict[str, Any]) -> bool:
    value = " ".join([str(font.get("subfamily", "")), *_name_values(font)]).casefold()
    return any(word in value for word in ("italic", "oblique", "斜体", "斜體"))


def _weight(font: dict[str, Any], target: int) -> tuple[int | float, dict[str, float | int], str]:
    for axis in font.get("axes") or []:
        if axis.get("tag") == "wght":
            low, high = float(axis["min"]), float(axis["max"])
            selected = max(low, min(high, float(target)))
            selected = int(selected) if selected.is_integer() else selected
            note = f"变量 wght 目标 {selected}（范围 {low:g}–{high:g}）；须由渲染器实际应用，PPT 不保证精确轴值。"
            if selected != target:
                note += f" 设计目标 {target} 不在所选面的轴范围内。"
            return selected, {"wght": selected}, note
    actual = int(font.get("weight") or 400)
    note = f"静态面实际 OS/2 字重 {actual}；设计目标 {target}。"
    if actual != target:
        note += " 该角色选择的面没有精确目标字重，已报告实际值，未假定合成字重。"
    return actual, {}, note


def _is_cjk(char: str) -> bool:
    point = ord(char)
    return (0x2E80 <= point <= 0x9FFF or 0xAC00 <= point <= 0xD7AF
            or 0xF900 <= point <= 0xFAFF or 0x20000 <= point <= 0x3134F
            or 0xFF01 <= point <= 0xFF60 or 0x3000 <= point <= 0x303F)


def _required(brief: str) -> dict[str, tuple[int, ...]]:
    # Slide text may be quoted or embedded in the brief. Classify every visible
    # character into a Chinese or Latin/numeric run, then test actual cmap.
    # Only line-breaking controls are omitted; sample spaces remain checked.
    cjk = DEFAULT_ZH + "".join(c for c in brief if _is_cjk(c))
    latin = DEFAULT_EN + "".join(c for c in brief if c.isascii() and c.isprintable() and not c.isspace())
    data = DEFAULT_DATA + "".join(c for c in brief if c.isascii() and (c.isdigit() or c in ".,%/-+"))
    latin += "".join(c for c in brief if not c.isascii() and not _is_cjk(c)
                     and (c.isalpha() or c.isnumeric() or c.isidentifier()))
    cjk += "".join(c for c in brief if not c.isascii() and not _is_cjk(c)
                   and not c.isspace() and not (c.isalpha() or c.isnumeric() or c.isidentifier()))
    return {
        "zh": tuple(sorted({ord(c) for c in cjk if c not in "\r\n\t"})),
        "en": tuple(sorted({ord(c) for c in latin if c not in "\r\n\t"})),
        "digits": tuple(sorted({ord(c) for c in data if c not in "\r\n\t"})),
    }


class _Context:
    def __init__(self, root: Path, records: list[dict[str, Any]]):
        self.root = Path(root).resolve()
        self.records: list[dict[str, Any]] = []
        self.codes: dict[int, str] = {}
        self.coverage_cache: dict[tuple[Any, ...], tuple[int, ...]] = {}
        self.stale = 0
        self.stale_paths: list[str] = []
        self.rejected = 0
        self.selection_cache: dict[tuple[Any, ...], tuple[dict[str, Any] | None, list[str]]] = {}
        for font in records:
            raw = font.get("path")
            if not isinstance(raw, str) or not raw or "\\" in raw:
                self.rejected += 1
                continue
            path = Path(raw)
            winpath = PureWindowsPath(raw)
            if path.is_absolute() or winpath.drive or ".." in path.parts:
                self.rejected += 1
                continue
            try:
                resolved = (self.root / path).resolve(strict=True)
                if self.root not in resolved.parents or not resolved.is_file():
                    self.rejected += 1
                    continue
                stat = resolved.stat()
            except (OSError, RuntimeError, ValueError):
                self.stale += 1
                continue
            if ((font.get("size") is not None and stat.st_size != font["size"])
                    or (font.get("mtime_ns") is not None and stat.st_mtime_ns != font["mtime_ns"])):
                self.stale += 1
                continue
            self.records.append(font)
            self.codes[id(font)] = _family_code(font)

    def missing(self, font: dict[str, Any], required: tuple[int, ...]) -> tuple[int, ...]:
        key = (font.get("sha256") or font.get("path"), font.get("face_index", 0), required)
        if key not in self.coverage_cache:
            coverage = font.get("coverage") or []  # sorted/unique by the index contract
            missing = []
            for point in required:
                position = bisect_left(coverage, point)
                if position == len(coverage) or coverage[position] != point:
                    missing.append(point)
            self.coverage_cache[key] = tuple(missing)
        return self.coverage_cache[key]


def _local(font: dict[str, Any], style: str) -> bool:
    return Path(font["path"]).parts[0].startswith(style + "_")


def _select(context: _Context, style: str, role: str, preferences: tuple[str, ...],
            required: tuple[int, ...], script: str) -> tuple[dict[str, Any] | None, list[str]]:
    target = ROLE_WEIGHTS[role]
    cache_key = (style, target, role in ("body", "chart", "caption"), preferences, required, script)
    if cache_key in context.selection_cache:
        return context.selection_cache[cache_key]
    choices = []
    for font in context.records:
        code = context.codes[id(font)]
        if role in ("body", "chart", "caption") and code == "youshe":
            continue  # display face is not a long-text fallback
        # An advertised language flag is only an index sample. Actual cmap
        # membership decides whether this exact script is usable.
        if context.missing(font, required):
            continue
        actual_weight, axis_values, weight_note = _weight(font, target)
        distance = abs(actual_weight - target)
        # Preserve local title identity even when its real weight differs;
        # body text may use a more readable regular face from another scheme.
        bad_weight = role in ("body", "chart", "caption") and distance > 200
        preference_rank = preferences.index(code) if code in preferences else len(preferences)
        choices.append(((bad_weight, _italic(font), not _local(font, style), preference_rank,
                         _region_rank(font, code), distance, font["path"], font.get("face_index", 0)),
                        font, actual_weight, axis_values, weight_note, code))
    if not choices:
        eligible = [font for font in context.records
                    if not (role in ("body", "chart", "caption") and context.codes[id(font)] == "youshe")]
        if eligible:
            closest = min(eligible, key=lambda font: len(context.missing(font, required)))
            missing = context.missing(closest, required)
            detail = " ".join(f"{chr(point)}(U+{point:04X})" for point in missing)
            note = f"最接近的 {closest.get('family', '')}（{closest['path']}，face {closest.get('face_index', 0)}）仍缺：{detail}。"
        else:
            note = "没有可供该角色使用的候选字体面。"
        return None, [f"{ROLE_LABELS[role]}：受限库没有覆盖全部检查字符的可用字体面；保持缺失，不调用系统回退。{note}"]
    _, font, actual_weight, axis_values, weight_note, code = min(choices, key=lambda item: item[0])
    notes = []
    if code != preferences[0]:
        original = FAMILY_LABELS.get(preferences[0], preferences[0])
        replacement = font.get("family") or "未命名家族"
        notes.append(f"原设计意向 {original}，当前按覆盖、字重、非斜体和本方案优先规则选择 {replacement}；造型和字面可能不同。")
    if not _local(font, style):
        notes.append("按覆盖、字重和非斜体优先规则选用受限库其他方案或 09 的文件，而非本方案目录文件。")
    if _region_rank(font, code) == 2:
        notes.append("使用非 CN 地区面；地区字形与简体 CN 可能不同。")
    if _italic(font):
        notes.append("按覆盖和可读字重排序选中斜体面；实际排版请复核。")
    result = ({"font": font, "weight": actual_weight, "axis_values": axis_values,
               "weight_note": weight_note}, notes)
    context.selection_cache[cache_key] = result
    return result


def _style_match(brief: str, code: str) -> tuple[int, list[str]]:
    folded = brief.casefold()
    found = [keyword for keyword in STYLES[code]["keywords"]
             if (re.search(r"(?<![a-z0-9])" + re.escape(keyword.casefold()) + r"(?![a-z0-9])", folded)
                 if keyword.isascii() else keyword.casefold() in folded)]
    # Longer and more specific phrases outweigh an incidental generic word.
    value = sum(min(len(keyword), 6) for keyword in found)
    if STYLES[code]["title"] in brief:
        value += 15
        found.append(STYLES[code]["title"])
    if re.search(rf"(?:风格|方案|style)\s*[:：#]?\s*{code}(?!\d)", folded) or brief.strip() == code:
        value += 20
        found.append(f"指定 {code}")
    return value, found


def _brief_observations(context: _Context, brief: str) -> list[str]:
    folded = _normalized(brief)
    observations = []
    for code, label in FAMILY_LABELS.items():
        if not any(_normalized(alias) in folded for alias in FAMILY_ALIASES[code]):
            continue
        matches = [font for font in context.records if context.codes[id(font)] == code]
        if matches:
            font = min(matches, key=lambda f: (_italic(f), f["path"], f.get("face_index", 0)))
            observations.append(f"现场可用索引中找到 {label}：{font['path']}，face {font.get('face_index', 0)}；如原先认为库内没有，以该实际文件为准，安装和授权需另核实。")
        else:
            observations.append(f"当前有效索引中未找到 {label} 的现存匹配面；请先刷新索引后再判断，安装状态不可由此推断。")
    return observations


def _candidate(context: _Context, style: str, brief: str, required: dict[str, tuple[int, ...]],
               observations: list[str]) -> dict[str, Any]:
    config = STYLES[style]
    dense = any(word in brief.casefold() for word in DENSE_WORDS)
    sizes = ({"cover": 44, "title": 32, "subtitle": 22, "body": 18, "data": 36,
              "english": 24, "chart": 14, "caption": 12} if dense else
             {"cover": 52, "title": 36, "subtitle": 24, "body": 20, "data": 48,
              "english": 30, "chart": 16, "caption": 14})
    palette = config["palette"].copy()
    roles: dict[str, Any] = {}
    warnings: list[str] = []
    for role in ROLE_LABELS:
        script = "en" if role == "english" else "digits" if role == "data" else "zh"
        family_key = ("english_families" if role == "english" else "data_families" if role == "data"
                      else "body_families" if role in ("body", "chart", "caption") else "title_families")
        choice, notes = _select(context, style, role, config[family_key], required[script], script)
        warnings.extend(notes)
        color = palette["accent"] if role in ("cover", "data") else palette["muted"] if role == "caption" else palette["text"]
        common = {"size": sizes[role], "spacing": 0.03 if role == "cover" else 0.06 if role == "english" else 0.0,
                  "color": color, "line_height": 1.3 if role == "body" else None,
                  "sample": "".join(chr(point) for point in required[script]), "sample_script": script,
                  "notes": notes}
        if choice is None:
            choice = {"font": None, "weight": None, "axis_values": {}, "weight_note": "缺少支持样本的字体面。"}
        roles[role] = {**choice, **common}

    missing = [ROLE_LABELS[role] for role, value in roles.items() if value["font"] is None]
    fonts = [value["font"] for value in roles.values() if value["font"] is not None]
    family_count = len({(context.codes[id(font)], _region_rank(font, context.codes[id(font)]))
                        if context.codes[id(font)] in ("serif", "sans", "kai")
                        else (context.codes[id(font)] or str(font.get("family", "")), 0)
                        for font in fonts})
    confirmed = sum((font.get("installed") or {}).get("status") == "已确认" for font in fonts)
    licenses_with_files = sum(bool((font.get("license") or {}).get("files")) for font in fonts)
    variable_count = sum(bool(value["axis_values"]) for value in roles.values())
    match, matched_words = _style_match(brief, style)
    available = len(roles) - len(missing)
    score = {
        "主题契合": {"score": min(25, 14 + match), "max": 25,
                     "basis": ("关键词：" + "、".join(matched_words)) if matched_words else "默认或对照风格；按人工主题规则估计，非视觉测量。"},
        "层级可读": {"score": round(20 * available / len(roles)), "max": 20,
                     "basis": f"{available}/8 角色有覆盖检查字符的面，字号采用 16:9 人工层级；未实测投影。"},
        "覆盖与可用": {"score": round(20 * available / len(roles)), "max": 20,
                       "basis": f"现存且大小/修改时间与索引一致的具体面覆盖所列字符：{available}/8；不代表完整语言覆盖。"},
        "搭配协调": {"score": 15 if 1 <= family_count <= 3 else 10 if family_count else 0, "max": 15,
                     "basis": f"设计规则：当前 {family_count} 个家族，优先 2–3 家族且展示体不用于长文；未测量字形协调。"},
        "实施便利": {"score": max(0, round(10 * confirmed / len(roles)) - (2 if variable_count else 0)), "max": 10,
                     "basis": f"{confirmed}/8 角色安装状态已确认，{variable_count}/8 使用变量轴；未确认并非未安装，目标软件轴兼容性待核实。"},
        "授权风险": {"score": round(5 * licenses_with_files / len(roles)), "max": 10,
                     "basis": f"{licenses_with_files}/8 角色发现邻近许可材料；仅为线索，条款和用途均待核实，分数不代表商业授权。"},
    }
    if context.stale:
        warnings.append(f"跳过 {context.stale} 个不存在或大小/时间戳与索引不一致的面；请重新 build，时间戳不变的替换需 --force。")
    if context.stale_paths:
        warnings.append("以下索引字体缺失或已更改，已跳过；请重新 build：" + "、".join(context.stale_paths))
    if context.rejected:
        warnings.append(f"跳过 {context.rejected} 个不安全或越出受限根的索引路径。")
    warnings.extend(observations)
    warnings.append("仅按列出的角色检查字符检查 cmap；实际文案须逐段重检，cmap 不保证塑形、地区字形或软件显示。")
    warnings.append("文件大小和时间戳未变化不证明内容未替换；怀疑替换时使用 build --force 重算哈希。")
    warnings.append("安装状态未确认不等于未安装；许可关联、条款及具体用途均需核实，不自动认定可商用。")
    warnings.append("可变字体仅给出推荐轴值，需渲染器实际应用；PowerPoint 不保证轴值或字间距。")
    if family_count > 3:
        warnings.append(f"当前组合涉及 {family_count} 个家族，超过 2–3 家族优先原则；可减少角色差异。")
    density_note = ("高密度：优先减少层级、合并标签、拆图或分页；正文 18 pt、图表标签 14 pt，不靠继续缩字解决溢出。"
                    if dense else "常规密度：保留层级与留白，投影正文尽量不低于 18 pt；需要时拆页。")
    return {
        "style": style, "title": config["title"], "description": config["description"],
        "roles": roles, "palette": palette, "missing": missing, "warnings": list(dict.fromkeys(warnings)),
        "use": config["description"],
        "mixing": "按中英文和数字分 run 指定各自角色字体；对实际文本逐字校验并复核基线、字距及标点。",
        "visual_relationship": "封面与数据以重点色建立焦点，主标题、正文、图表及图注用字号、字重和留白组织层级。",
        "density": density_note, "family_count": family_count, "scores": score,
        "score_total": sum(item["score"] for item in score.values()),
        "score_note": "启发式设计规则与库内证据，不是视觉、软件兼容性或授权实测。",
        "brief_observations": observations,
    }


def _context(root: str | Path | None) -> _Context:
    stale_paths: list[str] = []
    selected_root, records = load_index(root, allow_stale=True, stale_paths=stale_paths)
    context = _Context(selected_root, records)
    context.stale_paths = stale_paths
    return context


def recommend_style(style: str, root: str | Path | None = None) -> dict[str, Any]:
    """Return one precise 01–08 style, using the default preview samples."""
    if style not in STYLES:
        raise ValueError("style 必须是 '01' 至 '08'。")
    context = _context(root)
    return _candidate(context, style, "", _required(""), [])


def recommend_styles(root: str | Path | None = None, *,
                     records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Return eight styles; callers may pass records from load_index(root)."""
    if records is None:
        context = _context(root)
    else:
        if root is None:
            raise ValueError("传入 records 时必须提供 load_index 返回的 root。")
        context = _Context(Path(resolve_root(root)), records)
    required = _required("")
    return [_candidate(context, style, "", required, []) for style in STYLES]


def recommend(brief: str, root: str | Path | None = None) -> list[dict[str, Any]]:
    """Return up to three different real font combinations for a brief.

    Missing roles are explicit; if fewer than three distinct combinations exist,
    fewer are returned rather than inventing fonts or relabeling duplicates.
    """
    context = _context(root)
    required = _required(brief)
    observations = _brief_observations(context, brief)
    matches = {code: _style_match(brief, code)[0] for code in STYLES}
    primary = max(STYLES, key=lambda code: (matches[code], -int(code)))
    if not any(matches.values()):
        primary = "02"
    alternatives = STYLES[primary]["alternatives"]
    order = [primary] + sorted(alternatives, key=lambda code: (-matches[code], alternatives.index(code)))
    results = []
    seen = set()
    for style in order:
        candidate = _candidate(context, style, brief, required, observations)
        if not any(value["font"] is not None for value in candidate["roles"].values()):
            # Preserve a diagnostic candidate when nothing at all is usable;
            # otherwise never count an empty palette as another font pairing.
            if not results:
                results.append(candidate)
            continue
        signature = tuple((value["font"].get("sha256"), value["font"].get("face_index", 0), value["weight"])
                          if value["font"] else None for value in candidate["roles"].values())
        if signature in seen:
            continue
        seen.add(signature)
        results.append(candidate)
        if len(results) == 3:
            break
    actual_count = sum(any(value["font"] is not None for value in item["roles"].values()) for item in results)
    if actual_count < 3:
        note = f"仅有 {actual_count} 套含有效字体的不同实际组合；不能编造三套，缺失角色见各方案。"
        for candidate in results:
            candidate["warnings"].append(note)
    return results


def _render_text(candidates: list[dict[str, Any]], root: Path) -> None:
    print(f"字体根目录：{root}")
    for index, candidate in enumerate(candidates, 1):
        print(f"\n方案 {index}｜{candidate['style']} {candidate['title']}｜启发式 {candidate['score_total']}/100")
        print(candidate["description"])
        print("配色：" + " / ".join(f"{key} {value}" for key, value in candidate["palette"].items()))
        print(candidate["density"])
        print(candidate["mixing"])
        print(candidate["visual_relationship"])
        unique_fonts: dict[tuple[str, int], dict[str, Any]] = {}
        for role, value in candidate["roles"].items():
            font = value["font"]
            if font is None:
                print(f"  {ROLE_LABELS[role]}：缺失；目标 {value['size']} pt，未指定任何字体。")
                print(f"    逐字检查范围（去重）：{value['sample']}")
                for note in value["notes"]:
                    print(f"    缺失说明：{note}")
                continue
            key = (font["path"], font.get("face_index", 0))
            unique_fonts[key] = font
            print(f"  {ROLE_LABELS[role]}：{font.get('family', '')} / {font.get('subfamily', '')}；"
                  f"{value['size']} pt，字重 {value['weight']}，字间距 {value['spacing']} em，颜色 {value['color']}；"
                  f"文件 {root / font['path']}，face {font.get('face_index', 0)}")
            if value["line_height"] is not None:
                print(f"    行距：{value['line_height']} 倍")
            print(f"    {value['weight_note']}")
            print(f"    逐字检查范围（去重）：{value['sample']}")
            for note in value["notes"]:
                print(f"    替代说明：{note}")
        print("  评分依据：")
        for name, item in candidate["scores"].items():
            print(f"    {name} {item['score']}/{item['max']}：{item['basis']}")
        print("  字体安装与许可证据：")
        for (path, face), font in unique_fonts.items():
            installed = font.get("installed") or {}
            license_info = font.get("license") or {}
            print(f"    {path}（face {face}）：安装 {installed.get('status', '未确认')}；{installed.get('note', '')}")
            for match in installed.get("matches") or []:
                print(f"      注册表匹配：{match.get('hive', '')} {match.get('name', '')} {match.get('path', '')}")
            print(f"      许可：{license_info.get('status', '待核实')}；{license_info.get('note', '')}")
            for item in license_info.get("files") or []:
                print(f"      许可材料：{item.get('path', '')}（{item.get('source', '')}）；适用范围待核实。")
                content = item.get("content")
                if content:
                    print(f"      材料内容：\n{content}")
                else:
                    print("      未提供许可文件内容，须自行查阅。")
            for item in license_info.get("metadata") or []:
                print(f"      字体许可元数据 {item.get('source', '')}：{item.get('value', '')}")
        print("  风险和替代：")
        for warning in candidate["warnings"]:
            print(f"    - {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="根据受限字体库为 PPT 推荐三套可追溯的字体设计")
    parser.add_argument("--brief", required=True, help="主题、受众、场景及需要检查的样本文字")
    parser.add_argument("--root", help="字体根目录；默认使用环境变量或平台默认路径")
    parser.add_argument("--json", action="store_true", help="输出包含完整字体索引记录的 JSON")
    args = parser.parse_args(argv)
    try:
        root = Path(resolve_root(args.root))
        candidates = recommend(args.brief, root)
        if args.json:
            json.dump(candidates, sys.stdout, ensure_ascii=False, separators=(",", ":"))
            print()
        else:
            _render_text(candidates, root)
        return 0 if any(any(value["font"] is not None for value in item["roles"].values()) for item in candidates) else 1
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"推荐失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
