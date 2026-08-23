#!/usr/bin/env python3
"""Create, inspect, and merge resumable translation jobs.

The script does not translate by itself. It deterministically prepares source
segments/chunks and validates/merges translation JSON produced by the agent.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_DIRECT_LIMIT = 16000
DEFAULT_CHUNK_TARGET = 12000
DEFAULT_CHUNK_MAX = 16000
CONTEXT_CHARS = 500


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Top-level JSON must be an object")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_plain_file(path: Path, target_languages: list[str], source_language: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    raw_blocks = re.split(r"\n\s*\n", text.strip()) if text.strip() else []
    blocks: list[dict[str, Any]] = []
    order = 1
    for raw in raw_blocks:
        raw = raw.strip("\n")
        if not raw.strip():
            continue
        stripped = raw.strip()
        block_type = "paragraph"
        if path.suffix.lower() in {".md", ".markdown"} and re.match(r"^#{1,6}\s+", stripped):
            block_type = "heading"
        elif stripped.startswith("```"):
            block_type = "code"
        elif re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)", stripped):
            block_type = "list-item"
        blocks.append({
            "id": f"b{order:06d}",
            "type": block_type,
            "text": raw,
            "order": order,
            "source_file": path.name,
        })
        order += 1
    if not blocks:
        raise ValueError(f"No text blocks found in {path}")
    return {
        "title": path.stem,
        "source_name": path.name,
        "source_language": source_language,
        "target_languages": target_languages,
        "blocks": blocks,
    }


def load_source(path: Path, targets: list[str], source_language: str) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        data = read_json(path)
    else:
        data = normalize_plain_file(path, targets, source_language)
    if targets:
        data["target_languages"] = targets
    elif not data.get("target_languages"):
        # Match the skill contract: a Chinese request with no explicit target
        # defaults to Simplified Chinese. Callers can still override this with
        # one or more --target flags or a non-empty source manifest value.
        data["target_languages"] = ["zh-CN"]
    data.setdefault("source_language", source_language)
    validate_source(data)
    return data


def validate_source(data: dict[str, Any]) -> None:
    blocks = data.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise ValueError("source JSON must contain a non-empty blocks list")

    targets = data.get("target_languages")
    if not isinstance(targets, list) or not targets or not all(isinstance(x, str) and x.strip() for x in targets):
        raise ValueError("target_languages must be a non-empty list of strings")
    if len(set(targets)) != len(targets):
        raise ValueError("target_languages contains duplicates")

    seen_ids: set[str] = set()
    seen_orders: set[int] = set()
    for idx, block in enumerate(blocks, 1):
        if not isinstance(block, dict):
            raise ValueError(f"block {idx} must be an object")
        for key in ("id", "type", "text", "order"):
            if key not in block:
                raise ValueError(f"block {idx} missing required field: {key}")
        bid = block["id"]
        order = block["order"]
        text = block["text"]
        if not isinstance(bid, str) or not bid.strip():
            raise ValueError(f"block {idx}: id must be a non-empty string")
        if bid in seen_ids:
            raise ValueError(f"duplicate block id: {bid}")
        seen_ids.add(bid)
        if not isinstance(order, int):
            raise ValueError(f"block {bid}: order must be an integer")
        if order in seen_orders:
            raise ValueError(f"duplicate block order: {order}")
        seen_orders.add(order)
        if not isinstance(text, str):
            raise ValueError(f"block {bid}: text must be a string")

    data["blocks"] = sorted(blocks, key=lambda b: b["order"])


def safe_job_id(value: str | None = None) -> str:
    if value:
        if not re.match(r"^[A-Za-z0-9._-]+$", value):
            raise ValueError("job id may contain only letters, digits, dot, underscore, and hyphen")
        return value
    return f"tr-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def split_sentences(text: str) -> list[str]:
    # Split primarily after sentence terminators while preserving the terminator.
    parts = re.split(r"(?<=[.!?。！？])(?:\s+|(?=[A-Z\u4e00-\u9fff]))", text)
    parts = [p for p in parts if p]
    return parts or [text]


def hard_split(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    result: list[str] = []
    remaining = text
    while len(remaining) > max_chars:
        # Search only inside the allowed window. Looking at max_chars + 1
        # characters can select a delimiter at the boundary and emit a piece
        # that is one character larger than the hard limit.
        window = remaining[:max_chars]
        candidates = [window.rfind(x) for x in (" ", "\n", ";", "；", ",", "，", ":", "：")]
        cut = max(candidates)
        if cut < max_chars // 2:
            cut = max_chars
        else:
            cut = min(cut + 1, max_chars)
        result.append(remaining[:cut])
        remaining = remaining[cut:]
    if remaining:
        result.append(remaining)
    return result


def split_block_text(text: str, target_chars: int, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    sentences = split_sentences(text)
    pieces: list[str] = []
    current = ""
    for sent in sentences:
        if len(sent) > max_chars:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(hard_split(sent, max_chars))
            continue
        if not current:
            current = sent
            continue
        separator = " " if not current.endswith(("\n", " ")) and not sent.startswith(("\n", " ")) else ""
        candidate = current + separator + sent
        if len(candidate) <= target_chars:
            current = candidate
        else:
            pieces.append(current)
            current = sent
    if current:
        pieces.append(current)
    final: list[str] = []
    for piece in pieces:
        final.extend(hard_split(piece, max_chars))
    return final


def make_segments(source: dict[str, Any], chunk_target: int, chunk_max: int) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for block in source["blocks"]:
        pieces = split_block_text(block["text"], chunk_target, chunk_max)
        count = len(pieces)
        for i, piece in enumerate(pieces, 1):
            seg = {
                "segment_id": f"{block['id']}::s{i:03d}",
                "parent_id": block["id"],
                "type": block.get("type", "paragraph"),
                "source": piece,
                "order": block["order"],
                "segment_order": i,
                "segment_count": count,
            }
            for key, value in block.items():
                if key not in {"id", "type", "text", "order"}:
                    seg[key] = value
            segments.append(seg)
    return segments


def chunk_segments(segments: list[dict[str, Any]], target_chars: int, max_chars: int) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    for seg in segments:
        seg_chars = len(seg["source"])
        if seg_chars > max_chars:
            raise ValueError(f"segment {seg['segment_id']} exceeds hard max after splitting")
        if current and current_chars + seg_chars > target_chars:
            chunks.append(current)
            current = []
            current_chars = 0
        if current and current_chars + seg_chars > max_chars:
            chunks.append(current)
            current = []
            current_chars = 0
        current.append(seg)
        current_chars += seg_chars
    if current:
        chunks.append(current)
    return chunks


def create_job(args: argparse.Namespace) -> int:
    targets = args.target or []
    source = load_source(args.source, targets, args.source_language)
    if not targets:
        targets = list(source.get("target_languages", []))
    if not targets:
        targets = ["zh-CN"]
        source["target_languages"] = targets

    if args.chunk_target <= 0 or args.chunk_max <= 0 or args.chunk_target > args.chunk_max:
        raise ValueError("chunk sizes must be positive and chunk-target must be <= chunk-max")

    job_id = safe_job_id(args.job_id)
    job_dir = args.out_root / job_id
    if job_dir.exists():
        raise FileExistsError(f"job directory already exists: {job_dir}")
    (job_dir / "chunks").mkdir(parents=True)
    (job_dir / "translations").mkdir()
    (job_dir / "final").mkdir()

    segments = make_segments(source, args.chunk_target, args.chunk_max)
    chunks = chunk_segments(segments, args.chunk_target, args.chunk_max)

    source_chars = sum(len(b["text"]) for b in source["blocks"])
    manifest = {
        "job_id": job_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_name": source.get("source_name", args.source.name),
        "source_language": source.get("source_language", args.source_language),
        "target_languages": targets,
        "source_blocks": len(source["blocks"]),
        "source_characters": source_chars,
        "segment_count": len(segments),
        "chunk_count": len(chunks),
        "mode": "direct-sized" if source_chars <= args.direct_limit and len(chunks) == 1 else "chunked",
        "settings": {
            "direct_limit_chars": args.direct_limit,
            "chunk_target_chars": args.chunk_target,
            "chunk_hard_max_chars": args.chunk_max,
            "context_chars": CONTEXT_CHARS,
        },
    }
    write_json(job_dir / "manifest.json", manifest)
    write_json(job_dir / "source.json", source)
    write_json(job_dir / "glossary.json", {"job_id": job_id, "entries": []})

    flat = [seg for chunk in chunks for seg in chunk]
    index_by_id = {seg["segment_id"]: i for i, seg in enumerate(flat)}
    for idx, chunk in enumerate(chunks, 1):
        first_idx = index_by_id[chunk[0]["segment_id"]]
        last_idx = index_by_id[chunk[-1]["segment_id"]]
        before = flat[first_idx - 1]["source"][-CONTEXT_CHARS:] if first_idx > 0 else ""
        after = flat[last_idx + 1]["source"][:CONTEXT_CHARS] if last_idx + 1 < len(flat) else ""
        payload = {
            "job_id": job_id,
            "chunk_id": f"chunk-{idx:04d}",
            "source_language": manifest["source_language"],
            "target_languages": targets,
            "context_before": before,
            "context_after": after,
            "segments": chunk,
        }
        write_json(job_dir / "chunks" / f"chunk-{idx:04d}.json", payload)

    print(json.dumps({
        "job_id": job_id,
        "job_dir": str(job_dir),
        "mode": manifest["mode"],
        "source_characters": source_chars,
        "chunks": len(chunks),
        "targets": targets,
    }, ensure_ascii=False))
    return 0


def inspect_translation_file(chunk: dict[str, Any], translation_path: Path, targets: list[str]) -> list[str]:
    errors: list[str] = []
    if not translation_path.exists():
        return [f"missing translation file: {translation_path.name}"]
    try:
        data = read_json(translation_path)
    except Exception as exc:
        return [f"invalid JSON in {translation_path.name}: {exc}"]
    if data.get("job_id") != chunk.get("job_id"):
        errors.append(f"{translation_path.name}: job_id mismatch")
    if data.get("chunk_id") != chunk.get("chunk_id"):
        errors.append(f"{translation_path.name}: chunk_id mismatch")
    rows = data.get("translations")
    if not isinstance(rows, list):
        errors.append(f"{translation_path.name}: translations must be a list")
        return errors
    by_id: dict[str, dict[str, Any]] = {}
    for row_index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append(f"{translation_path.name}: row {row_index} must be an object")
            continue
        segment_id = row.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id:
            errors.append(f"{translation_path.name}: row {row_index} missing segment_id")
            continue
        if segment_id in by_id:
            errors.append(f"{translation_path.name}: duplicate segment {segment_id}")
            continue
        by_id[segment_id] = row
    expected_ids = [s["segment_id"] for s in chunk["segments"]]
    extras = sorted(set(by_id) - set(expected_ids))
    if extras:
        errors.append(f"{translation_path.name}: unexpected segment ids: {extras}")
    for seg_id in expected_ids:
        row = by_id.get(seg_id)
        if not row:
            errors.append(f"{translation_path.name}: missing segment {seg_id}")
            continue
        translated = row.get("translated")
        if not isinstance(translated, dict):
            errors.append(f"{translation_path.name}: segment {seg_id} missing translated object")
            continue
        for target in targets:
            value = translated.get(target)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{translation_path.name}: segment {seg_id} missing target {target}")
    return errors


def load_job(job_dir: Path) -> tuple[dict[str, Any], dict[str, Any], list[tuple[Path, dict[str, Any]]]]:
    manifest = read_json(job_dir / "manifest.json")
    source = read_json(job_dir / "source.json")
    chunk_files = sorted((job_dir / "chunks").glob("chunk-*.json"))
    if not chunk_files:
        raise ValueError("no chunk files found")
    chunks = [(p, read_json(p)) for p in chunk_files]
    if len(chunks) != manifest.get("chunk_count"):
        raise ValueError("manifest chunk_count does not match chunk files")
    return manifest, source, chunks


def status_job(args: argparse.Namespace) -> int:
    manifest, _, chunks = load_job(args.job_dir)
    targets = manifest["target_languages"]
    errors: list[str] = []
    complete = 0
    for chunk_path, chunk in chunks:
        trans_path = args.job_dir / "translations" / chunk_path.name
        chunk_errors = inspect_translation_file(chunk, trans_path, targets)
        if chunk_errors:
            errors.extend(chunk_errors)
        else:
            complete += 1
    summary = {
        "job_id": manifest["job_id"],
        "chunks_total": len(chunks),
        "chunks_complete": complete,
        "targets": targets,
        "ready_to_merge": not errors,
        "errors": errors,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def target_joiner(target: str) -> str:
    base = target.lower().split("-")[0]
    return "" if base in {"zh", "ja", "ko"} else " "


def merge_job(args: argparse.Namespace) -> int:
    manifest, source, chunks = load_job(args.job_dir)
    targets = manifest["target_languages"]
    errors: list[str] = []
    translation_rows: dict[str, dict[str, str]] = {}
    segment_index: dict[str, dict[str, Any]] = {}

    for chunk_path, chunk in chunks:
        for seg in chunk["segments"]:
            sid = seg["segment_id"]
            if sid in segment_index:
                errors.append(f"duplicate segment across chunks: {sid}")
            segment_index[sid] = seg
        trans_path = args.job_dir / "translations" / chunk_path.name
        errors.extend(inspect_translation_file(chunk, trans_path, targets))
        if trans_path.exists():
            try:
                data = read_json(trans_path)
            except Exception:
                continue
            for row in data.get("translations", []):
                if isinstance(row, dict) and isinstance(row.get("segment_id"), str):
                    translation_rows[row["segment_id"]] = row.get("translated", {})

    if errors:
        print(json.dumps({"job_id": manifest["job_id"], "merged": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 2

    by_parent: dict[str, list[dict[str, Any]]] = {}
    for seg in segment_index.values():
        by_parent.setdefault(seg["parent_id"], []).append(seg)
    for segs in by_parent.values():
        segs.sort(key=lambda s: s["segment_order"])

    merged_blocks: list[dict[str, Any]] = []
    for block in sorted(source["blocks"], key=lambda b: b["order"]):
        segs = by_parent.get(block["id"], [])
        if not segs:
            raise ValueError(f"no segments found for source block {block['id']}")
        translations: dict[str, str] = {}
        for target in targets:
            parts = [translation_rows[seg["segment_id"]][target].strip() for seg in segs]
            translations[target] = target_joiner(target).join(parts)
        merged = {
            "id": block["id"],
            "type": block.get("type", "paragraph"),
            "order": block["order"],
            "source": block["text"],
            "translations": translations,
        }
        for key, value in block.items():
            if key not in {"id", "type", "text", "order"}:
                merged[key] = value
        merged_blocks.append(merged)

    final = {
        "job_id": manifest["job_id"],
        "title": source.get("title", ""),
        "source_name": source.get("source_name", manifest.get("source_name", "")),
        "source_language": source.get("source_language", manifest.get("source_language", "auto")),
        "target_languages": targets,
        "blocks": merged_blocks,
    }
    if "notes" in source:
        final["notes"] = source["notes"]
    final_path = args.job_dir / "final" / "translation.json"
    write_json(final_path, final)
    print(json.dumps({"job_id": manifest["job_id"], "merged": True, "output": str(final_path), "blocks": len(merged_blocks)}, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create a translation job from normalized JSON or a text/Markdown file")
    create.add_argument("source", type=Path)
    create.add_argument("--out-root", type=Path, default=Path("translation_jobs"))
    create.add_argument("--target", action="append", help="target language code; repeat for multiple targets")
    create.add_argument("--source-language", default="auto")
    create.add_argument("--job-id")
    create.add_argument("--direct-limit", type=int, default=DEFAULT_DIRECT_LIMIT)
    create.add_argument("--chunk-target", type=int, default=DEFAULT_CHUNK_TARGET)
    create.add_argument("--chunk-max", type=int, default=DEFAULT_CHUNK_MAX)
    create.set_defaults(func=create_job)

    status = sub.add_parser("status", help="validate completion of translated chunk files")
    status.add_argument("job_dir", type=Path)
    status.set_defaults(func=status_job)

    merge = sub.add_parser("merge", help="merge completed translation chunks by stable segment IDs")
    merge.add_argument("job_dir", type=Path)
    merge.set_defaults(func=merge_job)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
