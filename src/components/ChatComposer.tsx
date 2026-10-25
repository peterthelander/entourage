import type { KeyboardEvent } from 'react';
import { Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

type Props = {
  draft: string;
  setDraft: (text: string) => void;
  chatReady: boolean;
  isThinking: boolean;
  handleSend: () => Promise<void>;
};

export function ChatComposer({ draft, setDraft, chatReady, isThinking, handleSend }: Props) {
  const isWebRuntime = Platform.OS === 'web';
  const disabled = !chatReady || !draft.trim() || isThinking;
  return (
    <>
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          value={draft}
          onChangeText={setDraft}
          placeholder="Ask your private assistant"
          placeholderTextColor="#7d8798"
          multiline
          blurOnSubmit={false}
          onKeyPress={isWebRuntime ? (event) => {
            const keyEvent = event as unknown as KeyboardEvent<HTMLTextAreaElement>;
            if (
              keyEvent.key === 'Enter' &&
              !keyEvent.shiftKey &&
              !keyEvent.nativeEvent.isComposing &&
              keyEvent.nativeEvent.keyCode !== 229
            ) {
              keyEvent.preventDefault();
              if (!keyEvent.repeat) {
                void handleSend();
              }
            }
          } : undefined}
          textAlignVertical="center"
        />
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Send message"
          style={[
            styles.sendButton,
            disabled && styles.sendButtonDisabled,
          ]}
          onPress={handleSend}
          disabled={disabled}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#0b2030',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#183550',
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginTop: 14,
  },
  input: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 10,
    color: '#edf7ff',
    fontSize: 15,
    maxHeight: 120,
  },
  sendButton: {
    backgroundColor: '#67e8f9',
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 12,
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: '#264968',
  },
  sendButtonText: {
    color: '#06131a',
    fontSize: 15,
    fontWeight: '700',
  },
});
