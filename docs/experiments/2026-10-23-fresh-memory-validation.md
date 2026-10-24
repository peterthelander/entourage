# Fresh-topic memory validation

Status: Local source-first baseline and controlled comparison completed; independent review remains pending.
Date: October 23, 2026.

## Scope and separation

This experiment tests new personal topics outside the developed recurring-trip
examples: grocery rescheduling, a school visiting-day correction, and cinema
ticket records. Topic choice and literal header rules were supplied by the coding
agent. They form a convenience sample, not representative archive sampling.

The original code/configuration identities were recorded before discovery.
Eight normalized source records, four manually reviewed articles, six two-turn
cases and source-backed expected findings were then frozen before inference.
Original selected MBOX byte hashes were verified. Both providers use the same
reviewed bundle, questions, production worker and application budgets in isolated
temporary stores. The source archive, live chat and active memory pointer are not
modified. Selected excerpts are sent to the hosted provider for comparison.

The same coding agent selected sources, curated articles, authored expectations
and reviewed answers. This is source-first evaluation, **not independent human
validation**. Once the first results were inspected these topics became
development/regression cases. Manual observations, membership and article writing
must not be counted as automatic ingestion success.

Private inputs, frozen manifests, full inference traces, source integrity checks,
stage reviews and explicit answer reviews are under ignored
`ingestion/data/reports/fresh-memory-20261023/`. No private source content or
generated personal articles are committed.

## Ingestion finding and fix

The existing two bounded catalogs contain 106,632 complete header records.
Applying the new manual literal rules initially normalized eight sources, rejected
two selected originals as unreadable and identified one exact duplicate. These
counts describe those rules within catalog prefixes, not archive-wide recall.

