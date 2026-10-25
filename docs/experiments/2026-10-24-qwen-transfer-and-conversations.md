# Qwen transfer controls and broader conversations

Status: Completed historical comparison; subsequent deployment and follow-up linked below.
Date: October 24, 2026.

Follow-up to the [two-case memory comparison](2026-10-24-qwen-memory-comparison.md).
The question is whether Qwen's complete-source improvement transfers to different
source-binding controls and ordinary personal-agent conversations.

## Subsequent state, October 24

This record preserves the original experiment and its deployment boundary. The
[thinking-disabled follow-up](2026-10-24-qwen-thinking-control.md) is complete:
it improved latency but did not preserve overall answer reliability. The later
[browser recovery](2026-10-24-browser-inference-recovery.md) repaired finalization,
context-limit handling, model display and error messages, and aligned the live
HP configuration with the Qwen model already loaded on the Mac. Live thinking
remains low. These later changes do not alter the scores or original traces below.

## Protocol and comparison boundaries

The same Mac llama.cpp endpoint served Qwen3.8-27B Q4_K_M, build
`b11669-620d2225c`, with 16,384 context tokens, 2,048 maximum output tokens and
production transport low reasoning effort. Sampling remained server-controlled.
Engine metadata matched before and after each experiment. Runs were sequential;
no candidate settings, prompt changes or source-context interventions were added.

1. Four fictional two-turn source-binding controls, twice each, using the unchanged
   reviewed transfer bundle and normal production retrieval. The diagnostic runner
   used a 90-second per-inference deadline and froze the bundle, code and expectations.
2. One complete sequential pass of the frozen 30-case/45-turn personal-agent suite.
   Compare with the retained first sequential gpt-oss pass, not its aggregate
   three-repeat result. The standard runner retains its production transport
   timeout. Cases, history, rubrics and code hashes were recorded before inference.

The transfer fixture and bundle hashes match the historical control. The broader
fixture definitions, all 30 initial model inputs and tool schemas match the
historical local report. Runner, adapter and production source code have changed
since the October 22 baseline; notably finalization and empty-answer handling
evolved. Exact changed-file hashes remain in the private artifacts. These are
historical comparisons of deployable setups, not an isolated weights experiment.
There was no new gpt-oss run on today's harness. Speed observations likewise do
not isolate model architecture, reasoning depth, sampling or engine conditions.

Evaluation uses temporary databases, synthetic device/web fixtures and process-local
model overrides. No live chat, actual device actions, public website calls,
published memory pointer or live inference configuration was changed. The broader
suite does not measure real website accessibility or search coverage.

All answers were reviewed by the coding agent against frozen expectations and
rubrics. This is unblinded development evidence, not independent validation.
Private traces, freeze manifests, report hashes, per-answer/per-criterion reviews
and summaries are under ignored `scratch/qwen-comparison-20261024/`.

## Source-binding and positive completion controls

| Measure | Historical gpt-oss | Qwen |
| --- | ---: | ---: |
| Planned/completed turns | 16 / 16 | 16 / 16 |
| Whole-answer passing turns | 12 | 15 |
| Failing turns | 4 | 1 |

Both Qwen repeats preserved separate order identities, ordered notices across
different UTC offsets, recognized a completed repair with a settled $96 charge
and zero balance, and retained the nonrefundable benefit-performance exception.
Attendance and refund eligibility remained unknown where evidence was absent.
Thus gains did not come only from refusing to recognize documented outcomes.

The one failure was an unnecessary calculation: the answer correctly listed a
2 PM to 11 AM change but called the time-of-day difference 3.5 hours. The second
repeat did not repeat the error. Correct core facts do not excuse an additional
incorrect factual claim. Median Qwen turn time was approximately 28 seconds.

## Broader conversation results

| Measure, first sequential pass | Historical gpt-oss | Qwen |
| --- | ---: | ---: |
| Case runs / planned turns | 30 / 45 | 30 / 45 |
| Completed turns | 45 | 44 |
| Full-case rubric passes | 21 | 25 |
| Median recorded turn time | 2.186 s | 20.027 s |

