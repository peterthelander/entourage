import { memo, type ReactNode } from 'react';
import Markdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

const plugins = [remarkGfm];

// Size short values to their contents; bound prose so wide tables still wrap.
function TableCellContent({ children }: { children: ReactNode }) {
  return <div style={{ width: 'max-content', maxWidth: '28ch', whiteSpace: 'normal', overflowWrap: 'anywhere' }}>{children}</div>;
}

const components: Components = {
  p: ({ children }) => <p style={{ margin: '0 0 10px', whiteSpace: 'pre-wrap' }}>{children}</p>,
  h1: ({ children }) => <h1 style={{ fontSize: 23, lineHeight: 1.3, margin: '12px 0 8px' }}>{children}</h1>,
  h2: ({ children }) => <h2 style={{ fontSize: 20, lineHeight: 1.3, margin: '12px 0 8px' }}>{children}</h2>,
  h3: ({ children }) => <h3 style={{ fontSize: 17, lineHeight: 1.4, margin: '12px 0 8px' }}>{children}</h3>,
  ul: ({ children }) => <ul style={{ paddingLeft: 24, margin: '6px 0 12px' }}>{children}</ul>,
  ol: ({ children, start }) => <ol start={start} style={{ paddingLeft: 24, margin: '6px 0 12px' }}>{children}</ol>,
  li: ({ children }) => <li style={{ marginBottom: 5 }}>{children}</li>,
  a: ({ children, href }) => href
    ? <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: '#8ecbff', textDecoration: 'underline' }}>{children}</a>
    : <span>{children}</span>,
  pre: ({ children }) => <pre style={{ overflowX: 'auto', maxWidth: '100%', padding: 12, borderRadius: 8, background: '#081b2a', whiteSpace: 'pre' }}>{children}</pre>,
  code: ({ children }) => <code style={{ fontFamily: 'monospace', fontSize: '0.9em', background: '#081b2a', borderRadius: 3, padding: '1px 3px' }}>{children}</code>,
  blockquote: ({ children }) => <blockquote style={{ borderLeft: '3px solid #547b98', margin: '8px 0', paddingLeft: 12, color: '#b2cbdc' }}>{children}</blockquote>,
  table: ({ children }) => <div role="region" aria-label="Table" tabIndex={0} style={{ overflowX: 'auto', maxWidth: '100%', margin: '10px 0' }}>
    <table style={{ width: 'max-content', tableLayout: 'auto', borderCollapse: 'collapse', fontSize: 14, overflowWrap: 'normal' }}>{children}</table>
  </div>,
  th: ({ children, style }) => <th style={{ ...style, border: '1px solid #36556d', padding: '8px 10px', verticalAlign: 'top', textAlign: style?.textAlign ?? 'left', background: '#16344b' }}><TableCellContent>{children}</TableCellContent></th>,
  td: ({ children, style }) => <td style={{ ...style, border: '1px solid #36556d', padding: '8px 10px', verticalAlign: 'top' }}><TableCellContent>{children}</TableCellContent></td>,
  // External images are not needed for text answers; retain the supplied description.
  img: ({ alt }) => <span>{alt}</span>,
};

export const MarkdownMessage = memo(function MarkdownMessage({ text }: { text: string }) {
  return <div style={{ color: '#e1edf7', fontFamily: 'inherit', fontSize: 15, lineHeight: '22px', minWidth: 0, maxWidth: '100%', overflowWrap: 'anywhere' }}>
    <Markdown remarkPlugins={plugins} components={components} skipHtml
      urlTransform={(url) => /^(https?:\/\/|mailto:)/i.test(url) ? url : ''}
    >{text}</Markdown>
  </div>;
});
