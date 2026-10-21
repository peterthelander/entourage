import { loadChat } from './chatStorage';
import type { AgentClient } from './serverClient';
import type { HistoryImport } from './serverTypes';

type ImportDraft = { id: string; body: HistoryImport; completed?: boolean };

export const hasSavedHistory = (): boolean => {
  try { return Boolean(loadChat()?.some((message) => message.id !== 'welcome')); } catch { return true; }
};

export const legacyPendingPrompt = (): string => {
  try { return JSON.parse(localStorage.getItem('entourage.pending-turn.v1') || 'null')?.prompt || ''; }
  catch { return ''; }
};

const readImport = (prefix: string): ImportDraft | null =>
  JSON.parse(localStorage.getItem(prefix + 'import') || 'null');

export const importCompleted = (prefix: string): boolean => Boolean(readImport(prefix)?.completed);

export const previewHistoryImport = async (api: AgentClient, prefix: string) => {
  let record = readImport(prefix);
  if (!record) {
    const history = loadChat();
    if (!history?.length) throw new Error('No saved browser history was found.');
    record = { id: crypto.randomUUID(), body: { messages: history } };
    localStorage.setItem(prefix + 'import', JSON.stringify(record));
  }
  return api.previewImport(record.body);
};

export const commitHistoryImport = async (api: AgentClient, prefix: string) => {
  const record = readImport(prefix)!;
  await api.importChatHistory(record.id, record.body);
  localStorage.setItem(prefix + 'import', JSON.stringify({ ...record, completed: true }));
};
