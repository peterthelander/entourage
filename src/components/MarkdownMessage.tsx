import { Text } from 'react-native';

// Native inference is deferred; browser rendering lives in the .web component.
export function MarkdownMessage({ text }: { text: string }) {
  return <Text selectable style={{ color: '#e1edf7', fontSize: 15, lineHeight: 22 }}>{text}</Text>;
}
