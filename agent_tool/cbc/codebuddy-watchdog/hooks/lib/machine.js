/**
 * The watchdog state machine: pure logic, no host API, no timers of its own.
 *
 * Every side effect arrives through the `io` object so the whole decision table
 * can be unit-tested without CodeBuddy:
 *
 *   io.now()                     -> number (ms since epoch)
 *   io.setTimer(ms, fn)          -> handle (call fn once, ms from now)
 *   io.clearTimer(handle)        -> void
 *   io.sendPrompt(text)          -> Promise<void>   (a new turn, not a keystroke)
 *   io.log(level, event, data)   -> void
 *   io.persist(snapshot)         -> void            (durable counters)
 *   io.status(text)              -> void            (one status line)
 *
 * Phases
 *   idle     nothing armed; a turn is running or the person owns the session
 *   counting a countdown is running after a turn ended
 *   checking an automated check was sent; waiting for watchdog_decide
 *   working  the model was told to continue and owes another turn
 *   stopped  a hard stop (limit reached, /watchdog off, wait_user, done)
 */

export const PHASE = Object.freeze({
  IDLE: 'idle',
  COUNTING: 'counting',
  CHECKING: 'checking',
  WORKING: 'working',
  STOPPED: 'stopped'
});

export const DECISION = Object.freeze({
  WAIT_USER: 'wait_user',
  DONE: 'done',
  CONTINUE: 'continue'
});

export const TOOL_NAME = 'watchdog_decide';

