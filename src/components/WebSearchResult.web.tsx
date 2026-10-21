import { MarkdownMessage } from './MarkdownMessage';

export function WebSearchResult({ output }: { output: string }) {
  let data;
  try { data = JSON.parse(output); } catch { return null; }
  if (data?.provider !== 'gemini_google_search' || data.status !== 'results') return null;
  const sources = Array.isArray(data.results) ? data.results : [];
  const html = typeof data.search_suggestions_html === 'string' ? data.search_suggestions_html : '';
  return (
    <section aria-label="Google Search research" style={{ color: '#cde4f5', maxWidth: 620, width: '100%', overflowWrap: 'anywhere', fontSize: 14 }}>
      <details>
        <summary style={{ cursor: 'pointer', padding: 10 }}>Google Search findings and sources</summary>
        <div style={{ padding: '0 10px' }}><MarkdownMessage text={typeof data.summary === 'string' ? data.summary : ''} /></div>
        <ul>
          {sources.map((source: { url?: string; title?: string }, index: number) => {
            if (typeof source.url !== 'string' || !/^https?:\/\//i.test(source.url)) return null;
            return <li key={index}><a href={source.url} target="_blank" rel="noopener noreferrer" style={{ color: '#8ecbff' }}>{source.title || source.url}</a></li>;
          })}
        </ul>
      </details>
      {html ? <iframe
        title="Google Search suggestions"
        sandbox="allow-popups allow-popups-to-escape-sandbox"
        referrerPolicy="no-referrer"
        srcDoc={`<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src https: data:; base-uri 'none'; form-action 'none'"><base target="_blank">${html}`}
        style={{ width: '100%', height: 160, border: 0, background: 'white', borderRadius: 8 }}
      /> : null}
    </section>
  );
}