Both unreadable originals had HTML with an opening `<head>` and an explicit
`<body>`, but no closing `</head>`. The normalizer's hidden-content stack never
left the head, so it discarded the visible message. The standard-library parser
emits tokens without performing HTML tree construction. Recognizing the explicit
body transition fixes this demonstrated case; it does not implement a full HTML
parser. See the [HTML parsing rules](https://html.spec.whatwg.org/multipage/parsing.html#parsing-main-inhead).

With only that parser change, the same catalogs, rules and bounds yield nine
unique normalized records, no unreadable bodies and two exact duplicates. The
newly readable repeated original now reaches deduplication. A synthetic regression
checks both explicit and omitted head endings while retaining metadata/script/style
exclusion and original-byte hashes. The original eight-record conversational
baseline remains unchanged; the recovered source was not slipped into it.

## Automatic article generation, scored separately

Three explicitly selected input groups (three grocery records, one school record,
one forwarded cinema record) ran twice through the existing local structured
source-span proposal code. No curated articles or expected answers were supplied
to the model. Record choice and grouping remain manual.

Five of six proposals passed structural checks. One failed on duplicate article
slugs and was preserved without repair. Semantic review found:

- Grocery synthesis retained three proposed windows but did not explain
  supersession or retain completion/payment unknowns.
- Both school proposals preserved class/date/time assignments. Neither recorded
  attendance uncertainty, and both chose a general concept for the dated notice.
- Both cinema proposals recovered ticket counts and total, but stated a refund
  rule without its source exception for some special events. Literal source-span
  validity did not preserve the full qualification.

All five structurally valid plans had empty unknowns. That alone is not a false
claim, but it leaves important gaps for later planning. No proposal was published.
There is no automatic observation-extraction or membership score: those stages
were manual for the reviewed conversational bundle. A complete independent
source inventory was not prepared, so discovery recall is unmeasured.

## Controlled evidence-excerpt comparison

The original local baseline completed all 12 case runs (24 turns). Explicit
unblinded turn review marked 18 passing and six failing. Failures included
incorrect timezone conversions, reversed correction order, an unsupported tip
statement, an incorrect date characterization, and overstated search coverage or
capabilities. Correct tables did not excuse contradictory prose. These are
reviewer findings on this convenience sample, not an independent quality estimate.

The hosted comparison is partial. Its first repeat completed three of six
two-turn cases. Two other cases failed when finalization requested more tools;
one failed on its first inference call with an adapter `RuntimeError` whose raw
cause is not established by the sanitized trace. The second repeat's first
question failed with `TimeoutError` after 572.010 seconds. Further hosted work
was stopped after that operational failure. The next active case's SQLite
checkpoint was captured read-only before stopping the owned evaluation process.

All 19 retained case runs (12 local, seven hosted) remain in the original report.
An explicitly labeled stopped-report companion preserves its hash, stop reason,
planned case set, five missing hosted case runs and the active partial checkpoint.
The original report was not rewritten to look complete. Hosted retained cases
contain eight completed turns, four failed turns and two unexecuted follow-ups;
ten more planned turns belong to the five missing cases. Unblinded review of the
retained hosted cases marks seven turns passing and seven failing (including
execution failures and unexecuted follow-ups), with missing cases kept separate.
This cannot support a complete two-repeat provider-quality comparison.

Initial answers exposed a curation weakness: the grocery article quotations
omitted order identifiers and payment qualifications that were present in the
original sources. A separate bundle expands only those evidence quotations to
include the existing order reference, authorization caveat and separate tip
statement. Claims, titles, unknowns, source records, questions, model, settings
and production service code stay unchanged.

Two focused two-turn cases ran twice locally with each bundle, using the new
freeze checks. All 16 turns completed. Explicit unblinded semantic review found:

| Evidence variant | Reviewed passing turns | Reviewed failing turns |
| --- | --- | --- |
| Original short quotations | 3/8 | 5/8 |
| Expanded source quotations | 6/8 | 2/8 |

Both expanded payment follow-ups correctly used the separate-tip qualification;
neither short-quotation follow-up did. However, both expanded chronology answers
still failed: one left alternative windows unresolved and the other reversed the
sequence in prose despite a correct table and visible shared order reference.
The short-quotation runs also contained unsupported extra claims and a noon versus
midnight error.

This small development comparison supports preserving relevant identifiers and
qualifications in evidence. It does not establish a general quality gain or solve
correction reasoning. The variant is retained for inspection in the isolated
experiment, not activated in live memory. No topic-specific retrieval rule or
new answering prompt was added to make these examples pass.

## Reusable evaluation support

`scripts/validate-memory-experiment.py` freezes code/input/settings identities,
creates report-bound review templates, and summarizes explicit reviewer findings.
It preserves pending/unclear judgments, missing planned runs and failed/unattempted
follow-ups. It cannot validate a reviewer's truth or independence. The knowledge
runner optionally enforces the freeze before and during runs, records planned
cases/settings, and preserves terminal failure/interruption state.
New runs also save the active case around every inference request and reply,
including inputs, responses, inference failures and earlier completed turns. This
addresses the case-level reporting gap exposed by the long hosted run. A local
two-turn live smoke and scripted failure/progress checks verify the new path.
See [commands and expectation format](conversation-evaluations.md#freezing-and-reviewing-a-memory-experiment).

Portable fictional regressions are committed as
`ingestion/fixtures/source-binding-memory/`,
`ingestion/fixtures/source-binding-conversations.json`, and
`ingestion/fixtures/source-binding-expectations.json`. Three two-turn cases cover
same-reference revision chronology, source date versus activity date, estimated
versus settled charges, refund exceptions, and unknown attendance/companions.
They derive from observed failures and are explicitly development fixtures,
not another holdout. Review snapshot bytes are pinned to LF across checkouts.
Two local repeats completed all 12 fictional turns. Unblinded semantic review
marked ten passing, one failing for labeling UTC source times as local, and one
unclear for an incomplete tip qualification. This easier authored fixture does
not replace the real-source baseline or erase its failures.

## Finalization transport diagnostic

A fresh hosted cinema follow-up reproduced the existing execution failure: after
three executed calls, a requested two-reader batch exceeded the four-call budget.
The answer-only finalization response requested tools again, so the worker rejected
it. This is an execution failure, not a successful uncertainty answer.

An isolated replay compared the captured finalization messages with `tools: []`
against the same request plus `tool_choice: "none"`. Two repeats per condition
were interleaved; no tools executed. Both replay conditions used a fixed
1,536-token output limit (the original conversation baseline used 2,048), so this
is a separate diagnostic rather than an exact repeat of the original turn. The
explicit-none condition requested tools in one of two replies; both control
replies returned text. HTTP responses were successful and retained privately.

This does not support adopting the parameter as a finalization fix. No transport
or live configuration change was made. Provider behavior varies across identical
inputs; a successful retry must not erase the original failed turn. Diagnostic
calls overlapped later hosted baseline work, so these runs are unsuitable for a
controlled provider-latency comparison.

## Next boundary

Preserve source identity and qualifications during article extraction, then
diagnose correction/supersession reasoning with the original evidence, explicit
source reads and a stronger reference. A correct table followed by reversed prose
must fail review. Avoid expanding archive coverage or enabling automatic
publication while these failures remain unresolved.

Independent source/answer review and a new untouched topic set are still needed
before claiming generalization. The new freeze tooling makes that next experiment
concrete without mislabeling this coding-agent-authored study as independent.

## Verification

131 server tests, 46 ingestion tests, 35 JavaScript tests, lint and TypeScript
checking passed. Documentation links and the preserved original-report hash were
checked. The active memory bundle and live inference settings were not changed.
