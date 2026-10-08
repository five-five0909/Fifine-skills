#!/bin/bash
# Generate a technical diagram via Gemini 3.1 Flash Image Preview
# Usage: ./generate.sh <prompt_file.json> <output.png> [model]
#
# Delegates to generate.py (API key or Vertex ADC). Keeps this script for SKILL.md compatibility.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "${SCRIPT_DIR}/generate.py" "$@"
