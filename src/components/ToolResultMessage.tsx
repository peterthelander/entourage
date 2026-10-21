import { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { WebSearchResult } from './WebSearchResult';

const toolLabels: Record<string, string> = {
  calculate: 'Calculator',
  getCurrentTime: 'Time',
  getCurrentLocation: 'Location',
  getDeviceContext: 'Device information',
  searchMemories: 'Memory search',
  getMemoryInventory: 'Memory inventory',
  readMemories: 'Read memories',
  searchWeb: 'Web search',
  readWebPage: 'Read web page',
};

export function ToolResultMessage({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const separator = text.indexOf('\n');
  const name = (separator === -1 ? text : text.slice(0, separator)).trim();
  const output = separator === -1 ? '' : text.slice(separator + 1);
  let searchFailed = false;
  if (name === 'searchWeb' || name === 'readWebPage') {
    try { searchFailed = JSON.parse(output).status !== (name === 'searchWeb' ? 'results' : 'read'); } catch { searchFailed = true; }
  }
  const failed = output.startsWith('Tool failed:') ||
    searchFailed ||
    (name === 'getCurrentLocation' && output.startsWith('Location permission was denied'));
  const toolName = toolLabels[name] ? `${toolLabels[name]} (${name})` : name || 'Tool';
  const label = `${toolName} ${failed ? 'unavailable' : 'completed'}`;

  return (
    <View style={styles.container}>
      <TouchableOpacity
        onPress={() => setExpanded((current) => !current)}
        accessibilityRole="button"
        accessibilityLabel={`${label}. ${expanded ? 'Hide' : 'Show'} details`}
        accessibilityState={{ expanded }}
        style={styles.toggle}
      >
        <Text style={[styles.label, failed && styles.failed]}>
          {failed ? '!' : '✓'} {label}
        </Text>
        <Text style={styles.chevron}>{expanded ? '▴' : '▾'}</Text>
      </TouchableOpacity>
      {expanded ? <Text selectable style={styles.details}>{text}</Text> : null}
      {name === 'searchWeb' ? <WebSearchResult output={output} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignSelf: 'flex-start', maxWidth: '100%' },
  toggle: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    minHeight: 44, paddingHorizontal: 10,
  },
  label: { color: '#9bb6c9', fontSize: 12, flexShrink: 1 },
  failed: { color: '#edba91' },
  chevron: { color: '#9bb6c9', fontSize: 12 },
  details: {
    color: '#9bb6c9', fontSize: 12, lineHeight: 18,
    paddingHorizontal: 10, paddingBottom: 8,
  },
});
