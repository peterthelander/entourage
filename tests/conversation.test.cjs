const assert = require('node:assert/strict');
const test = require('node:test');

const loadModule = require('./load-ts.cjs');

const { buildConversation } = loadModule('src/agent/conversation.ts');
const plain = (value) => JSON.parse(JSON.stringify(value));

test('latest exchange export includes only the newest turn, timestamps, and raw tool results', () => {
  const { formatLatestExchange } = loadModule('src/agent/exchangeExport.ts');
  assert.equal(formatLatestExchange([], 'test-model'), null);
  const text = formatLatestExchange([
    { id: 'user-1792080000000', role: 'user', text: 'Old private query' },
    { id: 'assistant-1792080001000', role: 'assistant', text: 'Old reply' },
    { id: 'user-1792080010000', role: 'user', text: 'What time is it?' },
    { id: 'toolresult-1792080011000-3', role: 'assistant', text: 'getCurrentTime\n{"localTime":"noon"}' },
    { id: 'assistant-1792080012000', role: 'assistant', text: 'It is noon.', createdAt: '2026-10-15T16:00:12.000Z' },
  ], 'qwen3.5:4b');
  assert.ok(!text.includes('Old'));
  assert.match(text, /Model: qwen3\.5:4b/);
  assert.match(text, /Tool calls recorded: 1/);
  assert.ok(text.includes(new Date(1792080010000).toISOString()));
  assert.match(text, /getCurrentTime\n{"localTime":"noon"}/);
  assert.match(text, /Agent response \[2026-10-15T16:00:12.000Z\]/);
  const failure = formatLatestExchange([
    { id: 'legacy', role: 'user', text: 'Hello' },
    { id: 'error-1792080012000', role: 'assistant', text: 'Request failed' },
  ], 'test-model');
  assert.match(failure, /Timestamp unavailable/);
  assert.match(failure, /Tool calls recorded: none/);
  assert.match(failure, /Agent error/);
});

test('exchange copy retains research evidence but omits display-only search HTML', () => {
  const { formatLatestExchange } = loadModule('src/agent/exchangeExport.ts');
  const evidence = { status: 'results', query: 'Harvest orchard', summary: 'Identity uncertain',
    results: [{ title: 'Official source', url: 'https://example.com' }],
    grounding_supports: [{ text: 'Identity uncertain', source_indices: [0] }],
    search_queries: ['Harvest orchard'], search_suggestions_html: '<style>bulky widget</style>' };
  const messages = [
    { id: 'user-1', role: 'user', text: 'Which orchard?' },
    { id: 'toolresult-1', role: 'assistant', text: 'searchWeb\n' + JSON.stringify(evidence) },
  ];
  const original = JSON.stringify(messages);
  const copy = formatLatestExchange(messages, 'test');
  assert.ok(!copy.includes('<style>'));
  assert.ok(copy.includes('HTML omitted from diagnostic copy'));
  for (const key of ['summary', 'results', 'grounding_supports', 'search_queries']) assert.ok(copy.includes(JSON.stringify(evidence[key])));
  assert.equal(JSON.stringify(messages), original);
  const malformed = formatLatestExchange([messages[0], { ...messages[1], text: 'searchWeb\nnot JSON' }], 'test');
  assert.ok(malformed.includes('searchWeb\nnot JSON'));
});

test('clock tool reads fresh client time and works when timezone names are unavailable', async () => {
  let instant = '2026-10-15T18:30:00.000Z';
  class Clock extends Date {
    constructor() { super(instant); }
  }
  const load = (intl) => loadModule('src/agent/toolRegistry.ts', {
    'expo-device': {}, 'expo-location': {},
  }, { Date: Clock, Intl: intl });
  const registry = load({ DateTimeFormat: () => ({ resolvedOptions: () => ({ timeZone: 'America/New_York' }) }) }).toolRegistry;
  const first = JSON.parse(await registry.getCurrentTime.execute());
  assert.equal(first.utcDateTime, instant);
  assert.equal(first.timeZone, 'America/New_York');
  assert.equal(first.localTime, new Date(instant).toLocaleTimeString());
  assert.equal(first.localDate, new Date(instant).toLocaleDateString());
  assert.equal(first.utcOffsetMinutes, -new Date(instant).getTimezoneOffset());
  instant = '2026-10-15T18:31:00.000Z';
  assert.equal(JSON.parse(await registry.getCurrentTime.execute()).utcDateTime, instant);
  const fallback = load({ DateTimeFormat: () => { throw new Error('Unavailable'); } });
  assert.equal(JSON.parse(fallback.getCurrentTime()).timeZone, 'Unknown');
  assert.equal(JSON.parse(fallback.getCurrentTime()).utcDateTime, instant);
});

