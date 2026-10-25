const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const load = require('./load-component.cjs');

function renderChat(overrides = {}) {
  const chat = { model: '/Users/example/Downloads/Qwen-new-Q4_K_M.gguf',
    inference: { status: 'ready', configured_model: 'Qwen-new-Q4_K_M.gguf',
      loaded_model: '/Users/example/Downloads/Qwen-new-Q4_K_M.gguf' },
    inferenceReady: true, ready: true, busy: false, error: '', messages: [], draft: 'Hello',
    latestTurn: null, hasLegacy: false, legacyPending: '', ...overrides };
  const { ServerChat } = load('src/components/ServerChat.tsx', {
    '../hooks/useServerChat': { useServerChat: () => chat },
    'expo-clipboard': { setStringAsync: async () => true },
    './MarkdownMessage': { MarkdownMessage: ({ text }) => React.createElement('p', null, text) },
  });
  return renderToStaticMarkup(React.createElement(ServerChat, { endpoint: 'https://agent.example' }));
}

const sendButton = (html) => html.match(/<button\b[^>]*aria-label="Send message"[^>]*>/)?.[0] || '';

test('loaded Qwen model is readable without a machine path and send is enabled', () => {
  const html = renderChat();
  assert.match(html, /Model: Qwen-new-Q4_K_M/);
  assert.ok(!html.includes('/Users/example/Downloads'));
  assert.match(html, /aria-label="Send message"/);
  assert.ok(sendButton(html));
  assert.doesNotMatch(sendButton(html), /aria-disabled="true"/);
});

test('after model swap display shows actual model, explicit mismatch and disabled send', () => {
  const html = renderChat({ inferenceReady: false, inference: { status: 'model_mismatch',
    loaded_model: '/Users/example/Downloads/Qwen-new-Q4_K_M.gguf', configured_model: 'gpt-oss-old.gguf',
    message: 'Configured model does not match. Update the setting and restart the agent.' } });
  assert.match(html, /Model: Qwen-new-Q4_K_M/);
  assert.doesNotMatch(html, /Model: gpt-oss/);
  assert.match(html, /role="alert"/);
  assert.match(html, /Update the setting and restart/);
  assert.match(sendButton(html), /aria-disabled="true"/);
});

test('failed memory turn retains tools, exposes error and explicit retry without success answer', () => {
  const html = renderChat({ error: 'The model reached the response token limit before finishing.',
    latestTurn: { status: 'failed' }, messages: [
      { id: 'u', kind: 'user', role: 'user', text: 'Recall the trip' },
      { id: 't', kind: 'tool', role: 'assistant', text: 'readKnowledgeArticle\n{"status":"ready"}' },
    ] });
  assert.match(html, /response token limit/);
  assert.match(html, /Copy request to retry/);
  assert.match(html, /Read memory article completed/);
  assert.doesNotMatch(html, /readKnowledgeArticle/);
  assert.doesNotMatch(html, /Thinking locally/);
});

test('unavailable knowledge is not labeled completed and offline inference disables send', () => {
  const html = renderChat({ inferenceReady: false, inference: { status: 'unavailable',
    configured_model: 'Qwen-new-Q4_K_M.gguf', message: 'Cannot verify the inference server.' },
    messages: [{ id: 't', kind: 'tool', role: 'assistant',
      text: 'readKnowledgeSource\n{"status":"unavailable"}' }] });
  assert.match(html, /Configured model: Qwen-new-Q4_K_M/);
  assert.match(html, /Read memory source unavailable/);
  assert.doesNotMatch(html, /Read memory source completed/);
  assert.match(sendButton(html), /aria-disabled="true"/);
});

test('specific failure explanations reach the rendered alert with retry available', () => {
  for (const error of [
    'The request needs 18,289 input tokens plus 2,048 reserved response tokens, exceeding the 16,384-token context window.',
    'The model reached the response token limit before finishing.',
    'The inference server took too long to respond.',
    'The connection to the inference server failed.',
    'The inference server rejected the conversation format.',
    'The inference response ended before the model finished.',
  ]) {
    const html = renderChat({ error, latestTurn: { status: 'failed' } });
    assert.ok(html.includes(error));
    assert.match(html, /role="alert"/);
    assert.match(html, /Copy request to retry/);
    assert.doesNotMatch(html, /Agent execution failed/);
  }
});
