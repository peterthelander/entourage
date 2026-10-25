/* global __dirname */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

// Render the actual shared React Native components using their web primitives.
// Boundary overrides keep network hooks and platform clipboard outside SSR.
module.exports = function loadComponent(file, dependencies = {}) {
  const cache = new Map();
  const load = (filename) => {
    if (cache.has(filename)) return cache.get(filename);
    const exports = {};
    cache.set(filename, exports);
    const source = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
    }).outputText;
    vm.runInNewContext(source, { exports, require: (name) => {
      if (name in dependencies) return dependencies[name];
      if (name === 'react-native') return require('react-native-web');
      if (!name.startsWith('.')) return require(name);
      const base = path.resolve(path.dirname(filename), name);
      const resolved = ['.web.tsx', '.tsx', '.ts'].map((extension) => base + extension)
        .find((candidate) => fs.existsSync(candidate));
      if (!resolved) throw new Error(`Cannot resolve ${name}`);
      return load(resolved);
    } }, { filename });
    return exports;
  };
  return load(path.resolve(__dirname, '..', file));
};