test('chat survives a new web module instance and rejects corrupt saved data', () => {
  const data = new Map();
  const localStorage = {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, value),
  };
  const load = () => loadModule('src/agent/chatStorage.ts', {
    'expo-file-system': {}, 'react-native': { Platform: { OS: 'web' } },
  }, { localStorage });
  assert.equal(load().loadChat(), null);
  const messages = [{ id: '1', role: 'user', text: 'Remember this after reload.' }];
  load().saveChat(messages);
  assert.deepEqual(plain(load().loadChat()), messages);
  data.set('entourage.chat.v1', '{broken');
  assert.throws(() => load().loadChat());
  assert.equal(data.get('entourage.chat.v1'), '{broken');
  data.set('entourage.chat.v1', JSON.stringify({ version: 1, messages: [{ role: 'system' }] }));
  assert.throws(() => load().loadChat(), /unsupported format/);
});

test('native chat restores from the document file on a new instance', () => {
  let content = null;
  class File {
    get exists() { return content !== null; }
    textSync() { return content; }
    write(raw) { content = raw; }
  }
  const load = () => loadModule('src/agent/chatStorage.ts', {
    'expo-file-system': { File, Paths: { document: 'documents' } },
    'react-native': { Platform: { OS: 'android' } },
  });
  assert.equal(load().loadChat(), null);
  const messages = [{ id: '2', role: 'assistant', text: 'Saved reply' }];
  load().saveChat(messages);
  assert.deepEqual(plain(load().loadChat()), messages);
});

test('follow-ups receive earlier questions and replies, with the latest prompt once', () => {
  const history = [
    { role: 'user', content: 'My favorite color is teal.' },
    { role: 'assistant', content: 'Got it.' },
  ];
  const messages = plain(buildConversation('What color did I mention?', history));
  assert.equal(messages[0].role, 'system');
  assert.deepEqual(messages.slice(1), [...history, {
    role: 'user', content: 'What color did I mention?',
  }]);
  assert.equal(history.length, 2);
});

test('long chats retain recent complete exchanges and the latest request', () => {
  const history = Array.from({ length: 30 }, (_, index) => ({
    role: index % 2 ? 'assistant' : 'user', content: String(index),
  }));
  const messages = plain(buildConversation('Latest', history));
  assert.equal(messages.length, 14);
  assert.equal(messages[1].content, '18');
  assert.equal(messages.at(-1).content, 'Latest');
});

test('character budget excludes oversized history and orphaned replies', () => {
  const messages = plain(buildConversation('Follow up', [
    { role: 'user', content: 'x'.repeat(7000) },
    { role: 'assistant', content: 'Old reply' },
  ]));
  assert.equal(messages.length, 2);
  assert.equal(messages[1].content, 'Follow up');
});

test('a long latest message is preserved even when history no longer fits', () => {
  const prompt = 'x'.repeat(7000);
  const messages = plain(buildConversation(prompt, [{ role: 'user', content: 'Earlier' }]));
  assert.equal(messages.length, 2);
  assert.equal(messages[1].content, prompt);
});

test('conversational requests go through inference with previous conversation', async () => {
  const location = 'Your location is latitude 40.0000, longitude -73.0000.';
  let received;
  const { runLocalAgent } = loadModule('src/agent/localModel.ts', {
    './llmService': { runLocalLlmInference: async (...args) => {
      received = args;
      return 'A follow-up answer';
    } },
    './toolRegistry': { toolRegistry: {} },
  });
  assert.equal(await runLocalAgent('What can you help me with?'), 'A follow-up answer');
  assert.equal(received[0], 'What can you help me with?');
  const history = [
    { role: 'user', content: 'Where am I?' },
    { role: 'assistant', content: location },
  ];
  assert.equal(await runLocalAgent('What does that mean?', undefined, undefined, history), 'A follow-up answer');
  assert.deepEqual(received, ['What does that mean?', undefined, history, undefined]);
});

test('chat requests share the inference path regardless of wording', async () => {
  const received = [];
  const { runLocalAgent } = loadModule('src/agent/localModel.ts', {
    './llmService': { runLocalLlmInference: async (...args) => {
      received.push(args);
      return 'Model answer';
    } },
  });
  const history = [{ role: 'user', content: 'Earlier question' }];
  const onToolResult = () => {};
  for (const prompt of ['What is your list of tools', 'What tools do you have?',
    'Invoke getCurrentTime now.', 'Check the device capabilities',
    'What device am I using?', "Don't check my device capabilities", 'What is 18 percent of 250?']) {
    assert.equal(await runLocalAgent(`  ${prompt}  `, undefined, undefined, history, onToolResult), 'Model answer');
    assert.deepEqual(received.at(-1), [prompt, undefined, history, onToolResult]);
  }
});

const { runToolLoop } = loadModule('src/agent/toolLoop.ts');
const toolCall = (name = 'getDeviceContext', args = {}) => ({
  id: 'call-1', type: 'function', function: { name, arguments: args },
});

