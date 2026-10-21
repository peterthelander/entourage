import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { KeyboardAvoidingView, Platform, StyleSheet, Text, View } from 'react-native';
import { useChat } from './src/hooks/useChat';
import { useModelSettings } from './src/hooks/useModelSettings';
import { ModelSettings } from './src/components/ModelSettings';
import { ChatMessages } from './src/components/ChatMessages';
import { ChatComposer } from './src/components/ChatComposer';
import { CopyLatestExchange } from './src/components/CopyLatestExchange';
import { ServerChat } from './src/components/ServerChat';

export default function App() {
  const endpoint = process.env.EXPO_PUBLIC_AGENT_SERVER_URL?.trim().replace(/\/+$/, '') ||
    (typeof window !== 'undefined' && !['localhost', '127.0.0.1'].includes(window.location.hostname)
      ? `${window.location.origin}/agent` : 'http://127.0.0.1:8000');
  if (Platform.OS === 'web') {
    return <SafeAreaProvider><SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <ServerChat key={endpoint} endpoint={endpoint} />
    </SafeAreaView></SafeAreaProvider>;
  }
  return <LocalApp />;
}

function LocalApp() {
  const model = useModelSettings();
  const chat = useChat(model.selectedModelId, model.selectedModelPath);
  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safeArea}>
        <StatusBar style="light" />
        <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
          <View style={styles.appShell}>
            <View style={styles.header}>
              <Text style={styles.title}>Entourage</Text>
              <View style={styles.statusPill}>
                <View style={styles.statusDot} />
                <Text style={styles.statusText}>Local</Text>
              </View>
            </View>
            {chat.storageError ? <Text accessibilityRole="alert" style={styles.error}>{chat.storageError}</Text> : null}
            {!chat.chatReady ? <Text style={styles.restoring}>Restoring conversation…</Text> : null}
            <ModelSettings model={model} />
            <ChatMessages messages={chat.messages} isThinking={chat.isThinking} />
            <CopyLatestExchange messages={chat.messages} model={model.modelName} busy={!chat.chatReady || chat.isThinking} />
            <ChatComposer
              draft={chat.draft}
              setDraft={chat.setDraft}
              chatReady={chat.chatReady}
              isThinking={chat.isThinking}
              handleSend={chat.handleSend}
            />
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#07131f',
  },
  container: {
    flex: 1,
    backgroundColor: '#07131f',
  },
  appShell: {
    flex: 1,
    paddingHorizontal: 18,
    paddingTop: 10,
    paddingBottom: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  title: {
    color: '#f3f7ff',
    fontSize: 26,
    fontWeight: '700',
    marginTop: 2,
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#12314a',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderWidth: 1,
    borderColor: '#1f5f7d',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#5eead4',
    marginRight: 6,
  },
  statusText: {
    color: '#dffaf6',
    fontSize: 12,
    fontWeight: '700',
  },
  error: { color: '#ffb4ab', padding: 12 },
  restoring: { color: '#ffffff', padding: 12 },
});
