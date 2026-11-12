#!/usr/bin/env bash
# The part that needs the real binary. It uses a throwaway HOME so nothing in
# your own setup is touched, and it needs no login: the mod engine loads and
# fires session.start before the auth gate.
#
#   CBC_BIN=codebuddy ./tests/real-cli.sh
# Env: CBC_BIN (default: codebuddy)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
CBC_BIN="${CBC_BIN:-codebuddy}"
command -v "$CBC_BIN" >/dev/null || { echo "SKIP: '$CBC_BIN' not on PATH"; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export HOME="$TMP/home"
export CODEBUDDY_CONFIG_DIR="$HOME/.codebuddy"
mkdir -p "$HOME"

echo "== $("$CBC_BIN" --version) at $(command -v "$CBC_BIN")"
echo "== plugin validate"
"$CBC_BIN" plugin validate "$ROOT" | tail -4
echo "== plugin add --yes"
"$CBC_BIN" plugin add "$ROOT" --yes | tail -3
echo "== one -p run (auth will fail; the mod still loads and boots)"
"$CBC_BIN" -p "watchdog probe" 2>&1 | head -3 || true

STATE="$(find "$HOME/.codebuddy/plugins/cache" -maxdepth 6 -type d -name state 2>/dev/null | head -1)"
echo "== state dir: ${STATE:-<none>}"
if [[ -n "${STATE:-}" && -f "$STATE/watchdog.log" ]]; then
  echo "== watchdog.log"; cat "$STATE/watchdog.log"
else
  echo "== no watchdog.log (the mod did not reach session.start)"
fi
LOG="$(ls -t "$HOME"/.codebuddy/logs/*/*.log 2>/dev/null | head -1 || true)"
if [[ -n "${LOG:-}" ]]; then
  echo "== engine view of the mod"
  grep -i 'mods:' "$LOG" | tail -5 || true
fi
