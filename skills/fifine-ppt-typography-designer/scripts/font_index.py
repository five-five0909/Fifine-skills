#!/usr/bin/env python3
"""Index a font library without installing fonts.

The default library is synced from ModelScope into its cache. The index
deduplicates face metadata by SHA256 and stores portable locations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from fontTools.ttLib import TTFont, sfnt


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = SKILL_DIR / "references" / "local-font-index.json"
DATASET_ID = "fifine/fifine-font"
FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".otc"}
COLLECTION_EXTENSIONS = {".ttc", ".otc"}
INDEX_FORMAT = "ppt-typography-font-index"
INDEX_VERSION = 1
COMMON_ZH = "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十"
BASIC_LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"
LICENSE_WORDS = ("license", "licence", "copyright", "ofl", "许可", "授权", "版权")
LICENSE_SUFFIXES = {"", ".txt", ".md", ".markdown", ".html", ".htm", ".rtf"}
REGISTRY_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"


def resolve_root(root: str | os.PathLike[str] | None = None) -> Path:
    """Use an explicit or environment root, otherwise sync the ModelScope dataset."""
    if root is not None:
        selected = Path(root).expanduser()
    elif os.environ.get("PPT_TYPOGRAPHY_FONT_ROOT"):
        selected = Path(os.environ["PPT_TYPOGRAPHY_FONT_ROOT"]).expanduser()
    else:
        try:
            from modelscope.hub.snapshot_download import dataset_snapshot_download
        except ImportError as exc:
            raise ValueError("缺少 modelscope；请安装 requirements.txt") from exc
        try:
            selected = Path(dataset_snapshot_download(
                DATASET_ID, token=os.environ.get("MODELSCOPE_API_TOKEN") or None
            ))
        except Exception as exc:
            raise ValueError("ModelScope 字体数据集同步失败；请检查网络、访问权限和 MODELSCOPE_API_TOKEN") from exc
        if (selected / "PPT推荐字体").is_dir():
            selected = selected / "PPT推荐字体"
        if not any(path.is_file() and path.suffix.lower() in FONT_EXTENSIONS
                   for path in selected.rglob("*")):
            raise ValueError("ModelScope 数据集中没有字体文件；请先上传字体库，或使用 --root 指定本地字体库")
    try:
        selected = selected.resolve(strict=True)
    except OSError as exc:
        raise FileNotFoundError(f"指定的受限字体目录不存在或无法访问：{selected}") from exc
    if not selected.is_dir():
        raise NotADirectoryError(f"字体根路径不是目录：{selected}")
    return selected


def _root_fingerprint(root: Path) -> str:
    # The archive contains no machine-specific absolute root path.
    normalized = os.path.normcase(str(root.resolve()))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _checked_path(root: Path, relative: str, *, strict: bool = True) -> Path:
    """Reject absolute, parent, noncanonical, or symlink-escaping paths."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError(f"无效索引相对路径：{relative!r}")
    pure = PurePosixPath(relative)
    if (pure.is_absolute() or pure.as_posix() != relative or
            any(part in ("", ".", "..") for part in pure.parts) or
            ":" in pure.parts[0]):
        raise ValueError(f"无效索引相对路径：{relative!r}")
    candidate = root.joinpath(*pure.parts)
    try:
        resolved = candidate.resolve(strict=strict)
    except OSError as exc:
        raise ValueError(f"索引中的文件不存在或无法访问：{relative}；请重新 build") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"索引路径越过字体根目录：{relative}") from exc
    return resolved


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _error_text(exc: Exception, root: Path) -> str:
    if isinstance(exc, OSError):
        detail = exc.strerror or str(exc.errno or "文件访问失败")
    else:
        detail = str(exc)
    # Errors in the portable index must not embed the local absolute root.
    for spelling in {str(root), str(root).replace("\\", "/"), str(root).replace("/", "\\")}:
        detail = detail.replace(spelling, "<font-root>")
    if isinstance(exc, OSError) and not exc.strerror:
        detail = "文件访问失败"
    return f"{type(exc).__name__}: {detail}"


