/* global __dirname */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

// Load pure TypeScript helpers with explicit runtime boundaries, without Expo.
module.exports = function loadModule(file, dependencies = {}, globals = {}) {
  const filename = path.resolve(__dirname, '..', file);
  const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS },
  }).outputText;
  const context = { ...globals, exports: {}, require: (name) => {
    if (name in dependencies) return dependencies[name];
    assert.ok(name.startsWith('.'), `Unexpected dependency: ${name}`);
    return module.exports(path.resolve(path.dirname(filename), name + '.ts'), dependencies, globals);
  } };
  vm.runInNewContext(compiled, context, { filename });
  return context.exports;
};
