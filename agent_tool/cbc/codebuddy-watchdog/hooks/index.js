/**
 * codebuddy-watchdog — a CodeBuddy Code (cbc) mod that sends one automated
 * "continue" when the session goes quiet, then makes the model decide through a
 * tool instead of guessing from prose. Port of GreenHatHG's
 * pi-extension-watchdog (Pi Coding Agent) onto the CodeBuddy mod API.
 *
 * Every host call below is from the vendored `codebuddy-code` mod API
 * (types/codebuddy-code.d.ts in @tencent-ai/codebuddy-code 2.176.0).
 */
import { createWatchdog, PHASE, DECISION, TOOL_NAME, checkPrompt } from './lib/machine.js';
import { normalizeConfig, mergeConfigs } from './lib/config.js';
import { createHost, resolveStateDir, safeCall } from './lib/host.js';

const PLUGIN = 'codebuddy-watchdog';

export function register(on, options) {
  let dog = null;
  let cfg = null;
  let host = null;
  let stateDir = null;
  let booting = null;
  let ticker = null;
  let currentSessionId = null;
  const problems = [];
  const pluginOptions = options && typeof options === 'object' ? options : {};

  async function boot($) {
    if (dog) return dog;
    if (booting) return booting;
    booting = (async () => {
      const root = $.plugin && $.plugin.root ? $.plugin.root : '.';
      const bootstrap = createHost({ $, cfg: { stateDir: 'default' }, sessionId: null, stateDir: `${String(root).replace(/\/+$/, '')}/state` });
      // 1. shipped defaults, 2. the person's own file inside the state dir
      const shippedRaw = await bootstrap.readConfigFile(`${root}/config/watchdog.config.json`);
      const shipped = normalizeConfig(shippedRaw);
      problems.push(...shipped.problems);
      const dir = resolveStateDir(shipped.cfg, root);
      stateDir = dir;
      const userRaw = await bootstrap.readConfigFile(`${dir}/config.json`);
      // A missing user file must not erase the shipped defaults: only a file
      // that exists and parses contributes overrides.
      const user = userRaw === undefined ? { cfg: {}, problems: [] } : normalizeConfig(userRaw);
      problems.push(...user.problems);
      const merged = normalizeConfig(mergeConfigs(shipped.cfg, user.cfg));
      cfg = merged.cfg;
      if (pluginOptions.enabled === false) cfg = { ...cfg, enabled: false };

      currentSessionId = await safe(() => $.session.id(), null);
      host = createHost({
        $,
        cfg,
        sessionId: currentSessionId,
        stateDir: dir,
        onConfigProblem: (problem) => problems.push(problem)
      });
      for (const problem of problems) host.io.log('warn', 'config_problem', { problem });
      dog = createWatchdog(cfg, host.io);
      dog.setTier(pluginOptions.tier || 'user');

      if (cfg.logToFile === false) {
        // A mod timer may run after hook dispatch, when every $.ui.* call is
        // denied. Keep counters/state only when file logging is disabled.
        host.io.log = () => {};
      }

      const previous = await host.readStoredState();
      // Make the boot itself observable: the state mirror and the first log line
      // exist before any turn runs, so a person can tell "loaded" from "silent".
      host.io.persist(dog.snapshot());
      host.io.log('info', 'ready', {
        timeoutMs: cfg.timeoutMs,
        maxChecks: cfg.maxChecks,
        enabled: cfg.enabled,
        stateDir: dir,
        previousSession: previous && previous.sessionId ? previous.sessionId : null,
        version: '1.0.0'
      });
      await host.io.settle();
      return dog;
    })();
    return booting;
  }

  async function ensure($) {
    try {
      return await boot($);
    } catch (error) {
      // Failing open: a broken watchdog must never block the session.
      return null;
    }
  }

  function toolNameOf(event) {
    return event && (event.tool || event.name || event.toolName || (event.call && event.call.name)) || '';
  }

  function isDecisionTool(name) {
    return name === TOOL_NAME || name === `mcp__${PLUGIN}__${TOOL_NAME}` || String(name).endsWith(`__${TOOL_NAME}`);
  }

  function originOf(event) {
    const origin = event && event.origin;
    if (!origin) return 'user';
    const kind = typeof origin === 'string' ? origin : origin.kind;
    if (['user', 'model', 'composer', 'bridge', 'sdk', 'slack-ping'].includes(kind)) return 'user';
    return kind || 'plugin';
  }

  on('session.start', async ($, event, next) => {
    const dogRef = await ensure($);
    if (dogRef) {
      try {
        await $.tool.register({
          name: TOOL_NAME,
          description:
            'The only answer to an automated watchdog check. Call it exactly once per check: ' +
            'decision="continue" if work remains, "wait_user" if you need the person, "done" if the request is complete.',
          inputSchema: {
            type: 'object',
            additionalProperties: false,
            required: ['decision'],
            properties: {
              decision: { type: 'string', enum: [DECISION.WAIT_USER, DECISION.DONE, DECISION.CONTINUE] },
              note: { type: 'string', description: 'one short line: what is left, or what you need' }
            }
          }
        });
        await $.command.register({ name: 'watchdog', description: 'watchdog: status | on | off | reset' });
      } catch (error) {
        host.io.log('error', 'register_failed', { message: String(error && error.message ? error.message : error) });
      }
      if (ticker === null) {
        try {
          ticker = $.clock.every(cfg.tickMs, async () => {
            // The 1 s ticker does what pi's ticker does: refresh the status line
            // and notice a draft in the prompt box (the person is typing), which
            // is the CodeBuddy equivalent of editorHasText.
            if (cfg.postponeOnDraft) {
              try {
                const box = await $.prompt.read();
                dogRef.setDraft(Boolean(box && typeof box.text === 'string' && box.text.trim() !== ''));
              } catch {
                /* a -p run draws no prompt box */
              }
            }
            dogRef.tick();
          });
        } catch (error) {
          host.io.log('warn', 'ticker_failed', { message: String(error && error.message ? error.message : error) });
        }
      }
    }
    return next(event);
  });

  on('turn.complete', async ($, event, next) => {
    const dogRef = await ensure($);
    if (dogRef) dogRef.onTurnComplete(event && event.reason ? event.reason : 'answer');
    return next(event);
  });

  on('prompt.submit', async ($, event, next) => {
    const dogRef = await ensure($);
    if (dogRef) {
      dog.onPromptSubmit({
        text: event && event.text,
        origin: originOf(event),
        internal: !!(event && event.internal)
      });
    }
    return next(event);
  });

  // The decision round: accept the registered short name and the model-facing fully-qualified name.
  on('tool.call', async ($, event, next) => {
    const dogRef = await ensure($);
    if (!dogRef || !cfg) return next(event);
    const name = toolNameOf(event);
    if (isDecisionTool(name)) {
      const input = (event && (event.input || event.args)) || {};
      const decision = input.decision;
      const note = typeof input.note === 'string' ? input.note : '';
      if (![DECISION.WAIT_USER, DECISION.DONE, DECISION.CONTINUE].includes(decision)) {
        return { result: { content: `watchdog: unknown decision "${decision}"; use wait_user, done or continue` } };
      }
      const outcome = await dogRef.onDecision(decision, note);
      return { result: { content: `watchdog: ${outcome.message}` } };
    }
    if (dogRef.decisionPending && cfg.requireDecisionTool && cfg.blockOtherToolsInDecisionRound) {
      return {
        deny:
          'The watchdog decision is pending: answer the check with one watchdog_decide call and call no other tool first. ' +
          'Real work happens after you choose continue.'
      };
    }
    return next(event);
  });

  on('command.run', { command: 'watchdog' }, async ($, event) => {
    const dogRef = await ensure($);
    if (!dogRef) return { text: 'watchdog: not running' };
    const raw = (event && (event.args || event.arguments || event.text)) || '';
    const action = String(raw).trim().split(/\s+/)[0] || 'status';
    if (action === 'on') {
      dog.enable();
      return { text: `watchdog: on (timeout ${cfg.timeoutMs}ms, max ${cfg.maxChecks})` };
    }
    if (action === 'off') {
      dog.disable('manual');
      return { text: 'watchdog: off for this session' };
    }
    if (action === 'reset') {
      dog.reset();
      return { text: 'watchdog: counters reset' };
    }
    const s = dog.snapshot();
    return {
      text: [
        `watchdog: ${cfg.enabled ? 'enabled' : 'disabled'} · phase ${s.phase}`,
        `checks ${s.checks}/${cfg.maxChecks} · continuations ${s.continuations} · postpones ${s.postpones} · missed decisions ${s.skips}`,
        `timeout ${cfg.timeoutMs}ms · grace ${cfg.graceMs}ms · min interval ${cfg.minIntervalMs}ms`,
        s.stopReason ? `stopped: ${s.stopReason}` : 'running',
        `log: ${stateDir}/watchdog.log`
      ].join('\n')
    };
  });

  // Context folding: drop watchdog rounds when the conversation is compacted.
  // Off by default — the mod API exposes no send-time suffix filter, so this is
  // the closest native equivalent (see REPORT: 未验证边界).
  on('session.compact', async ($, event, next) => {
    const dogRef = await ensure($);
    if (!dogRef || !cfg || !cfg.foldOnCompact) return next(event);
    const messages = Array.isArray(event && event.messages) ? event.messages : null;
    if (!messages) return next(event);
    const kept = messages.filter((message) => !containsMarker(message, cfg.marker));
    const dropped = messages.length - kept.length;
    if (dropped > 0) host.io.log('info', 'folded_on_compact', { dropped });
    return next({ ...event, messages: kept });
  });

  on('session.end', async ($, event, next) => {
    if (dog) {
      try {
        dog.shutdown();
      } catch {
        /* nothing left to save */
      }
    }
    if (ticker && typeof ticker.cancel === 'function') {
      try {
        ticker.cancel();
      } catch {
        /* already gone */
      }
      ticker = null;
    }
    if (host) {
      try {
        await host.io.settle();
      } catch {
        /* best effort */
      }
    }
    dog = null;
    cfg = null;
    host = null;
    stateDir = null;
    booting = null;
    currentSessionId = null;
    problems.length = 0;
    return next(event);
  });

  function containsMarker(message, marker) {
    try {
      return JSON.stringify(message).includes(marker);
    } catch {
      return false;
    }
  }
}

function safeJson(value) {
  try {
    return JSON.stringify(value);
  } catch {
    return '"unserialisable"';
  }
}

async function safe(fn, fallback) {
  try {
    const value = await fn();
    return value === undefined || value === null ? fallback : value;
  } catch {
    return fallback;
  }
}
