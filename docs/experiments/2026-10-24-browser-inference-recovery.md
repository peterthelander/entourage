# Browser inference failure diagnosis and recovery

Status: Causes reproduced; harness, display and error handling repaired and deployed.
Date: October 24, 2026.

## Observations and cause separation

A phone screenshot showed the old gpt-oss filename after the Mac had switched
to Qwen, plus a generic execution error following three successful memory calls.
Simple greetings still worked. At investigation time the HP agent was no longer
listening, while the Mac inference endpoint was healthy.

The saved failed turn reached answer-only finalization after three executed calls.
Replaying its exact finalization request against the same Mac returned HTTP 500:
the Qwen Jinja template requires system messages at the beginning. The worker had
appended a system message after tool results. Moving that instruction into the
initial system message made the replay complete with HTTP 200 and `stop`, using
the unchanged 16,384 context and 2,048 output limits. No extra tools executed.

An independent earlier failed turn contained a pasted debugging exchange. Exact
template/tokenizer measurement found 18,289 input tokens against a 16,384-token
slot, a genuine separate context overflow. Its answer-only form still exceeded
capacity. The screenshot's normalized finalization input measured 13,696 tokens,
which fits with the requested output allowance; context overflow was not needed
to explain that failure. Do not infer that all earlier generic errors had one
cause. The old reports and original failed turns remain preserved.

The model label was a configuration/display problem: HP still named gpt-oss,
and the UI presented that configured string as the running model. Restart alone
would not correct an unchanged model setting. The prior experiments intentionally
used process-local overrides and had not changed deployment configuration.

Private checkpoints, requests/replies, token measurements, successful UI retry,
and phone-width screenshot remain in ignored `scratch/browser-failure-20261024/`.
SQLite, previous settings and the memory pointer were backed up under ignored
service data before reconfiguration; the successful UI retry was backed up again
before the final restart. Accepted knowledge was not changed.

## Changes

- Tool-limit and context-pressure recovery share one bounded answer-only path.
  The instruction is merged into the first system message; tool evidence and
  tool IDs stay intact. Rejected extra calls never execute.
- Large llama.cpp transcripts use the running engine's chat template and tokenizer
  before inference, including tool definitions and the response allowance.
  Context pressure after retrieval can trigger one answer-only attempt; if that
  still cannot fit, the failure is explicit. This supplements approximate initial
  history selection, not a universal guarantee that every request can fit.
- Safe messages distinguish template rejection, context overflow, exhausted output
  allowance, connection/timeouts and other HTTP failures. Raw upstream bodies and
  private prompt text are not exposed as user errors.
- A separate authenticated inference-status endpoint checks loaded llama.cpp IDs
  and aliases against configuration. Process liveness remains separate. The UI
  displays the loaded model, shortens filesystem paths for readability, and warns
  and disables new sends on mismatch/unavailability while keeping history readable.
  Status refreshes periodically and on browser reload/reconnect. Other providers
  remain explicitly configured rather than falsely verified.
- Memory article/source rows have readable labels and unavailable source reads
  are not labeled completed. Send's visual disabled state matches its behavior.

## Regression coverage and live verification

The strict-template transport/worker regression reproduces three executed calls
followed by an over-budget two-call batch. It checks completion with exactly
three tool results, tools disabled during finalization and no later system role.
Additional tests cover actual-token preflight, bounded context recovery, failure
when evidence still cannot fit, distinct safe error causes, and absence of a
fabricated completed answer on failure.

Model-status tests cover swaps, explicit aliases, offline engines and malformed
metadata. Hook lifecycle tests cover reload, periodic model changes, retained
drafts, blocked sends and failed-turn restoration. Rendered React Native Web
component tests cover the visible model, mismatch/error/retry controls, Send
disabled state and knowledge-tool labels. These assert rendered states rather
than providing pixel-by-pixel screenshot regression testing.

Live verification includes the corrected failed-turn replay, an authenticated
calculator exchange through Tailscale and an explicit retry of the user's memory
request through the browser at 390-pixel phone width. That retry completed with
three memory calls and a displayed answer; the failure/retry banner cleared and
the header showed Qwen. This establishes execution/display recovery, not complete
semantic reliability of memory answers.

The HP service was restarted with its configured model matching the loaded Qwen
file. Thinking mode and context/output limits were not changed as a repair. The
separate thinking-disabled evaluation retains an exact pre-repair harness snapshot
so harness fixes are not attributed to that inference setting.

Validation after the functional changes: 151 Python server tests and 44 JavaScript
tests passed; Expo lint and TypeScript typecheck passed. Phone-width browser
screenshot proof is retained privately in `scratch/browser-failure-20261024/phone-success.png`.

## Failure messages

Known causes now retain separate safe explanations through persisted turn errors
and the rendered browser alert:

| Cause | Explanation and next step |
| --- | --- |
| Context window exceeded | Input plus reserved output tokens exceed capacity; measured counts are shown when preflight is available. Shorten the request or retrieved history, or coordinate a larger context in llama-server and agent settings. |
| Output token limit | The model did not finish within its response budget; thinking shares that budget. Shorten the request or adjust the output setting. |
| Prompt template rejected | The model rejected the conversation format; check template compatibility. |
| Connection failed | Check that inference is running and the Mac is reachable. |
| Timeout | Inference took too long; try a shorter request or check whether the model is busy. |
| Interrupted stream | No completed answer was saved; retry and inspect inference if it repeats. |
| Other upstream HTTP failure | Show the HTTP status without exposing raw server response bodies. |

Unknown exceptions still use a generic fallback rather than claiming an
unconfirmed cause. Raw upstream bodies, credentials and private prompt contents
are not copied into user-facing errors. Display regression coverage checks each
known explanation and the explicit retry control.
