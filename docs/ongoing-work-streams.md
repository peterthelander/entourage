# Ongoing work streams

Status: Active development overview; next steps are proposals, not scheduled work.
Updated: October 23, 2026.

The goal is a capable personal agent with natural conversation, useful recall and
reliable tools. These work streams connect everyday use, evaluation and targeted
experiments. Detailed findings belong in experiment records; implementation
limitations belong in the [technical backlog](technical-debt.md).

## 1. Evaluation quality and coverage

Started: a repeatable conversation runner, a seven-case regression fixture and a
broader 30-case comparison suite, including multi-turn conversations. Product
rubrics are separate from internal source-ID diagnostics. Reports preserve inputs,
answers, tool evidence and source hashes.

Next: turn observed failures into representative cases, retain a separate holdout
set, and improve honesty, factuality and completion criteria. Add human review;
keyword checks and unblinded coding-agent review are useful but incomplete.
Extend coverage to long histories, context pressure and journal refresh as those
become the subject of experiments. Avoid tuning the system to a fixed test set.

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

As of October 23, an explicitly reviewed 33-source/nine-article expansion is
published to the live Python service, with separate annual event histories and
related lodging, transportation and purchase evidence. Unified search,
snapshot-bound readers and bounded follow-up evidence are implemented. See the
[recurring-event experiment](experiments/2026-10-23-recurring-event-reconstruction.md).
The batch runner still produces unpublished candidates; automatic acceptance,
incremental updates and full-archive ingestion remain future work.

The service/reusable code is generic; the published history was assembled with
topic-specific discovery, user hints and coding-agent curation. This demonstrates
useful retrieval over reviewed knowledge, not independent automatic reconstruction.
User feedback reports a richer three-year summary, while controlled/live checks
still show car-versus-ski-rental confusion, mixed years and current-status claims.

Next: freeze the current implementation for an untouched-topic evaluation, score
ingestion stages separately from answering, and diagnose source binding in
follow-ups. Preserve the current cases as regressions. Larger-corpus ingestion,
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

The immediate proposed focus is independent memory validation and faithful use
of retrieved sources, alongside remaining search stopping/recovery failures.
Evaluation coverage and everyday feedback should continue together. Update this
overview when priorities or implementation status change. Keep machine configuration
in the local runbook and detailed results in linked experiment records.
