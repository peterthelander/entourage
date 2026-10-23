# Recurring event reconstruction

Status: Reviewed expansion active; bounded discovery, source review and conversation comparisons complete, with unresolved model reliability limits.
Updated: October 23, 2026.

## Question

Can a recurring event history connect announcements with lodging, transportation
and activity purchases that do not share the event's name, while keeping years,
cancellations and historical versus current status separate?

The original live bundle held one dinner announcement among five total sources.
Its narrow coverage could not reconstruct three annual weekends. This experiment
expands discovery and curation without treating every word match as membership or
processing the entire archive through inference.

## Discovery and review

Two bounded catalogs scan 9 GiB and 2 GiB prefixes of the larger mailboxes,
respectively: 106,632 complete header records, with 58,602 Promotions exclusions.
The header scan took about 155 and 10 seconds on this machine. These are prefix
coverage measures, not a corpus-wide recall estimate; header dates include outliers
and do not establish complete date-range coverage.

Private rules select school/event and travel-provider header leads over a broad
message-date window, allowing reservations from months before the activity. Full
readable bodies are normalized only for those leads, under 8 MiB/message and
explicit count/total-byte caps. This produced 488 per-mailbox leads, 444 unique
raw-message identities, from approximately 32.3 MiB of decoded source bytes. The
selected runs did not hit their discovery budgets. Exact raw deduplication does
not collapse forwards or prove independent corroboration.

Source-by-source coding-agent review identifies activity dates, locations,
references and source statuses. Generic link suggestions compare these reviewed
observations with three separate yearly events. Seventeen suggestions were
reviewed as historical context, including a cancelled reservation whose status
must stay cancelled. A January rental receipt received in February and a separate
future hotel reservation are negative controls: neither joins a past weekend.

The reviewed expansion preserves the four unrelated existing articles and adds
separate yearly instances, a broader series article and a separate future-booking
instance: 33 source records and nine articles in total. All original selected MBOX
byte-range hashes were verified before acceptance. The evidence distinguishes
hotel reservation from post-stay correspondence, planned rental return from a
later provider-reported return, equipment rental from lesson/lift purchases, and
hotel booking from dinner venue. An inconsistent date inside an old announcement
is preserved as a conflict rather than silently corrected.

Originals, catalogs, excerpts, reviewed extraction/link decisions and model inputs
remain ignored under `ingestion/data/`. No attachments or real bank/card export
were ingested. Email receipts can report purchases/charges but are not bank-verified
spending. Independent human review remains pending.

## Conversation evaluation

Six two-turn cases run twice through the production local model/worker in isolated
stores. Questions cover multi-year recall, early booking dates, rental return and
cost distinctions, equipment-rental evidence, changing yearly instructions and a
future reservation. Initial execution completed all 12 case runs (24 turns), but
semantic failures included misattributing the post-stay timestamp to the original
booking, claiming no rental evidence after reading an unrelated year's article,
mixing years on a follow-up and overstating a future reservation's current status.
Execution completion is not a semantic pass rate.

Tool traces exposed two concrete weaknesses. Source dates were separated from
their excerpts in an ID/date map, and fallback retrieval ranked unknown-only topic
mentions alongside direct topic evidence. Article reads now attach each source
timestamp to its own excerpt without changing frozen input JSON. Partial ranking
prioritizes titles and claims over unknowns and labels unknown-only matches. Final
curation also makes booking/post-stay roles explicit and puts an important receipt
in the series overview. These changes are evaluated together; the comparison does
not isolate the causal contribution of each change.

Private baseline and final reports live under
`ingestion/data/reports/event-discovery-20261023/`. Expanded evaluations record
hashes of the retrieval, contracts, store and inference code as well as the worker.
The main comparisons use local inference. A later focused hosted reference
comparison sends selected source excerpts for the two failure cases; production
inference remains local and no automatic routing is added.

## Generalization and limits

The reusable code contains no school, ski-trip, hotel-provider or year-specific
rules. Topic selectors and real article curation remain private experiment inputs.
A fictional conference fixture exercises early bookings, separate annual events,
a cancellation, a transaction and coincidental dates in another city. Date-only
matches remain weaker leads; a shared reference with conflicting dates is flagged.

Observation extraction and event membership still require semantic review. The
prototype is not automatic entity resolution, a complete event graph, fuzzy date
understanding or a bank adapter. Future work should broaden unrelated real cases,
evaluate extraction separately from linking, improve conversation reliability and
only then scale ingestion or add source-specific financial adapters.

