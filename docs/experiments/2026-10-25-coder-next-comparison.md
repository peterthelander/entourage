# Coder-Next versus earlier inference setups

Date: October 25, 2026 (America/New_York).
Third broader repeat added: October 26, 2026.
Status: Completed exploratory comparison; independent review absent.

Closeout, October 26: the owner settled on Qwen3.5-122B-A10B UD-IQ3_S for now
and closed this model-selection round. See the [decision record](2026-10-26-qwen122-comparison.md).
Further model experiments discussed below are deferred; historical findings remain unchanged.

Follow-up: the [October 26 current-service Qwen27 baseline](2026-10-26-qwen-current-baseline.md)
now supplies three low-thinking 27B repeats with matching current prompts and
service code (75/90 versus Coder-Next 65/90). Historical results and original
comparison limitations below remain unchanged.

Coder-Next is substantially faster than the previous Qwen3.8-27B setup, but
does not demonstrate better personal-agent answer quality. Both original broader repeats
pass 22 of 30 conversation cases, versus 25 of 30 in the saved 27B run. The
source-binding controls are competitive, while the real personal-memory cases
regress. Broad personal overviews remain unreliable even with complete selected
articles supplied. Keep the speed improvement separate from a reliability claim.

## Protocol and comparison limits

The Mac M2 Max with 64 GB unified memory serves Qwen3-Coder-Next Q4_K_M through
llama.cpp build `b11669-620d2225c`, one slot with 16,384 context tokens. The model
file SHA-256 is
`9e6032d2f3b50a60f17ce8bf5a1d85c71af9b53b89c7978020ae7c660f29b090`.
Application output remains 2,048 tokens and the execution budget remains four
tool calls. The embedded template reports structured tool support. It does not
support reasoning-effort selection; requesting low is not equivalent to the
previous thinking model's low setting. Engine metadata remains stable within
each batch. Sampling is server-controlled: both captured Qwen setups report
temperature 1.0, top-p approximately .95 and min-p approximately .05, but top-k
differs (40 for Coder-Next, 20 for 27B), as do templates and slot counts.

The broader suite ran twice (60 cases, 90 turns); fictional source-binding controls
twice (16 turns); two personal-memory cases twice under retrieval, supplied
articles and supplied complete sources (24 turns); and the compact overview
experiment once under three conditions (12 turns). All 142 turns completed.
No failures, partial attempts or cases were discarded. Each conversation has an
isolated store; public research and device calls are synthetic fixtures. No live
chat, accepted knowledge bundle or production prompt was changed by evaluation.

This compares deployable setups against historical reports, not randomized model
weights under identical conditions. The broader fixture, runner and tool schemas
match the 27B baseline; the memory fixtures and bundle snapshots also match.
The current system prompt adds conversational brevity/mobile-formatting guidance,
so initial system inputs are not byte-identical. The worker and adapter also
include subsequent finalization/context/error recovery repairs. The overview
inventory scope text has been corrected since the earlier run. Initial supplied
personal-memory user/evidence packets match; subsequent context includes each
model's actual answers. Historical outcomes are retained without retroactively
crediting old runs with newer fixes. Hardware load and thermal conditions were
not controlled, and no tokens-per-second or first-token benchmark was performed.

Reviews are unblinded coding-agent judgments against the existing source-first
expectations and product rubrics, not independent validation or a fresh holdout.
Mechanical checks and execution success are separate from semantic success.
Private traces, freezes, report-bound reviews and summaries are under ignored
`scratch/coder-next-20261025/`. Public findings below omit personal transcripts.

## Broader conversations

| Setup | Full-case rubric passes | Completed turns | Median turn time |
| --- | --- | --- | --- |
| Historical gpt-oss-20b MXFP4, three repeats | 59/90 | 135/135 | 2.186 s, first repeat |
| Historical Gemini 4 Argon, three repeats | 84/90 | 129/135 | 15.502 s, first repeat |
| Historical Qwen3.8-27B, low thinking, one repeat | 25/30 | 44/45 | 20.027 s |
| Historical Qwen3.8-27B, thinking disabled, one repeat | 24/30 | 44/45 | 11.642 s |
| Coder-Next, repeat 1 | 22/30 | 45/45 | 2.553 s |
| Coder-Next, repeat 2 | 22/30 | 45/45 | 2.207 s |
| Coder-Next, repeat 3, October 26 continuation | 21/30 | 45/45 | 2.564 s |
| Coder-Next, all three repeats | 65/90 | 135/135 | Per-repeat medians above |

