#!/usr/bin/env python3
"""Transcribe local video/audio files with ffmpeg + DashScope ASR."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from http import HTTPStatus
from pathlib import Path
from typing import Any

try:
    import dashscope
    from dashscope.audio.asr import Recognition
except ImportError as exc:  # pragma: no cover - user environment dependent
    print("Missing dependency: dashscope", file=sys.stderr)
    print("Install with: python -m pip install -r <skill>/requirements.txt", file=sys.stderr)
    raise SystemExit(2) from exc


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".m4v"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}
DEFAULT_MODEL = "fun-asr-realtime"
DEFAULT_SAMPLE_RATE = 16000


def safe_stem(path: Path) -> str:
    return "".join(ch if ch not in '<>:"/\\|?*\x00' else "_" for ch in path.stem).strip(" .") or "media"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe one local video/audio file.")
    parser.add_argument("media_path", help="Local video/audio file path.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Default: ./media-transcript-output/<name>-<timestamp>")
    parser.add_argument("--api-key", default=os.getenv("DASHSCOPE_API_KEY"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg executable path or command name.")
    audio_group = parser.add_mutually_exclusive_group()
    audio_group.add_argument("--keep-audio", dest="keep_audio", action="store_true", default=True, help="Keep normalized audio.wav. This is the default.")
    audio_group.add_argument("--delete-audio", dest="keep_audio", action="store_false", help="Delete audio.wav after successful transcription.")
    return parser.parse_args()


def classify_media(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    supported = ", ".join(sorted(VIDEO_EXTENSIONS | AUDIO_EXTENSIONS))
    raise ValueError(f"Unsupported file extension '{ext}'. This skill only handles local video/audio files: {supported}")


def ensure_ffmpeg(ffmpeg: str) -> None:
    if Path(ffmpeg).exists() or shutil.which(ffmpeg):
        return
    raise FileNotFoundError("ffmpeg not found on PATH. Install ffmpeg or pass --ffmpeg <path>.")


def normalize_audio(input_path: Path, output_wav: Path, sample_rate: int, ffmpeg: str) -> None:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-acodec",
        "pcm_s16le",
        str(output_wav),
        "-loglevel",
        "error",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg failed without stderr")


def extract_text(sentences: Any) -> str:
    if isinstance(sentences, list):
        return "".join(str(item.get("text", "")) for item in sentences if isinstance(item, dict))
    if isinstance(sentences, dict):
        return str(sentences.get("text", ""))
    if sentences is None:
        return ""
    return str(sentences)


def transcribe(audio_path: Path, api_key: str, model: str, sample_rate: int) -> tuple[str, Any]:
    dashscope.api_key = api_key
    recognition = Recognition(model=model, format="wav", sample_rate=sample_rate, callback=None)
    result = recognition.call(str(audio_path))
    if result.status_code != HTTPStatus.OK:
        raise RuntimeError(getattr(result, "message", None) or str(result))
    sentences = result.get_sentence()
    return extract_text(sentences), sentences


def main() -> int:
    args = parse_args()
    media_path = Path(args.media_path).expanduser().resolve()
    if not media_path.exists():
        print(f"ERROR: File not found: {media_path}", file=sys.stderr)
        return 1
    if not media_path.is_file():
        print(f"ERROR: Not a file: {media_path}", file=sys.stderr)
        return 1
    if not args.api_key:
        print("ERROR: Missing DashScope API key. Set DASHSCOPE_API_KEY or pass --api-key.", file=sys.stderr)
        return 2

    try:
        media_type = classify_media(media_path)
        ensure_ffmpeg(args.ffmpeg)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd() / "media-transcript-output" / f"{safe_stem(media_path)}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / "audio.wav"
    transcript_path = output_dir / "transcript.txt"
    sentences_path = output_dir / "sentences.json"
    manifest_path = output_dir / "manifest.json"

    try:
        print(f"Input: {media_path}")
        print(f"Detected media type: {media_type}")
        print(f"Normalizing audio: {audio_path}")
        normalize_audio(media_path, audio_path, args.sample_rate, args.ffmpeg)
        print("Transcribing with DashScope ASR...")
        text, sentences = transcribe(audio_path, args.api_key, args.model, args.sample_rate)
        transcript_path.write_text(text, encoding="utf-8")
        sentences_path.write_text(json.dumps(sentences, ensure_ascii=False, indent=2), encoding="utf-8")
        if not args.keep_audio:
            audio_path.unlink(missing_ok=True)
        manifest = {
            "input": str(media_path),
            "mediaType": media_type,
            "model": args.model,
            "sampleRate": args.sample_rate,
            "outputDir": str(output_dir),
            "audio": str(audio_path) if audio_path.exists() else None,
            "transcript": str(transcript_path),
            "sentences": str(sentences_path),
            "charCount": len(text),
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Done.")
    print(f"Output dir: {output_dir}")
    print(f"Transcript: {transcript_path}")
    print(f"Characters: {len(text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
