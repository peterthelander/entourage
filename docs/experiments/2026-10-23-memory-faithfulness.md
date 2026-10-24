# Memory faithfulness: evidence availability versus answering

Status: Comparisons completed; prompt and source-context changes rejected; empty-response execution fix implemented.
Date: October 23, 2026.

## Question and boundaries

Does memory accuracy fail because retrieval omits evidence, article quotations
lose qualifications, or the model misuses evidence it already has?

The existing [fresh-topic study](2026-10-23-fresh-memory-validation.md)
established both missing quotation context and incorrect chronology. This follow-up
keeps its original reviewed bundle, selected sources, questions and expectations.
These are development cases, not a new holdout. The same coding agent selected,
authored and scored this work; independent human/source review remains pending.

The prior validation/parser work was committed as `0e0d961` before this study.
Private manifests, complete requests/replies, intervention code and explicit
report-bound answer reviews are retained in ignored
`scratch/memory-faithfulness-20261023/`. No private bundle is published or changed
by the experiments. The local inference selection and application budgets remain
unchanged. Selected personal source text was supplied to the existing hosted
reference provider as part of the comparison.

## Diagnostic design

`scripts/diagnose-memory.py` runs three conditions:

- `retrieval`: the normal production worker selects and executes its tools.
- `articles`: manually selected reviewed article-reader results are supplied
  directly on each turn; further tools are disabled.
- `sources`: complete normalized originals cited by those selected articles are
  supplied directly on each turn; further tools are disabled.

Article selection is explicit fixture metadata, `diagnostic_articles`, not a
model decision or an independently scored discovery success. Sources are ordered
by actual timestamp instants, including offsets; complete source pagination is
assembled before inference. The data retain original timestamps, unknowns and
provenance. They contain no expected answers.

Supplied conditions bypass discovery, the worker's executed-call budget and
ordinary evidence selection. Evidence is supplied again on follow-up. They test
answering with known evidence, not production retrieval success or normal
follow-up retention. The original question and production system context remain;
supplied data are explicitly labeled untrusted historical evidence. Conditions
rotate across repeats and reports retain all inference inputs and responses.

An initial supplied-tool-history representation was rejected by Gemini with
HTTP 400 because fabricated function calls lacked provider thought signatures.
Those four attempted hosted cases and four unattempted follow-ups remain in
`diagnosis-reference/`, with explicit failing execution reviews. They are harness
failures, not provider-quality findings. The corrected representation supplies
reader data in the user input without forging tool calls. Both providers then
completed all planned conditions. The initial local tool-history oracles remain
in `diagnosis-short/`; their 16 turns are unscored exploratory evidence, excluded
from the main supplied-data comparison. Its normal retrieval condition is the
eight-turn baseline below.

## Findings

Two existing two-turn personal cases ran twice per condition. Counts below are
explicit unblinded reviewer judgments of entire answers, including extra claims
and contradictory prose. Execution completion is separate from semantic success.
An unclear finding is not counted as a pass.

| Condition | Pass | Fail | Unclear | Completed turns |
| --- | ---: | ---: | ---: | ---: |
| Local normal retrieval | 3 | 5 | 0 | 8/8 |
| Local supplied articles | 3 | 3 | 2 | 8/8 |
| Local supplied complete sources | 2 | 5 | 1 | 8/8 |
| Hosted supplied articles | 6 | 0 | 2 | 8/8 |
| Hosted supplied complete sources | 8 | 0 | 0 | 8/8 |

Short quotations omitted identifiers and a separate-charge qualification.
Supplying full originals made that qualification available and allowed the hosted
reference to preserve it. With the short article excerpts, the reference often
left the qualification unknown instead of inventing it; those answers are unclear
against the full-source expectations, not complete successes.

More evidence did not solve local answering. Failures included a correct table
followed by reversed chronology, UTC record times relabeled as user-local,
estimated charges treated as a payment ceiling, and a suggestion to add a tip to
an unsettled estimate as if that produced a final total. One empty local response
became the worker's ordinary "The model returned no answer" text: execution was
completed but the question remained unanswered.

The reference is a diagnostic comparison, not ground truth. Review used the
original sources and expectations. These small authored comparisons do not isolate
model weights, sampling, quantization or all provider differences. Initial runs
did not snapshot engine metadata; some runs overlapped and no controlled latency
claim is made. The reusable runner now records local engine metadata before and
after, and enforces a per-inference deadline around provider calls.

## Two isolated interventions

Both interventions used the same original bundle, questions, local model,
application limits and production worker. Separate process patches and their
exact code were frozen before inference; production files were unchanged while
the candidates ran. No failed result was repaired or silently rerun.

1. **Reconciliation instruction.** A short rule asked the model to group records
   by object, order source timestamps, distinguish plans from outcomes, retain
   qualifications and check its summary against its table. Incorrect timezone
   conversions and unresolved or inconsistent chronology remained. It was not
   adopted.
2. **Bounded original source context.** Article reads included up to 400 original
   characters before and after each uniquely located evidence quotation. This
   recovered nearby identifiers and qualifications without rewriting reviewed
   claims or requiring another retrieval call. Payment wording improved in one
   repeated follow-up; another remained incomplete. Chronology still failed.

