import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useServerChat } from '../hooks/useServerChat';
import { ChatMessages } from './ChatMessages';
import { ChatComposer } from './ChatComposer';
import { CopyLatestExchange } from './CopyLatestExchange';

export function ServerChat({ endpoint }: { endpoint: string }) {
  const chat = useServerChat(endpoint);
  return <View style={styles.container}>
    <Text style={styles.title}>Entourage</Text>
    {chat.model ? <Text style={styles.label}>{chat.model}</Text> : null}
    {!chat.ready ? <Text style={styles.label}>Connecting to your agent…</Text> : null}
    {chat.error ? <Text accessibilityRole="alert" style={styles.error}>{chat.error}</Text> : null}
    {chat.error && !chat.ready ? <TouchableOpacity accessibilityRole="button" onPress={chat.reconnect}><Text style={styles.button}>Reconnect</Text></TouchableOpacity> : null}
    {chat.ready && chat.legacyPending ? <View>
      <Text style={styles.label}>An old request is preserved in this browser. It will not run automatically.</Text>
      <TouchableOpacity accessibilityRole="button" onPress={() => chat.setDraft(chat.legacyPending)}>
        <Text style={styles.button}>Copy old request into draft</Text>
      </TouchableOpacity>
    </View> : null}
    {chat.ready && chat.hasLegacy ? <View>
      {!chat.importPreview ? <TouchableOpacity accessibilityRole="button" onPress={() => void chat.previewHistory()}>
        <Text style={styles.button}>Preview saved browser history</Text>
      </TouchableOpacity> : <View>
        <Text style={styles.label}>Import {chat.importPreview.users} user messages, {chat.importPreview.assistants} replies,
          {' '}{chat.importPreview.tools} tool results and {chat.importPreview.errors} errors into this chat. The browser copy will be kept.</Text>
        <TouchableOpacity accessibilityRole="button" onPress={() => void chat.commitHistory()}><Text style={styles.button}>Import saved history</Text></TouchableOpacity>
      </View>}
    </View> : null}
    {chat.ready && (chat.busy || chat.latestTurn?.status === 'needs_review') ?
      <TouchableOpacity accessibilityRole="button" onPress={() => void chat.stop()}>
        <Text style={styles.button}>{chat.busy ? 'Stop request' : 'Dismiss interruption'}</Text>
      </TouchableOpacity> : null}
    {chat.ready && chat.latestTurn?.status === 'failed' ?
      <TouchableOpacity accessibilityRole="button" onPress={chat.retry}><Text style={styles.button}>Copy request to retry</Text></TouchableOpacity> : null}
    <ChatMessages messages={chat.messages} isThinking={chat.busy} />
    <CopyLatestExchange messages={chat.messages} model={chat.model} busy={!chat.ready || chat.busy} />
    <ChatComposer draft={chat.draft} setDraft={chat.setDraft} chatReady={chat.ready && chat.latestTurn?.status !== 'needs_review'} isThinking={chat.busy}
      handleSend={chat.handleSend} />
  </View>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#07131f', padding: 18 },
  title: { color: '#f3f7ff', fontSize: 26, fontWeight: '700' },
  label: { color: '#dffaf6', paddingVertical: 6 },
  button: { color: '#5eead4', padding: 12 },
  error: { color: '#ffb4ab', paddingVertical: 8 },
});
