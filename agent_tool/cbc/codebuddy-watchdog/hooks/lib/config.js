/**
 * Watchdog configuration.
 *
 * Layered, first hit wins:
 *   1. `config/watchdog.config.json` next to the plugin (shipped defaults override)
 *   2. `<stateDir>/config.json` (the person's own file, written by bin/watchdogctl)
 *   3. `CODEBUDDY_WATCHDOG_*` environment variables are NOT read: a mod cannot see
 *      process.env (it runs in the mod sandbox; only the `$` host API is available).
 *
 * Every field is validated; an unusable value falls back to the default and is
 * reported back in `problems` so a bad config is visible instead of silent.
 */

export const DEFAULTS = Object.freeze({
  // master switch; `false` keeps the mod loaded but inert
  enabled: true,
  // how long the session may sit idle after a turn before the watchdog checks in
  timeoutMs: 60000,
  // never two automated checks closer than this (debounce)
  minIntervalMs: 8000,
  // hard stop: this many automated checks per session, then the watchdog stops
  maxChecks: 50,
  // a user action within this window postpones the check instead of racing it
  graceMs: 2000,
  // status-bar refresh period
  tickMs: 1000,
  // force the model through the watchdog_decide tool instead of free text
  requireDecisionTool: true,
  // while a decision is pending, deny every other tool (the decision round works alone)
  blockOtherToolsInDecisionRound: true,
  // postpone while the prompt box holds an unsent draft (the person is typing)
  postponeOnDraft: true,
  // after this many full draft postponements, check anyway to avoid a stale prompt box blocking forever
  maxDraftPostpones: 3,
  // drop watchdog rounds when the conversation is compacted (see README: unverified)
  foldOnCompact: false,
  // mirror state/logs to disk under stateDir (through $.fs, host-mediated)
  logToFile: true,
  // where the state mirror, log and your config.json live.
  // "default" = <plugin root>/state (a mod cannot read $HOME; bin/watchdogctl
  // writes an absolute path here when you point it somewhere else).
  stateDir: 'default',
  // text the model must see as "not user input"
  marker: '[Automated watchdog check'
});

const INT_FIELDS = ['timeoutMs', 'minIntervalMs', 'maxChecks', 'graceMs', 'tickMs', 'maxDraftPostpones'];
const BOOL_FIELDS = ['enabled', 'requireDecisionTool', 'blockOtherToolsInDecisionRound', 'postponeOnDraft', 'foldOnCompact', 'logToFile'];
const STR_FIELDS = ['stateDir', 'marker'];

const INT_BOUNDS = {
  timeoutMs: [1000, 3600000],
  minIntervalMs: [0, 3600000],
  maxChecks: [1, 100000],
  graceMs: [0, 600000],
  tickMs: [500, 60000],
  maxDraftPostpones: [0, 1000]
};

export function normalizeConfig(raw) {
  const problems = [];
  const cfg = { ...DEFAULTS };
  if (raw === undefined || raw === null) return { cfg, problems };
  if (typeof raw !== 'object' || Array.isArray(raw)) {
    problems.push('config root must be a JSON object; using defaults');
    return { cfg, problems };
  }
  for (const key of Object.keys(raw)) {
    const value = raw[key];
    if (BOOL_FIELDS.includes(key)) {
      if (typeof value === 'boolean') cfg[key] = value;
      else problems.push(`${key}: expected boolean, got ${typeOf(value)}; kept default ${DEFAULTS[key]}`);
    } else if (INT_FIELDS.includes(key)) {
      if (typeof value === 'number' && Number.isFinite(value) && Number.isInteger(value)) {
        const [lo, hi] = INT_BOUNDS[key];
        if (value < lo || value > hi) problems.push(`${key}: ${value} outside [${lo}, ${hi}]; kept default ${DEFAULTS[key]}`);
        else cfg[key] = value;
      } else problems.push(`${key}: expected integer, got ${typeOf(value)}; kept default ${DEFAULTS[key]}`);
    } else if (STR_FIELDS.includes(key)) {
      if (typeof value === 'string' && value.trim() !== '') cfg[key] = value;
      else problems.push(`${key}: expected non-empty string, got ${typeOf(value)}; kept default ${JSON.stringify(DEFAULTS[key])}`);
    } else {
      problems.push(`unknown key "${key}" ignored`);
    }
  }
  return { cfg, problems };
}

export function parseConfigText(text, source) {
  const problems = [];
  if (typeof text !== 'string' || text.trim() === '') return { raw: undefined, problems };
  try {
    return { raw: JSON.parse(text), problems };
  } catch (error) {
    problems.push(`${source}: not valid JSON (${error.message}); ignored`);
    return { raw: undefined, problems };
  }
}

export function mergeConfigs(base, override) {
  return { ...base, ...override };
}

function typeOf(value) {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  return typeof value;
}
