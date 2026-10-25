# Ongoing work streams

Status: Active development overview; next steps are proposals, not scheduled work.
Updated: October 25, 2026.

The goal is a capable personal agent with natural conversation, useful recall and
reliable tools. These work streams connect everyday use, evaluation and targeted
experiments. Detailed findings belong in experiment records; implementation
limitations belong in the [technical backlog](technical-debt.md).

## Current state, October 25

The supported browser -> HP Python service -> Mac llama.cpp path is running
Qwen3.8-27B Q4_K_M with low thinking, a 16,384-token context and a 2,048-token
output allowance. Model identity is verified separately from service health.
Machine addresses, startup details and backups remain in the ignored local runbook.

The reported browser failures are repaired: strict-template finalization, context
pressure handling, stale model labeling and cause-specific error messages. A
phone-width retry and authenticated Tailscale calculator check succeeded. The
regression suite passes 163 Python tests and 46 JavaScript tests, plus lint and
typecheck. Rendered component and hook tests cover the display and refresh
behavior; automated pixel screenshot comparison is not implemented. See the
[recovery record](experiments/2026-10-24-browser-inference-recovery.md).

The model comparison and thinking-disabled experiment are complete. Disabling
thinking reduced broader-suite median latency from 20.027 to 11.642 seconds,
but full-case rubric passes fell from 25/30 to 24/30 and thinking-marker leaks
increased from one answer to four. Keep thinking low. These exploratory results
do not establish general reliability; see the
[thinking-control record](experiments/2026-10-24-qwen-thinking-control.md).

The reviewed memory expansion is live: 69 sources and 27 articles, retaining the
previous 33 sources and nine articles. A seeded sample across mailbox/year strata
broadened historical coverage to 2005–2026. Original source hashes, bounded readers
and live retrieval through the phone's HTTPS route were verified. This is manual
curation from a bounded sample, not autonomous or full-archive ingestion.

Subsequent user feedback confirms richer recall, but the live overview mixed major
life areas with incidental episodes and added unsupported inferences. Its sole
recorded call read the flat inventory, not the supporting articles or journal
contents. The immediate agreed next experiment is thematic synthesis and
question-appropriate prioritization over the existing memory before another
volume increase. No synthesis or importance-ranking change has been implemented.
An [offline overview comparison](experiments/2026-10-24-memory-overview.md) now
separates inventory-only answers, complete selected article evidence, and the
same evidence with snapshot-bound editorial themes. This is experimental tooling,
not a live synthesis layer or automatic significance ranking.
Its completed first comparison did not justify adopting the thematic candidate:
both evidence conditions still overclaimed in broad overviews and timed out on
the first follow-up. A supplied-evidence detail control passed without grouping;
the grouped answer recovered the facts but added an unsupported attendance
inference. Retain the controls and investigate source binding before expansion.
Fresh-topic independent validation and latency that preserves answer quality
remain cross-cutting priorities. See the
[expansion and live feedback](experiments/2026-10-24-broader-memory-sample.md).

## 1. Evaluation quality and coverage

Started: a repeatable conversation runner, a seven-case regression fixture and a
broader 30-case comparison suite, including multi-turn conversations. Product
rubrics are separate from internal source-ID diagnostics. Reports preserve inputs,
answers, tool evidence and source hashes.

Next: turn observed failures into representative cases, retain a separate holdout
set, and improve honesty, factuality and completion criteria. Add human review;
keyword checks and unblinded coding-agent review are useful but incomplete.
Context-pressure, strict-template finalization, error-display and model-refresh
regressions are now covered. Extend long-history and journal-refresh coverage as
new failures are demonstrated. Avoid tuning the system to a fixed test set.

