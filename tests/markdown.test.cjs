const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const { MarkdownMessage } = require('./load-web-component.cjs')('src/components/MarkdownMessage.web.tsx');
const render = (text) => renderToStaticMarkup(React.createElement(MarkdownMessage, { text }));

test('assistant Markdown renders headings, emphasis, lists, links, tables and code', () => {
  const html = render('# Orchard\n\n**Apples** and *cider*.\n\n- Pick apples\n- [Official site](https://example.com)\n\n| Item | Cost |\n| --- | --- |\n| Cider | $5 |\n\n```js\nconst stars = "**";\n```');
  for (const tag of ['h1', 'strong', 'em', 'ul', 'li', 'a', 'table', 'th', 'td', 'pre', 'code']) {
    assert.ok(html.includes('<' + tag), `Missing ${tag}`);
  }
  assert.ok(!html.includes('**Apples**'));
  assert.match(html, /target="_blank" rel="noopener noreferrer"/);
  assert.match(html, /overflow-x:auto/);
  assert.ok(html.includes('**')); // Literal Markdown inside a code block is preserved.
});

test('untrusted Markdown cannot inject HTML, script links, or remote images', () => {
  const html = render('<script>alert(1)</script>\n\n[bad](javascript:alert%281%29)\n\n![Picture](https://example.com/track.png)');
  assert.ok(!html.includes('<script'));
  assert.ok(!html.includes('javascript:'));
  assert.ok(!html.includes('<img'));
  assert.ok(!html.includes('track.png'));
  assert.ok(html.includes('Picture'));
});

test('plain text and incomplete streaming Markdown remain renderable', () => {
  assert.ok(render('Hello & goodbye').includes('Hello &amp; goodbye'));
  assert.ok(render('Here is **an unfinished').includes('an unfinished'));
  assert.ok(render('3 * 4 = 12').includes('3 * 4 = 12'));
});
