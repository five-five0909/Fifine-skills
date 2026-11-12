#!/usr/bin/env node
/**
 * Scenario tests for codebuddy-watchdog against the mock host.
 *
 * Run: node tests/scenarios.mjs   (exit code 0 = every case passed)
 * A failing case prints the assertion and exits non-zero: no case is skipped.
 */
import { createHarness } from './harness.mjs';

const results = [];
let current = null;

function test(name, fn) {
  current = { name, checks: [] };
  results.push(current);
  return Promise.resolve()
    .then(fn)
    .then(() => {
      current.status = 'pass';
    })
    .catch((error) => {
      current.status = 'fail';
      current.error = error && error.stack ? error.stack : String(error);
    });
}

function eq(actual, expected, what) {
  const a = JSON.stringify(actual);
  const b = JSON.stringify(expected);
  current.checks.push(what);
  if (a !== b) throw new Error(`${what}: expected ${b}, got ${a}`);
}

function ok(value, what) {
  current.checks.push(what);
  if (!value) throw new Error(`${what}: expected truthy, got ${JSON.stringify(value)}`);
}

const CONFIG = (over = {}) => JSON.stringify({
  enabled: true,
  timeoutMs: 60000,
  graceMs: 2000,
  minIntervalMs: 0,
  maxChecks: 50,
  tickMs: 1000,
  requireDecisionTool: true,
  blockOtherToolsInDecisionRound: true,
  postponeOnDraft: true,
  maxDraftPostpones: 3,
  ...over
});

function boot(over = {}, extra = {}) {
  const files = { '/config/watchdog.config.json': CONFIG(over), ...(extra.files || {}) };
  return createHarness({ files, ...extra });
}

const START = { hook_event_name: 'SessionStart', source: 'startup' };
const turnEnd = (reason = 'answer') => ({ hook_event_name: 'Stop', reason });
const userPrompt = (text = 'do it', kind = 'composer') => ({ hook_event_name: 'UserPromptSubmit', text, origin: { kind } });

await test('启动后注册 watchdog_decide 工具与 /watchdog 命令', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.flush();
  eq(h.registeredTools.map((t) => t.name), ['watchdog_decide'], 'tool registered');
  eq(h.registeredTools[0].inputSchema.properties.decision.enum, ['wait_user', 'done', 'continue'], 'three decisions');
  eq(h.registeredCommands.map((c) => c.name), ['watchdog'], 'command registered');
  h.restore();
});

await test('短任务正常结束：只起表，不发继续', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(30000);
  eq(h.sent, [], 'no prompt before the countdown');
  ok(h.pendingTimers() >= 1, 'countdown armed');
  h.restore();
});

await test('模拟截断/空响应：到点发一条继续，且带"不是用户输入"标记', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(60000);
  eq(h.sent.length, 1, 'exactly one automated prompt');
  ok(h.sent[0].includes('[Automated watchdog check 1/50 — not user input]'), 'marker present');
  ok(h.sent[0].includes('watchdog_decide'), 'forces the tool');
  ok(h.sent[0].includes('counts as delivered'), 'declares delivered work');
  h.restore();
});

await test('决策轮只放行 watchdog_decide，其它工具被拒', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(60000);
  const denied = await h.emit('tool.call', { tool: 'Bash', input: { command: 'ls' } }, { tool: 'Bash' });
  ok(denied && typeof denied.deny === 'string', 'other tool denied');
  const allowed = await h.emit('tool.call', { tool: 'watchdog_decide', input: { decision: 'done' } }, { tool: 'watchdog_decide' });
  ok(!allowed.deny, 'watchdog tool allowed');
  h.restore();
});

