import { useEffect, useState } from 'react';
import { availableModels, getModelById } from '../agent/localModel';
import {
  checkLocalLlmModel, DEFAULT_MODEL_FILENAME,
  downloadModelToDevice, ensureModelOnDevice, getDefaultModelPath,
} from '../agent/llmService';

export function useModelSettings() {
  const [selectedModelId, setSelectedModelId] = useState(availableModels[0].id);
  const [selectedModelPath, setSelectedModelPath] = useState(
    getDefaultModelPath(),
  );
  const [modelStatus, setModelStatus] = useState(
    `Default device-local model path: ${getDefaultModelPath()}`,
  );
  const [isModelLoading, setIsModelLoading] = useState(false);
  useEffect(() => {
    const checkStatus = async () => {
      const status = await checkLocalLlmModel(selectedModelPath);
      setModelStatus(status);
    };

    checkStatus();
  }, [selectedModelPath]);

  const handleLoadModel = async () => {
    const trimmedPath = selectedModelPath.trim();
    setIsModelLoading(true);
    setModelStatus('Checking model file on this device…');

    try {
      if (!trimmedPath) {
        const fallbackPath = getDefaultModelPath();
        setModelStatus('Downloading the default Qwen model to device storage…');
        const resolvedPath = await ensureModelOnDevice(fallbackPath);
        setSelectedModelPath(resolvedPath);
        setModelStatus(`Model downloaded to device storage: ${resolvedPath}`);
        return;
      }

      const isRemoteDownload = /^https?:\/\//i.test(trimmedPath);
      if (isRemoteDownload) {
        setModelStatus('Downloading model from URL to this device…');
        const downloadedPath = await downloadModelToDevice(
          trimmedPath,
          DEFAULT_MODEL_FILENAME,
        );
        setSelectedModelPath(downloadedPath);
        setModelStatus(`Model downloaded to device storage: ${downloadedPath}`);
        const status = await checkLocalLlmModel(downloadedPath);
        setModelStatus(status);
        return;
      }

      const resolvedPath = await ensureModelOnDevice(trimmedPath);
      setSelectedModelPath(resolvedPath);
      setModelStatus(`Validating model at ${resolvedPath}`);
      const status = await checkLocalLlmModel(resolvedPath);
      setModelStatus(status);
    } catch (error) {
      setModelStatus(`Model preparation failed: ${String(error)}`);
    } finally {
      setIsModelLoading(false);
    }
  };

  return {
    selectedModelId, setSelectedModelId, selectedModelPath, setSelectedModelPath,
    modelStatus, isModelLoading, handleLoadModel,
    modelName: getModelById(selectedModelId).name,
  };
}
