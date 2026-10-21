import type { Message as SavedMessage } from './chatStorage';
import type { Message as ServerMessage } from './serverTypes';

export type PresentationMessage = {
  id: string;
  role: 'user' | 'assistant';
  kind: 'user' | 'assistant' | 'tool' | 'error';
  text: string;
  createdAt?: string;
};

// ID conventions belong only to the boundary for previously saved/native chats.
export const fromSavedMessage = (message: SavedMessage): PresentationMessage => {
  const legacyTime = /^(?:user|assistant|error|toolresult)-(\d{13})(?:-|$)/.exec(message.id)?.[1];
  return {
    ...message,
    kind: message.role === 'user' ? 'user' : message.id.startsWith('toolresult-') ? 'tool'
      : message.id.startsWith('error-') ? 'error' : 'assistant',
    createdAt: message.createdAt ?? (legacyTime ? new Date(Number(legacyTime)).toISOString() : undefined),
  };
};

export const fromServerMessage = (message: ServerMessage): PresentationMessage => ({
  // Keep existing UI identities stable, but never infer kind from these IDs.
  id: `${message.kind === 'tool' ? 'toolresult' : message.kind === 'error' ? 'error' : message.role}-${message.sequence}`,
  role: message.role === 'user' ? 'user' : 'assistant',
  kind: message.kind,
  text: message.text,
  createdAt: message.created_at,
});
