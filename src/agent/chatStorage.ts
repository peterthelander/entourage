import { File, Paths } from 'expo-file-system';
import { Platform } from 'react-native';

export type Message = { id: string; role: 'user' | 'assistant'; text: string; createdAt?: string };
const STORAGE_KEY = 'entourage.chat.v1';

export const loadChat = (): Message[] | null => {
  let raw: string | null;
  if (Platform.OS === 'web') {
    raw = localStorage.getItem(STORAGE_KEY);
  } else {
    const file = new File(Paths.document, 'chat-v1.json');
    raw = file.exists ? file.textSync() : null;
  }
  if (raw === null) return null;
  const value: unknown = JSON.parse(raw);
  if (!value || typeof value !== 'object' || !('version' in value) || value.version !== 1 ||
      !('messages' in value) || !Array.isArray(value.messages) ||
      !value.messages.every((message: unknown) =>
        message !== null && typeof message === 'object' &&
        'id' in message && typeof message.id === 'string' &&
        'role' in message && (message.role === 'user' || message.role === 'assistant') &&
        'text' in message && typeof message.text === 'string' &&
        (!('createdAt' in message) || (typeof message.createdAt === 'string' &&
          Number.isFinite(Date.parse(message.createdAt)))))) {
    throw new Error('Saved conversation has an unsupported format.');
  }
  return value.messages;
};

export const saveChat = (messages: readonly Message[]): void => {
  const raw = JSON.stringify({ version: 1, messages });
  if (Platform.OS === 'web') {
    localStorage.setItem(STORAGE_KEY, raw);
  } else {
    const file = new File(Paths.document, 'chat-v1.json');
    file.write(raw);
  }
};