await test('decision=continue：发工作回合，且检查轮的 turn.complete 不再叠一次倒计时', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(60000);
  await h.emit('tool.call', { tool: 'watchdog_decide', input: { decision: 'continue', note: 'step 3 left' } }, { tool: 'watchdog_decide' });
  await h.flush();
  eq(h.sent.length, 2, 'work prompt sent');
  ok(h.sent[1].includes('continue — not user input'), 'work prompt marker');
  ok(h.sent[1].includes('step 3 left'), 'note carried over');
  ok(h.sent[1].includes('every tool is available again'), 'tools re-opened');
  await h.emit('turn.complete', turnEnd('answer'));
  eq(h.store['watchdog:state'].phase, 'working', 'check round did not re-arm');
  await h.emit('turn.complete', turnEnd('answer'));
  eq(h.store['watchdog:state'].phase, 'counting', 'work turn re-armed the countdown');
  h.restore();
});

await test('decision=done / wait_user：停表，之后不再发继续', async () => {
  for (const decision of ['done', 'wait_user']) {
    const h = boot();
    await h.emit('session.start', START);
    await h.emit('turn.complete', turnEnd('answer'));
    await h.advance(60000);
    await h.emit('tool.call', { tool: 'watchdog_decide', input: { decision } }, { tool: 'watchdog_decide' });
    await h.flush();
    await h.emit('turn.complete', turnEnd('answer'));
    await h.advance(300000);
    eq(h.sent.length, 1, `${decision}: only the check was sent`);
    eq(h.store['watchdog:state'].stopReason, decision, `${decision}: stop reason recorded`);
    h.restore();
  }
});

await test('连续触发到上限：自动停止并留痕', async () => {
  const h = boot({ maxChecks: 2, timeoutMs: 1000 });
  await h.emit('session.start', START);
  for (let i = 0; i < 5; i += 1) {
    // a turn ends -> countdown; the check goes out when it elapses
    await h.emit('turn.complete', turnEnd('answer'));
    await h.advance(1000);
    await h.emit('tool.call', { tool: 'watchdog_decide', input: { decision: 'continue' } }, { tool: 'watchdog_decide' });
    await h.flush();
    // the check round ends, then the queued work turn runs and ends
    await h.emit('turn.complete', turnEnd('answer'));
    await h.emit('turn.complete', turnEnd('answer'));
    await h.flush();
  }
  eq(h.sent.filter((t) => /Automated watchdog check \d+\//.test(t)).length, 2, 'stopped at maxChecks');
  eq(h.store['watchdog:state'].stopReason, 'limit_reached', 'stop reason');
  eq(h.store['watchdog:state'].phase, 'stopped', 'phase stopped');
  h.restore();
});

await test('用户中途输入：倒计时取消，不发继续', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(30000);
  await h.emit('prompt.submit', userPrompt('等一下，先别动'), { origin: { kind: 'user' } });
  await h.advance(120000);
  eq(h.sent, [], 'nothing sent after the person typed');
  eq(h.store['watchdog:state'].phase, 'idle', 'disarmed');
  h.restore();
});

await test('用户刚输入的宽限期内到点：改期而不是抢话', async () => {
  const h = boot({ timeoutMs: 5000, graceMs: 3000 });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(4000);
  await h.emit('prompt.submit', userPrompt('继续写'), { origin: { kind: 'user' } });
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(5000);
  ok(h.sent.length <= 1, 'at most one check in the grace window');
  ok(h.store['watchdog:state'].postpones + h.sent.length >= 1, 'either postponed or sent once');
  h.restore();
});

await test('决策轮结束却没调用工具：视为没答，倒计时重来', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(60000);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.flush();
  eq(h.store['watchdog:state'].phase, 'counting', 're-armed');
  ok(h.store['watchdog:state'].skips >= 1, 'missed decision counted');
  await h.advance(60000);
  eq(h.sent.filter((t) => /Automated watchdog check \d+\//.test(t)).length, 2, 'a second check was sent');
  h.restore();
});

await test('中断/失败的回合不追', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('aborted'));
  await h.advance(120000);
  eq(h.sent, [], 'no check after an aborted turn');
  eq(h.store['watchdog:state'].phase, 'idle', 'idle');
  h.restore();
});

