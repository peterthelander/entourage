import { useRef } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import type { PresentationMessage } from '../agent/presentationMessage';
import { ToolResultMessage } from './ToolResultMessage';
import { MarkdownMessage } from './MarkdownMessage';

type Props = { messages: readonly PresentationMessage[]; isThinking: boolean };

export function ChatMessages({ messages, isThinking }: Props) {
  const scrollViewRef = useRef<ScrollView>(null);
  return (
    <ScrollView
      ref={scrollViewRef}
      style={styles.chatList}
      contentContainerStyle={styles.chatListContent}
      onContentSizeChange={() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }}
    >
      {messages.map((message) => message.kind === 'tool' ? (
        <ToolResultMessage key={message.id} text={message.text} />
      ) : (
        <View
          key={message.id}
          style={
            message.role === 'user'
              ? styles.userBubble
              : styles.assistantBubble
          }
        >
          {message.kind === 'assistant' ? <MarkdownMessage text={message.text} /> : <Text
            style={
              message.role === 'user'
                ? styles.userText
                : styles.assistantText
            }
          >
            {message.text}
          </Text>}
        </View>
      ))}

      {isThinking ? (
        <View style={styles.thinkingBubble}>
          <Text style={styles.thinkingText}>Thinking locally…</Text>
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  chatList: {
    flex: 1,
    borderRadius: 18,
    backgroundColor: '#081b2a',
    borderWidth: 1,
    borderColor: '#0f2940',
  },
  chatListContent: {
    padding: 14,
    gap: 10,
  },
  userBubble: {
    alignSelf: 'flex-end',
    maxWidth: '78%',
    backgroundColor: '#1d5d8b',
    borderRadius: 18,
    borderBottomRightRadius: 6,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  assistantBubble: {
    minWidth: 0,
    alignSelf: 'stretch',
    maxWidth: '100%',
    backgroundColor: '#10283a',
    borderRadius: 18,
    borderBottomLeftRadius: 6,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#1a3b54',
  },
  thinkingBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#122c41',
    borderRadius: 18,
    borderBottomLeftRadius: 6,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#1a3b54',
  },
  userText: {
    color: '#f4fbff',
    fontSize: 15,
    lineHeight: 22,
  },
  assistantText: {
    color: '#e1edf7',
    fontSize: 15,
    lineHeight: 22,
  },
  thinkingText: {
    color: '#9ad8ff',
    fontSize: 15,
    lineHeight: 22,
  },
});
