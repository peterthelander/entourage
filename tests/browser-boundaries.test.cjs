const assert = require('node:assert/strict');
const test = require('node:test');
const loadModule = require('./load-ts.cjs');

function environment() {
  const records = new Map();
  let next = 0;
  return {
    records,
    localStorage: {
      getItem: (key) => records.get(key) ?? null,
      setItem: (key, value) => records.set(key, value),
      removeItem: (key) => records.delete(key),
    },
    crypto: { randomUUID: () => `id-${++next}` },
  };
}

test('server kinds govern exchange output even when IDs suggest another kind', () => {
  const { fromServerMessage } = loadModule('src/agent/presentationMessage.ts');
  const { formatLatestExchange } = loadModule('src/agent/exchangeExport.ts');
  const messages = [
    fromServerMessage({ sequence: 1, kind: 'user', role: 'user', text: 'Question', created_at: '2026-10-18T11:00:00Z' }),
    { id: 'assistant-2', role: 'assistant', kind: 'tool', text: 'calculate\n156' },
    { id: 'toolresult-3', role: 'assistant', kind: 'error', text: 'Request failed' },
  ];
  const text = formatLatestExchange(messages, 'model');
  assert.match(text, /Tool calls recorded: 1/);
  assert.match(text, /Tool call \/ result \[Timestamp unavailable\]\ncalculate\n156/);
  assert.match(text, /Agent error \[Timestamp unavailable\]\nRequest failed/);
  assert.equal(messages[0].id, 'user-1');
});

test('device identity survives reconnect without generating new credentials', () => {
  const env = environment();
  const load = () => loadModule('src/agent/browserDevice.ts', { './toolRegistry': { toolRegistry: {} } }, env);
  const first = load().restoreDevice('prefix:');
  const second = load().restoreDevice('prefix:');
  assert.equal(second.id, first.id);
  assert.equal(second.key, first.key);
});

test('device acknowledgement retries reuse the saved result after network failure and reconnect', async () => {
  const env = environment();
  let executions = 0;
  const dependencies = { './toolRegistry': { toolRegistry: {
    getCurrentTime: { execute: async () => { executions++; return 'clock reading'; } },
  } } };
  const calls = [];
  const api = { async deviceResult(...args) {
    calls.push(args);
    if (calls.length === 1) throw new Error('Network interrupted after delivery');
  } };
  const identity = { id: 'device', key: 'secret' };
  const turn = { id: 'turn', device_requests: [{ id: 'request', device_id: identity.id,
    name: 'getCurrentTime', arguments: {}, result: null, expires_at: Date.now() / 1000 + 120 }] };
  const handler = () => loadModule('src/agent/browserDevice.ts', dependencies, env)
    .createDeviceHandler(api, 'prefix:', () => identity);
  await assert.rejects(handler()(turn), /Network interrupted/);
  await handler()(turn);
  assert.equal(executions, 1);
  assert.deepEqual(calls[0], calls[1]);
  assert.equal(calls[1][4], 'clock reading');
});

test('in-flight device requests are not repeated and interrupted requests are not replayed', async () => {
  const env = environment();
  let finish;
  let executions = 0;
  const result = new Promise((resolve) => { finish = resolve; });
  const acknowledgements = [];
  const { createDeviceHandler } = loadModule('src/agent/browserDevice.ts', {
    './toolRegistry': { toolRegistry: { getCurrentTime: { execute: async () => { executions++; return result; } } } },
  }, env);
  const identity = { id: 'device', key: 'secret' };
  const request = { id: 'request', device_id: identity.id, name: 'getCurrentTime', arguments: {},
    result: null, expires_at: Date.now() / 1000 + 120 };
  const serve = createDeviceHandler({ deviceResult: async (...args) => acknowledgements.push(args) }, 'prefix:', () => identity);
  const first = serve({ id: 'turn', device_requests: [request] });
  await serve({ id: 'turn', device_requests: [request] });
  assert.equal(executions, 1);
  finish('clock reading');
  await first;
  assert.equal(acknowledgements.length, 1);
  env.records.set('prefix:device-result:interrupted', JSON.stringify({ status: 'started' }));
  await serve({ id: 'turn', device_requests: [{ ...request, id: 'interrupted' }] });
  assert.equal(executions, 1);
  assert.match(acknowledgements[1][4], /interrupted; it was not replayed/);
});

test('device boundary ignores other devices and expired results and rejects unsupported operations', async () => {
  const env = environment();
  const outputs = [];
  const { createDeviceHandler } = loadModule('src/agent/browserDevice.ts', { './toolRegistry': { toolRegistry: {} } }, env);
  const request = { id: 'bad', device_id: 'device', name: 'calculate', arguments: {},
    result: null, expires_at: Date.now() / 1000 + 120 };
  await createDeviceHandler({ deviceResult: async (...args) => outputs.push(args[4]) }, 'prefix:',
    () => ({ id: 'device', key: 'secret' }))({ id: 'turn', device_requests: [
      { ...request, id: 'other', device_id: 'other' }, { ...request, id: 'expired', expires_at: 1 }, request,
    ] });
  assert.equal(outputs.length, 1);
  assert.match(outputs[0], /Tool failed: Error: Unsupported device request/);
});

test('history import keeps its ID, body and original storage through failed commit and retry', async () => {
  const env = environment();
  const source = [{ id: 'toolresult-1', role: 'assistant', text: 'calculate\n156' }];
  const original = JSON.stringify(source);
  const calls = [];
  const api = {
    previewImport: async (body) => { calls.push(['preview', JSON.stringify(body)]); return { total: 1 }; },
    importChatHistory: async (id, body) => {
      calls.push(['commit', id, JSON.stringify(body)]);
      if (calls.filter((call) => call[0] === 'commit').length === 1) throw new Error('Network interrupted');
    },
  };
  const helpers = loadModule('src/agent/browserHistoryImport.ts', { './chatStorage': { loadChat: () => source } }, env);
  await helpers.previewHistoryImport(api, 'prefix:');
  const pending = env.records.get('prefix:import');
  await assert.rejects(helpers.commitHistoryImport(api, 'prefix:'), /Network interrupted/);
  assert.equal(env.records.get('prefix:import'), pending);
  assert.equal(helpers.importCompleted('prefix:'), false);
  await helpers.commitHistoryImport(api, 'prefix:');
  assert.deepEqual(calls[1], calls[2]);
  assert.equal(helpers.importCompleted('prefix:'), true);
  assert.equal(JSON.stringify(source), original);
});