def _portable_error(error: str, path: Path, root: Path) -> str:
    """A deduplicated error may be reused for another identical file."""
    for value in (str(path), str(path).replace("\\", "/"), str(path).replace("/", "\\")):
        error = error.replace(value, "<font-file>")
    for value in (str(root), str(root).replace("\\", "/"), str(root).replace("/", "\\")):
        error = error.replace(value, "<font-root>")
    return error


def _name_values(font: TTFont, name_id: int) -> list[str]:
    if "name" not in font:
        return []
    values: list[str] = []
    for record in font["name"].names:
        if record.nameID != name_id:
            continue
        try:
            value = record.toUnicode().replace("\x00", "").strip()
        except (UnicodeError, ValueError, LookupError):
            continue
        if value and value not in values:
            values.append(value)
    return values


def _preferred_name(font: TTFont, name_id: int, values: list[str]) -> str:
    if "name" in font:
        try:
            value = font["name"].getDebugName(name_id)
            if value:
                return value.replace("\x00", "").strip()
        except (UnicodeError, ValueError, LookupError):
            pass
    return values[0] if values else ""


def _category(font: TTFont, names: dict[str, Any], monospace: bool) -> str:
    if monospace:
        return "monospace"
    os2 = font.get("OS/2")
    family_class = (int(getattr(os2, "sFamilyClass", 0)) >> 8) & 0xFF
    if family_class in {1, 2, 3, 4, 5, 7}:
        return "serif"
    if family_class == 8:
        return "sans"
    if family_class == 9:
        return "display"
    if family_class == 10:
        return "script"
    panose = getattr(os2, "panose", None)
    if getattr(panose, "bFamilyType", 0) == 2:
        serif_style = getattr(panose, "bSerifStyle", 0)
        if 2 <= serif_style <= 10:
            return "serif"
        if 11 <= serif_style <= 15:
            return "sans"
    family = " ".join([names["family"], names["typographic_family"]]).casefold()
    if "sans" in family or "黑体" in family:
        return "sans"
    if "serif" in family or "宋体" in family:
        return "serif"
    return "unknown"


