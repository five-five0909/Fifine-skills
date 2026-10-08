# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- **`scripts/generate.py`** — diagram image generation via `google.genai` with **Vertex ADC** (no API key) or optional `GEMINI_API_KEY` fallback; `generate.sh` delegates to it.

### Changed

- **Gemini Enterprise agent** moved to private [66degrees/tech-diagrams-agent](https://github.com/66degrees/tech-diagrams-agent); this repo is skill + icons only.

### Removed

- **`ge-agent/`** — GE hosting, Terraform, and CI now live in the private agent repository.
