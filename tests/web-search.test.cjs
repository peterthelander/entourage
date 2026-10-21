const assert = require('node:assert/strict');
const test = require('node:test');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

const { WebSearchResult } = require('./load-web-component.cjs')('src/components/WebSearchResult.web.tsx');
const render = (data) => renderToStaticMarkup(React.createElement(WebSearchResult, {
  output: typeof data === 'string' ? data : JSON.stringify(data),
}));

test('research shows clickable sources, escapes text, and isolates Google suggestion HTML', () => {
  const html = render({ provider: 'gemini_google_search', status: 'results',
    summary: '<script>bad()</script>', results: [
      { title: 'Orchard', url: 'https://example.com' },
      { title: 'Unsafe', url: 'javascript:bad()' },
    ], search_suggestions_html: '<div>Google suggestions</div>' });
  assert.match(html, /href="https:\/\/example.com"/);
  assert.ok(!html.includes('javascript:bad()'));
  assert.ok(!html.includes('<script>'));
  assert.match(html, /sandbox="allow-popups allow-popups-to-escape-sandbox"/);
  assert.match(html, /Google Search suggestions/);
  assert.match(html, /srcDoc=/i);
});

test('failed or malformed research does not display a successful result', () => {
  for (const input of ['invalid', 'null', { status: 'unavailable' },
    { provider: 'gemini_google_search', status: 'no_results' }]) {
    assert.equal(render(input), '');
  }
});