await test('/watchdog off 立刻停表，reset 清零，status 可读', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.emit('command.run', { command: 'watchdog', args: 'off' }, { command: 'watchdog' });
  await h.flush();
  await h.advance(120000);
  eq(h.sent, [], 'off stops the watchdog');
  const status = await h.emit('command.run', { command: 'watchdog', args: 'status' }, { command: 'watchdog' });
  ok(String(status.text).includes('disabled'), 'status reports disabled');
  await h.emit('command.run', { command: 'watchdog', args: 'reset' }, { command: 'watchdog' });
  await h.emit('command.run', { command: 'watchdog', args: 'on' }, { command: 'watchdog' });
  await h.flush();
  const after = await h.emit('command.run', { command: 'watchdog', args: 'status' }, { command: 'watchdog' });
  ok(String(after.text).includes('enabled'), 'on works');
  h.restore();
});

await test('session.end：定时器清空，状态落盘，无残留', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  ok(h.pendingTimers() >= 1, 'timer armed before end');
  await h.emit('session.end', { hook_event_name: 'SessionEnd', reason: 'exit' });
  await h.flush();
  eq(h.pendingTimers(), 0, 'no timer left');
  ok(h.files.has('/state/state.json'), 'state mirror written');
  ok(h.files.get('/state/watchdog.log').includes('shutdown'), 'shutdown logged');
  h.restore();
});

await test('损坏的配置：逐条报错并回落默认值，不炸', async () => {
  const h = createHarness({ files: { '/config/watchdog.config.json': '{"timeoutMs": "soon", "enabled": 1, "wat": true' } });
  await h.emit('session.start', START);
  await h.flush();
  eq(h.registeredTools.length, 1, 'still boots');
  await h.flush();
  const logged = h.files.get('/state/watchdog.log') || '';
  ok(logged.includes('config_problem'), 'problem is recorded in file log');
  h.restore();
});

await test('enabled:false 的配置：不装表、不发继续', async () => {
  const h = boot({ enabled: false });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(180000);
  eq(h.sent, [], 'inert when disabled');
  h.restore();
});

await test('纯逻辑：倒计时状态机不依赖宿主定时器也能推进', async () => {
  const h = boot({ timeoutMs: 1000 });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(1000);
  eq(h.store['watchdog:state'].checks, 1, 'one check counted');
  ok(h.store['watchdog:state'].lastCheckAt > 0, 'timestamp recorded');
  h.restore();
});

await test('完整 MCP 工具名可通过守卫并完成 continue 闭环', async () => {
  const h = boot({ timeoutMs: 1000 });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(1000);
  const fullName = 'mcp__codebuddy-watchdog__watchdog_decide';
  const result = await h.emit('tool.call', { tool: fullName, input: { decision: 'continue', note: 'finish tests' } });
  await h.flush();
  ok(result && result.result && String(result.result.content).includes('work turn queued'), 'full tool name handled');
  eq(h.store['watchdog:state'].continuations, 1, 'continue counted');
  eq(h.sent.length, 2, 'work turn queued');
  h.restore();
});

await test('trail 保存真实事件对象，不再序列化为 null', async () => {
  const h = boot();
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  const trail = h.store['watchdog:state'].trail;
  ok(Array.isArray(trail) && trail.length > 0, 'trail exists');
  eq(trail.at(-1).kind, 'turn.complete', 'event kind preserved');
  h.restore();
});

await test('composer bridge sdk 都按用户输入处理并清零检查计数', async () => {
  for (const kind of ['composer', 'bridge', 'sdk']) {
    const h = boot({ timeoutMs: 1000 });
    await h.emit('session.start', START);
    await h.emit('turn.complete', turnEnd('answer'));
    await h.advance(1000);
    ok(h.store['watchdog:state'].checksSinceUser > 0, kind + ': check counted');
    await h.emit('prompt.submit', userPrompt('user activity', kind));
    eq(h.store['watchdog:state'].checksSinceUser, 0, kind + ': reset');
    eq(h.store['watchdog:state'].phase, 'idle', kind + ': disarmed');
    h.restore();
  }
});

