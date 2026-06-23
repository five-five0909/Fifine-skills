from __future__ import annotations
from pathlib import Path
import json
import re
from typing import Any

try:
    import fitz
except Exception:
    fitz = None


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_pdf_snapshot(pdf_path: Path, max_pages: int = 8) -> dict[str, Any]:
    snapshot = {'metadata': {}, 'pages': [], 'errors': []}
    if fitz is None:
        snapshot['errors'].append('PyMuPDF not installed')
        return snapshot
    try:
        doc = fitz.open(pdf_path)
        snapshot['metadata'] = doc.metadata or {}
        for i in range(min(max_pages, len(doc))):
            page = doc.load_page(i)
            snapshot['pages'].append({'page': i + 1, 'text': page.get_text('text')})
        doc.close()
    except Exception as e:
        snapshot['errors'].append(str(e))
    return snapshot


def sanitize_filename_part(text: str) -> str:
    text = re.sub(r'[<>:"/\|?*]+', '-', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def normalize_title_lines(lines: list[str]) -> str:
    cleaned: list[str] = []
    for line in lines:
        s = re.sub(r"\s+", " ", line).strip()
        if not s:
            continue
        if s.lower().startswith("published as"):
            continue
        if s.upper() == "ABSTRACT" or s.upper().startswith("1 INTRODUCTION"):
            break
        cleaned.append(s)
    if not cleaned:
        return ""

    title_parts: list[str] = []
    for line in cleaned:
        if re.search(r"department|university|@|abstract", line, re.I):
            break
        # 作者行：多个 Title Case 人名 + 连接符
        if len(title_parts) >= 1 and re.search(r"([A-Z][a-zA-Z´`'’-]+(?:\s+[A-Z][a-zA-Z´`'’-]+)+)", line) and re.search(r"\s&\s|\sand\s", line, re.I):
            break
        title_parts.append(line)
    title = " ".join(title_parts).strip()
    title = re.sub(r"\s+", " ", title)
    return title


def normalize_authors_from_lines(lines: list[str]) -> str:
    for i, line in enumerate(lines):
        s = re.sub(r"\s+", " ", line).strip()
        if not s:
            continue
        # 邮箱行上方通常就是作者行
        if "@" in s and i > 0:
            prev = re.sub(r"\s+", " ", lines[i - 1]).strip()
            prev = re.sub(r"[*†‡0-9]+", "", prev).strip()
            if re.search(r"department|university", prev, re.I) and i > 1:
                prev = re.sub(r"\s+", " ", lines[i - 2]).strip()
                prev = re.sub(r"[*†‡0-9]+", "", prev).strip()
            if prev:
                return prev

    for line in lines[:12]:
        s = re.sub(r"\s+", " ", line).strip()
        if not s:
            continue
        if re.search(r"department|university|@|abstract|published as", s, re.I):
            continue
        if "&" in s and len(s.split()) <= 12:
            return re.sub(r"[*†‡0-9]+", "", s).strip()
    return ""


def shorten_authors(authors_raw: str) -> str:
    s = authors_raw.strip()
    if not s:
        return "Unknown Author"
    if re.search(r"\bet al\.?\b", s, re.I):
        first = s.split()[0]
        return f"{first} et al."
    parts = [p.strip() for p in re.split(r"\s*&\s*|,\s*| and ", s) if p.strip()]
    if not parts:
        return "Unknown Author"

    def last_name(name: str) -> str:
        toks = [t for t in name.split() if t]
        return toks[-1] if toks else name

    if len(parts) == 1:
        return last_name(parts[0])
    if len(parts) == 2:
        return f"{last_name(parts[0])} & {last_name(parts[1])}"
    return f"{last_name(parts[0])} et al."


def shorten_title_for_key(title: str, max_words: int = 14) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    words = title.split()
    if len(words) <= max_words:
        return title
    return " ".join(words[:max_words])


def parse_named_pdf_stem(pdf_stem: str) -> tuple[str, str, str]:
    """
    解析像 2022_Efficiently Modeling Long Sequences with Structured State Spaces_Gu et al
    这种规范命名。
    """
    m = re.match(r"^(?P<year>\d{4})_(?P<title>.+)_(?P<authors>[^_]+)$", pdf_stem)
    if not m:
        return "", "", ""
    return m.group("year").strip(), m.group("title").strip(), m.group("authors").strip()


def build_reference_key(year: str, title: str, authors: str) -> str:
    year = (year or '0000').strip()
    title = sanitize_filename_part(title or 'Unknown Title')
    authors = sanitize_filename_part(authors or 'Unknown Author')
    return f"{year}_{title}_{authors}"


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))
