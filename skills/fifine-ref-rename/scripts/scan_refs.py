#!/usr/bin/env python3
"""
scan_refs.py — Recursively find PDFs and dump raw metadata + first-page text.

This script does NOT interpret or judge anything. It only extracts raw data.
The AI agent reads the output and decides what is title, author, year, etc.

Usage:
    python scan_refs.py <path>                     # Scan all PDFs
    python scan_refs.py <path> --incremental       # Skip already-renamed files
    python scan_refs.py <path> -o output.json      # Write to file (UTF-8)

Naming pattern (standardized):
    Files matching `YYYY_<title>_<author>.pdf` are considered already renamed.
    The --incremental flag skips these files.

Dependencies: PyMuPDF (fitz) — pip install PyMuPDF
"""

import sys
import os
import json
import re
import argparse

# Fix Windows GBK encoding issue for Chinese locale
if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import fitz
except ImportError:
    print("ERROR: PyMuPDF not installed. Run: pip install PyMuPDF", file=sys.stderr)
    sys.exit(1)

FIRST_PAGE_LINES = 20  # how many raw lines to extract from first page

# Pattern: YYYY_<at least one char>_<at least one char>.pdf
# Matches files already named by the ref-rename skill
STANDARDIZED_RE = re.compile(r"^\d{4}_.+_.+\.pdf$", re.IGNORECASE)


def is_standardized_name(filename: str) -> bool:
    """Check if filename matches the standardized YYYY_Title_Author.pdf pattern."""
    return bool(STANDARDIZED_RE.match(filename))


def scan_pdf(filepath: str) -> dict:
    """Extract raw data from one PDF. No interpretation."""
    info = {
        "path": filepath,
        "filename": os.path.basename(filepath),
        "metadata": {},       # raw PDF metadata (title, author, subject, etc.)
        "first_page_lines": [],  # first N non-empty lines from page 1
    }

    try:
        doc = fitz.open(filepath)
    except Exception as e:
        info["error"] = str(e)
        return info

    # --- Raw metadata (pass through as-is) ---
    meta = doc.metadata or {}
    for key in ("title", "author", "subject", "creator", "creationDate", "modDate"):
        val = (meta.get(key) or "").strip()
        if val:
            info["metadata"][key] = val

    # --- First-page text: split into non-empty lines ---
    try:
        page = doc[0]
        text = page.get_text()[:3000]
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        info["first_page_lines"] = lines[:FIRST_PAGE_LINES]
    except Exception:
        pass

    doc.close()
    return info


def find_pdfs(root_path: str, incremental: bool = False) -> tuple:
    """Recursively find all PDF files under root_path.
    
    Returns (pdf_paths, skipped_count) where skipped_count is the number
    of files that match the standardized naming pattern (only in incremental mode).
    """
    if os.path.isfile(root_path):
        if root_path.lower().endswith(".pdf"):
            if incremental and is_standardized_name(os.path.basename(root_path)):
                return [], 1
            return [root_path], 0
        return [], 0
    pdfs = []
    skipped = 0
    for dirpath, _, filenames in os.walk(root_path):
        for fn in sorted(filenames):
            if fn.lower().endswith(".pdf"):
                if incremental and is_standardized_name(fn):
                    skipped += 1
                    continue
                pdfs.append(os.path.join(dirpath, fn))
    return pdfs, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Scan PDFs and dump raw metadata + first-page text")
    parser.add_argument("path", help="Folder or single PDF to scan")
    parser.add_argument("-o", "--output", help="Output file path (UTF-8). If omitted, prints to stdout.")
    parser.add_argument("--incremental", action="store_true",
                        help="Skip files already matching YYYY_Title_Author.pdf pattern")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"ERROR: Path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    pdf_paths, skipped = find_pdfs(args.path, incremental=args.incremental)
    if args.incremental and skipped > 0:
        print(f"Incremental mode: {skipped} already-renamed file(s) skipped.", file=sys.stderr)

    if not pdf_paths:
        if skipped > 0:
            print(f"All {skipped} file(s) already renamed. Nothing to do.", file=sys.stderr)
        else:
            print("No PDF files found.", file=sys.stderr)
        sys.exit(0)

    results = []
    for p in pdf_paths:
        entry = scan_pdf(p)
        entry["rel_path"] = (
            os.path.relpath(p, args.path) if os.path.isdir(args.path)
            else os.path.basename(p)
        )
        results.append(entry)

    json_str = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Written {len(results)} entries to {args.output}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
