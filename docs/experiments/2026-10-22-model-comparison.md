# Personal-agent model comparison

Status: Complete; three repeats per model and coding-agent rubric review complete.
Independent human review pending. October 22, 2026.

Implementation follow-up, October 22: after completing this frozen comparison,
the Gemini transport moved into `server/entourage_server/gemini.py` and became a
supported service provider. Evaluation and service now share that implementation.
The original reports and their recorded source hashes remain unchanged; the
protocol below describes the code and behavior at the time of the experiment.

## Results and interpretation

Replacing the inference model improved this fixed synthetic suite substantially,
especially recall and handling corrected or conflicting memories. It also made
the agent slower and exposed repeated-search failures under the existing tool
budget. Keep the production model unchanged while investigating these tradeoffs.

| Measure | Local gpt-oss-20b MXFP4 | Gemini 4 Argon |
| --- | ---: | ---: |
| Case runs / user turns | 90 / 135 | 90 / 135 |
| Completed case runs | 90 | 84 |
| Full case rubric passes | 59 | 84 |
| Mechanical passes | 69 | 81 |
| Actual tool calls | 123 | 183 |
| Median turn time, first sequential repeat | 2.186 s | 15.502 s |

Counts include failures; missing-memory refusals are useful only when an answer
actually completes. The six hosted failures all end with the worker's tool-call
limit error: missing-memory in all three repeats, recall-punctuation in repeat 2,
and recall-after-pause and ambiguous-venue in repeat 3. No inference exception or
provider HTTP failure was recorded in either arm. Successful hosted responses
reported at most 721 completion tokens; no rejected/truncated response was
recorded. The adapter groups some invalid completion reasons into a generic error,
so future error analysis should preserve safe structured finish reasons.

| Case category | Local rubric passes | Gemini rubric passes |
| --- | ---: | ---: |
| Continuity | 16 / 18 | 18 / 18 |
| Corrections | 9 / 12 | 12 / 12 |
| Recall | 8 / 18 | 16 / 18 |
| Tool use | 3 / 9 | 9 / 9 |
| Uncertainty | 8 / 12 | 9 / 12 |
| Untrusted data | 8 / 9 | 9 / 9 |
| Web evidence | 7 / 12 | 11 / 12 |

Concrete differences:

- Gemini recovered the rain-garden guides in two repeats; local missed them in
  all three. It recovered paused picnic guests in two repeats; local missed all
  three. The other hosted attempts failed at the tool budget.
- Gemini consistently distinguished current window-seat preference from earlier
  aisle preference, recovered both tentative club venues, and summarized all
  three topics on the requested date. Local often missed these facts or only
  surfaced one alternative.
- Both models produced correct arithmetic. Local's tool-use losses reflect
  skipping the calculator required by the rubric and adding an unspecified dollar
  currency, rather than incorrect numerical results. Gemini used the calculator
  and preserved the follow-up total.
- Local clarified the museum town and gave the correct time, but omitted its
  required source URL in all repeats. Gemini supplied the matching source.
- Gemini repeatedly searched for nonexistent allergy information until the worker
  failed. Local completed with appropriate uncertainty. Better retrieval ability
  does not guarantee better stopping behavior.

The first sequential repeats took 117.262 recorded turn-seconds locally and
1,044.427 hosted. Across mixed pacing, hosted turn times summed to 2,318.944 s
and had a median of 10.719 s; local totals were 337.719 s and 2.186 s. These are
observations from this run, not a throughput or first-token benchmark. Hosted
responses reported 545,134 prompt and 23,166 completion tokens; local usage was
unavailable, not zero. No billing estimate is inferred from those counts.

The shared fixture, runner, adapter, production source hashes, initial inputs,
tool schemas and application settings all matched. Full and filtered segment
case definitions were checked before composing 90 unique case/repeat results.
The reported hosted model alias was `gemini-4-argon` throughout.