A case passes only if every frozen product-rubric criterion passes across all its
turns. These case scores are not comparable units to the per-turn transfer scores.
The mechanical checks passed 28 Qwen cases, illustrating why they are insufficient
as the semantic score. All planned cases and turns were retained; there were no
missing cases or discarded failed runs. Recorded Qwen turn time sums to about
15 minutes, not a throughput or first-token benchmark.

| Category | Cases | gpt-oss passes | Qwen passes |
| --- | ---: | ---: | ---: |
| Continuity | 6 | 6 | 5 |
| Recall | 6 | 3 | 6 |
| Corrections | 4 | 3 | 4 |
| Uncertainty | 4 | 3 | 2 |
| Web evidence | 4 | 3 | 2 |
| Untrusted data | 3 | 2 | 3 |
| Tool use | 3 | 1 | 3 |

Seven previously failing cases passed: paused picnic recall, punctuation-sensitive
guide recall, changed seat preference, user evidence versus assistant recollection,
dated topic overview, calculator follow-up and bounded calculation. Three
previously passing cases failed: missing allergy information, ambiguous event
source links and sustained home-plan recap. Net four additional case passes does
not mean every category improved.

### Five failed Qwen cases

- **Missing allergy information:** after three searches, a requested two-tool
  batch would exceed four executed calls. The worker entered answer-only
  finalization, whose inference raised a sanitized `RuntimeError`. No successful
  uncertainty answer resulted. The trace does not establish whether the reply
  was truncated, malformed or failed for another transport reason; do not label
  it a confirmed repeated-tool finalization failure.
- **Ambiguous event:** correctly asked which of two events the user meant, but
  omitted source URLs for the listed factual event details.
- **Unresolved venue conflict:** retrieved only tentative Library Room evidence,
  answered definitively and missed the alternative Station Cafe proposal.
- **Museum follow-up:** identified the town and correct 10 AM opening time but
  omitted the URL required by the rubric.
- **Sustained home planning:** quantities were correctly scaled from six to four,
  and food remained vegetarian and olive-free. The final requested plan recap
  omitted the puzzle and quiet at-home activity, failing the continuity criterion.

### Additional defects retained outside the frozen rubric score

The dated-topic answer retrieved all three correct topics but duplicated its
entire answer with a literal `</think>` marker. It passes the frozen content
rubric, not a broader claim of flawless presentation. The review also records
unnecessary narration of a historical injection, unspecified currency in the
bounded calculation, an Earl Grey classification error in a snack suggestion and
verbose responses. Currency was handled consistently with the historical review:
it is an explicit failure criterion for the calculator follow-up, but only a
recorded additional issue in the bounded-calculation case. Do not quietly change
the old rubric to make a preferred model win.

## Decision and next experiment

Qwen warrants further evaluation: its improvement extends beyond the original
two personal topics, particularly in recall and recognizing explicit outcomes.
The latency cost and uncertainty/retrieval failures prevent calling it an
unqualified replacement. No production configuration change was made.

The next bounded experiment should address the practical operating tradeoff:
measure whether less thinking or a different inference configuration can retain
the source-binding and positive-completion gains at acceptable latency. Keep a
frozen set of both successes and failures and change one setting at a time;
record template behavior rather than assume `low` has equal meaning across
models. Preserve first failed turns. Better safe diagnostic detail for rejected
finish reasons is needed before attributing the finalization failure to a specific
cause. Neither a larger tool budget nor a prompt rule is established as a fix.

A second/third repeat of the broader suite and independent human/source review
on fresh topics remain necessary before a reliable generalization claim. The
current results do not validate automatic synthesis/publication or larger-archive
ingestion.

## Verification

Report-bound reviews cover every planned control turn and broader case/criterion.
Frozen file identities, matched baseline inputs and stable engine metadata were
checked. Lint, TypeScript checking and diff whitespace checks passed. No
application code or live configuration was changed.
