#!/usr/bin/env python3
"""Heuristic QA for Gemini Flash Lite technical-diagram roughs."""

from __future__ import annotations

import argparse
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path


FORBIDDEN = {
    "hex color": re.compile(r"#[0-9a-f]{3,8}\b", re.I),
    "pixel instruction": re.compile(r"\b\d+\s*px\b", re.I),
    "construction copy": re.compile(
        r"\b(?:no shadow|no gradient|corner radius|authoring[- ]only|construction note|"
        r"layout note|icon filename|image identifier|visible title|visible subtitle)\b",
        re.I,
    ),
    "probable node id": re.compile(r"\b(?:[A-Z]{1,3}\d{1,2})\b"),
}


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        signature = stream.read(24)
    if len(signature) < 24 or signature[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    return struct.unpack(">II", signature[16:24])


def collect(inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            paths.extend(path.rglob("*.png"))
        elif path.suffix.lower() == ".png" and path.exists():
            paths.append(path)
    return sorted(set(paths))


def ocr(path: Path) -> str:
    result = subprocess.run(
        ["tesseract", str(path), "stdout", "--psm", "11"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="PNG files or directories")
    parser.add_argument("--skip-ocr", action="store_true", help="Check dimensions only")
    args = parser.parse_args()

    images = collect(args.paths)
    if not images:
        print("ERROR: no PNG files found", file=sys.stderr)
        return 2
    if not args.skip_ocr and not shutil.which("tesseract"):
        print("ERROR: tesseract is required for copy QA", file=sys.stderr)
        return 2

    failures = 0
    for path in images:
        findings: list[str] = []
        try:
            width, height = png_size(path)
            ratio = width / height
            if abs(ratio - 16 / 9) > 0.035:
                findings.append(f"aspect ratio {width}x{height} is not 16:9")
        except ValueError as error:
            findings.append(str(error))
            width = height = 0

        text = ""
        if not args.skip_ocr:
            text = ocr(path)
            for label, pattern in FORBIDDEN.items():
                matches = sorted(set(pattern.findall(text)))
                if matches:
                    findings.append(f"{label}: {', '.join(matches[:8])}")

        if findings:
            failures += 1
            print(f"FAIL {path} ({width}x{height})")
            for finding in findings:
                print(f"  - {finding}")
        else:
            print(f"PASS {path} ({width}x{height})")

    print(f"\nChecked {len(images)} image(s); {failures} flagged.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