## Publication and recovery

The reviewed 33-source/nine-article bundle is now active at
`server/data/vault/knowledge/bundles/recurring-events-20261023/`. The four unrelated
previous articles are preserved. The old bundle and pointer backup remain
available, and a consistent SQLite backup was taken before the idle service was
restarted. Inference provider/model selection is unchanged.

`activity_period` and `series_slug` are optional validated instance fields. They
separate event dates and recurrence from mail observation dates, and generated
views preserve that distinction. These are reviewed annotations, not automatic
extraction or proof that the event occurred. The final follow-up check uses this
explicit activity metadata; earlier conversation results describe earlier frozen
candidate versions.

## Final local checks and known failures

The revised broad local comparison completed 12 case runs/24 turns. Both early
booking answers recovered the original confirmation date, but some broad answers
still invented equipment rentals in years where the selected evidence does not
establish them, and one follow-up mixed source and activity years.

With explicit activity-period metadata, six focused case runs/12 turns completed.
Both repeats recovered the early confirmation date and kept the documented
rental-purchase year separate from the other two years. Future reservation status
remained inconsistent: one repeat correctly said current status was unknown; the
other called the reservation active. This is a remaining model error, not an
accepted fact in the published memory. Small selected follow-up checks do not
establish general reliability or isolate causation.

An unrelated four-case/seven-turn conversation regression completed. Core recall
and missing-attendance answers were useful, but a bicycle follow-up added an
unsupported general maintenance interval. No semantic all-pass claim is justified.

The live inventory returned nine articles/33 sources. A live two-turn check
recovered all three hotel histories, but then incorrectly cited car-rental
agreements as ski-equipment purchases and overgeneralized the Red Lion's role.
It is recorded as a semantic failure despite successful retrieval/execution. The
source articles distinguish vehicle records, equipment purchases and dinner/lodging
roles; the live assistant's answer is not new evidence and must not be promoted
into imported memory.

Private `conversation-review.json` records unblinded review findings separately
from execution-only reports. The old bundle remains available for rollback, but
the expanded source-grounded records are retained: answer-quality defects must
not silently rewrite the evidence. More independent evaluation and better source
binding in follow-ups are needed before trusting autonomous planning or spending
summaries.

## Focused hosted reference

The reference completed the same two-turn hotel-to-equipment follow-up correctly:
it separated user lodging from the dinner venue and identified the documented
rental-purchase year without promoting car-rental records into ski rentals. This
supports a model/source-binding limitation on that example; one reference run is
not proof of general accuracy.

Its future-booking case failed before an answer. Three searches consumed three
calls, then the next two-reader batch exceeded the four-call budget. The answer-only
finalization response requested tools again and was rejected by the worker. This
is an execution failure, not a successful answer or absence of booking evidence.
No retries were used to select a favorable result and no live inference switch
was made. The explicit reference comparison sent selected private excerpts to the
existing hosted provider; the archive itself was not uploaded.

Verification: 121 server tests, 45 ingestion tests, lint and TypeScript checking
passed. Reusable code and fictional fixtures are committed separately from private
catalogs, source data, reviews, reports, generated journals and machine settings.

## Session feedback and separation audit

The user's subsequent agent test produced a richer summary of three yearly
weekends with lodging, car and mountain bookings, and identified the documented
equipment-rental year. Only the ending excerpt was supplied; the full answer and
tool trace were not inspected. Treat this as encouraging everyday feedback, not
an independently scored pass. Its future-year wording still needed qualification:
a reservation is not a completed hotel stay, confirmed school-event schedule or
present-status check; bounded missing evidence is not archive-wide absence.

An audit found no trip/travel-provider-specific memory rules in the service or reusable
catalog, selector and event-link code. The retained `find_ski_trip.py` is explicitly
an exploratory topic-specific script and is not imported by production. Private
search rules, user-provided leads and coding-agent curation were topic-specific;
accepted articles intentionally contain personal topic facts. Production retrieves
those reviewed articles, not raw mailboxes, this coding chat or experiment reports.

The current demonstration is therefore retrieval over hand-curated knowledge.
It is not independent automatic reconstruction. These cases informed curation,
ranking and date presentation and are now development/regression examples. The
same coding agent reviewed sources and answers; independent human review and an
untouched real-topic holdout have not occurred. The fictional conference fixture
checks generic mechanics only. See the proposed
[holdout protocol](conversation-evaluations.md#memory-experiments-and-holdout-separation)
before claiming general ingestion or answer-quality gains.
