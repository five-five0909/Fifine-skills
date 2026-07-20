#!/usr/bin/env python3
"""Parse PDFs/images with PaddleOCR-VL through the official AI Studio API."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError as exc:  # pragma: no cover - user environment dependent
    print("Missing dependency: requests", file=sys.stderr)
    print("Install with: python -m pip install -r <skill>/requirements.txt", file=sys.stderr)
    raise SystemExit(2) from exc


JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
DEFAULT_MODEL = "PaddleOCR-VL-1.6"


def safe_name(value: str) -> str:
    name = Path(urlparse(value).path).stem if value.startswith(("http://", "https://")) else Path(value).stem
    name = name or "paddleocr-output"
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", name).strip(" .") or "paddleocr-output"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse a PDF/image using PaddleOCR-VL AI Studio API.")
    parser.add_argument("file_path", help="Local file path or HTTP(S) file URL.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Default: ./paddleocr-output/<input-name>-<timestamp>")
    parser.add_argument("--token", default=os.getenv("PADDLEOCR_AISTUDIO_TOKEN"))
    parser.add_argument("--model", default=os.getenv("PADDLEOCR_MODEL", DEFAULT_MODEL))
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--request-timeout", type=float, default=120.0)
    image_group = parser.add_mutually_exclusive_group()
    image_group.add_argument(
        "--images",
        dest="download_images",
        action="store_true",
        default=True,
        help="Download Markdown referenced images and output images. This is the default.",
    )
    image_group.add_argument(
        "--no-images",
        dest="download_images",
        action="store_false",
        help="Skip image downloads and only write Markdown/JSONL outputs.",
    )
    parser.add_argument("--use-doc-orientation-classify", action="store_true")
    parser.add_argument("--use-doc-unwarping", action="store_true")
    parser.add_argument("--use-chart-recognition", action="store_true")
    parser.add_argument("--optional-payload-json", default=None, help="JSON object merged into optionalPayload.")
    return parser.parse_args()


def build_optional_payload(args: argparse.Namespace) -> dict:
    payload = {
        "useDocOrientationClassify": bool(args.use_doc_orientation_classify),
        "useDocUnwarping": bool(args.use_doc_unwarping),
        "useChartRecognition": bool(args.use_chart_recognition),
    }
    if args.optional_payload_json:
        extra = json.loads(args.optional_payload_json)
        if not isinstance(extra, dict):
            raise ValueError("--optional-payload-json must be a JSON object")
        payload.update(extra)
    return payload


def submit_job(args: argparse.Namespace, headers: dict, optional_payload: dict) -> str:
    file_path = args.file_path
    print(f"Processing file: {file_path}")
    if file_path.startswith(("http://", "https://")):
        request_headers = dict(headers)
        request_headers["Content-Type"] = "application/json"
        response = requests.post(
            JOB_URL,
            json={"fileUrl": file_path, "model": args.model, "optionalPayload": optional_payload},
            headers=request_headers,
            timeout=args.request_timeout,
        )
    else:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        data = {"model": args.model, "optionalPayload": json.dumps(optional_payload, ensure_ascii=False)}
        with path.open("rb") as file:
            response = requests.post(
                JOB_URL,
                headers=headers,
                data=data,
                files={"file": file},
                timeout=args.request_timeout,
            )

    print(f"Submit response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response content: {response.text}", file=sys.stderr)
    response.raise_for_status()
    body = response.json()
    return body["data"]["jobId"]


def poll_job(job_id: str, headers: dict, args: argparse.Namespace) -> dict:
    deadline = time.monotonic() + args.timeout
    print(f"Job submitted successfully. job id: {job_id}")
    print("Start polling for results")
    last_state = None
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Timed out waiting for PaddleOCR job after {args.timeout} seconds: {job_id}")
        response = requests.get(f"{JOB_URL}/{job_id}", headers=headers, timeout=args.request_timeout)
        response.raise_for_status()
        data = response.json()["data"]
        state = data["state"]
        if state != last_state:
            print(f"Job state: {state}")
            last_state = state
        if state == "pending":
            pass
        elif state == "running":
            progress = data.get("extractProgress") or {}
            total = progress.get("totalPages")
            extracted = progress.get("extractedPages")
            if total is not None and extracted is not None:
                print(f"Running, total pages: {total}, extracted pages: {extracted}")
            else:
                print("Running...")
        elif state == "done":
            progress = data.get("extractProgress") or {}
            print(
                "Job completed, successfully extracted pages: "
                f"{progress.get('extractedPages')}, start time: {progress.get('startTime')}, end time: {progress.get('endTime')}"
            )
            return data
        elif state == "failed":
            raise RuntimeError(f"Job failed: {data.get('errorMsg')}")
        else:
            print(f"Unknown job state: {state}")
        time.sleep(args.poll_interval)


def download_text(url: str, timeout: float) -> str:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def download_binary(url: str, path: Path, timeout: float) -> None:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)


def write_outputs(job_data: dict, output_dir: Path, args: argparse.Namespace) -> dict:
    result_url = job_data.get("resultUrl") or {}
    jsonl_url = result_url.get("jsonUrl")
    if not jsonl_url:
        raise RuntimeError(f"Missing resultUrl.jsonUrl in job data: {json.dumps(job_data, ensure_ascii=False)[:1000]}")

    output_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = output_dir / "pages"
    images_dir = output_dir / "images"
    pages_dir.mkdir(parents=True, exist_ok=True)

    jsonl_text = download_text(jsonl_url, args.request_timeout)
    (output_dir / "result.jsonl").write_text(jsonl_text, encoding="utf-8")

    merged_parts: list[str] = []
    page_num = 0
    image_count = 0
    page_files: list[str] = []

    for line_num, line in enumerate(jsonl_text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        result = item.get("result") or {}
        layout_results = result.get("layoutParsingResults") or []
        for res in layout_results:
            markdown = res.get("markdown") or {}
            text = markdown.get("text") or ""
            md_path = pages_dir / f"doc_{page_num}.md"
            md_path.write_text(text, encoding="utf-8")
            page_files.append(str(md_path))
            merged_parts.append(f"\n\n<!-- page {page_num} -->\n\n{text}".strip())
            print(f"Markdown document saved at {md_path}")

            if args.download_images:
                for img_path, img_url in (markdown.get("images") or {}).items():
                    target = images_dir / img_path
                    download_binary(img_url, target, args.request_timeout)
                    image_count += 1
                    print(f"Image saved to: {target}")
                for img_name, img_url in (res.get("outputImages") or {}).items():
                    target = images_dir / f"{img_name}_{page_num}.jpg"
                    download_binary(img_url, target, args.request_timeout)
                    image_count += 1
                    print(f"Image saved to: {target}")
            page_num += 1

    merged_path = output_dir / "merged.md"
    merged_path.write_text("\n\n".join(merged_parts).strip() + "\n", encoding="utf-8")
    manifest = {
        "jobId": job_data.get("jobId"),
        "state": job_data.get("state"),
        "jsonlUrl": jsonl_url,
        "outputDir": str(output_dir),
        "mergedMarkdown": str(merged_path),
        "pageMarkdownFiles": page_files,
        "pageCount": page_num,
        "imageCount": image_count,
        "extractProgress": job_data.get("extractProgress"),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    args = parse_args()
    if not args.token:
        print("Missing token. Pass --token or set PADDLEOCR_AISTUDIO_TOKEN.", file=sys.stderr)
        return 2

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd() / "paddleocr-output" / f"{safe_name(args.file_path)}-{timestamp}"
    headers = {"Authorization": f"bearer {args.token}"}
    optional_payload = build_optional_payload(args)

    try:
        job_id = submit_job(args, headers, optional_payload)
        job_data = poll_job(job_id, headers, args)
        manifest = write_outputs(job_data, output_dir, args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Done.")
    print(f"Output dir: {manifest['outputDir']}")
    print(f"Merged Markdown: {manifest['mergedMarkdown']}")
    print(f"Pages: {manifest['pageCount']}, images: {manifest['imageCount']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
