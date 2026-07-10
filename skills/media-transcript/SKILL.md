---
name: media-transcript
description: Transcribe local video or audio files into text using ffmpeg plus Alibaba DashScope ASR. Use only when the user asks to process a local video/audio file, extract a transcript, convert media speech to text, or generate a text稿/文稿/subtitle-like plain transcript. Do not use for URL downloading, web scraping, Douyin link parsing, PDFs, images, or general text files.
---

# Media Transcript

## Overview

Use this skill to transcribe local video/audio files. The workflow is intentionally narrow: normalize media to 16 kHz mono WAV with `ffmpeg`, call DashScope `fun-asr-realtime`, and write transcript artifacts.

## Quick Start

Run from this skill directory or replace `.\scripts\transcribe_media.py` with the installed script path:

```powershell
python .\scripts\transcribe_media.py "<absolute-path-to-video-or-audio>"
```

Specify output directory:

```powershell
python .\scripts\transcribe_media.py "<absolute-path-to-media>" --output-dir "<output-dir>"
```

## Inputs

Supported local media extensions:

- Video: `.mp4`, `.mov`, `.mkv`, `.avi`, `.flv`, `.webm`, `.m4v`
- Audio: `.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, `.ogg`, `.opus`, `.wma`

Reject non-media paths by default. This skill is not a downloader and should not accept Douyin/share URLs.

## Outputs

The script writes:

- `audio.wav` — normalized 16 kHz mono WAV used for ASR.
- `transcript.txt` — plain transcript text.
- `sentences.json` — raw sentence-level ASR payload when available.
- `manifest.json` — input/output metadata.

## Requirements

Install the Python dependency:

```powershell
python -m pip install -r .\requirements.txt
```

System requirements:

- `ffmpeg` must be on `PATH`.
- `DASHSCOPE_API_KEY` must be set, or pass `--api-key`.

## API Key Setup

The script reads the Alibaba Cloud DashScope key from `DASHSCOPE_API_KEY` by default.

For a one-time PowerShell session:

```powershell
$env:DASHSCOPE_API_KEY = "<your-dashscope-api-key>"
```

For a persistent Windows user environment variable:

```powershell
[Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "<your-dashscope-api-key>", "User")
```

Restart terminals, IDEs, Claude Code, or Codex after setting the persistent variable so new processes inherit it.

To verify the current shell can read it:

```powershell
echo $env:DASHSCOPE_API_KEY
```

Do not commit real API keys into this repository. Use `--api-key KEY` only for a local one-off run when environment variables are not available.

## Options

- `--api-key KEY` supplies DashScope API key for one run.
- `--model MODEL` defaults to `fun-asr-realtime`.
- `--sample-rate 16000` defaults to the source workflow's 16 kHz.
- `--keep-audio` keeps `audio.wav`; this is enabled by default.
- `--delete-audio` removes normalized audio after successful transcription.

## Rules

- Use only for local video/audio transcription.
- Do not use this skill for downloading Douyin links; prepare the media file first.
- If transcription succeeds, read `transcript.txt` before summarizing or restructuring the transcript.
- If transcription fails, report the missing dependency, API error, or `ffmpeg` error exactly.