These are hand-authored scenarios reviewed by the same coding agent that added
them, without blinding. Repeated cases are correlated; 84/90 is not an estimate
of general personal-agent accuracy. Rubrics are narrow: for example, local's
correct final pottery dates conceal an earlier false calendar-access implication,
and one vegetarian answer incorrectly described yogurt as free of animal products.
Those issues remain in review notes. Food advice was not independently audited.
Some mechanical no-tool checks also reject useful answers with unnecessary
searches. Message-ID formatting remains diagnostic and does not drive rubric
scores. Synthetic pages do not establish real-world browsing quality, and the
suite does not stress the full 16K context limit or long-running journal refresh.

## Next experiments

1. Trace repeated empty memory searches and budget handling. Test a single
   coherent stopping/recovery change against both arms, including useful searches
   that require multiple attempts. Preserve the current comparison as baseline.
2. Run a small blinded human review using natural personal-agent queries and add
   newly observed failures as a separate holdout set. Tighten broad honesty and
   factuality criteria before the next frozen comparison.
3. Investigate local recall inputs/tool selection against Gemini's successful
   traces. Accept harness changes only when they improve repeatable outcomes
   without harming ordinary conversation or uncertainty handling.
4. Compare another practical model/configuration for latency and quality before
   choosing a production provider. This run establishes model sensitivity, not
   whether weight count, quantization, training, provider compute or architecture
   causes the difference. Context size remains an untested factor here.

Local artifacts (ignored `scratch/`): `personal-agent-local.json`, composed
`personal-agent-gemini.json`, preserved `personal-agent-gemini-prefix.json`,
`personal-agent-gemini-r2.json`, `personal-agent-gemini-r3.json`,
`personal-agent-rubric-review.json`, and
`personal-agent-comparison-statistics.json`. The composed report records segment
provenance and repeat mapping. The original 32-result prefix remains intact.

Validation: 102 Python tests, 35 client tests, Expo lint and TypeScript typecheck
passed after the evaluation changes. `git diff --check` passed. Production agent,
model selection and service configuration were not changed by this experiment.

## Question and fixed protocol

Does replacing local gpt-oss-20b MXFP4 with hosted Gemini 4 Argon improve the
current personal agent, without modifying its prompt, memory, context selection,
worker, tools or recovery rules? This compares deployable model/provider setups,
not parameter counts or an isolated training architecture. No production provider
change or service restart is part of this experiment.

Frozen fixture: `server/tests/fixtures/personal-agent-comparison.json`, 30 cases,
45 user turns per complete repeat.
Fixture SHA-256: `3f802b7b37cb8c463fe48e74fb9d0ab1c0d8f813dcbab16c86f96777e361146b`.
Preserve the original ten-case snapshot and
seven-case regression fixture separately. This fixture adds ordinary updates,
short follow-ups, returns after tangents, active preferences, cancelled plans,
ambiguous people, unresolved alternatives, 43-message recall with distractors,
changed preferences, false assistant recollections, dated overviews, originals
before many updates, arithmetic follow-ups, bounded calculations, unavailable
sources, place disambiguation, unsupported booking requests, memory injection,
and a sustained four-turn plan. All names, facts and URLs are synthetic.

Primary evaluation is user-facing correctness, current intent, preserved
constraints/corrections, grounded claims, useful uncertainty, honest capability
claims and completion. Internal message-ID checks are `diagnostic_checks`,
separate from the product checks and primary rubrics. Do not reject a natural
correct answer merely for omitting a message ID. Requested web source links remain
part of the relevant user-facing questions. Mechanical checks are narrow signals,
not semantic verdicts. Perform coding-agent rubric inspection and identify its
limitations; independent human review remains pending.

Run each case three times per model, sequentially within each arm: 180 case runs,
up to 270 user turns. Freeze scenario wording/rubrics before provider pilots;
do not modify fixtures, prompts or retrieval in response to model results.
Compatibility pilots are separate reports and excluded from comparison counts.