test('model tool requests execute and actual results reach the answering request', async () => {
  let requests = 0;
  let executions = 0;
  const recorded = [];
  const result = await runToolLoop([{ role: 'user', content: 'Invoke getDeviceContext' }], async (messages) => {
    requests += 1;
    if (requests === 1) return { tool_calls: [toolCall()] };
    assert.equal(messages[1].tool_calls[0].function.name, 'getDeviceContext');
    assert.equal(messages[2].role, 'tool');
    assert.equal(messages[2].tool_call_id, 'call-1');
    assert.equal(messages[2].content, 'Actual device result');
    return { content: 'Answer using actual device result' };
  }, { getDeviceContext: { execute: async () => { executions += 1; return 'Actual device result'; } } }, (result) => recorded.push(result));
  assert.equal(result, 'Answer using actual device result');
  assert.equal(executions, 1);
  assert.equal(requests, 2);
  assert.deepEqual(plain(recorded), [{ name: 'getDeviceContext', content: 'Actual device result' }]);
});

test('invalid names and arguments never execute and errors are sent to the model', async () => {
  for (const call of [toolCall('__proto__'), toolCall('getDeviceContext', '{bad'), toolCall('getDeviceContext', []), toolCall('getDeviceContext', 42)]) {
    let requests = 0;
    await runToolLoop([], async (messages) => {
      if (++requests === 1) return { tool_calls: [call] };
      assert.match(messages.at(-1).content, /Tool failed:/);
      return { content: 'Could not execute tool' };
    }, { getDeviceContext: { execute: async () => assert.fail('Must not execute') } });
  }
});

test('no-input tools ignore invented object fields and tolerate omitted arguments', async () => {
  for (const args of [{ device: 'my phone' }, '{"arguments":{}}', null, undefined, '', {}]) {
    let requests = 0;
    let executions = 0;
    const call = toolCall();
    call.function.arguments = args;
    const result = await runToolLoop([], async (messages) => {
      if (++requests === 1) return { tool_calls: [call] };
      assert.equal(messages.at(-1).content, 'Actual device info');
      return { content: 'The real device result' };
    }, { getDeviceContext: { execute: async (...receivedArgs) => {
      assert.equal(receivedArgs.length, 0);
      executions += 1;
      return 'Actual device info';
    } } });
    assert.equal(result, 'The real device result');
    assert.equal(executions, 1);
  }
});

test('tool failures reach the model and multiple calls are handled in one turn', async () => {
  let requests = 0;
  await runToolLoop([], async (messages) => {
    if (++requests === 1) return { tool_calls: [toolCall('getCurrentLocation', '{}'), toolCall()] };
    assert.match(messages[1].content, /permission denied/);
    assert.equal(messages[2].content, 'Device info');
    return { content: 'Location unavailable; here is device info.' };
  }, {
    getCurrentLocation: { execute: async () => { throw new Error('permission denied'); } },
    getDeviceContext: { execute: async () => 'Device info' },
  });
});

test('repeated tool calls stop at the turn limit', async () => {
  let executions = 0;
  const result = await runToolLoop([], async () => ({ tool_calls: [toolCall()] }), {
    getDeviceContext: { execute: async () => { executions += 1; return 'Device info'; } },
  });
  assert.equal(executions, 4);
  assert.match(result, /tool-call limit/);
});

test('ordinary answers execute no tools', async () => {
  assert.equal(await runToolLoop([], async () => ({ content: 'Hello' }), {
    getDeviceContext: { execute: async () => assert.fail('Must not execute') },
  }), 'Hello');
});

test('calculator handles arithmetic and rejects invalid or unsafe inputs', async () => {
  const { calculate, toolRegistry } = loadModule('src/agent/toolRegistry.ts', {
    'expo-device': {}, 'expo-location': {},
  });
  for (const [operation, a, b, expected] of [
    ['add', 12, 7, 19], ['subtract', 12, 20, -8], ['multiply', -3, 7, -21],
    ['divide', 7, 2, 3.5], ['power', 2, 10, 1024], ['percentage', 18, 250, 45],
  ]) assert.equal(JSON.parse(calculate({ operation, a, b })).result, expected);
  for (const args of [undefined, { operation: 'divide', a: 1, b: 0 },
    { operation: 'add', a: '1', b: 2 }, { operation: 'add', a: Infinity, b: 2 },
    { operation: 'power', a: 10, b: 1000 }, { operation: 'eval', a: 1, b: 2 },
    { operation: 'add', a: 1, b: 2, code: 'alert(1)' }]) {
    assert.throws(() => calculate(args));
  }
  const { runToolLoop, getToolDefinitions } = loadModule('src/agent/toolLoop.ts');
  assert.deepEqual(plain(getToolDefinitions(toolRegistry).find((t) => t.function.name === 'calculate')
    .function.parameters.required), ['operation', 'a', 'b']);
  let turn = 0;
  const results = [];
  const answer = await runToolLoop([], async (messages) => {
    if (turn++ === 0) return { tool_calls: [{ function: { name: 'calculate',
      arguments: '{"operation":"percentage","a":18,"b":250}' } }] };
    assert.equal(JSON.parse(messages.at(-1).content).result, 45);
    return { content: '18 percent of 250 is 45.' };
  }, toolRegistry, (result) => results.push(result));
  assert.match(answer, /45/);
  assert.equal(results[0].name, 'calculate');
});
