import { useEffect, useRef, useState } from 'react';
import { loadChat, saveChat, type Message } from '../agent/chatStorage';
import { runLocalAgent } from '../agent/localModel';
import { fromSavedMessage } from '../agent/presentationMessage';

const initialMessages: Message[] = [
  {
    id: 'welcome',
    role: 'assistant',
    text:
      'Hi, I’m Entourage. What’s on your mind?',
  },
];

// Retained native on-device chat; browser conversations belong to the Python server.
export function useChat(selectedModelId: string, selectedModelPath: string) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [chatReady, setChatReady] = useState(false);
  const [storageError, setStorageError] = useState('');
  const storageReadable = useRef(false);
  const [draft, setDraft] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const requestInFlight = useRef(false);

  useEffect(() => {
    try {
      const saved = loadChat();
      if (saved) setMessages(saved);
      storageReadable.current = true;
    } catch {
      setStorageError('Could not restore saved chat. Existing saved data has been kept; new messages may not be saved.');
    } finally {
      setChatReady(true);
    }
  }, []);

  useEffect(() => {
    if (!chatReady || !storageReadable.current || isThinking) return;
    try {
      saveChat(messages);
      setStorageError('');
    } catch {
      setStorageError('Could not save this conversation. Keep this window open to retain the current messages.');
    }
  }, [messages, chatReady, isThinking]);

  const handleSend = async () => {
    const trimmed = draft.trim();
    if (!chatReady || !trimmed || requestInFlight.current) {
      return;
    }
    requestInFlight.current = true;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: trimmed,
      createdAt: new Date().toISOString(),
    };

    setMessages((current) => [...current, userMessage]);
    setDraft('');
    setIsThinking(true);

    try {
      const assistantText = await runLocalAgent(
        trimmed,
        selectedModelId,
        selectedModelPath,
        messages
          .filter((message) => message.id !== 'welcome' && !message.id.startsWith('error-'))
          .map((message) => ({ role: message.role, content: message.text })),
        (result) => {
          setMessages((current) => [...current, {
          id: `toolresult-${Date.now()}-${current.length}`,
          role: 'assistant',
          text: `${result.name}\n${result.content}`,
          createdAt: new Date().toISOString(),
          }]);
        },
      );

      setMessages((current) => [...current, {
        id: `assistant-${Date.now()}`, role: 'assistant', text: assistantText, createdAt: new Date().toISOString(),
      }]);
    } catch (error) {
      setMessages((current) => [...current, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        text: `Could not complete this request: ${error instanceof Error ? error.message : String(error)}`,
        createdAt: new Date().toISOString(),
      }]);
    } finally {
      requestInFlight.current = false;
      setIsThinking(false);
    }
  };

  return { messages: messages.map(fromSavedMessage), chatReady, storageError, draft, setDraft, isThinking, handleSend };
}
