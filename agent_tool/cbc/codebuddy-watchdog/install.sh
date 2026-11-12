#!/usr/bin/env bash
# Installs codebuddy-watchdog into CodeBuddy Code.
#
#   ./install.sh                 install + enable, keep the default 60s/50-check limits
#   ./install.sh --dry-run       print every command, change nothing
#   ./install.sh --state-dir DIR put the state mirror/log/config in DIR
#   ./install.sh --uninstall     same as ./uninstall.sh
#
# Everything it touches is listed by `bin/watchdogctl where`, and every file it
# overwrites gets a timestamped .bak copy next to it.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CBC_BIN="${CODEBUDDY_BIN:-codebuddy}"
PLUGIN_NAME="codebuddy-watchdog"
STATE_DIR="${CODEBUDDY_WATCHDOG_STATE_DIR:-$HOME/.codebuddy/watchdog}"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --state-dir) STATE_DIR="$2"; shift 2 ;;
    --uninstall) exec "$HERE/uninstall.sh" "${@:2}" ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

run() {
  if [[ $DRY_RUN -eq 1 ]]; then printf '+ %s\n' "$*"; else "$@"; fi
}

if ! command -v "$CBC_BIN" >/dev/null 2>&1; then
  echo "error: '$CBC_BIN' is not on PATH. Install it first:" >&2
  echo "  npm install -g @tencent-ai/codebuddy-code" >&2
  echo "Set CODEBUDDY_BIN=/path/to/codebuddy to use a specific binary." >&2
  exit 1
fi

echo "== 1/5 validate the plugin manifest"
run "$CBC_BIN" plugin validate "$HERE"

echo "== 2/5 back up the settings file (if any)"
SETTINGS="$HOME/.codebuddy/settings.json"
if [[ -f "$SETTINGS" ]]; then
  BACKUP="$SETTINGS.watchdog-backup-$(date +%Y%m%d-%H%M%S)"
  run cp "$SETTINGS" "$BACKUP"
  echo "   backup: $BACKUP"
else
  echo "   no settings.json yet (nothing to back up)"
fi

echo "== 3/5 install and enable the plugin"
run "$CBC_BIN" plugin add "$HERE" --yes

echo "== 4/5 pin the state dir and remember where the plugin landed"
RUNTIME_ROOT=""
if [[ $DRY_RUN -eq 0 ]]; then
  RUNTIME_ROOT="$(find "$HOME/.codebuddy/plugins/cache" -maxdepth 3 -type d -name "$PLUGIN_NAME" 2>/dev/null | sort | tail -1)"
fi
[[ -z "$RUNTIME_ROOT" ]] && RUNTIME_ROOT="$HERE"
echo "   runtime root: $RUNTIME_ROOT"
run mkdir -p "$STATE_DIR"
if [[ $DRY_RUN -eq 0 ]]; then
  python3 - "$RUNTIME_ROOT" "$STATE_DIR" <<'PY'
import json, pathlib, sys
root, state = sys.argv[1], sys.argv[2]
file = pathlib.Path(state) / 'config.json'
data = {}
if file.exists():
    try:
        data = json.loads(file.read_text())
    except Exception:
        data = {}
data['stateDir'] = state
file.write_text(json.dumps(data, indent=2) + '\n')
shipped = pathlib.Path(root) / 'config' / 'watchdog.config.json'
base = json.loads(shipped.read_text())
base['stateDir'] = state
shipped.write_text(json.dumps(base, indent=2) + '\n')
(pathlib.Path(state) / 'pointer.json').write_text(json.dumps({'pluginRoot': root, 'stateDir': state}, indent=2) + '\n')
print(f'   wrote {file}')
print(f'   wrote {shipped}')
PY
else
  echo "   + write stateDir=$STATE_DIR into $STATE_DIR/config.json and $RUNTIME_ROOT/config/watchdog.config.json"
fi

echo "== 5/5 verify"
run "$CBC_BIN" plugin list
if [[ $DRY_RUN -eq 0 ]]; then
  "$HERE/bin/watchdogctl" status || true
fi
cat <<'TXT'

Installed. Next:
  1. keep the hard switch handy:            <plugin>/bin/watchdogctl on|off
  2. in a session:                          /watchdog status | off | reset
  3. after a real session:                  <plugin>/bin/watchdogctl status
  4. everything it touches:                 <plugin>/bin/watchdogctl where
Rollback: ./uninstall.sh   (and restore the .bak files it prints)
TXT
