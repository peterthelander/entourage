export type ToolCall = {
  type?: string;
  id?: string;
  function: { name: string; arguments: unknown };
};
export type AgentMessage = {
  role: string;
  content: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  tool_name?: string;
  name?: string;
};
export type ModelReply = { content?: string; tool_calls?: ToolCall[] };
export type ExecutableTool = {
  description: string;
  parameters?: Record<string, unknown>;
  execute: (args?: Record<string, unknown>) => Promise<string>;
};
export type ToolResult = { name: string; content: string };

export const getToolDefinitions = (tools: Record<string, ExecutableTool>) =>
  Object.entries(tools).map(([name, tool]) => ({
    type: 'function',
    function: { name, description: tool.description,
      parameters: tool.parameters ?? { type: 'object', properties: {}, required: [], additionalProperties: false } },
  }));

// Keep tool results in this turn's context, including failures, until the model answers.
export const runToolLoop = async (
  initialMessages: AgentMessage[],
  generate: (messages: AgentMessage[]) => Promise<ModelReply>,
  tools: Record<string, ExecutableTool>,
  onToolResult?: (result: ToolResult) => void,
): Promise<string> => {
  const messages = [...initialMessages];
  let callsUsed = 0;
  let pendingCalls: ToolCall[] = [];
  for (;;) {
    if (!pendingCalls.length) {
      const reply = await generate(messages);
      const calls = reply.tool_calls ?? [];
      if (!Array.isArray(calls)) throw new Error('Model returned malformed tool calls.');
      if (!calls.length) return reply.content?.trim() || 'The model returned no answer.';
      if (calls.length + callsUsed > 4) return 'I reached the tool-call limit for this request. Please try a simpler request.';
      callsUsed += calls.length;
      messages.push({ role: 'assistant', content: reply.content ?? '', tool_calls: calls });
      pendingCalls = [...calls];
    }
    while (pendingCalls.length) {
      const call = pendingCalls[0];
      const name = call?.function?.name;
      let content: string;
      try {
        if (!name || !Object.prototype.hasOwnProperty.call(tools, name)) throw new Error('Unknown tool requested.');
        const rawArgs = call.function.arguments;
        const args = typeof rawArgs === 'string'
          ? (rawArgs.trim() ? JSON.parse(rawArgs) : {}) : rawArgs ?? {};
        if (!args || typeof args !== 'object' || Array.isArray(args)) {
          throw new Error('Invalid tool arguments. Retry with an object matching the tool schema. The app generates arguments; the user does not need to supply them.');
        }
        // Only tools with an input schema receive model-provided arguments.
        content = tools[name].parameters
          ? await tools[name].execute(args as Record<string, unknown>)
          : await tools[name].execute();
      } catch (error) {
        content = `Tool failed: ${error instanceof Error ? error.message : String(error)}`;
      }
      messages.push({ role: 'tool', content, tool_name: name || 'unknown', name: name || 'unknown', tool_call_id: call?.id });
      pendingCalls.shift();
      onToolResult?.({ name: name || 'unknown', content });
    }
  }
};
