import { Directory, File, Paths } from 'expo-file-system';
import { Platform } from 'react-native';
import { buildConversation, type ConversationMessage } from './conversation';
import { toolRegistry } from './toolRegistry';
import { getToolDefinitions, runToolLoop, type ToolResult } from './toolLoop';

export type LocalModelPathConfig = {
  resolvedPath?: string;
  hasModel: boolean;
};

export const DEFAULT_MODEL_FILENAME = 'qwen2.5-1.5b-instruct-q4_k_m.gguf';
export const DEFAULT_MODEL_PATH = '';
export const DEFAULT_MODEL_DOWNLOAD_URL =
  'https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf';

const isRemoteModelUrl = (value: string): boolean =>
  /^https?:\/\//i.test(value.trim());

const isWebRuntime = Platform.OS === 'web';

const getNativeLlamaRuntime = async () => {
  const llamaRuntime = await import('llama.rn');
  return {
    initLlama: llamaRuntime.initLlama,
    loadLlamaModelInfo: llamaRuntime.loadLlamaModelInfo,
  };
};

export const getDefaultModelPath = (): string => {
  if (isWebRuntime) {
    return '';
  }

  const baseDirectory = Paths.document.uri ?? 'file://';
  return `${baseDirectory}models/${DEFAULT_MODEL_FILENAME}`;
};

export const downloadModelToDevice = async (
  sourceUrl: string,
  fileName = DEFAULT_MODEL_FILENAME,
): Promise<string> => {
  if (isWebRuntime) {
    throw new Error(
      'Direct model file download is only available in native builds. Web mode uses a local HTTP LLM endpoint.',
    );
  }

  const normalizedUrl = sourceUrl.trim();
  if (!normalizedUrl) {
    throw new Error('A model download URL is required.');
  }

  const modelsDirectory = new Directory(Paths.document, 'models');
  modelsDirectory.create({ intermediates: true, idempotent: true });

  const destination = new File(modelsDirectory, fileName);
  const downloadedFile = await File.downloadFileAsync(normalizedUrl, destination, {
    idempotent: true,
  });

  if (!downloadedFile?.uri) {
    throw new Error('The model download did not provide a usable file path.');
  }

  return downloadedFile.uri;
};

export const getModelPathConfig = (customPath?: string): LocalModelPathConfig => {
  const initialPath = customPath?.trim() || getDefaultModelPath();
  const resolvedPath = initialPath || getDefaultModelPath();
  const isExpectedModelFile =
    resolvedPath.toLowerCase().endsWith('.gguf') ||
    resolvedPath.toLowerCase().endsWith('.ggml') ||
    isRemoteModelUrl(resolvedPath);

  return {
    resolvedPath,
    hasModel: resolvedPath.length > 0 && isExpectedModelFile,
  };
};

export const ensureModelOnDevice = async (
  pathOrUrl?: string,
): Promise<string> => {
  if (isWebRuntime) {
    return '';
  }

  const candidate = pathOrUrl?.trim() || getDefaultModelPath();
  const candidateFile = candidate && !isRemoteModelUrl(candidate) ? new File(candidate) : null;

  if (candidateFile) {
    const info = await candidateFile.info();
    if (info.exists) {
      return candidate;
    }
  }

  const localTarget = getDefaultModelPath();
  const downloaded = await downloadModelToDevice(
    isRemoteModelUrl(candidate) ? candidate : DEFAULT_MODEL_DOWNLOAD_URL,
    DEFAULT_MODEL_FILENAME,
  );

  if (downloaded) {
    return downloaded;
  }

  return localTarget;
};

const formatRuntimeError = (error: unknown): string => {
  const message = error instanceof Error ? error.message : String(error ?? '');

  if (
    message.includes("install of null") ||
    message.includes('RNLlama') ||
    message.includes('JSI bindings not installed') ||
    message.includes('TurboModuleRegistry')
  ) {
    return 'The llama.rn native module is not available in this app build. This project requires a native development build, not Expo Go. Rebuild the app with `npx expo run:ios` or `npx expo run:android`, or create an EAS development build.';
  }

  return String(error ?? 'Unknown runtime error');
};

