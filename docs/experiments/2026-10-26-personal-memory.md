# Current-model personal-memory diagnostics

Date: October 26, 2026 (America/New_York).
Status: Detailed/overview baselines and paragraph comparison complete; transfer
interrupted. Continued October 28 with fresh matched controls. No production
context change adopted.

Closeout: the [October 30 acceptance decision](2026-10-30-memory-milestone.md)
ends this experiment round without adoption. Findings and commands below remain
historical references; no continuation is queued.

## Question

With the selected Qwen3.5-122B-A10B setup held fixed, which remaining memory
failures arise from discovery, omitted article context, interpretation, or broad
summary selection? This begins the [dependable memory work](../personal-memory-development.md).
It does not reopen model selection or change the published knowledge bundle.

## Baseline

Private inputs and reports live under ignored `scratch/personal-memory-20261026/`.
The existing runner records source snapshots, effective model/context/output
settings, frozen code/input hashes, engine metadata, attempted turns and failures.
All execution uses isolated stores; real device and web operations are intercepted.
Local inference runs serially on the selected engine.

- `baseline-detail`: the existing two real two-turn memory-faithfulness cases,
  twice each under normal retrieval, supplied articles and complete-source
  controls (24 planned turns). The older six-source reviewed diagnostic bundle
  is used, not the unrelated active bundle; selectors are validated before inference.
- `baseline-overview`: the existing broad three-turn overview and one specific
  episode, with inventory, flat selected evidence and editorial thematic evidence
  (12 planned turns). Uses the existing 69-source/27-article reviewed bundle and
  eight-article experimental overview plan.
- `baseline-transfer`: three newly authored two-turn conversations about a
  reported refund, a tentative reunion trip and wedding arrangements (six planned
  normal-retrieval turns). Expected findings were prepared from reviewed claims
  and checked against original normalized sources before candidate inference.

These are development cases. Existing source curation and coding-agent authorship
and review preclude an independent-validation claim. New transfer questions are
not a substitute for independently prepared untouched topics.

## Bounded context candidates

`scripts/diagnose-memory-context.py` wraps the existing runner without modifying
the live service. Its freeze manifest includes the wrapper and context-builder
hashes and records the exact treatment. It refuses combined treatments and
conditions in which the selected treatment would have no effect.

1. **Original paragraph context.** `scripts/memory_source_context.py` derives
   complete original paragraphs around uniquely located article quotations.
   It preserves canonical claims/quotes/unknowns and source dates, merges
   overlapping passages, exposes character offsets and partial coverage, and
   reports ambiguous/oversized/budget-omitted passages. Limits are 3,000 UTF-8
   bytes per passage and 8,000 bytes including context metadata, within the
   existing 64,000-byte article response ceiling. It is experimental, not a
   live article-reader change. Unlike the older fixed-character trial, it does
   not cut a paragraph before a nearby qualification.
2. **Withheld uninspected index.** The overview treatment removes uninspected
   inventory entries and adjusts only the scope statement. Selected articles,
   quotations, unknowns, thematic hypotheses, snapshot and coverage metadata
   remain identical. This is an answer-context diagnostic, not autonomous
   retrieval or an implemented significance mechanism.

Example commands, using fresh output directories:

```powershell
.\server\.venv\Scripts\python.exe scripts/diagnose-memory-context.py `
  --source-context paragraphs `
  --bundle ingestion/fixtures/source-binding-memory `
  --fixture ingestion/fixtures/source-binding-conversations.json `
  --expected ingestion/fixtures/source-binding-expectations.json `
  --modes retrieval --repeats 2 --output scratch/source-context-example

.\server\.venv\Scripts\python.exe scripts/diagnose-memory-context.py `
  --overview-index omit `
  --bundle ingestion/fixtures/memory-overview-memory `
  --fixture ingestion/fixtures/memory-overview-conversations.json `
  --expected ingestion/fixtures/memory-overview-expectations.json `
  --overview ingestion/fixtures/memory-overview.json `
  --modes flat_overview thematic_overview --repeats 2 `
  --output scratch/overview-index-example
```

Use `--source-context none --overview-index include` for the unchanged control.
Review using the existing report-bound workflow before comparing scores.
Mechanical invariants do not establish answer accuracy, personal significance or
production adoption. Positive completion/refund controls matter alongside
uncertainty: blanket abstention is not a successful result.

## Completed detailed baseline

All 24 planned turns completed. Engine metadata before/after matched the selected
122B model, IQ3_S, engine build `b11669-620d2225c`, one slot and 16,384-token
context. Effective output limit remained 2,048 tokens. No live configuration,
conversation, source record or knowledge pointer was changed.