def _face_metadata(font: TTFont, face_index: int) -> dict[str, Any]:
    all_names = {number: _name_values(font, number) for number in (1, 2, 4, 5, 6, 16, 17)}
    names: dict[str, Any] = {
        "family": _preferred_name(font, 1, all_names[1]),
        "typographic_family": _preferred_name(font, 16, all_names[16]),
        "full": _preferred_name(font, 4, all_names[4]),
        "postscript": _preferred_name(font, 6, all_names[6]),
        "aliases": list(dict.fromkeys(
            value for number in (1, 16, 4, 6) for value in all_names[number]
        )),
    }
    family = names["typographic_family"] or names["family"] or names["full"] or names["postscript"]
    if not family:
        raise ValueError("字体面没有可识别的内部名称")
    subfamily = (_preferred_name(font, 17, all_names[17]) or
                 _preferred_name(font, 2, all_names[2]) or "Unknown")
    os2 = font.get("OS/2")
    weight = int(getattr(os2, "usWeightClass", 400) or 400)
    axes = []
    if "fvar" in font:
        axes = [{"tag": axis.axisTag, "min": float(axis.minValue),
                 "default": float(axis.defaultValue), "max": float(axis.maxValue)}
                for axis in font["fvar"].axes]
    codepoints: set[int] = set()
    if "cmap" in font:
        for table in font["cmap"].tables:
            if table.isUnicode():
                codepoints.update(cp for cp, glyph in table.cmap.items()
                                  if isinstance(cp, int) and 0 <= cp <= 0x10FFFF
                                  and glyph and glyph != ".notdef")
    common = set(map(ord, COMMON_ZH))
    latin = set(map(ord, BASIC_LATIN))
    digits = set(map(ord, DIGITS))
    zh_hit = len(codepoints & common)
    cjk_count = sum(0x4E00 <= cp <= 0x9FFF for cp in codepoints)
    mono = bool(getattr(font.get("post"), "isFixedPitch", 0))
    license_metadata = []
    for name_id, source in ((0, "name ID 0 copyright"), (7, "name ID 7 trademark"),
                            (8, "name ID 8 manufacturer"), (9, "name ID 9 designer"),
                            (13, "name ID 13 license"), (14, "name ID 14 license URL")):
        for value in _name_values(font, name_id):
            license_metadata.append({"source": source, "value": value})
    return {
        "family": family, "names": names, "subfamily": subfamily,
        "weight": weight, "axes": axes, "face_index": face_index,
        "version": _preferred_name(font, 5, all_names[5]),
        "coverage": sorted(codepoints),
        "cjk": zh_hit * 5 >= len(common) * 4,
        "latin": latin.issubset(codepoints), "digits": digits.issubset(codepoints),
        "coverage_summary": {"common_chinese_covered": zh_hit,
                             "common_chinese_sample_size": len(common),
                             "cjk_unified_count": cjk_count,
                             "latin_covered": len(codepoints & latin),
                             "latin_sample_size": len(latin),
                             "digits_covered": len(codepoints & digits),
                             "digits_sample_size": len(digits)},
        "monospace": mono, "category": _category(font, names, mono),
        "license_metadata": license_metadata,
        "metadata_source": "字体内部 name、OS/2、post、fvar 与 Unicode cmap 表",
    }


def _parse_file(path: Path, root: Path) -> dict[str, Any]:
    """Parse TTC/OTC faces independently so one corrupt face does not hide others."""
    faces: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    try:
        with path.open("rb") as stream:
            collection = stream.read(4) == b"ttcf"
            if collection:
                count = sfnt.readTTCHeader(stream).numFonts
                if count <= 0:
                    raise ValueError("字体集合不包含字体面")
            else:
                count = 1
    except Exception as exc:
        return {"faces": [], "errors": [{"face_index": None,
                                         "error": _portable_error(_error_text(exc, root), path, root)}]}
    for face_index in range(count):
        try:
            font = TTFont(str(path), fontNumber=face_index if collection else -1,
                          lazy=True)
            try:
                faces.append(_face_metadata(font, face_index))
            finally:
                font.close()
        except Exception as exc:
            errors.append({"face_index": face_index,
                           "error": _portable_error(_error_text(exc, root), path, root)})
    return {"faces": faces, "errors": errors, "collection": collection}


def _discover_fonts(root: Path) -> tuple[list[Path], list[dict[str, Any]]]:
    paths: list[Path] = []
    errors: list[dict[str, Any]] = []

    def onerror(exc: OSError) -> None:
        name = Path(exc.filename) if exc.filename else root
        try:
            relative = _relative_path(root, name)
        except ValueError:
            relative = "."
        errors.append({"path": relative, "face_index": None, "error": _error_text(exc, root)})

    for base, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
        parent = Path(base)
        # Skipping all directory links also prevents duplicate scans and loops.
        for name in list(dirs):
            if (parent / name).is_symlink():
                dirs.remove(name)
                errors.append({"path": _relative_path(root, parent / name), "face_index": None,
                               "error": "跳过目录符号链接，未遍历其目标"})
        dirs.sort()
        for name in sorted(files):
            path = parent / name
            if path.suffix.casefold() not in FONT_EXTENSIONS:
                continue
            relative = _relative_path(root, path)
            try:
                _checked_path(root, relative)
            except ValueError as exc:
                errors.append({"path": relative, "face_index": None, "error": _error_text(exc, root)})
                continue
            paths.append(path)
    return paths, errors


