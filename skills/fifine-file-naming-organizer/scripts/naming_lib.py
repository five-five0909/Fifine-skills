#!/usr/bin/env python3
"""
naming_lib.py — Shared grammar and safety checks for file/folder naming.

Canonical file name:
    [【状态标签】]YYYYMMDD_核心信息[_版本号][.ext]
    e.g. 【定稿】20260918_秋季活动-报价单_V4.docx

Canonical folder name:
    [YYYYMMDD_]核心信息        (no status tag, no version)
    e.g. 20260910_秋季活动 / 交付物

Used by audit_names.py (read-only) and apply_naming.py (executor).
Dependencies: Python 3.7+ standard library only.
"""

import datetime as _dt
import io
import os
import re
import sys
import unicodedata

# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

STATUS_TAGS = ("草稿", "待审", "待改", "定稿", "归档")
LOCKED_TAGS = ("定稿", "归档")

_TAG_ALT = "|".join(STATUS_TAGS)

# One keyword: CJK / latin / digit, then up to 39 more of the same or spaces.
# Deliberately excludes - _ . 【 】 so those stay reserved as syntax.
SEG = r"[0-9A-Za-z一-鿿][0-9A-Za-z一-鿿 ]{0,39}"

# 核心信息: files need 2-5 keywords (项目-内容); folders tolerate 1-5.
CORE_FILE = SEG + r"(?:-" + SEG + r"){1,4}"
CORE_DIR = SEG + r"(?:-" + SEG + r"){0,4}"

VER = r"V[1-9]\d*(?:\.\d{1,2}){0,2}"

# One dot-segment, or a known composite archive suffix. A general "{1,2}" would
# silently swallow the dot in "-V1.2.pptx" as an extension called ".2.pptx".
EXT_RE = re.compile(r"\.[0-9A-Za-z]{1,8}|\.tar\.(?:gz|bz2|xz|zst)")

FILE_RE = re.compile(
    r"^(?:【(?P<tag>" + _TAG_ALT + r")】)?"
    r"(?P<date>\d{8})_"
    r"(?P<core>" + CORE_FILE + r")"
    r"(?:_(?P<ver>" + VER + r"))?"
    r"(?P<ext>" + EXT_RE.pattern + r")?$"
)

DIR_RE = re.compile(
    r"^(?:(?P<date>\d{8})_)?"
    r"(?P<core>" + CORE_DIR + r")$"
)

BRACKETED_TAG_RE = re.compile(r"^[【\[](.{1,6})[】\]]")

# ---------------------------------------------------------------------------
# Cross-platform safety
# ---------------------------------------------------------------------------

# Hard reject: illegal on Windows and/or acts as a path separator.
ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Legal but fragile: breaks unquoted shell commands and glob patterns.
SHELL_HOSTILE = re.compile(r"[&%#()\[\]{};,@$`^~=!'+]")

RESERVED_NAME = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..*)?$", re.IGNORECASE)

MULTI_SUFFIX = (".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst")

# Hand-edited deliverables, so a version suffix is expected.
EDITABLE_EXTS = (
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".md", ".pdf",
    ".key", ".pages", ".numbers", ".psd", ".ai", ".sketch", ".wps",
)

MAX_STEM = 100
MAX_KEYWORD = 40
MAX_FULL_PATH = 240
# Most filesystems cap one path component at 255 BYTES; a CJK character costs
# three, so the character limits above are not sufficient on their own.
MAX_NAME_BYTES = 200

EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".agents", ".claude", ".codex", ".trellis", ".vscode",
    "node_modules", "__pycache__", ".venv", "venv", ".cache", ".paddlex",
    "dist", "build", ".pytest_cache", ".idea",
}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", "ntuser.dat"}

# Generic role folders. They carry no 项目 information, so the auditor skips
# them while walking upward for a project keyword.
STRUCTURAL_DIRS = {
    "交付物", "输出", "成果", "终稿", "过程稿", "素材", "原始素材", "参考", "参考资料",
    "参考文献", "图片", "图表", "附件", "数据", "存档", "归档", "收件箱", "其他",
    "临时", "版本备份", "output", "outputs", "inputs", "assets", "refs", "references",
    "data", "draft", "drafts", "final", "finals", "archive", "misc", "other", "temp",
    "images", "figures", "tables", "src", "docs",
}

MODES = ("solo", "collab")


def utf8_streams():
    """Keep Chinese output alive on a Windows GBK console."""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
                continue
            except (AttributeError, ValueError):
                pass
        buf = getattr(stream, "buffer", None)
        if buf is not None:
            setattr(sys, name, io.TextIOWrapper(buf, encoding="utf-8", errors="replace",
                                                line_buffering=True))


