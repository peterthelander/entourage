import type { AgentClient } from './serverClient';
import type { Turn } from './serverTypes';
import { toolRegistry } from './toolRegistry';

export type BrowserDevice = { id: string; key: string };

export const restoreDevice = (prefix: string): BrowserDevice => {
  let identity: BrowserDevice | null = JSON.parse(localStorage.getItem(prefix + 'device') || 'null');
  if (!identity) {
    identity = { id: crypto.randomUUID(), key: crypto.randomUUID() + crypto.randomUUID() };
    localStorage.setItem(prefix + 'device', JSON.stringify(identity));
  }
  return identity;
};

// One handler per connection lifecycle; keep acknowledgement and retry semantics.
export const createDeviceHandler = (api: AgentClient, prefix: string, getIdentity: () => BrowserDevice) => {
  const resultsInFlight = new Set<string>();
  return async (turn: Turn) => {
    const identity = getIdentity();
    for (const request of turn.device_requests ?? []) {
      if (request.device_id !== identity.id || request.result !== null ||
          request.expires_at * 1000 <= Date.now() || resultsInFlight.has(request.id)) continue;
      resultsInFlight.add(request.id);
      try {
        const key = prefix + 'device-result:' + request.id;
        let record: { status: string; content?: string } | null = JSON.parse(localStorage.getItem(key) || 'null');
        if (!record) {
          localStorage.setItem(key, JSON.stringify({ status: 'started' }));
          let content: string;
          try {
            if (!['getCurrentTime', 'getCurrentLocation', 'getDeviceContext'].includes(request.name) ||
                Object.keys(request.arguments).length) throw new Error('Unsupported device request.');
            content = await toolRegistry[request.name as 'getCurrentTime' | 'getCurrentLocation' | 'getDeviceContext'].execute();
          } catch (failure) { content = `Tool failed: ${String(failure)}`; }
          record = { status: 'completed', content };
          localStorage.setItem(key, JSON.stringify(record));
        }
        const content = record.content ?? 'Tool failed: device operation was interrupted; it was not replayed.';
        await api.deviceResult(turn.id, request.id, identity.id, identity.key, content);
      } finally { resultsInFlight.delete(request.id); }
    }
  };
};