await test('陈旧 draft 只延期有限次数，随后仍会检查', async () => {
  const h = boot({ timeoutMs: 1000, maxDraftPostpones: 2 }, { promptText: 'stale draft' });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(3000);
  eq(h.store['watchdog:state'].postpones, 2, 'draft postponed twice');
  eq(h.store['watchdog:state'].checks, 1, 'check eventually sent');
  eq(h.sent.length, 1, 'one check sent');
  h.restore();
});

await test('API error/context-limit 结束后也进入恢复检查，用户 aborted 仍不追', async () => {
  const h = boot({ timeoutMs: 1000 });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('error'));
  await h.advance(1000);
  eq(h.sent.length, 1, 'error triggers recovery check');
  h.restore();
});

await test('requireDecisionTool=false 时不阻止其它工具', async () => {
  const h = boot({ timeoutMs: 1000, requireDecisionTool: false });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(1000);
  const result = await h.emit('tool.call', { tool: 'Bash', input: { command: 'true' } });
  ok(!result.deny, 'other tool allowed');
  await h.emit('turn.complete', turnEnd('answer'));
  eq(h.store['watchdog:state'].skips, 0, 'missing decision is not counted');
  h.restore();
});

await test('session.end 后新的 session.start 会重建状态机和 ticker', async () => {
  const h = boot({ timeoutMs: 1000 });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.emit('session.end', { reason: 'switch' });
  eq(h.pendingTimers(), 0, 'old timers cleared');
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(1000);
  eq(h.sent.length, 1, 'new session watchdog works');
  h.restore();
});

await test('done 后的 turn.complete 不会让 watchdog 复活', async () => {
  const h = boot({ timeoutMs: 1000 });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(1000);
  await h.emit('tool.call', { tool: 'mcp__codebuddy-watchdog__watchdog_decide', input: { decision: 'done' } });
  await h.emit('turn.complete', turnEnd('answer'));
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(5000);
  eq(h.store['watchdog:state'].phase, 'stopped', 'remains stopped');
  eq(h.store['watchdog:state'].stopReason, 'done', 'stop reason preserved');
  eq(h.sent.length, 1, 'no second check');
  h.restore();
});

await test('Hook 完成后 UI API 全部拒绝，定时器仍无异常完成闭环', async () => {
  const h = boot({ timeoutMs: 1000 }, { denyUi: true });
  await h.emit('session.start', START);
  await h.emit('turn.complete', turnEnd('answer'));
  await h.advance(1000);
  const result = await h.emit('tool.call', { tool: 'mcp__codebuddy-watchdog__watchdog_decide', input: { decision: 'done' } });
  await h.emit('turn.complete', turnEnd('answer'));
  await h.flush();
  ok(String(result?.result?.content || '').includes('stopped'), 'decision completed without UI');
  eq(h.store['watchdog:state'].stopReason, 'done', 'state persisted');
  ok(h.files.get('/state/watchdog.log').includes('decision'), 'file log persisted');
  h.restore();
});

let failed = 0;
for (const item of results) {
  if (item.status === 'pass') {
    console.log(`PASS  ${item.name}  (${item.checks.length} assertions)`);
  } else {
    failed += 1;
    console.log(`FAIL  ${item.name}`);
    console.log(`      ${String(item.error).split('\n').slice(0, 4).join('\n      ')}`);
  }
}
console.log(`\n${results.length - failed}/${results.length} cases passed, ${results.reduce((n, r) => n + r.checks.length, 0)} assertions`);
process.exit(failed === 0 ? 0 : 1);