def _read_index(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到字体索引：{path}；请先运行 font_index.py build") from None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取字体索引 {path}：{exc}") from exc
    if (not isinstance(data, dict) or data.get("format") != INDEX_FORMAT or
            data.get("version") != INDEX_VERSION or
            not isinstance(data.get("files"), list) or not isinstance(data.get("contents"), dict)):
        raise ValueError(f"文件不是支持的字体索引：{path}")
    return data


def _index_output(output: str | os.PathLike[str] | None, root: Path) -> Path:
    path = Path(output).expanduser().resolve() if output is not None else DEFAULT_INDEX.resolve()
    try:
        path.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("索引输出不能写入只读字体根目录")
    return path


def _write_index(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent,
                                         prefix=".font-index-", suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            json.dump(data, stream, ensure_ascii=False, separators=(",", ":"))
            stream.write("\n")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def build_index(root: str | os.PathLike[str] | None = None,
                output: str | os.PathLike[str] | None = None,
                force: bool = False) -> dict[str, Any]:
    """Build an incremental index; metadata is deduplicated by content SHA256."""
    root_path = resolve_root(root)
    output_path = _index_output(output, root_path)
    fingerprint = _root_fingerprint(root_path)
    previous: dict[str, Any] = {}
    if output_path.exists():
        # Refuse to overwrite an unrelated file, including invalid JSON.
        try:
            previous = _read_index(output_path)
        except ValueError as exc:
            raise FileExistsError(f"拒绝覆盖非本工具索引：{output_path}") from exc
    same_root = previous.get("root_fingerprint") == fingerprint
    previous_files = {item.get("path"): item for item in previous.get("files", [])
                      if isinstance(item, dict)} if same_root else {}
    previous_contents = previous.get("contents", {}) if same_root else {}
    paths, errors = _discover_fonts(root_path)
    entries: list[dict[str, Any]] = []
    contents: dict[str, Any] = {}
    reused = parsed = hashed = 0

    for path in paths:
        relative = _relative_path(root_path, path)
        try:
            real_path = _checked_path(root_path, relative)
            stat = real_path.stat()
            if not real_path.is_file():
                raise ValueError("不是普通文件")
            old = previous_files.get(relative, {})
            digest = old.get("sha256", "")
            reusable = (not force and old.get("size") == stat.st_size and
                        old.get("mtime_ns") == stat.st_mtime_ns and
                        digest in previous_contents and isinstance(previous_contents[digest], dict))
            if reusable:
                content = contents.get(digest, previous_contents[digest])
                reused += 1
            else:
                digest = _hash_file(real_path)
                hashed += 1
                if digest in contents:
                    content = contents[digest]
                elif not force and digest in previous_contents and isinstance(previous_contents[digest], dict):
                    content = previous_contents[digest]
                else:
                    content = _parse_file(real_path, root_path)
                    parsed += 1
            after = real_path.stat()
            if (stat.st_size, stat.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError("扫描期间字体文件发生变化；请重新 build")
            contents[digest] = content
            entries.append({"path": relative, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                            "sha256": digest})
            for item in content.get("errors", []):
                errors.append({"path": relative, **item})
        except Exception as exc:
            errors.append({"path": relative, "face_index": None, "error": _error_text(exc, root_path)})

    faces = sum(len(contents[item["sha256"]].get("faces", [])) for item in entries)
    families = sorted({face["family"] for content in contents.values() for face in content.get("faces", [])})
    schemes = sorted({PurePosixPath(item["path"]).parts[0] for item in entries})
    # Store portable references, but refresh their content on every load.
    # A directory association is not a verified license grant.
    license_cache: dict[tuple[str, ...], tuple[list[dict[str, str]], list[str]]] = {}
    for entry in entries:
        parts = PurePosixPath(entry["path"]).parts
        key = tuple(parts[:2]) if len(parts) >= 3 else (entry["path"],)
        if key not in license_cache:
            license_cache[key] = _family_licenses(root_path, entry["path"])
        license_files, warnings = license_cache[key]
        entry["license"] = {
            "status": "待核实",
            "files": [{"path": item["path"], "source": item["source"]} for item in license_files],
            "note": "家族目录关联及适用条款待人工核实，不代表免费商用"
                    + ("；" + "；".join(warnings) if warnings else ""),
        }
    summary = {"font_files": len(paths), "indexed_files": len(entries), "font_faces": faces,
               "font_families": len(families), "schemes": schemes, "unique_sha256": len(contents),
               "duplicate_files": len(entries) - len(contents), "errors": len(errors),
               "reused_files": reused, "hashed_files": hashed, "parsed_contents": parsed}
    data = {"format": INDEX_FORMAT, "version": INDEX_VERSION, "root_fingerprint": fingerprint,
            "generated_at": datetime.now(timezone.utc).isoformat(), "files": entries,
            "contents": contents, "errors": errors, "summary": summary}
    _write_index(output_path, data)
    if not paths:
        raise ValueError(f"受限字体目录没有 TTF/OTF/TTC/OTC 文件；已写入诊断索引：{output_path}")
    if not faces:
        raise ValueError(f"没有可解析的字体面；已写入诊断索引：{output_path}")
    return {**summary, "output": str(output_path)}


def _read_license(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _family_licenses(root: Path, relative: str) -> tuple[list[dict[str, str]], list[str]]:
    parts = PurePosixPath(relative).parts
    # The library layout is scheme/family/font; never inspect a sibling family.
    if len(parts) < 3:
        return [], ["字体文件没有明确的方案/家族目录，未扩展搜索许可证"]
    family_path = root.joinpath(*parts[:2])
    try:
        _checked_path(root, PurePosixPath(*parts[:2]).as_posix())
    except ValueError:
        return [], ["字体家族目录无法安全访问"]
    found: list[dict[str, str]] = []
    warnings: list[str] = []

    def onerror(exc: OSError) -> None:
        warnings.append("许可证目录读取失败：" + _error_text(exc, root))

    for base, dirs, files in os.walk(family_path, followlinks=False, onerror=onerror):
        parent = Path(base)
        dirs[:] = sorted(name for name in dirs if not (parent / name).is_symlink())
        for name in sorted(files):
            file = parent / name
            lower = name.casefold()
            relative_parts = file.relative_to(family_path).parts
            in_license_dir = any(any(word in part.casefold() for word in LICENSE_WORDS)
                                 for part in relative_parts[:-1])
            if (file.suffix.casefold() not in LICENSE_SUFFIXES or
                    not (in_license_dir or any(word in lower for word in LICENSE_WORDS))):
                continue
            rel = _relative_path(root, file)
            try:
                resolved = _checked_path(root, rel)
                resolved.relative_to(family_path.resolve())
                found.append({"path": rel, "source": "同一方案的字体家族目录",
                              "content": _read_license(resolved)})
            except (OSError, ValueError, UnicodeError) as exc:
                warnings.append(f"无法读取 {rel}：{_error_text(exc, root)}")
    return found, warnings


def _registered_fonts(sizes: set[int]) -> tuple[dict[str, list[dict[str, str]]], str]:
    """Hash only paths explicitly registered in Windows, never scan font folders."""
    if sys.platform != "win32":
        return {}, "非 Windows 系统，不查询注册表；安装状态未确认"
    try:
        import winreg
    except ImportError:
        return {}, "无法使用 Windows 注册表模块；安装状态未确认"
    registered: dict[str, list[dict[str, str]]] = defaultdict(list)
    errors: list[str] = []
    digest_cache: dict[str, str | None] = {}
    for hive, label in ((winreg.HKEY_LOCAL_MACHINE, "HKLM"), (winreg.HKEY_CURRENT_USER, "HKCU")):
        try:
            with winreg.OpenKey(hive, REGISTRY_KEY) as key:
                count = winreg.QueryInfoKey(key)[1]
                values = []
                for index in range(count):
                    try:
                        values.append(winreg.EnumValue(key, index))
                    except OSError as exc:
                        errors.append(f"{label} 第 {index} 条注册项读取失败：{exc.strerror or exc}")
        except OSError as exc:
            errors.append(f"{label} 字体注册表读取失败：{exc.strerror or exc}")
            continue
        for name, raw, _ in values:
            if not isinstance(raw, str) or not raw.strip():
                continue
            value = os.path.expandvars(raw.strip().strip('"'))
            # Do not reach network shares in the course of checking installations.
            if value.startswith(("\\\\", "//")):
                continue
            candidate = Path(value)
            if candidate.drive and not candidate.is_absolute():
                # Drive-relative paths have process-dependent resolution.
                continue
            if candidate.is_absolute():
                candidates = [candidate]
            else:
                candidates = []
                if os.environ.get("WINDIR"):
                    candidates.append(Path(os.environ["WINDIR"]) / "Fonts" / candidate)
                if label == "HKCU" and os.environ.get("LOCALAPPDATA"):
                    candidates.append(Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts" / candidate)
            for candidate in candidates:
                try:
                    candidate = candidate.resolve()
                except OSError:
                    continue
                # Do not follow a registered local symlink onto a network share.
                if str(candidate).startswith(("\\\\", "//")):
                    continue
                key_path = os.path.normcase(os.path.abspath(candidate))
                if key_path not in digest_cache:
                    try:
                        # Size is a necessary condition for an identical SHA256 file.
                        digest_cache[key_path] = (_hash_file(candidate)
                                                  if candidate.is_file() and candidate.stat().st_size in sizes
                                                  else None)
                    except OSError:
                        digest_cache[key_path] = None
                digest = digest_cache[key_path]
                if digest:
                    registered[digest].append({"hive": label, "name": name,
                                               "path": str(candidate), "sha256": digest})
    note = "以注册表指向的文件 SHA256 比较；未确认不代表未安装或未加载"
    if errors:
        note += "；" + "；".join(errors)
    return dict(registered), note


def load_index(root: str | os.PathLike[str] | None = None, *, allow_stale: bool = False,
               stale_paths: list[str] | None = None) -> tuple[Path, list[dict[str, Any]]]:
    """Return (root, records), validating source files and refreshing live facts.

    Default rejects changed or missing indexed files. With allow_stale=True,
    skip those files and append their relative paths to stale_paths, while still
    rejecting unsafe paths or a corrupt index. Rebuild first; use --force for
    changes retaining size and mtime.
    """
    root_path = resolve_root(root)
    data = _read_index(DEFAULT_INDEX)
    if data.get("root_fingerprint") != _root_fingerprint(root_path):
        raise ValueError("字体索引与当前根目录不匹配；请在当前机器和根目录重新 build")
    valid: list[tuple[dict[str, Any], Path]] = []
    seen: set[str] = set()
    for entry in data["files"]:
        if not isinstance(entry, dict):
            raise ValueError("字体索引文件记录无效；请重新 build")
        relative = entry.get("path")
        if not isinstance(relative, str) or relative in seen:
            raise ValueError("字体索引路径无效或重复；请重新 build")
        seen.add(relative)
        # Check content structure before an optional stale-file skip.
        digest = entry.get("sha256")
        content = data["contents"].get(digest)
        if not isinstance(content, dict) or not isinstance(content.get("faces"), list):
            raise ValueError(f"索引字体内容记录损坏：{relative}；请重新 build")
        # Even absent paths must be safe: do not relax absolute, parent or
        # symlink-escape checks when allow_stale is enabled.
        path = _checked_path(root_path, relative, strict=False)
        reason = ""
        try:
            stat = path.stat()
            if (not path.is_file() or stat.st_size != entry.get("size") or
                    stat.st_mtime_ns != entry.get("mtime_ns")):
                reason = "文件不是普通文件或大小/修改时间已变化"
        except OSError:
            reason = "文件不存在或无法访问"
        if reason:
            if not allow_stale:
                raise ValueError(f"索引字体不可用：{relative}（{reason}）；请重新 build")
            if stale_paths is not None:
                stale_paths.append(relative)
            continue
        valid.append((entry, path))
    if not valid:
        if allow_stale:
            return root_path, []
        raise ValueError("索引没有可用字体文件；请检查扫描错误并重新 build")
    installed, registry_note = _registered_fonts({entry["size"] for entry, _ in valid})
    licenses: dict[tuple[str, ...], tuple[list[dict[str, str]], list[str]]] = {}
    records: list[dict[str, Any]] = []
    for entry, path in valid:
        relative = entry["path"]
        parts = PurePosixPath(relative).parts
        family_key = tuple(parts[:2]) if len(parts) >= 3 else (relative,)
        if family_key not in licenses:
            licenses[family_key] = _family_licenses(root_path, relative)
        license_files, warnings = licenses[family_key]
        matches = installed.get(entry["sha256"], [])
        collection = bool(data["contents"][entry["sha256"]].get("collection"))
        # A matching collection file does not establish which face is registered.
        confirmed = bool(matches) and not collection
        install_note = registry_note
        if matches and not confirmed:
            install_note += "；集合文件哈希匹配但注册表未确认具体字体面"
        for face in data["contents"][entry["sha256"]]["faces"]:
            if not isinstance(face, dict):
                raise ValueError(f"索引字体面无效：{relative}；请重新 build")
            metadata = face.get("license_metadata", [])
            record = {**face, **entry,
                      "scheme": parts[0] if parts else "",
                      "installed": {"status": "已确认" if confirmed else "未确认",
                                    "matches": matches, "note": install_note},
                      "license": {"status": "待核实", "files": license_files,
                                  "metadata": metadata,
                                  "note": "许可文件及字体元数据的对应关系和适用范围须人工核实，不代表免费商用"
                                          + ("；" + "；".join(warnings) if warnings else "")}}
            records.append(record)
    if not records and not allow_stale:
        raise ValueError("索引没有可解析的字体面；请检查扫描错误并重新 build")
    return root_path, records


SCENARIOS = {
    "01": ("典藏", "黑金", "奢华", "商务", "收藏"),
    "02": ("瑞士", "秩序", "极简", "网格", "理性"),
    "03": ("深海", "未来", "科技", "技术", "ai", "赛博"),
    "04": ("杂志", "新奢", "时尚", "编辑"),
    "05": ("自然", "人文", "温暖", "生态"),
    "06": ("东方", "国风", "传统", "文化"),
    "07": ("先锋", "海报", "潮流", "冲击"),
    "08": ("圆润", "创意", "活泼", "亲子"),
    "09": ("通用", "基础"),
}

# Explicit cross-language aliases are added only when an actual internal name
# identifies the family. Directory names never establish font identity.
FAMILY_ALIASES = (
    ("Source Han Sans", "思源黑体"),
    ("Source Han Serif", "思源宋体"),
    ("Alibaba PuHuiTi", "阿里巴巴普惠体"),
    ("XiaWuWenKai", "霞鹜文楷"),
    ("LXGW WenKai", "霞鹜文楷"),
    ("YouSheBiaoTiHei", "优设标题黑"),
)


def _contains(query: str, values: list[str]) -> bool:
    needle = query.casefold().strip()
    return any(needle in value.casefold() for value in values)


def _scenario_match(record: dict[str, Any], query: str) -> bool:
    normalized = query.casefold().strip()
    scheme = record["scheme"]
    if normalized in scheme.casefold():
        return True
    return any(scheme.startswith(code + "_") and any(word in normalized for word in words)
               for code, words in SCENARIOS.items())


def _weight_match(record: dict[str, Any], weight: int) -> bool:
    if record["weight"] == weight:
        return True
    return any(axis.get("tag") == "wght" and axis.get("min", 0) <= weight <= axis.get("max", 0)
               for axis in record["axes"])


def _search(args: argparse.Namespace) -> int:
    root, records = load_index(args.root)
    results: list[dict[str, Any]] = []
    category_aliases = {"黑体": "sans", "无衬线": "sans", "sans-serif": "sans", "sans serif": "sans",
                        "宋体": "serif", "衬线": "serif", "等宽": "monospace", "mono": "monospace",
                        "展示": "display", "手写": "script", "楷体": "script"}
    for record in records:
        names = record["names"]
        name_values = [record["family"], names["family"], names["typographic_family"],
                       names["full"], names["postscript"], *names["aliases"]]
        if args.name:
            matches_name = _contains(args.name, name_values)
            if not matches_name:
                matches_name = any(
                    _contains(args.name, list(pair)) and
                    any(_contains(alias, name_values) for alias in pair)
                    for pair in FAMILY_ALIASES
                )
            if not matches_name:
                continue
        if args.style and not _contains(args.style, [record["subfamily"], record["scheme"], names["full"]]):
            continue
        if args.scenario and not _scenario_match(record, args.scenario):
            continue
        if args.category:
            wanted = category_aliases.get(args.category.casefold(), args.category.casefold())
            if wanted not in record["category"].casefold():
                continue
        if args.weight is not None and not _weight_match(record, args.weight):
            continue
        if args.language and not record[{"zh": "cjk", "en": "latin", "digits": "digits"}[args.language]]:
            continue
        # Do not print large coverage arrays, but verify any provided text exactly.
        summary = {key: value for key, value in record.items() if key not in {"coverage", "license_metadata"}}
        summary["absolute_path"] = str(root / Path(*PurePosixPath(record["path"]).parts))
        if args.text is not None:
            from bisect import bisect_left
            coverage = record["coverage"]
            def missing_char(char: str) -> bool:
                index = bisect_left(coverage, ord(char))
                return index == len(coverage) or coverage[index] != ord(char)
            missing = list(dict.fromkeys(char for char in args.text if missing_char(char)))
            summary["text_coverage"] = {"text": args.text, "complete": not missing, "missing": missing,
                                        "note": "逐字符检查 Unicode cmap；不保证复杂排版或字形外观"}
        results.append(summary)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for record in results:
            print(json.dumps(record, ensure_ascii=False))
        if not results:
            print("没有匹配的库内字体面；请调整条件。", file=sys.stderr)
    return 0 if results else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="同步或指定字体库，建立索引、核验和检索；不安装字体")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="增量构建字体索引")
    build.add_argument("--root", help="受限字体库目录，优先于环境变量")
    build.add_argument("--output", help="索引输出路径（不得位于字体库内）")
    build.add_argument("--force", action="store_true", help="重新哈希并解析所有字体内容")
    search = subparsers.add_parser("search", help="根据索引检索真实字体面")
    search.add_argument("--root", help="受限字体库目录，优先于环境变量")
    search.add_argument("--name", help="字体内部名称或内部本地化别名")
    search.add_argument("--style", help="内部子家族或方案风格")
    search.add_argument("--scenario", help="应用场景或方案名称")
    search.add_argument("--category", help="serif / sans / monospace / display / script")
    search.add_argument("--weight", type=int, help="真实 OS/2 字重或可变 wght 轴内的数值")
    search.add_argument("--language", choices=("zh", "en", "digits"))
    search.add_argument("--text", help="以实际文案逐字符检查 cmap，不静默回退")
    search.add_argument("--json", action="store_true", help="输出 JSON 数组")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            print(json.dumps(build_index(args.root, args.output, args.force), ensure_ascii=False, indent=2))
            return 0
        return _search(args)
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