The same eight cases fail semantic review in the first two Coder-Next repeats:

- Corrected historical code: does not search for available evidence.
- Ambiguous event: asks a useful question but omits links for factual listings.
- Punctuation-sensitive recall: literal searches miss the available hyphenated entry.
- Ambiguous person: does not retrieve the two people who share a name.
- Conflicting venue: finds one tentative proposal and misses the alternative.
- Changed seat preference: initially denies knowing it without retrieval; one
  repeat later recovers it, but that does not repair the failed whole conversation.
- Calculator follow-up: executes arithmetic correctly but invents dollar currency.
- Museum clarification: correct place/hours, missing required source URL.

Compared with the reviewed 27B first pass, missing-information handling and the
sustained home-plan recap improve. Historical corrections, punctuation recall,
person ambiguity, changed preferences and the currency-free calculator follow-up
regress. Continuity is strong; memory discovery is inconsistent. Category passes
across the two Coder-Next repeats are continuity 12/12, recall 10/12, corrections
4/8, uncertainty 4/8, web evidence 4/8, untrusted data 6/6 and tool use 4/6.

Mechanical case passes are 26/30 and 25/30, exceeding semantic 22/30 in each.
Conversely, quoting and rejecting an injected wrong time fails a mechanical
exclusion but passes the existing product rubric, consistent with earlier review.
Additional defects include verbosity, unnecessary injection narration, an
unneeded clock request in both planning recaps, and unsupported dollar symbols
in the separate bounded-calculation case. The latter remains outside that case's
frozen rubric, as in the earlier reviews; it is not hidden by the passing score.

## Memory source binding

The fictional controls preserve separate order identities, proposal versus actual
attendance, explicit completion/payment receipts, and refund exceptions. Coder-Next
passes 15/16 reviewed turns, matching 27B's 15/16. Median turn time is 5.363 seconds
versus 27.6305 seconds historically. All 16 complete.

The failing Coder-Next answer lists the correct dates, then adds an incorrect
day-after chronology; source notices are one hour apart on the same day. Correct
core facts do not excuse an added false factual claim. A different answer adds a
speculative cause for a price reduction: retained as an additional unsupported
explanation outside the frozen outcome criterion, not a verified source fact.

The two original personal-memory cases are harder:

| Evidence condition | Historical gpt-oss pass/fail/unclear | Historical 27B pass/fail/unclear | Coder-Next pass/fail/unclear | Coder-Next median |
| --- | --- | --- | --- | --- |
| Normal retrieval | 3/5/0 | 4/4/0 | 2/6/0 | 5.977 s |
| Supplied articles | 3/3/2 | 4/3/1 | 1/5/2 | 6.462 s |
| Supplied complete sources | 2/5/1 | 7/1/0 | 3/5/0 | 8.502 s |

Each row has eight planned turns. Supplied evidence bypasses autonomous discovery
and is not an end-to-end retrieval score. Article-only uncertainty remains unclear
where payment terms are absent from the packet, rather than being counted as a
full-source success. All 24 Coder-Next turns complete.

Failures include inventing separate orders from revisions to the same order,
labeling UTC source hours as Eastern without converting them, inventing a notice
time, and treating a higher authorization as evidence that final payment must
exceed an estimate. The private-notice question triggers no memory lookup in
either retrieval repeat; one instead attempts three public searches. Those calls
are intercepted by fixtures, so no private query is actually sent to the web in
this evaluation. Complete sources improve the payment explanation but do not
eliminate unsupported claims.

## Evidence-backed overviews

The same compact editorial plan, source snapshot, selected articles, questions
and expectations from the earlier overview experiment are reused. Three broad
overview turns and one specific dinner-detail turn run per condition.

| Condition | Coder-Next whole cases passing | Historical 27B whole cases passing | Coder-Next median attempted turn |
| --- | --- | --- | --- |
| Inventory only | 0/2 | 0/2 | 10.648 s |
| Flat selected evidence | 1/2 | 1/2 | 26.046 s |
| Thematic selected evidence | 1/2 | 0/2 | 25.333 s |

Coder-Next completes all 12 turns; the historical comparison completed eight,
failed two and skipped two follow-ups after timeouts. Both use a 180-second
per-inference deadline. All three Coder-Next broad overview conversations fail;
no grouping or synthesis layer earns adoption from these results.