def nfc(text):
    return unicodedata.normalize("NFC", text)


def split_ext(name):
    """Return (stem, ext); composite archive suffixes stay whole."""
    low = name.lower()
    for suf in MULTI_SUFFIX:
        if low.endswith(suf):
            return name[:-len(suf)], name[-len(suf):]
    return os.path.splitext(name)


def parse_date(raw):
    """Return (date|None, error|None) for an 8-digit YYYYMMDD token."""
    if not re.fullmatch(r"\d{8}", raw or ""):
        return None, "日期不是 8 位数字 YYYYMMDD"
    try:
        day = _dt.datetime.strptime(raw, "%Y%m%d").date()
    except ValueError:
        return None, "日期不是真实存在的日历日"
    if day > _dt.date.today() + _dt.timedelta(days=366):
        return None, "日期晚于一年以后，疑似笔误"
    return day, None


def build_name(tag=None, date=None, core=None, ver=None, ext=""):
    """Assemble a canonical name; returns None when core is missing."""
    if not core:
        return None
    out = "【%s】" % tag if tag else ""
    out += "%s_" % date if date else ""
    out += core
    if ver:
        out += "_%s" % ver
    if ext:
        out += ext if ext.startswith(".") else "." + ext
    return out


def clean_keyword(text, limit=MAX_KEYWORD):
    """Turn an arbitrary legacy fragment into one legal keyword, or None."""
    if not text:
        return None
    out = re.sub(r"[【】\[\]()（）{}<>]", "", ILLEGAL_CHARS.sub("", text))
    out = re.sub(r"[_/,;:|'\"`~!@#$%^&*+=?]", "-", out)
    out = re.sub(r"-{2,}", "-", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" -.")
    if len(out) > limit:
        out = out[:limit].strip(" -.")
    if not out or not re.search(r"[0-9A-Za-z一-鿿]", out):
        return None
    return out


NOISE_TOKEN_RE = re.compile(
    r"(?i)^(v\d+(\.\d+)*|最终版?|最新版?|终稿|副本|备份|修改版?|定稿版?|new|final|draft|copy|"
    r"conflicted copy|sketch|word|excel|docx?|xlsx?|pptx?|pdf|tmp|temp)\d*(\(\d+\))?$"
)

# "报告(1)" / "报告（2）" — the browser/IM duplicate counter, always last.
DUP_COUNTER_RE = re.compile(r"\s*[(（]\d{1,3}[)）]\s*$")

# Chinese glues these onto real content ("会议纪要最终版"), so whole-token
# matching alone cannot drop them.
TRAILING_NOISE_RE = re.compile(
    r"(?i)(最终版?|最新版?|终稿|副本|备份|修改版|定稿版?|重命名|新建|(?:conflicted )?copy|"
    r"new|final|draft|tmp|temp)\s*$"
)

DATE_HINT_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})[-_./ ]?(\d{2})[-_./ ]?(\d{2})(?!\d)")
VERSION_TAIL_RE = re.compile(r"([_\-\s]?[vV])(\d+(?:\.\d+)*)$")
SPLIT_HINT_RE = re.compile(r"[-_.()\[\]{}【】，,、\s]+")


def core_candidates(stem):
    """Split a legacy stem into plausible keywords for AI-assisted naming."""
    cleaned = re.sub(r"[【】]", " ", ILLEGAL_CHARS.sub(" ", stem))
    parts = [p for p in SPLIT_HINT_RE.split(cleaned) if p]
    out, seen = [], set()
    for part in parts:
        p = part
        if NOISE_TOKEN_RE.match(p):
            continue
        for _ in range(4):
            shorter = TRAILING_NOISE_RE.sub("", p).strip(" -_")
            shorter = re.sub(r"(?i)[_-]?v\d+(\.\d+)*$", "", shorter).strip(" -_")
            if shorter == p:
                break
            p = shorter
        if not p or p.isdigit() or NOISE_TOKEN_RE.match(p):
            continue
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def salvage(name, kind="file"):
    """
    Recover whatever the canonical grammar can reuse from a broken name.

    Returns {"tag", "date", "ver", "ext", "stem_rest", "keywords"}; a legacy
    name should lose as little information as possible on the way to a proposal.
    """
    stem, ext = split_ext(name)
    tag = None

    bracketed = BRACKETED_TAG_RE.match(stem)
    if bracketed:
        if bracketed.group(1) in STATUS_TAGS:
            tag = bracketed.group(1)
        stem = stem[bracketed.end():]

    ver = None
    if kind == "file":
        for _ in range(2):
            counter = DUP_COUNTER_RE.search(stem)
            if not counter:
                break
            stem = stem[:counter.start()]
        version = VERSION_TAIL_RE.search(stem)
        if version and len(version.group(0)) <= 8:
            ver = "V%s" % version.group(2)
            stem = stem[:version.start()]

    date = None
    dated = DATE_HINT_RE.search(stem)
    if dated:
        raw = "".join(dated.groups())
        valid, _ = parse_date(raw)
        if valid:
            date = raw
            stem = (stem[:dated.start()] + " " + stem[dated.end():]).strip()

    return {"tag": tag, "date": date, "ver": ver, "ext": ext,
            "stem_rest": stem, "keywords": core_candidates(stem)}


