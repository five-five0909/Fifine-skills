#!/usr/bin/env bash
# Removes codebuddy-watchdog. Your config and logs under the state dir are kept
# unless you pass --purge. Prints every backup it made.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CBC_BIN="${CODEBUDDY_BIN:-codebuddy}"
PURGE=0
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --purge) PURGE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
run() { if [[ $DRY_RUN -eq 1 ]]; then printf '+ %s\n' "$*"; else "$@"; fi; }

echo "== disable + remove"
if command -v "$CBC_BIN" >/dev/null 2>&1; then
  run "$CBC_BIN" plugin disable codebuddy-watchdog || true
  # 2.176.0 refuses `plugin uninstall` for a locally added plugin
  # ("Marketplace undefined is not found"), so the cache entry is removed below.
  run "$CBC_BIN" plugin uninstall codebuddy-watchdog || true
else
  echo "   '$CBC_BIN' not found; removing files only"
fi

echo "== strip installed_plugins.json entries"
if [[ $DRY_RUN -eq 0 ]]; then
  python3 - <<'PY'
import json, os, pathlib, time
p = pathlib.Path(os.path.expanduser('~/.codebuddy/plugins/installed_plugins.json'))
if p.exists():
    backup = p.with_name(p.name + f'.watchdog-backup-{int(time.time())}')
    backup.write_text(p.read_text())
    data = json.loads(p.read_text() or '{}')
    def strip(v):
        if isinstance(v, list): return [x for x in v if not str(x).startswith('codebuddy-watchdog')]
        if isinstance(v, dict):
            for k in list(v):
                if k.startswith('codebuddy-watchdog'): del v[k]
                else: v[k] = strip(v[k])
        return v
    p.write_text(json.dumps(strip(data), indent=2) + '\n')
    print(f'   backup: {backup}')
PY
fi

echo "== remove cache copies"
if [[ $DRY_RUN -eq 0 ]]; then
  find "$HOME/.codebuddy/plugins/cache" -maxdepth 3 -type d -name codebuddy-watchdog -print -exec rm -rf {} + 2>/dev/null || true
fi

if [[ $PURGE -eq 1 ]]; then
  echo "== purge state dir"
  run rm -rf "$HOME/.codebuddy/watchdog"
fi
echo "Done. Any settings.json.watchdog-backup-* file is yours to delete once you are happy."
