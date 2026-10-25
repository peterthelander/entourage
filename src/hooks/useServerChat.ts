import { useEffect, useRef, useState } from 'react';
import { AgentClient, AgentApiError } from '../agent/serverClient';
import { createDeviceHandler, restoreDevice, type BrowserDevice } from '../agent/browserDevice';
import { hasSavedHistory, legacyPendingPrompt, importCompleted, previewHistoryImport, commitHistoryImport } from '../agent/browserHistoryImport';
import { fromServerMessage, type PresentationMessage } from '../agent/presentationMessage';
import type { ImportPreview, InferenceStatus, Turn } from '../agent/serverTypes';

type Pending = { conversation: string; id: string; text: string };

export function useServerChat(endpoint: string) {
  const prefix = `entourage.server.v1:${endpoint}:`;
  const [connectionAttempt, setConnectionAttempt] = useState(0);
  const [messages, setMessages] = useState<PresentationMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [model, setModel] = useState('');
  const [inference, setInference] = useState<InferenceStatus | null>(null);
  const [latestTurn, setLatestTurn] = useState<Turn | null>(null);
  const [importPreview, setImportPreview] = useState<ImportPreview | null>(null);
  const [hasLegacy, setHasLegacy] = useState(hasSavedHistory);
  const [legacyPending] = useState(legacyPendingPrompt);
  const client = useRef<AgentClient | null>(null);
  const device = useRef<BrowserDevice | null>(null);
  const currentConversation = useRef('');
  const sending = useRef(false);
  const submissionError = useRef('');
  const refresh = useRef<() => Promise<void>>(async () => {});

  useEffect(() => {
    const api = new AgentClient(endpoint);
    client.current = api;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    let polling = false;
    let checkingInference = false;
    let lastInferenceCheck = 0;
    const serveDevice = createDeviceHandler(api, prefix, () => device.current!);

    const checkInference = async () => {
      if (checkingInference || cancelled) return;
      checkingInference = true;
      try {
        const status = await api.inference();
        if (cancelled) return;
        setInference(status);
        setModel(status.loaded_model || status.configured_model);
      } catch {
        if (!cancelled) {
          setModel('');
          setInference({ status: 'unavailable', configured_model: '',
            message: 'Could not verify the inference server. Check the agent connection.' });
        }
      } finally {
        checkingInference = false;
        lastInferenceCheck = Date.now();
      }
    };

    const poll = async () => {
      if (cancelled || polling || !currentConversation.current) return;
      polling = true;
      try {
        if (Date.now() - lastInferenceCheck >= 15000) void checkInference();
        const identity = device.current!;
        const pending: Pending | null = JSON.parse(localStorage.getItem(prefix + 'pending') || 'null');
        if (pending) {
          try {
            await api.submit(pending.conversation, pending.id, pending.text, identity.id);
            localStorage.removeItem(prefix + 'pending');
          } catch (failure) {
            if (failure instanceof AgentApiError && [403, 404, 409, 422].includes(failure.status)) {
              localStorage.removeItem(prefix + 'pending');
              submissionError.current = `Message was not accepted: ${failure.message}`;
              setDraft(pending.text);
            } else throw failure;
          }
        }
        const selected = currentConversation.current;
        const turn = await api.latest(selected);
        const history = await api.messages(selected);
        if (cancelled || selected !== currentConversation.current) return;
        const rendered = history.map(fromServerMessage);
        if (turn?.partial_answer && !['completed', 'failed', 'needs_review'].includes(turn.status)) {
          rendered.push({ id: `partial-${turn.id}`, role: 'assistant', kind: 'assistant', text: turn.partial_answer });
        }
        setMessages(rendered);
        setLatestTurn(turn);
        // A send may have queued locally while this poll was awaiting history.
        setBusy(Boolean(localStorage.getItem(prefix + 'pending')) ||
          Boolean(turn && ['queued', 'running', 'waiting_for_device'].includes(turn.status)));
        setReady(true);
        setError(submissionError.current || (turn && ['failed', 'needs_review'].includes(turn.status) ? turn.error || 'This turn failed. Try a new request.' : ''));
        if (turn?.status === 'waiting_for_device') void serveDevice(turn).catch((failure) => {
          if (!cancelled) setError(`Could not return device result: ${String(failure)}`);
        });
      } catch (failure) {
        if (!cancelled) setError(`Connection interrupted. Reconnecting… ${String(failure)}`);
      } finally { polling = false; }
    };
    refresh.current = poll;

    const start = async () => {
      try {
        const health = await api.health();
        if (cancelled) return;
        if (!health.execution_enabled) throw new Error('Enable execution on the Python server first.');
        setModel(health.model || 'Server model');
        await checkInference();
        if (cancelled) return;
        const identity = restoreDevice(prefix);
        device.current = identity;
        await api.register(identity.id, identity.key);
        const shared = await api.chat();
        if (cancelled) return;
        if (importCompleted(prefix)) setHasLegacy(false);
        currentConversation.current = shared.id;
        await poll();
        const tick = async () => { await poll(); if (!cancelled) timer = setTimeout(tick, 1000); };
        if (!cancelled) timer = setTimeout(tick, 1000);
      } catch (failure) {
        if (!cancelled) {
          setError(String(failure));
          if (!(failure instanceof AgentApiError && [401, 403].includes(failure.status))) {
            timer = setTimeout(() => void start(), 3000);
          }
        }
      }
    };
    void start();
    return () => { cancelled = true; clearTimeout(timer); client.current = null; };
  }, [endpoint, prefix, connectionAttempt]);

  const reconnect = () => {
    setReady(false);
    setInference(null);
    setModel('');
    setConnectionAttempt((value) => value + 1);
  };
  const inferenceReady = inference?.status === 'ready' || inference?.status === 'configured';
  const handleSend = async () => {
    if (!draft.trim() || !ready || !inferenceReady || busy || latestTurn?.status === 'needs_review' || sending.current) return;
    if (draft.trim().length > 16000) { setError('Please shorten the message to 16,000 characters.'); return; }
    sending.current = true;
    submissionError.current = '';
    try {
      // Guard the durable slot as well as React state, which may be stale.
      if (localStorage.getItem(prefix + 'pending')) { setBusy(true); return; }
      const pending = { conversation: currentConversation.current, id: crypto.randomUUID(), text: draft.trim() };
      localStorage.setItem(prefix + 'pending', JSON.stringify(pending));
      setBusy(true);
      setDraft('');
      await refresh.current();
    } catch (failure) { setError(String(failure)); }
    finally { sending.current = false; }
  };

  const stop = async () => {
    if (!latestTurn) return;
    try { await client.current!.cancel(latestTurn.id); await refresh.current(); }
    catch (failure) { setError(String(failure)); }
  };
  const retry = () => {
    const last = [...messages].reverse().find((message) => message.role === 'user');
    if (last) setDraft(last.text);
  };
  const previewHistory = async () => {
    try {
      setImportPreview(await previewHistoryImport(client.current!, prefix));
    } catch (failure) { setError(String(failure)); }
  };
  const commitHistory = async () => {
    try {
      await commitHistoryImport(client.current!, prefix);
      setImportPreview(null);
      setHasLegacy(false);
      await refresh.current();
    } catch (failure) { setError(String(failure)); }
  };

  return { reconnect, messages, draft, setDraft, error, ready, busy, model, inference, inferenceReady, handleSend,
    latestTurn, stop, retry, hasLegacy, importPreview, previewHistory, commitHistory, legacyPending };
}