export function createWatchdog(cfg, io) {
  const state = {
    phase: PHASE.IDLE,
    // automated checks sent in this session
    checks: 0,
    // automated checks sent since the last human prompt
    checksSinceUser: 0,
    // how many work turns we asked for
    continuations: 0,
    // reasons we did not send a check (counted, useful for tuning)
    postpones: 0,
    skips: 0,
    stopReason: null,
    lastUserActivityAt: 0,
    lastCheckAt: 0,
    startedAt: io.now(),
    deadlineAt: null,
    // a decision round is open: only the watchdog tool may run
    decisionPending: false,
    // a decision stopped us; swallow the turn.complete of that very round
    suppressArm: false,
    // a work turn is queued for after the check round ends
    expectQueuedTurn: false,
    draftActive: false,
    draftPostpones: 0
  };

  let timer = null;
  let tier = null;
  let seq = 0;
  const trail = [];

  function remember(record) {
    trail.push(record);
    if (trail.length > 80) trail.shift();
    return record;
  }

  function ev(event, data) {
    const record = { seq: ++seq, at: io.now(), event, data: data ?? null };
    return record;
  }

  function log(level, event, data) {
    io.log(level, event, data);
  }

  function snapshot() {
    return {
      phase: state.phase,
      checks: state.checks,
      checksSinceUser: state.checksSinceUser,
      continuations: state.continuations,
      postpones: state.postpones,
      skips: state.skips,
      stopReason: state.stopReason,
      lastUserActivityAt: state.lastUserActivityAt,
      lastCheckAt: state.lastCheckAt,
      startedAt: state.startedAt,
      decisionPending: state.decisionPending,
      draftActive: state.draftActive,
      draftPostpones: state.draftPostpones,
      tier,
      trail: trail.slice(-20)
    };
  }

  function persist() {
    io.persist(snapshot());
  }

  function cancelTimer() {
    if (timer !== null) {
      io.clearTimer(timer);
      timer = null;
    }
    state.deadlineAt = null;
  }

  function setStatus() {
    if (state.phase === PHASE.COUNTING) {
      const left = Math.max(0, Math.ceil(((state.deadlineAt ?? io.now()) - io.now()) / 1000));
      io.status(`watchdog ${left}s (${state.checks}/${cfg.maxChecks})`);
      return;
    }
    if (state.phase === PHASE.CHECKING) return io.status('watchdog checking');
    if (state.phase === PHASE.WORKING) return io.status('watchdog continuing');
    if (state.phase === PHASE.STOPPED) return io.status(`watchdog stopped (${state.stopReason})`);
    io.status(undefined);
  }

  function stopWatching(reason, level = 'info') {
    cancelTimer();
    state.phase = PHASE.STOPPED;
    state.stopReason = reason;
    state.decisionPending = false;
    log(level, 'stop', { reason, checks: state.checks });
    setStatus();
    persist();
  }

  function armCountdown(trigger) {
    if (!cfg.enabled) return;
    if (state.phase === PHASE.STOPPED) return;
    cancelTimer();
    state.phase = PHASE.COUNTING;
    state.deadlineAt = io.now() + cfg.timeoutMs;
    log('debug', 'countdown_started', { trigger, timeoutMs: cfg.timeoutMs, checks: state.checks });
    timer = io.setTimer(cfg.timeoutMs, () => {
      timer = null;
      state.deadlineAt = null;
      void onTimer();
    });
    setStatus();
    persist();
  }

  function postpone(reason) {
    state.postpones += 1;
    log('debug', 'postponed', { reason, postpones: state.postpones });
    armCountdown(`postpone:${reason}`);
  }

  async function onTimer() {
    if (state.phase === PHASE.STOPPED) return;
    if (!cfg.enabled) return stopWatching('disabled');
    const now = io.now();
    if (state.draftActive && cfg.postponeOnDraft && state.draftPostpones < cfg.maxDraftPostpones) {
      state.draftPostpones += 1;
      return postpone('draft');
    }
    if (state.draftActive && cfg.postponeOnDraft) {
      log('warn', 'draft_postpone_limit_reached', { maxDraftPostpones: cfg.maxDraftPostpones });
    }
    state.draftPostpones = 0;
    if (now - state.lastUserActivityAt < cfg.graceMs) return postpone('recent_user_activity');
    if (now - state.lastCheckAt < cfg.minIntervalMs) return postpone('min_interval');
    if (state.checks >= cfg.maxChecks) {
      log('warn', 'limit_reached', { maxChecks: cfg.maxChecks });
      return stopWatching('limit_reached', 'warn');
    }
    state.draftPostpones = 0;
    state.checks += 1;
    state.checksSinceUser += 1;
    state.lastCheckAt = now;
    state.phase = PHASE.CHECKING;
    state.decisionPending = true;
    const text = checkPrompt(cfg, state.checks);
    log('info', 'check_sent', { attempt: state.checks, max: cfg.maxChecks });
    setStatus();
    persist();
    try {
      await io.sendPrompt(text);
    } catch (error) {
      // Sending failed: do not leave a phantom decision round behind.
      state.decisionPending = false;
      state.phase = PHASE.IDLE;
      log('error', 'check_send_failed', { message: String(error && error.message ? error.message : error) });
      persist();
    }
  }

  /**
   * A model turn ended. `reason` is CodeBuddy's TurnCompleteReason
   * ('answer' | 'aborted' | 'refusal' | 'error').
   */
  function onTurnComplete(reason) {
    remember({ at: io.now(), kind: 'turn.complete', reason });
    if (state.suppressArm) {
      state.suppressArm = false;
      log('debug', 'arm_suppressed', { reason });
      if (state.phase !== PHASE.STOPPED) state.phase = state.decisionPending ? PHASE.CHECKING : PHASE.IDLE;
      persist();
      return;
    }
    if (state.expectQueuedTurn) {
      state.expectQueuedTurn = false;
      log('debug', 'arm_skipped_queued_turn', { reason });
      persist();
      return;
    }
    if (state.phase === PHASE.STOPPED || !cfg.enabled) return;
    if (reason !== 'answer' && reason !== 'error') {
      // User interruption and refusal need a person or policy change; do not chase them.
      state.phase = PHASE.IDLE;
      state.decisionPending = false;
      setStatus();
      persist();
      return;
    }
    if (state.decisionPending) {
      state.decisionPending = false;
      if (!cfg.requireDecisionTool) {
        log('info', 'decision_round_completed_without_tool', { attempt: state.checks });
        return armCountdown('decision_round_complete');
      }
      log('warn', 'decision_missing', { attempt: state.checks });
      state.skips += 1;
      return armCountdown('decision_missing');
    }
    armCountdown('turn.complete');
  }

  /** A prompt was submitted. `origin` is 'user' | 'plugin'<name> | 'peer'. */
  function onPromptSubmit({ text, origin, internal }) {
    remember({ at: io.now(), kind: 'prompt.submit', origin, internal: !!internal });
    if (origin === 'user') {
      state.lastUserActivityAt = io.now();
      state.checksSinceUser = 0;
      state.draftPostpones = 0;
      cancelTimer();
      if (state.phase !== PHASE.STOPPED) state.phase = PHASE.IDLE;
      state.decisionPending = false;
      log('debug', 'user_activity', { chars: typeof text === 'string' ? text.length : 0 });
      setStatus();
      persist();
      return;
    }
    if (internal) {
      log('debug', 'internal_prompt', { origin });
      return;
    }
    // somebody else's prompt (a peer session, another plugin): treat as activity
    state.lastUserActivityAt = io.now();
    cancelTimer();
    if (state.phase !== PHASE.STOPPED) state.phase = PHASE.IDLE;
    persist();
  }

  /** The watchdog_decide tool was called. */
  async function onDecision(decision, note) {
    remember({ at: io.now(), kind: 'decision', decision, note: note ?? null });
    if (!state.decisionPending) {
      log('warn', 'decision_out_of_round', { decision });
      return { ok: false, message: 'no watchdog check is pending; this call was ignored' };
    }
    state.decisionPending = false;
    log('info', 'decision', { decision, note: note ?? null, checks: state.checks });
    if (decision === DECISION.CONTINUE) {
      state.continuations += 1;
      state.phase = PHASE.WORKING;
      // the work prompt is queued by the engine and starts once this round is idle,
      // so the check round's own turn.complete must not arm another countdown
      state.expectQueuedTurn = true;
      setStatus();
      persist();
      try {
        await io.sendPrompt(workPrompt(cfg, note));
      } catch (error) {
        state.expectQueuedTurn = false;
        state.phase = PHASE.IDLE;
        log('error', 'work_send_failed', { message: String(error && error.message ? error.message : error) });
        persist();
        return { ok: false, message: 'could not queue the work turn' };
      }
      return { ok: true, message: 'work turn queued' };
    }
    state.suppressArm = true;
    stopWatching(decision === DECISION.DONE ? 'done' : 'wait_user');
    return { ok: true, message: `watchdog stopped (${decision})` };
  }

  /** Status of the prompt box; a non-empty draft means the person is typing. */
  function setDraft(isActive) {
    if (state.draftActive === isActive) return;
    state.draftActive = isActive;
    log('debug', 'draft_changed', { draftActive: isActive });
  }

  function tick() {
    setStatus();
    if (state.phase === PHASE.COUNTING && state.deadlineAt !== null && io.now() >= state.deadlineAt) {
      // the host timer is authoritative, this is only a safety net
      cancelTimer();
      void onTimer();
    }
  }

  async function sendWorkTurn(note) {
    const text = workPrompt(cfg, note);
    state.phase = PHASE.WORKING;
    setStatus();
    persist();
    await io.sendPrompt(text);
  }

  function enable() {
    if (cfg.enabled && state.phase !== PHASE.STOPPED) return;
    cfg.enabled = true;
    state.phase = PHASE.IDLE;
    state.stopReason = null;
    log('info', 'enabled');
    setStatus();
    persist();
  }

  function disable(reason = 'manual') {
    cfg.enabled = false;
    stopWatching(reason);
  }

  function reset() {
    cancelTimer();
    state.phase = PHASE.IDLE;
    state.checks = 0;
    state.checksSinceUser = 0;
    state.continuations = 0;
    state.postpones = 0;
    state.skips = 0;
    state.stopReason = null;
    state.decisionPending = false;
    state.suppressArm = false;
    state.expectQueuedTurn = false;
    state.lastCheckAt = 0;
    state.draftPostpones = 0;
    state.startedAt = io.now();
    trail.length = 0;
    log('info', 'reset');
    setStatus();
    persist();
  }

  function shutdown() {
    cancelTimer();
    state.phase = PHASE.STOPPED;
    state.stopReason = 'session_end';
    state.decisionPending = false;
    log('info', 'shutdown', { checks: state.checks });
    setStatus();
    persist();
  }

  function setTier(value) {
    tier = value;
  }

  return {
    state,
    snapshot,
    trail: () => trail.slice(),
    armCountdown,
    onTimer,
    onTurnComplete,
    onPromptSubmit,
    onDecision,
    setDraft,
    tick,
    sendWorkTurn,
    enable,
    disable,
    reset,
    shutdown,
    setTier,
    get decisionPending() {
      return state.decisionPending;
    }
  };
}