def diagnose_file(name):
    """Concrete, actionable reasons why a file name is not canonical."""
    stem, ext = split_ext(name)
    notes = []

    rest = stem
    bracketed = BRACKETED_TAG_RE.match(stem)
    if bracketed:
        inner = bracketed.group(1)
        rest = stem[bracketed.end():]
        if inner not in STATUS_TAGS:
            notes.append("状态标签「%s」不在封闭集合（%s），需替换" % (inner, "/".join(STATUS_TAGS)))

    if re.match(r"^\d{8}[-.]", rest):
        notes.append("日期后必须用下划线 _，当前用的是「%s」" % rest[8])
    elif not re.match(r"^\d{8}_", rest):
        notes.append("缺 YYYYMMDD_ 日期前缀")
        date_part = None
    else:
        date_part = rest[:8]
        rest = rest[9:]
        _, date_err = parse_date(date_part)
        if date_err:
            notes.append(date_err)

    if not rest:
        notes.append("缺核心信息（项目-内容）")
        return notes

    version_part = None
    ver_match = re.search(r"_(V\d+(?:\.\d+)*)$", rest)
    low_ver = re.search(r"[_-]?[vV](\d+(?:\.\d+)*)$", rest)
    if ver_match:
        version_part = ver_match.group(1)
        rest = rest[:ver_match.start()]
    elif low_ver and not re.search(r"[一-鿿]$", rest[:low_ver.start()]):
        notes.append("版本号格式应为 _V1 / _V1.1（大写 V、前置下划线）")
        rest = rest[:low_ver.start()]

    core = rest
    if "_" in core:
        notes.append("核心信息内部禁止下划线，关键词请用中划线 - 连接")
    keywords = [k for k in re.split(r"-+", core) if k]
    if not keywords:
        notes.append("缺核心信息（项目-内容）")
    elif len(keywords) == 1 and not ext:
        notes.append("无扩展名，确认是否为脚本/可执行文件")
    elif len(keywords) == 1:
        notes.append("核心信息只有 1 个关键词「%s」，应为「项目-内容」两段以上" % keywords[0])
    elif len(keywords) > 5:
        notes.append("核心信息有 %d 个关键词，上限 5" % len(keywords))
    for kw in keywords:
        if kw != kw.strip():
            notes.append("中划线两侧不留空格（「%s」）" % kw.strip())
        if len(kw) > MAX_KEYWORD:
            notes.append("关键词「%s」%d 字符，上限 %d" % (kw, len(kw), MAX_KEYWORD))
        if "." in kw:
            notes.append("核心信息内不得出现点号；版本号请写成 _V 前置下划线并放在扩展名之前（如 _V%s）"
                         % kw.lstrip("Vv"))
        elif ILLEGAL_CHARS.search(kw):
            notes.append("关键词「%s」含非法字符" % kw)
        elif SHELL_HOSTILE.search(kw):
            notes.append("关键词「%s」含 shell 不友好字符" % kw)
    if version_part and not re.fullmatch(VER, version_part):
        notes.append("版本号「%s」格式不合法" % version_part)
    if ext and not EXT_RE.fullmatch(ext):
        notes.append("扩展名「%s」异常（只允许单个 .后缀，或 .tar.gz 这类已知复合后缀）" % ext)
    return notes