Scheduling amendment after the first hosted repeat: the remaining two independent
hosted repeats run in separate concurrent processes to reduce wall-clock waiting.
Every conversation remains sequential; temporary stores and model requests remain
isolated. No case wording, scoring, prompt, model, sampling request or application
limit changes. Preserve raw segment reports and compose the final report with
explicit repeat identities and segment provenance. This changes request pacing,
so use the first sequential hosted repeat for any like-paced timing comparison;
pooled hosted timings describe mixed pacing, not a controlled speed benchmark.
The same number of completed cases/repeats is retained.

At the transition, 32 completed results were preserved (all 30 of repeat 1 and
the first two cases of repeat 2). The remaining 28 cases of repeat 2 and all
30 of repeat 3 run independently. No completed result is discarded or selected
based on its answer. Any unrecorded in-flight work on the next case at operator
interruption is excluded and the case restarts from its fixed initial state.

Both arms use the production worker, temporary SQLite stores, real journal
retrieval, the same system prompt/tool schemas, 16,384 application context tokens,
2,048 maximum output tokens and the four-call budget. Web and page tools receive
the same fixture responses; no Gemini built-in search, file search or other
provider-hosted tools are enabled. Device calls cannot reach a real device.
Multi-turn histories contain each model's actual replies, so later inputs can
appropriately diverge while the initial inputs and user sequence remain fixed.
As in the original synthetic harness, seeded journals are exported at case start;
the production background refresher and browser/device lifecycle are not running.
This isolates the agent loop rather than reproducing the entire live application.

Use production low effort locally and Gemini's low reasoning-effort setting.
These are provider-specific settings, not equal internal compute budgets.
Sampling remains provider-controlled. Local inference streams while the hosted
adapter returns a complete response; compare total turn time, not time to first
token. Tokenizers and provider output/reasoning accounting differ; record usage
where returned and count truncations explicitly. This primary experiment tests
the current operational limits, not each model's maximum context or unlimited
tool/reasoning capacity.

## Provider and artifacts

The existing key's model inventory includes `gemini-4-argon`; metadata is retained
locally in `scratch/gemini-model-inventory.json`. This is Google's documented
[flagship reasoning model](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon).
Use its [OpenAI-compatible API](https://ai.google.dev/gemini-api/docs/openai)
through `scripts/evaluation_gemini.py`, an evaluation-only adapter. Preserve
opaque provider extensions on tool calls for signature-compatible continuation.
Do not serialize credentials or raw provider error bodies. Record model identity
and token usage on responses; stop a batch on provider HTTP failures rather than
treat an access/quota error as 90 independent model-quality failures.

The Google key is read only for explicitly selected live Gemini inference. The
settings object's research key remains a synthetic placeholder: public web-tool
calls are intercepted. Personal history and production SQLite are never opened.

Controls remain the current code after explicit source IDs were introduced.
Reports record fixture, runner, adapter and production source hashes, initial
inputs, model replies/tool calls/results, inference failures and engine snapshots
where available. `evaluated_model` identifies the actual inference model;
`settings` retains shared production application settings/budgets, including the
local configuration, even when hosted inference is explicitly selected.

```powershell
.\server\.venv\Scripts\python.exe scripts/evaluate-conversations.py --live --fixture server/tests/fixtures/personal-agent-comparison.json --repeats 3 --output scratch/personal-agent-local.json
.\server\.venv\Scripts\python.exe scripts/evaluate-conversations.py --live --fixture server/tests/fixtures/personal-agent-comparison.json --repeats 3 --gemini-model gemini-4-argon --output scratch/personal-agent-gemini.json --baseline scratch/personal-agent-local.json
```

Excluded pilots: `scratch/gemini-adapter-pilot.json` (calculator) and
`scratch/gemini-memory-pilot.json` (memory correction/follow-up). Only transport
compatibility is assessed there; pilot outcomes do not change scenario wording.
Source metadata and credentials stay in ignored local files; no keys are placed
in model prompts, command arguments or committed artifacts.
