#!/usr/bin/env python3
"""Generate a diagram PNG via google.genai (API key or Vertex ADC).

Usage:
    python3 generate.py <request.json> <output.png> [model]

Auth (first match wins):
  1. Vertex + ADC: GOOGLE_GENAI_USE_VERTEXAI=1 and GOOGLE_CLOUD_PROJECT (+ optional GOOGLE_CLOUD_LOCATION)
  2. Vertex + ADC: GOOGLE_CLOUD_PROJECT set and no GEMINI_API_KEY / GOOGLE_API_KEY
  3. API key: GEMINI_API_KEY or GOOGLE_API_KEY (Google AI Studio / Gemini API)
"""

from __future__ import annotations

import base64
import io
import json
import os
import sys


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def _use_vertex_adc() -> bool:
    if _env_truthy("GOOGLE_GENAI_USE_VERTEXAI") or _env_truthy("TECH_DIAGRAMS_USE_ADC"):
        return True
    has_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    return bool(os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")) and not has_key


def _make_client():
    from google import genai

    if _use_vertex_adc():
        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        if not project:
            print(
                "ERROR: Vertex/ADC mode requires GOOGLE_CLOUD_PROJECT "
                "(or set GEMINI_API_KEY for API-key mode).",
                file=sys.stderr,
            )
            sys.exit(1)
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        print(f"Using Vertex AI with ADC (project={project}, location={location})")
        return genai.Client(vertexai=True, project=project, location=location)

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(
            "ERROR: Set GOOGLE_CLOUD_PROJECT for ADC/Vertex, or GEMINI_API_KEY for API-key mode.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("Using Gemini API with API key")
    return genai.Client(api_key=api_key)


def _load_request(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _build_config(body: dict):
    from google.genai import types

    gen = body.get("generationConfig") or {}
    modalities = gen.get("responseModalities") or ["TEXT", "IMAGE"]
    image_cfg = gen.get("imageConfig") or {}
    aspect = image_cfg.get("aspectRatio", "16:9")
    image_size = image_cfg.get("imageSize")

    return types.GenerateContentConfig(
        response_modalities=modalities,
        image_config=types.ImageConfig(aspect_ratio=aspect, image_size=image_size),
    )


def _normalize_contents(contents: list) -> list:
    """Vertex + google.genai require role on each content (user/model)."""
    normalized = []
    for item in contents:
        if isinstance(item, dict):
            entry = dict(item)
            if "role" not in entry:
                entry["role"] = "user"
            normalized.append(entry)
        else:
            normalized.append(item)
    return normalized


def _save_image(data: bytes, output_path: str, mime_type: str | None) -> int:
    """Save bytes in the format promised by the output filename."""
    suffix = os.path.splitext(output_path)[1].lower()
    expected = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG"}.get(suffix)
    actual = (mime_type or "").lower()
    magic_is_png = data.startswith(b"\x89PNG\r\n\x1a\n")
    magic_is_jpeg = data.startswith(b"\xff\xd8\xff")
    matches = (
        (expected == "PNG" and (actual == "image/png" or magic_is_png))
        or (expected == "JPEG" and (actual in ("image/jpeg", "image/jpg") or magic_is_jpeg))
    )

    if expected and not matches:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as image:
            if expected == "JPEG" and image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            image.save(output_path, format=expected)
        return os.path.getsize(output_path)

    with open(output_path, "wb") as stream:
        stream.write(data)
    return len(data)


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(1)

    request_path = sys.argv[1]
    output_path = sys.argv[2]
    model = (
        sys.argv[3]
        if len(sys.argv) > 3
        else os.environ.get("TECH_DIAGRAMS_MODEL", "gemini-3.1-flash-image-preview")
    )

    body = _load_request(request_path)
    client = _make_client()
    config = _build_config(body)

    contents = _normalize_contents(body["contents"])

    print(f"Generating diagram with {model}...")
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    saved = False
    for part in response.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            data = inline.data
            if isinstance(data, str):
                data = base64.b64decode(data)
            mime_type = getattr(inline, "mime_type", None)
            saved_bytes = _save_image(data, output_path, mime_type)
            print(f"Saved: {output_path} ({saved_bytes:,} bytes; source {mime_type or 'unknown MIME'})")
            saved = True
        elif getattr(part, "text", None):
            print(part.text[:500])

    if not saved:
        print("ERROR: No image data in response", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
