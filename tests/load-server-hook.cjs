const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const loadModule = require('./load-ts.cjs');

module.exports = function hookHarness(Client, storage = new Map()) {
  const slots = [], timers = [];
  let cursor = 0, effect, cleanup, previousDeps, clock = 100000, id = 0;
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
    useEffect(callback, dependencies) {
      if (!previousDeps || dependencies.some((value, index) => value !== previousDeps[index])) {
        effect = callback;
        previousDeps = dependencies;
      }
    },
  };
  const context = { exports: {}, require(name) {
    if (name === 'react') return react;
    if (name.endsWith('serverClient')) return { AgentClient: Client, AgentApiError: Error };
    if (name.endsWith('presentationMessage')) return loadModule('src/agent/presentationMessage.ts');
    if (name.endsWith('browserDevice')) return { restoreDevice: () => ({ id: 'device', key: 'key' }),
      createDeviceHandler: () => async () => {} };
    if (name.endsWith('browserHistoryImport')) return { hasSavedHistory: () => false,
      legacyPendingPrompt: () => '', importCompleted: () => false };
    throw new Error(`Unexpected hook boundary: ${name}`);
  }, localStorage: { getItem: (key) => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, value), removeItem: (key) => storage.delete(key) },
  crypto: { randomUUID: () => `request-${++id}` },
  Date: class extends Date { static now() { return clock; } },
  setTimeout: (callback) => { timers.push(callback); return callback; },
  clearTimeout: (callback) => { const index = timers.indexOf(callback); if (index >= 0) timers.splice(index, 1); } };
  const source = fs.readFileSync(path.resolve(__dirname, '../src/hooks/useServerChat.ts'), 'utf8');
  vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, context);
  const render = () => { cursor = 0; return context.exports.useServerChat('https://test'); };
  const settle = () => new Promise((resolve) => setImmediate(resolve));
  return {
    render, storage,
    advance: (milliseconds) => { clock += milliseconds; },
    async mount() { render(); if (cleanup) cleanup(); cleanup = effect(); await settle(); return render(); },
    async poll() { await timers.shift()(); await settle(); return render(); },
    close() { cleanup?.(); },
  };
};
