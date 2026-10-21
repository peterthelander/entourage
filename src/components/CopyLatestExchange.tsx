import * as Clipboard from 'expo-clipboard';
import { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import type { PresentationMessage } from '../agent/presentationMessage';
import { formatLatestExchange } from '../agent/exchangeExport';

export function CopyLatestExchange({ messages, model, busy }: {
  messages: readonly PresentationMessage[];
  model: string;
  busy: boolean;
}) {
  const [status, setStatus] = useState('');
  const [copying, setCopying] = useState(false);
  const [fallback, setFallback] = useState('');
  const [copiedExchange, setCopiedExchange] = useState<string | null>(null);
  const text = formatLatestExchange(messages, model);
  const disabled = busy || copying || !text;

  const copy = async () => {
    if (disabled || !text) return;
    setCopying(true);
    setCopiedExchange(text);
    setFallback('');
    try {
      // Invoke directly from the tap so mobile browsers retain user activation.
      const copied = await Clipboard.setStringAsync(text);
      if (!copied) throw new Error('Clipboard unavailable');
      setStatus('Copied');
    } catch {
      setStatus('Could not copy. Select the text below to copy manually.');
      setFallback(text);
    } finally {
      setCopying(false);
    }
  };

  return (
    <View>
      <View style={styles.row}>
        <Text accessibilityLiveRegion="polite" style={styles.status}>{copiedExchange === text ? status : ''}</Text>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Copy latest exchange"
          accessibilityHint="Copies the latest query, responses, timestamps, and recorded tool results."
          accessibilityState={{ disabled }}
          disabled={disabled}
          onPress={copy}
          style={[styles.button, disabled && styles.disabled]}
        >
          <Text style={styles.label}>{copying ? 'Copying…' : 'Copy latest'}</Text>
        </TouchableOpacity>
      </View>
      {fallback && copiedExchange === text ? <Text selectable style={styles.fallback}>{fallback}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  status: { flex: 1, color: '#9bb6c9', fontSize: 12 },
  button: { minHeight: 44, paddingHorizontal: 12, justifyContent: 'center' },
  disabled: { opacity: 0.4 },
  label: { color: '#7dd3fc', fontSize: 13, fontWeight: '600' },
  fallback: { color: '#dffaf6', fontSize: 12, lineHeight: 18, maxHeight: 160 },
});
