import { useState } from 'react';
import { StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { availableModels } from '../agent/localModel';
import type { useModelSettings } from '../hooks/useModelSettings';

type Props = { model: ReturnType<typeof useModelSettings> };

export function ModelSettings({ model }: Props) {
  const [showModelDetails, setShowModelDetails] = useState(false);
  const {
    modelName, selectedModelId, setSelectedModelId, selectedModelPath,
    setSelectedModelPath, modelStatus, isModelLoading, handleLoadModel,
  } = model;
  const hasLongModelPath = selectedModelPath.length > 80;
  return (
    <View style={styles.modelBanner}>
      <View style={styles.modelSummaryRow}>
      <Text
        style={[styles.modelValue, styles.modelSummaryName]}
        numberOfLines={1}
      >
        {modelName}
      </Text>
      <TouchableOpacity
        onPress={() => setShowModelDetails((current) => !current)}
        accessibilityRole="button"
        accessibilityLabel={showModelDetails ? 'Hide model settings' : 'Show model settings'}
        accessibilityState={{ expanded: showModelDetails }}
        style={styles.detailsButton}
      >
        <Text style={styles.detailsButtonText}>
          {showModelDetails ? 'Done' : 'Settings'}
        </Text>
      </TouchableOpacity>
      </View>
      {showModelDetails ? <>
          <View style={styles.modelSelector}>
            {availableModels.map((model) => (
              <TouchableOpacity
                key={model.id}
                style={[
                  styles.modelChip,
                  selectedModelId === model.id && styles.modelChipSelected,
                ]}
                onPress={() => setSelectedModelId(model.id)}
              >
                <Text
                  style={[
                    styles.modelChipText,
                    selectedModelId === model.id && styles.modelChipTextSelected,
                  ]}
                >
                  {model.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.modelInputRow}>
            <TextInput
              style={styles.modelInput}
              value={selectedModelPath}
              onChangeText={setSelectedModelPath}
              placeholder="file:///path/to/model.gguf"
              placeholderTextColor="#7d8798"
              autoCapitalize="none"
              autoCorrect={false}
            />
            <TouchableOpacity
              style={[
                styles.modelLoadButton,
                isModelLoading && styles.modelLoadButtonDisabled,
              ]}
              onPress={handleLoadModel}
              disabled={isModelLoading}
            >
              <Text style={styles.modelLoadButtonText}>
                {isModelLoading ? 'Loading…' : 'Load'}
              </Text>
            </TouchableOpacity>
          </View>

      <Text
        style={[styles.deviceSummary, hasLongModelPath && styles.deviceSummaryCompact]}
        numberOfLines={4}
        ellipsizeMode="tail"
      >
        {modelStatus}
      </Text>
      </> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  modelBanner: {
    backgroundColor: '#0d2235',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: '#1a3b54',
    marginBottom: 14,
  },
  modelSummaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  modelSummaryName: {
    flex: 1,
    fontSize: 14,
  },
  detailsButton: {
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  detailsButtonText: {
    color: '#7dd3fc',
    fontSize: 13,
    fontWeight: '600',
  },
  modelValue: {
    color: '#edf7ff',
    fontSize: 16,
    fontWeight: '600',
  },
  modelSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  modelChip: {
    backgroundColor: '#13314b',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: '#254d6c',
  },
  modelChipSelected: {
    backgroundColor: '#67e8f9',
    borderColor: '#67e8f9',
  },
  modelChipText: {
    color: '#d9f5ff',
    fontSize: 11,
    fontWeight: '700',
  },
  modelChipTextSelected: {
    color: '#031a26',
  },
  modelInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 12,
  },
  modelInput: {
    flex: 1,
    backgroundColor: '#071b2a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#214d69',
    color: '#edf7ff',
    fontSize: 12,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  modelLoadButton: {
    backgroundColor: '#67e8f9',
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 10,
  },
  modelLoadButtonDisabled: {
    backgroundColor: '#38657d',
  },
  modelLoadButtonText: {
    color: '#051b25',
    fontSize: 12,
    fontWeight: '700',
  },
  deviceSummary: {
    color: '#bfe8ff',
    fontSize: 12,
    lineHeight: 18,
    marginTop: 8,
  },
  deviceSummaryCompact: {
    fontSize: 10,
    lineHeight: 14,
  },
});
