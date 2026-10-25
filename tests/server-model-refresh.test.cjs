const assert = require('node:assert/strict');
const test = require('node:test');
const harness = require('./load-server-hook.cjs');

function backend() {
  const state = { status: { status: 'ready', configured_model: 'old.gguf', loaded_model: 'old.gguf' },
    submissions: [], latest: null };
  state.Client = class {
    async health() { return { execution_enabled: true, model: 'old.gguf' }; }
    async inference() { return state.status; }
    async register() {}
    async chat() { return { id: 'shared' }; }
    async latest() { return state.latest; }
    async messages() { return []; }
    async submit(...args) { state.submissions.push(args); }
  };
  return state;
}

test('browser refresh resolves actual model rather than trusting the old configured health label', async () => {
  const state = backend();
  const first = harness(state.Client);
  assert.equal((await first.mount()).model, 'old.gguf');
  first.close();
  state.status = { status: 'model_mismatch', configured_model: 'old.gguf', loaded_model: 'Qwen.gguf', message: 'Restart agent.' };
  const refreshed = harness(state.Client, first.storage);
  const chat = await refreshed.mount();
  assert.equal(chat.model, 'Qwen.gguf');
  assert.equal(chat.ready, true); // Reading saved chat still works.
  assert.equal(chat.inferenceReady, false);
  chat.setDraft('Hello');
  await refreshed.render().handleSend();
  assert.equal(state.submissions.length, 0);
  refreshed.close();
});

test('polling detects a model swap and recovers after agent settings change without losing draft', async () => {
  const state = backend(), browser = harness(state.Client);
  await browser.mount();
  browser.render().setDraft('Remember my trip');
  state.status = { status: 'model_mismatch', configured_model: 'old.gguf', loaded_model: 'Qwen.gguf' };
  browser.advance(15001);
  let chat = await browser.poll();
  assert.equal(chat.model, 'Qwen.gguf');
  assert.equal(chat.inferenceReady, false);
  assert.equal(chat.draft, 'Remember my trip');
  await chat.handleSend();
  assert.equal(state.submissions.length, 0);
  state.status = { status: 'ready', configured_model: 'Qwen.gguf', loaded_model: 'Qwen.gguf' };
  browser.advance(15001);
  chat = await browser.poll();
  assert.equal(chat.inferenceReady, true);
  assert.equal(chat.draft, 'Remember my trip');
  await chat.handleSend();
  assert.equal(state.submissions.length, 1);
  browser.close();
});

test('failed turn after refresh exposes failure with no partial answer and permits explicit retry', async () => {
  const state = backend();
  state.latest = { status: 'failed', partial_answer: 'Incomplete provisional text',
    error: 'The inference server rejected the conversation format.' };
  const browser = harness(state.Client), chat = await browser.mount();
  assert.equal(chat.busy, false);
  assert.equal(chat.messages.length, 0);
  assert.equal(chat.error, state.latest.error);
  assert.equal(chat.inferenceReady, true);
  assert.equal(state.submissions.length, 0);
  browser.close();
});

test('connection and inference warnings clear after service recovery without a refresh', async () => {
  const state = backend();
  let offline = false;
  const Base = state.Client;
  state.Client = class extends Base {
    async inference() {
      if (offline) throw new Error('Service unavailable');
      return super.inference();
    }
    async latest() {
      if (offline) throw new Error('Service unavailable');
      return super.latest();
    }
  };
  const browser = harness(state.Client);
  await browser.mount();
  browser.render().setDraft('Keep my draft');
  offline = true;
  browser.advance(15001);
  let chat = await browser.poll();
  assert.match(chat.error, /Connection interrupted/);
  assert.equal(chat.inference.status, 'unavailable');
  offline = false;
  browser.advance(15001);
  chat = await browser.poll();
  assert.equal(chat.error, '');
  assert.equal(chat.inferenceReady, true);
  assert.equal(chat.model, 'old.gguf');
  assert.equal(chat.draft, 'Keep my draft');
  browser.close();
});