Specific dinner details pass with flat and thematic evidence, including dates,
party size, time, declined overnight invitation and unconfirmed attendance. The
inventory answer honestly limits itself to index information but cannot recover
the required detailed episode. In the earlier thematic answer, an added likely
attendance inference failed; Coder-Next avoids that ending here.

Broad failures include joining an unnamed camp purchase to a named child,
mistaking a school name for a daughter, calling planned events completed,
inferring current family/residence/employment circumstances from dated records,
and linking a future booking to a particular tradition without sufficient evidence.
One priority-challenge answer rejects message counts but substitutes recent
transactional receipts as proof of today's priorities. The flat condition's
priority-challenge follow-up is more careful and passes that individual turn;
it does not repair the failed overview conversation.

## Interpretation and next boundary

### October 26 repeat-count clarification and continuation

The historical 90-case results mean 30 distinct scenarios repeated three times,
not 90 different scenarios. Each repeat contains 45 user turns. The October 25
Coder-Next broader comparison used two repeats; the earlier 27B study used one
per thinking condition. Different repeat counts were an exploratory scope choice,
not different coverage of the scenario set. Future model-selection comparisons
should use the [three-repeat protocol](conversation-evaluations.md).

A third Coder-Next repeat ran October 26 without changing prompts, inference
settings, fixture, runner or service code. Those identities, initial inputs, tool
schemas and before/after engine metadata match the original two repeats. The
standalone raw report and review are `broad-third.json` and
`broad-third-review.json` in the same private experiment folder. Derived
`broad-three-repeats.json`, its review and summary bind the original reports by
SHA-256; only the derived aggregate relabels the standalone repeat as repeat 3.
Original reports and the October 25 summary remain unchanged.

The third repeat passes 21/30, giving 65/90 across repeats (22, 22, 21), with all
135 user turns completed. Its median is 2.564 seconds. It recovers the historical
code correction missed earlier, but the final home-plan recap loses the puzzle
and quiet-at-home activity. A make-ahead answer adds blanket 4–5-day refrigerated
cooked-rice advice, exceeding the USDA's 3–4-day guidance; the frozen rubric
explicitly excludes unsupported storage claims. The injection-page answer still
states 7 PM with its source and does not obey the malicious instruction, but
unnecessarily questions both times because the domain is fictional. These
variations reinforce the need to retain repeated runs and review actual answers.
Food-storage reference: [USDA shelf-stable food guidance](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/shelf-stable-food).

The other three batches were not repeated again. Total new-model evaluation now
contains 187 turns, including the original 142 and the additional 45. Earlier 27B
conditions still need two more repeats each; they are not reported as 90-case
results or extrapolated to that denominator. Matching repeat counts alone would
not remove historical prompt/service differences.

### What parameter counts explain

The [official Coder-Next model card](https://huggingface.co/Qwen/Qwen3-Coder-Next)
specifies 80B total parameters, about 3B active per token, routed experts plus a
shared expert, and non-thinking-only operation. Routing can select different
experts for different tokens. This reduces compute per token while retaining a
large collection of learned weights; it does not make the model equivalent to a
fixed dense 3B model. Quantization changes weight precision, not parameter count.

Sparse activation and lack of a separate thinking phase are plausible contributors
to speed, alongside architecture, output length and serving behavior. The current
comparison does not establish sparse activation as the cause of recall failures.
Coding-focused training, reasoning behavior, prompts and sampling all differ.
Observed failures are behavioral evidence (skipped retrieval and unsupported source
inferences), not a direct measurement of expert routing or model capacity.

Coder-Next is a fast, tool-capable candidate, not an established personal-agent
quality upgrade. The earlier broken Qwen2-72B run, with a content-only template
and 4K context, remains a setup failure rather than a meaningful model ranking.
The new results also do not establish that coder specialization generally improves
personal memory or that a larger parameter count predicts performance.

Leave the running Coder-Next setup available for practical use; no model switch
was made during comparison. Before promoting it for reliability, investigate
whether a general-purpose candidate or controlled configuration retains its speed
while recovering corrections/preferences and preserving source qualifications.
Any intervention should rerun both positive and negative controls, preserve first
failures, and move tested cases into development rather than call them fresh
holdouts. A matched rerun of earlier models on the current worker and independent
review on untouched topics are needed for stronger model-selection claims.

Lint, TypeScript checking and whitespace checks passed. Report-bound memory
review validation confirms complete planned coverage, unchanged frozen inputs
within batches and no missing runs. The live knowledge pointer remains unchanged.
No application code was changed; these checks validate the experiment artifacts,
not the truth of model answers.
