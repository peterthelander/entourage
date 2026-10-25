# Qwen memory comparison

Status: Completed diagnostic comparison; no production model selection made.
Date: October 24, 2026.

## Subsequent state, October 24

This record preserves the original experiment and its deployment boundary. The
[thinking-disabled follow-up](2026-10-24-qwen-thinking-control.md) is complete:
it improved latency but did not preserve overall answer reliability. The later
[browser recovery](2026-10-24-browser-inference-recovery.md) repaired finalization,
context-limit handling, model display and error messages, and aligned the live
HP configuration with the Qwen model already loaded on the Mac. Live thinking
remains low. These later changes do not alter the scores or original traces below.

## Method

Reran the two frozen two-turn personal memory cases from the
[memory-faithfulness study](2026-10-23-memory-faithfulness.md), twice in each
condition: normal retrieval, supplied reviewed articles and supplied complete
sources. All 24 planned Qwen turns completed. Supplied conditions bypass discovery
and ordinary tool budgets; their scores are not production retrieval scores.

The Mac served Qwen3.8-27B Q4_K_M through llama.cpp build b11669-620d2225c.
The model file SHA-256 is
`c600de0300ae8a0eb3a6c0b8b5561b8b96f16bd2c863c2a66c42de29d391a747`.
The engine reported four slots, a 16,384-token context, temperature 1.0,
top-k 20, top-p approximately 0.95 and min-p approximately 0.05. Engine metadata
before and after matched. The production transport requested low reasoning
effort; how the model template interprets it is not a controlled reasoning-depth
comparison. No thinking-mode override from the earlier connection smoke was used.

The bundle snapshot and fixture hashes match the historical gpt-oss-20b MXFP4
baseline. Both use 16,384 context tokens and 2,048 maximum output tokens. The
new runner enforced a 90-second per-inference deadline. Source records,
articles, expectations and production prompts were not tuned for Qwen.

This is a historical comparison of deployable setups, not a randomized experiment
isolating weights. Architecture, quantization, template and sampling can differ.
The original baseline predates the empty-answer execution fix and later diagnostic
validation/deadline safeguards. Its original reports and reviews remain unchanged.

Private frozen inputs, full inference traces, report-bound reviews and comparison
summaries are under ignored `scratch/qwen-comparison-20261024/`. Execution used
temporary stores and a process-local model override; live inference configuration,
shared chat and the published memory pointer were not changed.

## Results

Counts are explicit, unblinded coding-agent judgments of full answers, including
follow-ups and unsupported extra details. These authored development cases are
not an independent holdout or a population quality estimate.

| Condition | gpt-oss pass/fail/unclear | Qwen pass/fail/unclear |
| --- | --- | --- |
| Normal retrieval | 3 / 5 / 0 | 4 / 4 / 0 |
| Supplied articles | 3 / 3 / 2 | 4 / 3 / 1 |
| Supplied complete sources | 2 / 5 / 1 | 7 / 1 / 0 |

Qwen reconstructed the shared-order correction sequence correctly in both
complete-source repeats. It also preserved the estimate, higher authorization
and separate-tip qualifications in both complete-source payment follow-ups.
The remaining complete-source failure asserted that additional items had been
added, although the sources only establish a changed estimate. Explicitly labeled
suggestions were distinguished from claims that the action occurred.

Normal retrieval and article-only correction answers remained variable. Some
divided notices for the same order into different orders based on their totals,
then carried that mistake into follow-ups. Correct tables did not excuse incorrect
summaries. Normal-retrieval payment follow-ups asserted tip/payment mechanics
without reading the originals; article-only evidence omitted those qualifications.
One article-only answer honestly left tip inclusion unknown and was scored unclear
against the complete-source expectations, rather than a complete pass.

All Qwen turns completed without timeout, truncation or tool-loop execution failure.
The run took approximately 21 minutes. Observed median turn times were 69 seconds
for retrieval, 33 for supplied articles and 54 for supplied sources. These include
different work per condition and are descriptive, not controlled provider-speed
comparisons or tokens-per-second measurements.

## Interpretation and next boundary

The strongest signal is improved reasoning with complete evidence already present.
The much smaller normal-retrieval gain does not establish a reliable end-to-end
replacement. Do not describe the aggregate as general memory accuracy.

Next, test the promising setup on the existing positive completion and source-binding
controls, then a broader conversation suite and independently reviewed fresh topics.
Inspect when original-source reads are needed and whether article extraction loses
identifiers or qualifications before adopting a context/retrieval change. Retain the
current source-budget and prompt baselines; do not infer that increasing budgets or
adding prompt rules is already justified. Measure responsiveness alongside accuracy.

## Verification

The report-bound semantic review covers every planned turn; no runs are missing.
Frozen input hashes and stable engine metadata were checked. Lint and TypeScript
checking passed. No application code or live configuration changed.
