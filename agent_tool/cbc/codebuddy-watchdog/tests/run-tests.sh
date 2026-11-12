#!/usr/bin/env bash
# Runs everything that can be checked without a logged-in CodeBuddy session and
# writes one log per step under tests/logs/.
#   ./tests/run-tests.sh                 unit + scenario tests only
#   CBC_BIN=codebuddy ./tests/run-tests.sh --with-cli   also the real-CLI probe
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
LOGS="$HERE/logs"
mkdir -p "$LOGS"
WITH_CLI=0
[[ "${1:-}" == "--with-cli" ]] && WITH_CLI=1
CBC_BIN="${CBC_BIN:-codebuddy}"
FAILED=0

step() { echo; echo "=== $1"; }
check() { # name, logfile
  if [[ $? -eq 0 ]]; then echo "PASS  $1"; else echo "FAIL  $1  (see $2)"; FAILED=1; fi
}

step "syntax: every JS module parses"
for f in "$ROOT"/hooks/index.js "$ROOT"/hooks/lib/*.js "$ROOT"/bin/watchdogctl "$ROOT"/tests/*.mjs; do
  node --check "$f" >>"$LOGS/syntax.log" 2>&1
done
check "node --check" "$LOGS/syntax.log"

step "watchdogctl: null trail entries do not break status"
CTL_HOME="$LOGS/watchdogctl-home"
rm -rf "$CTL_HOME"
mkdir -p "$CTL_HOME/.codebuddy/watchdog" "$CTL_HOME/plugin/config"
printf '{"pluginRoot":"%s","stateDir":"%s"}\n' "$CTL_HOME/plugin" "$CTL_HOME/.codebuddy/watchdog" > "$CTL_HOME/.codebuddy/watchdog/pointer.json"
printf '{"stateDir":"default"}\n' > "$CTL_HOME/plugin/config/watchdog.config.json"
printf '{"stateDir":"%s"}\n' "$CTL_HOME/.codebuddy/watchdog" > "$CTL_HOME/.codebuddy/watchdog/config.json"
printf '{"phase":"idle","checks":0,"continuations":0,"postpones":0,"skips":0,"stopReason":null,"sessionId":"test","updatedAt":"now","trail":[null,{"kind":"ready"},null]}\n' > "$CTL_HOME/.codebuddy/watchdog/state.json"
HOME="$CTL_HOME" CODEBUDDY_WATCHDOG_PLUGIN_ROOT="$CTL_HOME/plugin" node "$ROOT/bin/watchdogctl" status > "$LOGS/watchdogctl-null.log" 2>&1
grep -q '  - ready' "$LOGS/watchdogctl-null.log"
check "null trail handling" "$LOGS/watchdogctl-null.log"

step "config: defaults, type errors and unknown keys"
node --input-type=module -e "
import { normalizeConfig, DEFAULTS } from '$ROOT/hooks/lib/config.js';
const r = normalizeConfig({ timeoutMs: 'soon', maxChecks: 1000000, nope: 1, enabled: false });
if (r.cfg.timeoutMs !== DEFAULTS.timeoutMs) throw new Error('timeoutMs not clamped');
if (r.cfg.maxChecks !== DEFAULTS.maxChecks) throw new Error('maxChecks not clamped');
if (r.cfg.enabled !== false) throw new Error('enabled not applied');
if (r.problems.length !== 3) throw new Error('expected 3 problems, got ' + r.problems.length);
console.log('ok');
" >"$LOGS/config.log" 2>&1
check "config validation" "$LOGS/config.log"

step "scenarios: 25 cases against the mock host"
node "$ROOT/tests/scenarios.mjs" >"$LOGS/scenarios.log" 2>&1
check "scenario tests" "$LOGS/scenarios.log"

step "packaging: plugin package layout"
python3 - "$ROOT" >"$LOGS/layout.log" 2>&1 <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
manifest = json.loads((root/'.codebuddy-plugin'/'plugin.json').read_text())
assert manifest['name'] == 'codebuddy-watchdog', manifest
hooks = json.loads((root/'hooks'/'hooks.json').read_text())
assert hooks['modules'] == ['./index.js'], hooks
pkg = json.loads((root/'package.json').read_text())
assert pkg['type'] == 'module'
src = (root/'hooks'/'index.js').read_text()
for banned in ["require('node:", 'require("node:', "from 'node:"]:
    assert banned not in src, f'mod sandbox forbids node builtins: {banned}'
print('ok')
PY
check "package layout" "$LOGS/layout.log"

if [[ $WITH_CLI -eq 1 ]]; then
  step "real CLI: manifest validation + mod load probe"
  "$ROOT/tests/real-cli.sh" >"$LOGS/real-cli.log" 2>&1
  check "real CLI probe" "$LOGS/real-cli.log"
fi

echo
if [[ $FAILED -eq 0 ]]; then echo "ALL CHECKS PASSED (logs in $LOGS)"; else echo "SOME CHECKS FAILED (logs in $LOGS)"; fi
exit $FAILED
