# Inference limits

See [server configuration](../../server/README.md) for supported settings and defaults,
and [service operations](../../server/EXECUTION.md) for portable service operation.
Restart Python after changing server settings. The launcher reads ignored
`server/data/inference.json`; explicit environment variables take precedence.

## Provider and application limits

Python sends configured context/output limits to Ollama as `num_ctx` and
`num_predict`. For llama.cpp, the output limit becomes `max_tokens`; the engine's
context capacity is set when starting the engine. The application context setting
does not resize a running llama.cpp server.

Settings validate supported ranges, but cannot guarantee that a particular model
or machine can support them. Larger contexts consume memory and may increase
latency. The output cap is a ceiling, not a target response length.

## Context selection

The Python service selects recent user/assistant history from the current session,
then applies a character budget with room reserved for instructions, tools and
output. The configured inactivity gap controls session boundaries. See
[current context behavior](../../server/EXECUTION.md#start-python).

This is approximate budgeting, not exact token counting. The latest prompt is
preserved, and accumulated tool results can still exceed engine capacity.
Provider response-size, timeout and tool-call limits remain independent of the
configured output cap.

The deferred native on-device path has its own smaller context policy in
`src/agent/conversation.ts`. It does not determine browser-service behavior.

## Comparing strategies

Use `scripts/compare-context.py` for a repeatable comparison with synthetic
conversation data. Its default mode prepares inputs without contacting inference.
Optional live comparisons record complete inputs, responses and settings; tools
are recorded but never executed. See [context experiments](../experiments/context-experiments.md).