/** The text sent when the countdown elapses. It must never read as user input. */
export function checkPrompt(cfg, attempt) {
  return [
    `${cfg.marker} ${attempt}/${cfg.maxChecks} — not user input]`,
    'The session went quiet after a turn ended. This message is not from your user and needs no',
    cfg.requireDecisionTool
      ? 'conversation: answer it with exactly one `' + TOOL_NAME + '` call, and call no other tool first.'
      : 'conversation: you may call `' + TOOL_NAME + '` or continue the unfinished work directly.',
    '',
    `- ${DECISION.CONTINUE}: work remains (a truncated stream, an unfinished edit, a step you said you would do).`,
    `- ${DECISION.WAIT_USER}: you need a decision, a credential or information only your user has.`,
    `- ${DECISION.DONE}: the request is complete and no further work is pending.`,
    '',
    'Do not re-state, re-summarise or re-write anything you have already delivered: anything you already',
    'wrote counts as delivered. This check round is not work. If you answer `' + DECISION.CONTINUE + '`, the work',
    'happens in the next turn.'
  ].join('\n');
}

/** The text sent after the model chose `continue`. */
export function workPrompt(cfg, note) {
  return [
    `${cfg.marker} continue — not user input]`,
    'The check round is over and every tool is available again. Continue the unfinished work now.',
    'Do not repeat, restate or expand on anything you have already delivered.',
    note ? `Your own note from the check: ${note}` : 'No note was given.'
  ].join('\n');
}
