/**
 * A mock CodeBuddy mod host: the same shape the real engine gives a hooks module
 * (`register(on, options)` + `$`), with a virtual clock so a 60 s countdown runs
 * instantly. Used by the scenario tests; it is NOT the CLI.
 */
import { register } from '../hooks/index.js';

export function createHarness({ root = '/tmp/fake-plugin', files = {}, store = {}, options = {}, sessionId = 'test-session', promptText = '', denyUi = false } = {}) {
  let now = Date.parse('2026-10-26T00:00:00Z');
  const realNow = Date.now;
  const timers = new Set();
  const timersEvery = new Set();
  const sent = [];
  const logs = [];
  const statuses = [];
  const uiLogs = [];
  const registeredTools = [];
  const registeredCommands = [];
  const fs = new Map(Object.entries(files));
  let timerSeq = 0;

  Date.now = () => now;

  const $ = {
    plugin: { name: 'codebuddy-watchdog', root },
    session: {
      id: async () => sessionId,
      cwd: async () => '/tmp/project'
    },
    store: {
      get: async (key) => store[key],
      set: async (key, value) => {
        store[key] = value;
      },
      delete: async (key) => {
        delete store[key];
      },
      keys: async () => Object.keys(store)
    },
    fs: {
      read: async (path) => {
        const key = normalise(path);
        if (!fs.has(key)) throw new Error(`ENOENT: ${path}`);
        return fs.get(key);
      },
      write: async (path, text) => {
        fs.set(normalise(path), text);
      },
      exists: async (path) => fs.has(normalise(path)),
      list: async () => [],
      stat: async () => ({ kind: 'file', size: 0, mtimeMs: now, isLink: false })
    },
    clock: {
      now: async () => now,
      sleep: async (ms) => advance(ms),
      after: (ms, fn) => {
        const timer = { id: ++timerSeq, at: now + ms, fn, kind: 'after' };
        timers.add(timer);
        return { cancel: () => timers.delete(timer) };
      },
      every: (ms, fn) => {
        const timer = { id: ++timerSeq, at: now + ms, fn, period: ms, kind: 'every' };
        timersEvery.add(timer);
        return { cancel: () => timersEvery.delete(timer) };
      }
    },
    ui: {
      log: (text) => { if (denyUi) throw new Error('$.ui.log denied'); uiLogs.push(text); },
      status: (text) => { if (denyUi) throw new Error('$.ui.status denied'); statuses.push(text); },
      notice: () => { if (denyUi) throw new Error('$.ui.notice denied'); }
    },
    prompt: {
      submit: async ({ text }) => {
        sent.push(text);
        return { submitted: true };
      },
      read: async () => ({ text: promptText, cursor: promptText.length }),
      fill: async () => ({ isFilled: false }),
      suggest: async () => ({ isShown: false })
    },
    tool: {
      register: async (tool) => {
        registeredTools.push(tool);
        return { tool: `mcp__codebuddy-watchdog__${tool.name}` };
      },
      unregister: async () => {},
      call: async () => ({}),
      check: async () => ({ decision: 'allow' })
    },
    command: {
      register: async (command) => {
        registeredCommands.push(command);
      },
      run: async () => ({ text: '' }),
      list: async () => registeredCommands
    },
    sessionSend: async () => ({ isDelivered: true })
  };

  const hooks = [];
  function on(name, matcherOrHandler, maybeHandler) {
    const matcher = typeof matcherOrHandler === 'function' ? undefined : matcherOrHandler;
    const handler = typeof matcherOrHandler === 'function' ? matcherOrHandler : maybeHandler;
    hooks.push({ name: String(name), matcher, handler });
  }

  register(on, options);

  function normalise(path) {
    return String(path).replace(/^\/tmp\/fake-plugin/, '').replace(/\/+/g, '/');
  }

  const next = (event) => Promise.resolve(event);

  async function emit(name, event, matcherValue) {
    let last = event;
    for (const hook of hooks.filter((h) => h.name === name)) {
      if (hook.matcher && matcherValue === undefined) continue;
      if (hook.matcher && Object.entries(hook.matcher).some(([k, v]) => matcherValue[k] !== v)) continue;
      const result = await hook.handler($, last, (replacement) => {
        last = replacement === undefined ? last : replacement;
        return Promise.resolve(last);
      });
      if (result !== undefined) last = result;
    }
    return last;
  }

  async function flush() {
    for (let i = 0; i < 6; i += 1) await new Promise((r) => setImmediate(r));
  }

  async function advance(ms) {
    const target = now + ms;
    for (;;) {
      const due = [...timers].filter((t) => t.at <= target).sort((a, b) => a.at - b.at)[0];
      const dueEvery = [...timersEvery].filter((t) => t.at <= target).sort((a, b) => a.at - b.at)[0];
      if (!due && !dueEvery) break;
      if (dueEvery && (!due || dueEvery.at <= due.at)) {
        now = dueEvery.at;
        timersEvery.delete(dueEvery);
        await dueEvery.fn();
        dueEvery.at = now + dueEvery.period;
        timersEvery.add(dueEvery);
      } else {
        now = due.at;
        timers.delete(due);
        await due.fn();
      }
      await flush();
    }
    now = target;
    await flush();
  }

  function restore() {
    Date.now = realNow;
    timers.clear();
    timersEvery.clear();
  }

  return {
    $,
    on,
    emit,
    advance,
    flush,
    restore,
    sent,
    logs,
    statuses,
    uiLogs,
    registeredTools,
    registeredCommands,
    files: fs,
    store,
    radius: { hooks },
    pendingTimers: () => timers.size + timersEvery.size
  };
}
