import { runLocalLlmInference } from './llmService';
import { type ConversationMessage } from './conversation';
import { type ToolResult } from './toolLoop';

export type LocalModel = {
  id: string;
  name: string;
  size: string;
  quantization: string;
  status: 'ready' | 'loading';
};

export const availableModels: LocalModel[] = [
  {
    id: 'qwen-2.5-1.5b',
    name: 'Qwen 2.5 1.5B',
    size: '1.5B',
    quantization: 'Q4_K_M',
    status: 'ready',
  },
  {
    id: 'llama-3.2-3b',
    name: 'Llama 3.2 3B',
    size: '3B',
    quantization: 'Q4_K_M',
    status: 'ready',
  },
  {
    id: 'custom-gptq',
    name: 'Custom SQ',
    size: '1.6B',
    quantization: 'Q4_0',
    status: 'loading',
  },
];

export const getModelById = (modelId: string): LocalModel =>
  availableModels.find((model) => model.id === modelId) ?? availableModels[0];

export const runLocalAgent = async (
  prompt: string,
  modelId = 'qwen-2.5-1.5b',
  modelPath?: string,
  history: readonly ConversationMessage[] = [],
  onToolResult?: (result: ToolResult) => void,
): Promise<string> => {
  const selectedModel = getModelById(modelId);

  const safePrompt = prompt.trim();
  if (selectedModel.status === 'loading') {
    return `Using ${selectedModel.name} (${selectedModel.quantization}), I am waiting for a real GGUF model payload. The app is prepared for llama.rn, but no local model file is currently selected yet.`;
  }

  const localModelResponse = await runLocalLlmInference(safePrompt, modelPath, history, onToolResult);

  return localModelResponse;
};
