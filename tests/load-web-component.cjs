/* global __dirname */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

module.exports = function loadWebComponent(file) {
  const filename = path.resolve(__dirname, '..', file);
  const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  const context = { exports: {}, require: (name) => name.startsWith('.')
    ? module.exports(path.resolve(path.dirname(filename), name + '.web.tsx')) : require(name) };
  vm.runInNewContext(compiled, context, { filename });
  return context.exports;
};