| Local two-case comparison | Pass | Fail | Unclear |
| --- | ---: | ---: | ---: |
| Normal retrieval baseline | 3 | 5 | 0 |
| Added reconciliation instruction | 3 | 3 | 2 |
| Added source context | 5 | 2 | 1 |

The source-context candidate was also checked on four freshly authored fictional
two-turn controls, twice each. They were frozen before the intervention and cover
distinct order references, differing timestamp offsets and reversed claim order,
an explicit completion/payment receipt, and a conditional refund exception.
The receipt is a positive control: an improvement must recognize established
historical outcomes rather than abstain on everything.

| Transfer controls, 16 turns per arm | Pass | Fail | Unclear |
| --- | ---: | ---: | ---: |
| Normal article reads | 12 | 4 | 0 |
| Article reads with source context | 13 | 3 | 0 |

Both arms preserved corrected dates, refund exceptions and explicit settled
payment. Remaining failures confused collection of an item with collection of
money and invented a camera model from a repair reference. The controls are
authored development fixtures, not independent real-topic validation. These small
differences are descriptive, not a reliable general improvement estimate.

## Broader check and rejection

The bounded context candidate was implemented in the shared reader and checked
in isolated stores before deployment. It left canonical claims, quotations,
records and snapshots unchanged, used explicit offsets/partial flags, refused
ambiguous quote locations, and stayed within an 8,000-byte addition budget and
the existing 64,000-byte response ceiling. Mechanical tests passed.

The broader check used all six existing two-turn personal cases, twice each.
A matched control removed only the derived context fields, retaining the same
reader tool description, original bundle, model, application settings and worker.
Both arms completed all 24 turns. Explicit full-answer reviews found:

| Broader local comparison | Pass | Fail | Unclear |
| --- | ---: | ---: | ---: |
| Matched control without derived context | 14 | 8 | 2 |
| Derived source context | 13 | 8 | 3 |

This does not establish a reliable regression either; the model is variable and
the sample small. It does not justify adopting the candidate as an improvement.
Errors still included swapped notice/window assignments, noon becoming midnight,
unsupported archive/account access, and leaked assistant/function syntax in an
otherwise correct answer. Additional inspection found that the character window
could itself end partway through a qualification. More characters are not a
semantic evidence-preservation contract.

The source-context reader change, its tool-description change and its temporary
production tests were removed. Its frozen candidate code and complete results
remain in the private experiment directory. The production article reader and
answering prompt retain their pre-study behavior. No topic rules, larger call
budget, automatic publication, model routing or new production context mechanism
were added. Independent review and a new real-topic set remain outstanding.

## Implemented execution fix

The comparisons exposed repeated empty local replies. The worker previously
substituted "The model returned no answer" and marked the turn completed. It
now marks a blank/whitespace-only answer as failed with an explicit retryable
message, without creating a fabricated assistant answer. Evaluation stops the
case there and retains subsequent planned turns as unexecuted. A regression
checks the terminal status, preserved blank response and unexecuted follow-up.
The answer-only retrieval-limit uncertainty fallback remains a separate behavior.

Original reports are not rewritten: their empty replies remain recorded as
completed execution with failing semantic review. New reports use the corrected
execution contract. This fixes outcome reporting, not source reasoning.

The diagnostic runner and semantic-review tooling retain mode identity, missing
conditions, failed and unattempted turns. Answer-only tool requests are preserved
as rejected replies and never executed. A provider requesting tools after they
are disabled is still a failure; this study does not fix production finalization.

## Next boundary

The strongest remaining signal is a local reasoning limitation with correct
evidence already present. A next model/configuration experiment should use these
frozen failures alongside the positive completion controls, with source-grounded
review and execution failures scored separately. Avoid more topic-specific prompt
rules or archive expansion as a presumed cure.

Independent expectations and answer review on new real topics are still needed.
Autonomous coding-agent authorship cannot supply that independence. None of these
results authorizes autonomous synthesis or publication.

## Verification

140 server tests, 46 ingestion tests, 35 JavaScript tests, lint, TypeScript
checking and diff whitespace checks passed after the retained code changes.
The source-context candidate's five temporary mechanical tests also passed before
that candidate and its tests were removed; they are not part of the final count.

The finalized diagnostic runner completed a six-turn fictional smoke across all
three modes, with identical captured local engine metadata before and after.
Semantic review found one passing and five failing turns, including unsupported
default refund eligibility, an empty reply and invented seat numbers. This is
additional evidence of variability, not another successful quality benchmark.
It ran before the empty-response execution fix; its original completed-empty
status remains preserved.

After confirming zero active/queued turns, an online SQLite backup and pointer/
configuration identities were saved under ignored
`server/data/backups/memory-faithfulness-20261023/`. The Python service was
restarted with the retained execution fix. Authenticated real-inference calculator
checks passed through localhost and the Tailscale `/agent` route. A live inventory
check confirmed the existing nine articles and 33 sources. Inference configuration
and active memory pointer hashes still match their pre-restart values. Verification
conversations are excluded from shared-chat consolidation.

Private comparison directories retain separate original reports, reviews and
summaries. The broader candidate run is named `final-personal/` and its matched
control `final-control/`; that name does not imply candidate acceptance. Pending
findings in the initial exploratory format remain pending rather than being
counted as successful validation.
