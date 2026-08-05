from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PLACEHOLDER_PREFIX = "<填:"
LEADING_CONNECTOR_RISK = ("因此", "但", "于是", "所以", "然而", "由此可见")


def slugify_path(path: Path) -> str:
    stem = path.stem.lower()
    stem = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", stem).strip("-")
    return stem or "paper"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def find_unfilled(data: Any, path: str = "") -> list[str]:
    missing: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            sub = f"{path}.{k}" if path else k
            missing.extend(find_unfilled(v, sub))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            missing.extend(find_unfilled(v, f"{path}[{i}]"))
    elif isinstance(data, str) and data.strip().startswith(PLACEHOLDER_PREFIX):
        missing.append(path)
    return missing


def validate_no_braces(data: Any, path: str = "") -> list[str]:
    issues: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            sub = f"{path}.{k}" if path else k
            issues.extend(validate_no_braces(v, sub))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            issues.extend(validate_no_braces(v, f"{path}[{i}]"))
    elif isinstance(data, str) and ("{" in data or "}" in data):
        issues.append(f"{path} 中包含花括号 {{}}，会破坏模板渲染，请去掉或改写")
    return issues


def check_leading_connectors(label: str, value: str) -> list[str]:
    value = str(value or "").strip()
    if value.startswith(LEADING_CONNECTOR_RISK):
        return [f"{label} 开头是连接词 '{value[:4]}...'，会和模板自带连接词重复，请删掉开头连接词。"]
    return []


def ensure_pdf(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"主论文 PDF 不存在：{path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"入口文件必须是 PDF：{path}")
