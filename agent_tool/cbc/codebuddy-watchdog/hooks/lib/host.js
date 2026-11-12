/**
 * Host adapter: turns the `$` API into the small `io` surface the state machine
 * needs. Everything here goes through the documented mod API — no Node builtin,
 * no direct file system, no shell (a mod module is bundled in a sandbox where a
 * bare `node:` import is refused: "Mod import node:fs is unavailable; use the $
 * host API").
 */

/** Resolves `~` and relative state dirs against the plugin root (the only
 *  absolute path a mod is guaranteed to know). */
export function resolveStateDir(cfg, pluginRoot) {
  const raw = String(cfg.stateDir || '').trim();
  const root = String(pluginRoot || '.').replace(/\/+$/, '');
  if (raw === '' || raw === 'default') return `${root}/state`;
  if (raw.startsWith('~/')) return `${root}/state${raw.slice(1)}`.replace(/\/\.\//g, '/');
  if (raw.startsWith('/')) return raw.replace(/\/+$/, '');
  return `${root}/${raw}`.replace(/\/+/g, '/');
}

export function createHost({ $, cfg, sessionId, stateDir, onConfigProblem }) {
  const logFile = `${stateDir}/watchdog.log`;
  const stateFile = `${stateDir}/state.json`;
  let buffer = [];
  let logChain = Promise.resolve();
  let lastPersist = 0;
  let persistChain = Promise.resolve();
  const pending = new Set();
  let storeBroken = false;
  const counters = { errors: 0, dropped: 0 };

  function stamp() {
    return new Date(Date.now()).toISOString();
  }

  function line(level, event, data) {
    let detail = '';
    if (data !== undefined && data !== null) {
      try {
        detail = ' ' + JSON.stringify(data);
      } catch {
        detail = ' {"note":"unserialisable"}';
      }
    }
    return `${stamp()} [${level}] ${event}${detail} session=${sessionId || '?'}`;
  }

  function flush() {
    if (buffer.length === 0) return logChain;
    const batch = buffer.splice(0, buffer.length);
    logChain = logChain.then(async () => {
      try {
        const previous = await readOr($, logFile, '');
        const lines = previous.split('\n').filter(Boolean).concat(batch);
        const kept = lines.slice(-600);
        await $.fs.write(logFile, kept.join('\n') + '\n');
      } catch {
        counters.errors += 1;
        counters.dropped += batch.length;
      }
    });
    return logChain.then(() => (buffer.length > 0 ? flush() : undefined));
  }

  const io = {
    now: () => Date.now(),
    setTimer(ms, fn) {
      try {
        return $.clock.after(ms, fn);
      } catch (error) {
        io.log('error', 'timer_failed', { message: String(error && error.message ? error.message : error) });
        return { cancel() {} };
      }
    },
    clearTimer(handle) {
      try {
        if (handle && typeof handle.cancel === 'function') handle.cancel();
      } catch {
        /* a cancelled timer is not an error */
      }
    },
    async sendPrompt(text) {
      // The documented way to make a turn: prompt.submit, not a keystroke.
      // `asUser` is left out on purpose: the model must see the plugin frame.
      await $.prompt.submit({ text });
    },
    log(level, event, data) {
      buffer.push(line(level, event, data));
      void flush();
    },
    status() {
      // Timers outlive the hook dispatch. Calling $.ui.* here is denied by
      // CodeBuddy after the hook completes, so runtime status is file-only.
    },
    persist(snapshot) {
      // Every state change is written; the snapshot is small and the store API
      // is the documented durable home. No throttle: a dropped final write would
      // lose the stop reason (the one thing a person looks at).
      const now = Date.now();
      lastPersist = now;
      const record = { ...snapshot, sessionId, updatedAt: new Date(now).toISOString(), config: cfg };
      const text = JSON.stringify(record, null, 2) + '\n';
      const write = persistChain.then(async () => {
        // 1. the file mirror (works in every probe so far)
        try {
          await $.fs.write(stateFile, text);
        } catch (error) {
          counters.errors += 1;
          io.log('warn', 'persist_file_failed', { message: String(error && error.message ? error.message : error) });
        }
        // 2. the plugin store, as the durable cross-session copy. It rejected a
        //    plain snapshot in the 2.176.0 probe ("value is not JSON data"),
        //    so a JSON round-trip is tried once and a refusal is logged, never
        //    thrown: the file mirror already holds the state.
        if (storeBroken) return;
        try {
          await $.store.set('watchdog:state', JSON.parse(text));
        } catch (error) {
          storeBroken = true;
          counters.errors += 1;
          io.log('warn', 'persist_store_unavailable', {
            message: String(error && error.message ? error.message : error),
            fallback: 'state file mirror'
          });
        }
      });
      persistChain = write.catch(() => {});
      pending.add(write);
      write.finally(() => pending.delete(write));
      return write;
    },
    async settle() {
      // Awaits every write still in flight (session.end uses it so the state
      // mirror on disk is complete before the process goes away).
      for (let i = 0; i < 20 && pending.size > 0; i += 1) {
        await Promise.allSettled([...pending]);
      }
      await flush();
    },
    flush
  };

  return {
    io,
    logFile,
    stateFile,
    async readConfigFile(path) {
      try {
        const text = await $.fs.read(path);
        const parsed = parseConfigTextLoose(text, path);
        if (parsed.problems.length > 0) {
          for (const problem of parsed.problems) {
            io.log('warn', 'config_problem', { problem });
            if (onConfigProblem) onConfigProblem(problem);
          }
        }
        return parsed.raw;
      } catch {
        return undefined;
      }
    },
    async readStoredState() {
      try {
        return await $.store.get('watchdog:state');
      } catch {
        return undefined;
      }
    },
    counters
  };
}

export function safeCall(fn) {
  try {
    const result = fn();
    if (result && typeof result.catch === 'function') result.catch(() => {});
    return result;
  } catch {
    return undefined;
  }
}

function parseConfigTextLoose(text, source) {
  try {
    return { raw: JSON.parse(text), problems: [] };
  } catch (error) {
    return { raw: undefined, problems: [`${source}: not valid JSON (${error.message}); ignored`] };
  }
}

async function readOr($, path, fallback) {
  try {
    return await $.fs.read(path);
  } catch {
    return fallback;
  }
}
