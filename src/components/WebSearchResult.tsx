// The supported lookup UI is the browser. Keep the deferred native path type-correct.
export function WebSearchResult({ output }: { output: string }) {
  void output;
  return null;
}