The recurring-event memory examples have now informed source curation, ranking
and date presentation. Treat them as development/regression cases. No untouched
real-topic holdout has yet been evaluated; independent expected findings and a
frozen first run are the next validation boundary. See the
[memory evaluation protocol](experiments/conversation-evaluations.md#memory-experiments-and-holdout-separation).

Reference: [evaluation guide](experiments/conversation-evaluations.md).

## 2. Model comparisons and operating tradeoffs

Started: the same agent was tested with local gpt-oss-20b MXFP4 and hosted Gemini
4 Argon, using the same initial inputs, tools and application budgets, three
repeats per case. Gemini is now a supported service provider, sharing its adapter
with evaluations. The running setup was left on local inference.

The first comparison found 59/90 local versus 84/90 hosted rubric passes. Gemini
improved recall and corrections, but was slower and exhausted the tool budget in
six runs. These synthetic results show sensitivity to the model/provider setup;
they do not isolate weight count, quantization, training or context capacity.

Next: use the stronger model as a reference when diagnosing failures, compare
practical model/configuration alternatives, and measure actual usage cost alongside
quality and latency. Success on one model and failure on another is evidence to
investigate, not proof that the harness is correct or that the model alone is at
fault. Change one relevant factor at a time and preserve repeated baselines.

For the current owner, local inference is attractive primarily for avoiding
per-token charges and retaining control, provided capability is sufficient.
Sending personal history to a hosted model is acceptable; privacy is not the main
reason for choosing local inference. Other users may have different preferences.
No automatic model routing or fallback has been implemented or selected.

Reference: [comparison results and limitations](experiments/2026-10-22-model-comparison.md).

## 3. Harness, retrieval and tool-loop reliability

Started: Python owns context selection, durable execution and journal retrieval.
Memory tools support source-message reads, speaker/order controls, pagination and
date-based reading. Explicit numeric source IDs were retained after evaluation;
other retrieval/prompt trials have not justified adoption.

Implemented since the initial comparison: unified conversation/import search,
snapshot-bound article/source reads, bounded follow-up evidence and an answer-only
finalization pass when the next batch would exceed four executed calls. The pass
can still fail if a provider requests tools after they have been disabled.

Next: trace remaining source-binding and stopping/recovery failures, including
cases that genuinely require several useful calls. Compare local retrieval/tool
choices with successful hosted traces. Check nearby conversation and uncertainty
behavior before accepting fixes.
The objective is a useful grounded answer or honest uncertainty, not merely more
tool calls or better citation formatting.

References: [design principles](design-principles.md),
[technical backlog](technical-debt.md), and
[execution and recovery](../server/EXECUTION.md).

## 4. Everyday use and feedback

Started: the browser connects to the Python service through the supported private
access path; both local and hosted inference can be selected server-side.

Next: try natural personal-agent conversations and capture concrete mismatches
between the user's intent and the response. Preserve enough context, selected
model and tool evidence to investigate, then create a minimal reproduction and
an evaluation case where useful. Include successful conversations so improvements
do not make ordinary interactions worse. Keep private examples and raw reports
in ignored local storage; use synthetic versions in committed fixtures.

This stream checks whether gains on synthetic cases help in actual use, including
response speed and interaction friction. It is not replaced by an automated score.

## 5. Longer-term memory development

Implemented foundation: durable conversation history and refreshed daily journals.
A small reviewed article pilot is live as of October 23, 2026. Consolidation,
incremental article updates and a larger-corpus index remain proposals.

An isolated [generic ingestion pipeline](memory-ingestion.md) now runs bounded mail
filtering/normalization, source-span article proposals, advisory support checks and
candidate rendering. Structure and evidence references are validated, but experiments
still found unsupported and stale claims. Outputs are unpublished; model agreement
is not approval. A stronger reference reviewer helped on synthetic cases without
changing the live model or adding automatic routing.

The October 23 33-source/nine-article pilot supplied separate annual event
histories and related evidence. The October 24 expansion adds 36 sources and
18 articles from a broader seeded sample, for 69 sources and 27 articles live.
Unified search, snapshot-bound readers and bounded follow-up evidence are
implemented. See the [broader sample and limits](experiments/2026-10-24-broader-memory-sample.md)
and earlier [recurring-event experiment](experiments/2026-10-23-recurring-event-reconstruction.md).
The batch runner still produces unpublished candidates; automatic acceptance,
incremental updates and full-archive ingestion remain future work.

The service/reusable code is generic; earlier history used topic-specific
discovery and user hints, while the latest sample used seeded mailbox/year
selection. Both used coding-agent curation and review. This demonstrates
useful retrieval over reviewed knowledge, not independent automatic reconstruction.
User feedback reports a richer three-year summary, while controlled/live checks
still show car-versus-ski-rental confusion, mixed years and current-status claims.

Next: compare evidence-backed thematic overviews with the flat-index baseline.
Investigate lasting relevance, recurrence, explicit user emphasis and consequences
as candidate significance signals, without imposing a fixed taxonomy or assuming
frequent events are always important. Test broad summaries, detailed questions
and follow-ups together, including attribution and historical/current status.
Preserve these cases as development/regression material and retain untouched
questions with independently prepared expectations for validation. Score
ingestion separately from answering. Larger-corpus ingestion,
real transaction adapters, attachments and consolidation follow bounded evidence
of their usefulness; they are not implemented by the fictional transaction test.

Reference: [personal context and memory roadmap](personal-context-roadmap.md).

Guiding ingestion use case: ask the agent to review prior Chapin daddy-daughter
ski trips and help plan the upcoming one. Evaluate whether retained source records
support a history across years and useful next steps, with historical facts kept
separate from current requirements. See the roadmap's guiding use case.

## How these streams work together

Observe a problem in use or evaluation, inspect its inputs and execution trace,
then use a controlled model or harness comparison to narrow the explanation.
Test the smallest justified change against the failure and nearby behavior.
Record improvements, regressions and inconclusive outcomes before deciding what
to keep. A change without a score gain can still be justified by a demonstrated
benefit such as maintainability; record that reason explicitly.

The immediate agreed memory experiment is synthesis and prioritization over the
expanded bundle. Independent validation, faithful source use and remaining search
stopping/recovery failures remain part of that work.
The [memory-faithfulness comparison](experiments/2026-10-23-memory-faithfulness.md)
now separates evidence availability from answering. A bounded source-context
candidate and a reconciliation prompt were rejected. Complete evidence still
produces local reasoning failures, making a controlled model/configuration
comparison more informative than further prompt rules or archive expansion.
The [fresh-topic source-first study](experiments/2026-10-23-fresh-memory-validation.md)
adds frozen experiment/review tooling and a verified HTML ingestion fix. Its
controlled local excerpt comparison improves payment qualifications but retains
chronology errors; it is coding-agent-reviewed development evidence, not an
independent holdout result.

The [Qwen comparison](experiments/2026-10-24-qwen-memory-comparison.md) reran the
frozen two-case diagnostic with Qwen3.8-27B Q4_K_M. All 24 turns completed;
complete-source answers passed 7/8 versus the historical gpt-oss result of 2/8,
while normal retrieval passed 4/8 versus 3/8. This supports further evaluation of
the inference setup, not a production selection or independent generalization
claim. Source identity, article qualifications and unsupported additions remain
limitations. That experiment used process-local overrides; the later browser
recovery aligned the live configuration with Qwen.

The [transfer and broader conversation follow-up](experiments/2026-10-24-qwen-transfer-and-conversations.md)
finds 15/16 Qwen control turns passing versus 12/16 historically, including both
settled-receipt positive controls. On the matched first pass of 30 broader cases,
Qwen passes 25 versus gpt-oss's 21, but median recorded turn time rises from
2.186 to 20.027 seconds. All 45 turns were attempted; 44 completed. Recall gains
coexist with finalization, unresolved-conflict, source-link and recap failures,
plus a literal thinking-marker/duplicate-answer presentation defect. Repeated
validation remains necessary before treating the observed gains as
general. The later thinking-control experiment and deployment recovery are
recorded above; this comparison itself did not change live settings.

Evaluation coverage and everyday feedback should continue together. Update this
overview when priorities or implementation status change. Keep machine configuration
in the local runbook and detailed results in linked experiment records.
