import type { Conversation, HealthResponse, HistoryImport, ImportPreview, ImportReceipt, Message, MessagePage, Turn } from './serverTypes';

export class AgentApiError extends Error {
  constructor(readonly status: number, message: string) { super(message); }
}

export class AgentClient {
  constructor(readonly endpoint: string, private token = '') {}

  async request<T>(path: string, method = 'GET', body?: unknown, deviceKey?: string): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(`${this.endpoint}/api/v1${path}`, {
        method, signal: controller.signal,
        headers: { ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}), ...(body ? { 'Content-Type': 'application/json' } : {}),
          ...(deviceKey ? { 'X-Device-Key': deviceKey } : {}) },
        body: body ? JSON.stringify(body) : undefined,
      });
      const result = await response.json();
      if (!response.ok) throw new AgentApiError(response.status, result.error?.message || `Agent service returned ${response.status}.`);
      return result as T;
    } finally { clearTimeout(timeout); }
  }

  health = () => this.request<HealthResponse>('/health');
  chat = () => this.request<Conversation>('/chat', 'PUT');
  importChatHistory = (id: string, body: HistoryImport) => this.request<ImportReceipt>(`/chat/imports/${id}`, 'PUT', body);
  register = (id: string, key: string) => this.request(`/devices/${id}`, 'PUT', { key });
  turn = (id: string) => this.request<Turn>(`/turns/${id}`);
  cancel = (id: string) => this.request<Turn>(`/turns/${id}/cancellation`, 'PUT');
  previewImport = (body: HistoryImport) => this.request<ImportPreview>('/import-preview', 'POST', body);
  latest = (conversation: string) => this.request<Turn | null>(`/conversations/${conversation}/latest-turn`);
  submit = (conversation: string, id: string, text: string, device: string) =>
    this.request<Turn>(`/conversations/${conversation}/turns/${id}`, 'PUT', { text, device_id: device });
  deviceResult = (turn: string, request: string, device: string, key: string, content: string) =>
    this.request(`/turns/${turn}/device-results/${request}`, 'PUT', { device_id: device, content }, key);

  async messages(conversation: string): Promise<Message[]> {
    let after = 0;
    const items: Message[] = [];
    for (;;) {
      const page = await this.request<MessagePage>(`/conversations/${conversation}/messages?after=${after}&limit=100`);
      items.push(...page.items);
      if (page.next_after === null) return items;
      after = page.next_after;
    }
  }
}
