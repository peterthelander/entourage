/* global __dirname */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const ts = require('typescript');
const loadModule = require('./load-ts.cjs');

function load(fetch) {
  const source = fs.readFileSync(path.join(__dirname, '../src/agent/serverClient.ts'), 'utf8');
  const context = { exports: {}, fetch, AbortController, setTimeout, clearTimeout };
  vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, context);
  return context.exports;
}

test('browser connects automatically without a bearer token', async () => {
  let headers;
  const { AgentClient } = load(async (_url, options) => {
    headers = options.headers;
    return { ok: true, json: async () => ({ items: [], next_after: null }) };
  });
  await new AgentClient('https://hp.example.ts.net/agent').chat();
  assert.equal(headers.Authorization, undefined);
});

test('single chat resolution does not create a client-specific conversation', async () => {
  const calls = [];
  const { AgentClient } = load(async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => ({ id: 'shared' }) };
  });
  const client = new AgentClient('https://agent.example/agent');
  assert.equal((await client.chat()).id, 'shared');
  assert.equal((await client.chat()).id, 'shared');
  assert.ok(calls.every(({ url, options }) => url.endsWith('/api/v1/chat') && options.method === 'PUT'));
});

test('server client preserves turn IDs on retries and keeps credentials in headers', async () => {
  const requests = [];
  const { AgentClient } = load(async (url, options) => {
    requests.push({ url, options });
    return { ok: true, json: async () => ({ status: 'queued' }) };
  });
  const client = new AgentClient('https://agent.example', 'private-owner-token');
  await client.submit('conversation', 'same-turn', 'Hello', 'device');
  await client.submit('conversation', 'same-turn', 'Hello', 'device');
  assert.equal(requests[0].url, requests[1].url);
  assert.equal(requests[0].options.body, requests[1].options.body);
  assert.equal(requests[0].options.headers.Authorization, 'Bearer private-owner-token');
  assert.ok(requests.every(({ url }) => !url.includes('private-owner-token')));
  await client.deviceResult('turn', 'request', 'device', 'device-secret', 'Denied');
  assert.equal(requests[2].options.headers['X-Device-Key'], 'device-secret');
  assert.equal(JSON.parse(requests[2].options.body).content, 'Denied');
});

test('server client reads all pages and exposes permanent rejection status', async () => {
  const urls = [];
  const { AgentClient, AgentApiError } = load(async (url) => {
    urls.push(url);
    if (url.includes('/turns/')) return { ok: false, status: 409, json: async () => ({ error: { message: 'Already active' } }) };
    return { ok: true, json: async () => url.includes('after=0')
      ? { items: [{ sequence: 2 }], next_after: 2 } : { items: [{ sequence: 3 }], next_after: null } };
  });
  const client = new AgentClient('https://agent.example', 'token');
  assert.deepEqual(JSON.parse(JSON.stringify(await client.messages('conversation'))), [{ sequence: 2 }, { sequence: 3 }]);
  assert.match(urls[1], /after=2/);
  await assert.rejects(client.turn('turn'), (error) => error instanceof AgentApiError && error.status === 409);
});

test('stop and history import keep deterministic IDs and original message kinds', async () => {
  const calls = [];
  const { AgentClient } = load(async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => ({}) };
  });
  const client = new AgentClient('https://agent.example/agent', 'token');
  await client.cancel('turn');
  await client.cancel('turn');
  assert.equal(calls[0].url, calls[1].url);
  assert.match(calls[0].url, /\/agent\/api\/v1\/turns\/turn\/cancellation$/);
  const history = { messages: [{ id: 'toolresult-1', role: 'assistant', text: 'calculate\n156' }] };
  const original = JSON.stringify(history);
  await client.previewImport(history);
  await client.importChatHistory('same-import', history);
  await client.importChatHistory('same-import', history);
  assert.equal(calls[3].url, calls[4].url);
  assert.equal(calls[3].options.body, original);
  assert.equal(JSON.stringify(history), original);
});

test('sending during a poll preserves the pending message and blocks a stale second send', async () => {
  const slots = [];
  let cursor = 0;
  let effect;
  const timers = [];
  const storage = new Map();
  let releaseHistory;
  const delayedHistory = new Promise((resolve) => { releaseHistory = resolve; });
  let historyCalls = 0;
  const submissions = [];
  let active = null;
  class FakeClient {
    async health() { return { execution_enabled: true }; }
    async register() {}
    async chat() { return { id: 'shared' }; }
    async latest() { return active; }
    async messages() { if (++historyCalls === 2) await delayedHistory; return []; }
    async submit(conversation, id, text) {
      submissions.push({ conversation, id, text });
      active = { id, status: 'queued' };
    }
  }
  const react = {
    useState(initial) {
      const index = cursor++;
      if (!(index in slots)) slots[index] = typeof initial === 'function' ? initial() : initial;
      return [slots[index], (value) => { slots[index] = typeof value === 'function' ? value(slots[index]) : value; }];
    },
    useRef(initial) {
      const index = cursor++;
      if (!(index in slots)) slots[index] = { current: initial };
      return slots[index];
    },
    useEffect(callback) { if (!effect) effect = callback; },
  };
  let id = 0;
  const context = {
    exports: {},
    require(name) {
      if (name === 'react') return react;
      if (name.endsWith('serverClient')) return { AgentClient: FakeClient, AgentApiError: Error };
      if (name.endsWith('chatStorage')) return { loadChat: () => null };
      if (name.endsWith('presentationMessage')) return loadModule('src/agent/presentationMessage.ts');
      if (name.endsWith('browserDevice')) return loadModule('src/agent/browserDevice.ts', {
        './toolRegistry': { toolRegistry: {} },
      }, context);
      if (name.endsWith('browserHistoryImport')) return loadModule('src/agent/browserHistoryImport.ts', {
        './chatStorage': { loadChat: () => null },
      }, context);
      return { toolRegistry: {} };
    },
    localStorage: { getItem: (key) => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value), removeItem: (key) => storage.delete(key) },
    crypto: { randomUUID: () => `id-${++id}` },
    setTimeout: (callback) => { timers.push(callback); return timers.length; },
    clearTimeout() {},
  };
  const source = fs.readFileSync(path.join(__dirname, '../src/hooks/useServerChat.ts'), 'utf8');
  vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, context);
  const render = () => { cursor = 0; return context.exports.useServerChat('https://test'); };
  render();
  const cleanup = effect();
  await new Promise((resolve) => setImmediate(resolve));
  let chat = render();
  assert.equal(chat.ready, true);
  chat.setDraft('First message');
  const firstSend = render().handleSend;
  chat.setDraft('Second message');
  const staleSecondSend = render().handleSend;
  const polling = timers.shift()();
  await new Promise((resolve) => setImmediate(resolve));
  await firstSend();
  const key = 'entourage.server.v1:https://test:pending';
  const pending = storage.get(key);
  assert.equal(JSON.parse(pending).text, 'First message');
  render().setDraft('Second message');
  releaseHistory();
  await polling;
  assert.equal(render().busy, true);
  await staleSecondSend();
  assert.equal(storage.get(key), pending);
  assert.equal(render().draft, 'Second message');
  await timers.shift()();
  assert.equal(submissions.length, 1);
  assert.equal(submissions[0].text, 'First message');
  assert.equal(submissions[0].id, JSON.parse(pending).id);
  assert.equal(storage.has(key), false);
  assert.equal(render().busy, true);
  active = { status: 'completed' };
  await timers.shift()();
  assert.equal(render().busy, false);
  cleanup();
});