def _check_common(name, errors, warnings):
    if ILLEGAL_CHARS.search(name):
        bad = sorted(set(ILLEGAL_CHARS.findall(name)))
        errors.append("含 Windows 非法字符: %s" % " ".join(repr(b) for b in bad))
    if SHELL_HOSTILE.search(name):
        bad = sorted(set(SHELL_HOSTILE.findall(name)))
        warnings.append("含 shell/通配符不友好字符: %s（建议改写）" % " ".join(bad))
    if RESERVED_NAME.match(name):
        errors.append("命中 Windows 保留设备名")
    if name in (".", ".."):
        errors.append("相对引用名不可用作文件名")
    if nfc(name) != name:
        warnings.append("非 NFC 规范化形式，同步盘可能生成重名副本")
    if name.endswith(".") or name.endswith(" "):
        errors.append("名称不能以点号或空格结尾")
    name_bytes = len(nfc(name).encode("utf-8"))
    if name_bytes > MAX_NAME_BYTES:
        errors.append("名称单段 %d 字节，超过 %d 字节预算（中文每字约 3 字节）" % (
            name_bytes, MAX_NAME_BYTES))
    if "  " in name or name != name.strip():
        warnings.append("存在多余首尾或连续空格")


def validate(name, kind="file", mode="solo", dir_path=None, depth=None):
    """
    Check one name against the canonical grammar.

    kind  : "file" | "dir"
    mode  : "solo" (tag optional) | "collab" (tag expected for files)
    depth : folder depth relative to the organizing root (dirs only)

    Returns {"ok", "status", "locked", "parsed", "errors", "warnings"}.
    """
    errors, warnings = [], []
    parsed = {"tag": None, "date": None, "core": None, "ver": None, "ext": ""}

    if not name:
        errors.append("空名称")
        return {"ok": False, "status": "INVALID", "locked": False, "parsed": parsed,
                "errors": errors, "warnings": warnings}
    if name in EXCLUDED_FILES or name.startswith("."):
        return {"ok": False, "status": "SKIP-EXCLUDED", "locked": False, "parsed": parsed,
                "errors": ["点号开头的系统/配置名，按名读取，不参与整理"], "warnings": []}

    _check_common(name, errors, warnings)
    stem, ext = split_ext(name)

    if kind == "dir":
        match = DIR_RE.match(name)
        if not match:
            errors.append("目录名不符合 [YYYYMMDD_]核心信息")
        else:
            parsed["date"] = match.group("date")
            parsed["core"] = match.group("core")
            if match.group("date"):
                _, date_err = parse_date(match.group("date"))
                if date_err:
                    errors.append("目录" + date_err)
            elif depth == 1:
                errors.append("归档根第一层目录必须带 YYYYMMDD_ 前缀才能按时间排序")
        if "【" in name or "】" in name:
            errors.append("目录名不得带状态标签")
        if re.search(r"_V\d", name):
            errors.append("目录名不得带版本号")
        if len(name) > MAX_STEM:
            errors.append("目录名 %d 字符，超过 %d 上限" % (len(name), MAX_STEM))
    else:
        match = FILE_RE.match(name)
        if not match:
            notes = diagnose_file(name)
            errors.extend(notes or ["文件名不符合【状态标签】+YYYYMMDD+核心信息+版本号"])
        else:
            parsed["tag"] = match.group("tag")
            parsed["date"] = match.group("date")
            parsed["core"] = match.group("core")
            parsed["ver"] = match.group("ver")
            parsed["ext"] = match.group("ext") or ""
            _, date_err = parse_date(match.group("date"))
            if date_err:
                errors.append(date_err)
            keywords = parsed["core"].split("-")
            if len(keywords) < 2:
                errors.append("核心信息只有 1 个关键词，需「项目-内容」两段以上")
            if mode == "collab" and not parsed["tag"]:
                warnings.append("协作场景建议补状态标签")
            if ext.lower() in EDITABLE_EXTS and not parsed["ver"]:
                smuggled = re.search(r"[-_]?([vV]\d+(?:\.\d+)*)$", parsed["core"])
                if smuggled:
                    warnings.append("版本号被当成核心信息的一部分，应改为放在扩展名前的 _%s"
                                    % smuggled.group(1).upper())
                else:
                    warnings.append("可编辑交付物缺版本号，若有迭代建议补 _V1")
            if not ext:
                warnings.append("无扩展名，确认是否需要保留")
        if len(stem) > MAX_STEM:
            errors.append("主名 %d 字符，超过 %d 上限" % (len(stem), MAX_STEM))

    if dir_path is not None and os.path.join(dir_path, name) != "":
        full_len = len(os.path.join(dir_path, name))
        if full_len > MAX_FULL_PATH:
            errors.append("完整路径 %d 字符，超过 %d 预算（缩短核心信息）" % (full_len, MAX_FULL_PATH))

    locked = kind == "file" and parsed["tag"] in LOCKED_TAGS
    ok = not errors
    return {"ok": ok, "status": "COMPLIANT" if ok else "NON_CANONICAL", "locked": locked,
            "parsed": parsed, "errors": errors, "warnings": warnings}