const getNestedValue = (source: unknown, path: string): unknown => {
  const segments = path.split('.');
  let current: unknown = source;

  for (const segment of segments) {
    if (!current || typeof current !== 'object' || !(segment in current)) {
      return undefined;
    }
    current = (current as Record<string, unknown>)[segment];
  }

  return current;
};

const summarizeModelMetadata = (modelInfo: unknown): string => {
  if (!modelInfo || typeof modelInfo !== 'object') {
    return 'model metadata is available';
  }

  const name =
    getNestedValue(modelInfo, 'general.name') ??
    getNestedValue(modelInfo, 'general.model_name') ??
    getNestedValue(modelInfo, 'model_name') ??
    'This model';

  const architecture =
    getNestedValue(modelInfo, 'general.architecture') ??
    getNestedValue(modelInfo, 'architecture') ??
    'unknown';

  const contextLength =
    getNestedValue(modelInfo, 'general.context_length') ??
    getNestedValue(modelInfo, 'context_length') ??
    'unknown';

  return `${String(name)} • ${String(architecture)} • context ${String(contextLength)}`;
};

export const checkLocalLlmModel = async (
  modelPath?: string,
): Promise<string> => {
  if (isWebRuntime) {
    return 'Browser inference is managed by the Python agent service.';
  }

  const { resolvedPath, hasModel } = getModelPathConfig(modelPath);

  if (!hasModel || !resolvedPath) {
    return 'No GGUF model file is currently selected. Add a local model asset or paste a Hugging Face model URL to activate the llama.rn runtime.';
  }

  try {
    const { loadLlamaModelInfo } = await getNativeLlamaRuntime();
    const file = new File(resolvedPath);
    const fileInfo = await file.info();
    if (!fileInfo.exists) {
      return `The model file is not present on this device yet: ${resolvedPath}`;
    }

    const modelInfo = await loadLlamaModelInfo(resolvedPath);
    return `Model ready at ${resolvedPath}. ${summarizeModelMetadata(modelInfo)}.`;
  } catch (error) {
    return `Local model is configured, but model metadata could not be loaded: ${formatRuntimeError(error)}`;
  }
};

export const runLocalLlmInference = async (
  prompt: string,
  modelPath?: string,
  history: readonly ConversationMessage[] = [],
  onToolResult?: (result: ToolResult) => void,
): Promise<string> => {
  if (isWebRuntime) {
    throw new Error('Browser inference must use the Python agent service.');
  }

  const { resolvedPath, hasModel } = getModelPathConfig(modelPath);

  if (!hasModel || !resolvedPath) {
    return 'The local model runtime is ready to initialize, but no GGUF file is selected yet. Once a model is added, llama.rn can load it on-device.';
  }

  try {
    const { initLlama } = await getNativeLlamaRuntime();
    const fileInfo = await new File(resolvedPath).info();
    if (!fileInfo.exists) {
      return `The selected model file does not exist on this device: ${resolvedPath}. Download or copy a valid GGUF into the app storage first.`;
    }

    const context = await initLlama({
      model: resolvedPath,
      use_mlock: false,
      n_ctx: 4096,
      n_gpu_layers: 20,
    });

    try {
      return await runToolLoop(buildConversation(prompt, history), async (messages) => {
        const result = await context.completion(
          {
            messages,
            jinja: true,
            tools: getToolDefinitions(toolRegistry),
            tool_choice: 'auto',
            parallel_tool_calls: false,
            n_predict: 256,
            stop: ['</s>', '<|eot_id|>', '<|end_of_text|>'],
          },
          () => undefined,
        );

        return { content: result.content || result.text, tool_calls: result.tool_calls };
      }, toolRegistry, onToolResult);
    } finally {
      await context.release();
    }
  } catch (error) {
    return `The llama.rn runtime is installed and ready, but local model initialization failed: ${formatRuntimeError(error)}`;
  }
};