| Condition | Pass / fail / unclear turns | Whole cases passing | Median attempted turn |
| --- | --- | --- | --- |
| Normal retrieval | 6 / 0 / 2 | 2/4 | 23.311 s |
| Supplied articles | 6 / 2 / 0 | 2/4 | 19.888 s |
| Complete sources | 7 / 1 / 0 | 3/4 | 28.280 s |

These are two cases repeated twice, not four independent subjects. Full-answer
coding-agent review is bound to the report and frozen expectations. All modes
preserve the correction chronology on both repeats. Normal retrieval reads the
article but not the original payment text, then says tip treatment is unspecified.
The article indeed omits explicit separate-tip and higher-authorization wording;
those answers are incomplete, not full-source passes. Article-only controls
instead supply unsupported generic tip-timing/fee advice. Complete sources recover
the qualifications, but one repeat adds an unsupported final-amount formula even
while correctly saying actual delivered items determine the charge.

The distinction supports testing evidence selection, not treating source access
as sufficient for accuracy. A mistyped source ID in one otherwise passing
correction follow-up is recorded separately from frozen criteria. Scores do not
count flawless answers, and this is not a matched historical model comparison.

## Completed overview baseline

All twelve turns completed, with unchanged captured engine metadata. The full
evidence conditions no longer hit the earlier study's follow-up timeout, but
neither produces a passing broad overview conversation.

| Condition | Pass / fail turns | Whole cases passing | Median attempted turn |
| --- | --- | --- | --- |
| Inventory only | 1 / 3 | 0/2 | 30.032 s |
| Flat selected evidence | 2 / 2 | 1/2 | 62.441 s |
| Editorial thematic evidence | 2 / 2 | 1/2 | 62.986 s |

Each condition includes one three-turn broad conversation and one detailed
episode. All three correctly reject message/article count as a measure of user
importance on the narrow frozen importance criterion. Both evidence conditions
recover the dinner reservation/overnight-plan details and withhold attendance;
the inventory answer instead prints an unexecuted article-read code block.

The inventory overview mistakes a school name for a child and labels trip
arrangements completed. Flat evidence removes that identity error but asserts
school attendance from dated correspondence, promotes employment verification
to employment history, and later conflates notice dates. The thematic answer
still promotes a planned wedding itinerary and indexed ski arrangements into
stronger claims than the inspected evidence establishes. Importance follow-ups
can satisfy their narrow criterion while retaining unsupported contextual gloss.
The flat dinner answer also cites internal evidence-map numbers instead of source
record IDs. These qualifications remain in the full report-bound review.

The result supports retaining the broad/detail controls, not deploying editorial
themes or claiming a solved significance mechanism. Withholding uninspected index
entries is a separate controlled trial; changing evidence availability alone is
not assumed to repair interpretation of inspected articles.

## Paragraph trial and interruption

The completed `paragraph-detail` trial attempted all eight normal-retrieval
turns: six pass, two fail, with two of four whole cases passing and a 29.799 s
median attempted turn. The unchanged baseline also passes two of four whole
cases (six pass/two incomplete turns), at 23.311 s. These are small repeated
development cases, not a causal performance estimate.

The paragraph condition recovers the explicit payment qualifications on both
repeats, but regresses chronology in both correction answers. One suggests
different orders despite matching references; the other gives a correct table
and then invents an earlier Friday-to-Saturday change. It swaps which subject
passes rather than demonstrating an overall improvement. **Do not adopt the
paragraph enrichment in production.** Retain the bounded builder and controls
for reproducible diagnosis.

The following transfer run stopped after two complete case runs (four turns),
during the third case. On October 28 no experiment processes remained. Its exact
unfinished report is preserved as `paragraph-transfer/interrupted-report.json`;
the working report is explicitly marked interrupted. The incomplete active trace
is not a completed turn or a semantic pass. No checkpoint or live turn is replayed.
The queued index/other controls never ran and are not outstanding background jobs.

All existing freeze files were verified before evolving the diagnostic runner.
Exact historical runner/context-builder code is saved in ignored
`scratch/personal-memory-20261026/historical-code/`, with hashes in the interruption
record. Existing source records, reports and completed reviews remain intact.

The selected model and engine build still match, but engine context increased
from 16,384 to 32,768 and the chat-template hash changed. Generation parameters
captured in `params` match; the application's 16,384 context/2,048 output limits
remain unchanged. The template change's cause has not been established. Do not
pool the new conditions with the October 26 baseline. See the
[October 28 continuation](2026-10-28-personal-memory.md).
