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

Initial history selection still uses approximate budgeting. The latest prompt is
preserved, and accumulated tool results can exceed the planned budget. Large
llama.cpp transcripts additionally use `/apply-template` and `/tokenize` on the
configured engine before generation, counting the actual template and tool
definitions and reserving the requested output allowance. Hash-heavy source IDs
can tokenize much more densely than ordinary prose.

When a tool-enabled request no longer fits after retrieval, the worker can make
one answer-only finalization attempt with the same evidence and no tool
definitions. Its instruction is part of the initial system message, not an extra
system turn after the tool results. If the answer-only request also exceeds the
budget, it fails with a context-limit message. When preflight measured the request,
the message includes input tokens, reserved response tokens and configured context
capacity. A larger llama.cpp context requires changing the engine startup setting
and the agent setting together. No source text is silently cut off.
Oversized user prompts, engine capacity differing from configured capacity, and
output exhaustion can still fail. A model's thinking consumes its output budget;
the output-limit message distinguishes this from a lost server connection.
Provider response-size, timeout and tool-call limits remain independent of the
configured output cap.

The deferred native on-device path has its own smaller context policy in
`src/agent/conversation.ts`. It does not determine browser-service behavior.

## Comparing strategies

Use `scripts/compare-context.py` for a repeatable comparison with synthetic
conversation data. Its default mode prepares inputs without contacting inference.
Optional live comparisons record complete inputs, responses and settings; tools
are recorded but never executed. See [context experiments](../experiments/context-experiments.md).
