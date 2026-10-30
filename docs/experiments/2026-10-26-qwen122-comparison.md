# Qwen122 versus the current local baselines

Date: October 26, 2026 (America/New_York).
Status: Closed October 26, 2026; owner selected Qwen122 for now.
Evaluation: Three broader repeats and unblinded coding-agent review complete; independent review absent.

Qwen3.5-122B-A10B UD-IQ3_S passes 77/90 case runs, versus current-service
Qwen3.8-27B Q4_K_M low thinking at 75/90 and Qwen3-Coder-Next Q4_K_M at 65/90.
Its median whole-turn time is 8.162 seconds, about half the 27B setup's time.
The owner has selected this model for ongoing use for now and closed this
model-selection round. The small aggregate quality lead does not establish a
reliable accuracy improvement. Different cases regress,
and coding ability has not been evaluated.

## Activation and comparison conditions

The owner loaded the Mac model. Entourage's ignored local inference selection
was aligned, and the Windows scheduled service restarted after checking for active
turns. Authenticated readiness, private HTTPS health and the calculator smoke
passed: one executed calculator call, final answer 156. The new model remains
active. Successful inference establishes operation, not measured memory headroom
or freedom from swapping on the 64 GB M2 Max.

The unchanged authored fixture contains **30 distinct scenarios**, repeated three
times: **90 case runs and 135 user turns** per setup. These are repeated scenarios,
not 90 distinct questions. All 135 turns completed for each of the three current
setups. Cases use isolated temporary stores and synthetic web/device responses;
the live knowledge pointer is unchanged.

Fixture, runner, evaluation adapter, production source hashes, initial system and
conversation inputs, and tool definitions match the
[current 27B comparison](2026-10-26-qwen-current-baseline.md) and the
[three-repeat Coder-Next report](2026-10-25-coder-next-comparison.md).
Application context is 16,384 tokens, output 2,048, session gap 60 minutes and
tool budget four calls. Engine build is `b11669-620d2225c`. Qwen122 reports one
16,384-token slot and structured tool support; 27B reported four slots with the
same per-slot context, Coder-Next one.

The Qwen122 template reports no reasoning-effort support and content-only
generation. The adapter's low-effort request therefore does not establish matched
reasoning compute with 27B. Its captured sampling defaults include temperature
0.6 and top-k 20; the earlier setups reported temperature 1.0, with differing
templates and top-k. Engine metadata stays stable within the batch. Hardware load,
thermal state and sampling randomness were not controlled. These are comparisons
of running setups, not an isolated test of parameter count or quantization.

Rubrics predate inference. Full answers and tool results were reviewed by the
coding agent without blinding; there is no independent reviewer or fresh holdout.
Mechanical checks, semantic case success and additional defects are separate.
Private raw results, frozen plan, report-bound review and paired summary are in
ignored `scratch/qwen122-20261026/`. Original reports remain unchanged.

## Results

| Measure | Qwen122 IQ3_S | Qwen27 Q4, low thinking | Coder-Next Q4 |
| --- | --- | --- | --- |
| Full-case rubric passes | 77/90 | 75/90 | 65/90 |
| Passes by repeat | 26, 26, 25 | 24, 25, 26 | 22, 22, 21 |
| Completed user turns | 135/135 | 135/135 | 135/135 |
| Median turn time, all repeats | 8.162 s | 15.439 s | 2.489 s |
| Per-repeat median seconds | 8.012, 7.890, 8.621 | 15.715, 14.906, 16.384 | 2.553, 2.207, 2.564 |
| Executed tool calls | 108 | 122 | 84 |
| Answers with literal tool-call markup | 0 | 3 | 0 |
| Answers with closing thinking markers | 0 | 2 | 0 |

Whole-turn timing includes tool activity, not just token generation. Skipped or
unsuccessful retrieval can reduce latency, so this is not equal-work throughput.

| Category | Qwen122 | Qwen27 | Coder-Next |
| --- | --- | --- | --- |
| Continuity | 16/18 | 17/18 | 16/18 |
| Corrections | 12/12 | 12/12 | 7/12 |
| Recall | 16/18 | 17/18 | 15/18 |
| Uncertainty | 6/12 | 4/12 | 6/12 |
| Web evidence | 9/12 | 7/12 | 6/12 |
| Untrusted data | 9/9 | 9/9 | 9/9 |
| Tool use | 9/9 | 9/9 | 6/9 |

Qwen122 answers all three missing-allergy cases with useful uncertainty instead
of the 27B setup's literal tool-call output. All three ambiguous-event cases ask
for identifying detail without choosing an unsupported event, and all three
mixed-occasion cases avoid inventing a combined guest list. The latter two are
valid clarification responses under the existing rubric, even where a mechanical
check expects more retrieval. It also retains all three extended home plans.

However, all three two-Alex cases fail after unsuccessful literal searches;
27B retrieves and distinguishes both people in all three. All three unresolved
venue cases still fail: two promote a tentative Library Room suggestion, while
one fails to find either alternative. All three museum follow-ups omit their
required source URL despite correct opening hours. One punctuation-sensitive
guide lookup fails, as does one dated-topic overview: it treats the requested
2026 date as future based on its knowledge cutoff rather than retrieving memories.

Two picnic follow-ups add unsupported household/family participants to the guest
list. They fail the no-invented-plans criterion under a conservative reading.
Because the wording partly qualifies those participants, these are borderline:
accepting both would give 79/90 instead of 77/90. Neither reading establishes a
decisive quality advantage over 75/90 on this small repeated development set.

Additional defects remain visible outside the frozen score: a correctly tracked
workshop date is initially described as over a year away, unsupported dollar
notation appears in the bounded arithmetic case, and some answers narrate rejected
injections or imply records were updated. Replies are often much longer than
requested. The frozen date-correction rubric checks old/current date mapping and
external booking/reminder claims; it was not expanded after seeing the incorrect
relative-time statement. A score of 77/90 is not a count of completely flawless
answers.

## Decision and deferred investigations

The [earlier comparison](2026-10-25-coder-next-comparison.md) preserves gpt-oss-20b
at 59/90 and Gemini 4 Argon at 84/90, both across three repeats. Their prompts and
worker versions differ from this matched current-service group. The old 27B
low-thinking and thinking-disabled samples remain 25/30 and 24/30, respectively;
the latter has not been expanded to three current-service repeats. Do not multiply
those scores into hypothetical 90-run results. Six Gemini user turns did not
complete, whereas all turns completed in the three current local conditions.

**Decision, October 26:** settle on Qwen3.5-122B-A10B UD-IQ3_S for now,
retaining the current 16,384-token context, 2,048-token application output limit
and one inference slot. The service is already using this model; no additional
configuration change is needed. This line of model-selection work is closed.
27B and Coder-Next remain recorded comparison results.

Further downloads, quantization/reasoning sweeps and repeat comparisons are
deferred. Known retrieval, ambiguity and citation weaknesses remain documented;
they do not require keeping model selection open. Revisit the choice if everyday
use exposes a material limitation or a specific coding-client requirement calls
for evaluation.

The older real-memory, source-supplied and overview experiments have **not** been
run on Qwen122. Better personal-memory synthesis and long-running coding
reliability therefore remain unproven. Evidence-discovery controls and real coding
tasks are possible future investigations if this work is reopened, not pending
steps required to close this selection round.

Frozen source identities, all 90 review entries/135 turns, rubric identity,
report hashes and unchanged live knowledge pointer were verified. Lint,
TypeScript checking and whitespace checks passed. No application code or prompt
was changed for this comparison.
