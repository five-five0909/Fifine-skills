---
name: document-paddleocr-vl
description: Use PaddleOCR-VL through the official AI Studio HTTP API to parse PDFs, screenshots, scans, images, and image-only documents into Markdown. Trigger when the user asks to OCR, parse, extract text/layout/tables/charts, convert a PDF/image to Markdown, or use PaddleOCR/PaddleOCR-VL without MCP.
---

# PaddleOCR VL

## Overview

Use this skill for on-demand OCR/document parsing with PaddleOCR-VL. It does not use MCP and does not start a persistent server; it calls the official AI Studio job API, polls until completion, and downloads JSONL results, Markdown pages, and images by default.

## Quick Start

Run the bundled parser script:

```powershell
$env:PADDLEOCR_AISTUDIO_TOKEN = "<your-ai-studio-token>"
python .\scripts\parse.py "<absolute-path-to-file.pdf>"
```

For a URL:

```powershell
python .\scripts\parse.py "https://example.com/file.pdf"
```

Specify an output folder:

```powershell
python .\scripts\parse.py "<absolute-path-to-file.pdf>" --output-dir "<output-dir>"
```

## What the Script Produces

- `pages/doc_<n>.md` — one Markdown file per parsed page/result block.
- `merged.md` — all page Markdown concatenated in order.
- `result.jsonl` — raw JSONL downloaded from AI Studio.
- `images/` — downloaded Markdown and output images by default.
- `manifest.json` — job metadata and output paths.

## Options

- `--token TOKEN` supplies the AI Studio token for one run.
- `PADDLEOCR_AISTUDIO_TOKEN` supplies the AI Studio token through the environment.
- `--model MODEL` defaults to `PaddleOCR-VL-1.6`.
- `--output-dir DIR` controls where outputs are written.
- Images are downloaded by default.
- `--images` is accepted for explicitness but is already the default.
- `--no-images` skips image downloads when you only want Markdown/JSONL.
- `--poll-interval SEC` defaults to `5`.
- `--timeout SEC` defaults to `1800`.
- `--use-doc-orientation-classify`, `--use-doc-unwarping`, and `--use-chart-recognition` enable optional PaddleOCR features.
- `--optional-payload-json '{...}'` merges extra official API options into `optionalPayload`.

## Rules

- Prefer absolute local paths on Windows.
- If `requests` is missing, install this skill's requirements:

```powershell
python -m pip install -r .\requirements.txt
```

- Run commands from this skill directory, or replace `.\scripts\parse.py` and `.\requirements.txt` with the installed skill's actual paths.
- If parsing succeeds, read `merged.md` before summarizing or answering questions about the document.
- If parsing fails, report the API state/error message and the output directory, if created.
