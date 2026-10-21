import type { Message as SavedMessage } from './chatStorage';
import { fromSavedMessage, type PresentationMessage } from './presentationMessage';

function diagnosticText(message: PresentationMessage): string {
  if (message.kind !== 'tool' || !message.text.startsWith('searchWeb\n')) return message.text;
  try {
    const result = JSON.parse(message.text.slice('searchWeb\n'.length));
    if (!result || typeof result !== 'object' || Array.isArray(result)) return message.text;
    const { search_suggestions_html: suggestions, ...evidence } = result;
    if (typeof suggestions !== 'string') return message.text;
    return `searchWeb\n${JSON.stringify({ ...evidence,
      search_suggestions_display: `HTML omitted from diagnostic copy (${suggestions.length} characters); retained in saved result`,
    })}`;
  } catch { return message.text; }
}

export const formatLatestExchange = (input: readonly (SavedMessage | PresentationMessage)[], model: string): string | null => {
  const messages = input.map((message) => 'kind' in message ? message : fromSavedMessage(message));
  let start = messages.length - 1;
  while (start >= 0 && messages[start].role !== 'user') start--;
  if (start < 0) return null;
  const exchange = messages.slice(start);
  const tools = exchange.filter((message) => message.kind === 'tool');
  const entries = exchange.map((message) => {
    const label = message.role === 'user' ? 'User query'
      : message.kind === 'tool' ? 'Tool call / result'
        : message.kind === 'error' ? 'Agent error' : 'Agent response';
    return `${label} [${message.createdAt ?? 'Timestamp unavailable'}]\n${diagnosticText(message)}`;
  });
  return ['Entourage — latest exchange', `Model: ${model}`,
    `Tool calls recorded: ${tools.length ? tools.length : 'none'}`,
    ...entries].join('\n\n');
};
