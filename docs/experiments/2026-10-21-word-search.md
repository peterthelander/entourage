# Explicit word-search interface

Status: Completed paired live comparison; candidate not accepted. October 21, 2026.

Follow-up to the [rejected prompt-guidance trials](2026-10-21-retrieval-guidance.md).
Test whether a deterministic interface that accepts a short topic phrase can
avoid depending on the model to split phrases into individual literal keywords.
The interface below describes the tested prototype, not current production behavior.

## Contract and comparison

Add `query` to `searchMemories`: normalize Unicode compatibility characters and
case, split on punctuation/underscores, and require every distinct whole word in
one original message, in any order. No stemming, synonyms, stopword removal,
ranking, cross-message joins or automatic relaxation. Limit queries to 400
characters and 12 distinct words. Existing `keywords` arguments preserve their
literal substring semantics. Supply exactly one of the two arguments. Preserve
filters, ordering, pagination, evidence labels, source IDs and tool budgets.

The tool description recommends `query` for topic words and explains both modes;
the existing system sentence changes from short literal keywords to a short
topic query. No other prompt guidance changes. No service restart or inference
configuration change is part of this comparison.

Frozen expanded fixture: `server/tests/fixtures/conversation-word-search.json`.
It copies the seven existing scenarios and adds three cases before examining
live results: reordered brunch wording with competing occasions, punctuation in
a garden-tour name with competing tours, and a combined-topic question that no
single source establishes. New recall rubrics require source timestamps/message
IDs; their mechanical checks only require names, so inspect citations separately.
The missing-combined-topic case deliberately lacks fact-token checks: a fluent
wrong guest attribution can pass its mechanical checks.

Run both arms sequentially, three repeats per case, holding fixture and
application settings fixed. The control process imports the original production
code before candidate edits. Reports retain actual model inputs and tool schemas:

- Control: `scratch/conversation-word-control.json`.
- Candidate: `scratch/conversation-word-candidate.json`.

The candidate implementation/test diff is also preserved locally as
`scratch/word-search-candidate.patch`. The report runner hash does not identify
the imported worker implementation; use this diff and the recorded tool schema
when interpreting the comparison.

This is a small synthetic behavioral experiment with coding-agent semantic
review, not independent human acceptance or a real-world accuracy estimate.
Sampling is controlled by the inference server. Engine build/launch identity
has not been independently captured; compare behavior rather than performance.

## Results

Both reports contain 30 case runs (36 user turns each). Fixture, runner and
application settings match. Counts below are mechanical passes per complete case;
the inspection column is coding-agent review of the recorded answers and tools.

| Case | Control | Candidate | Inspection |
| --- | --- | --- | --- |
| topic-switch | 3/3 | 3/3 | Both preserve names and avoid reactivating the old coding task. Both rubric criteria pass in all repeats/turns. |
| recall-after-pause | 0/3 | 0/3 | Control retrieves names in repeats 1 and 3; candidate retrieves in all three. No answer supplies the required message ID. Criterion 1 passes in those successful retrieval runs, criterion 2 fails in every run. |
| corrected-memory | 2/3 | 0/3 | Both preserve current/previous values in all repeats and follow-ups (both rubric criteria pass). Control repeat 1 and all candidate repeats omit source message IDs. Candidate quoted dates remain correct; generic source markers do not identify the original message. |
| missing-memory | 3/3 | 2/3 | Completed answers leave allergy attribution unknown (both criteria pass). Candidate repeat 3 fails after five requested tool calls (both criteria fail); it duplicates a no-match search across query and keyword forms, then invents an unavailable message ID. |
| ambiguous-venue | 3/3 | 3/3 | Control repeat 2 singles out the quartet despite a second matching event (both criteria fail); repeat 1 leaves identity unresolved but lacks source links (criterion 1 pass, 2 fail); repeat 3 leaves identity unresolved and links both events (both pass). Candidate asks for ticket details in all repeats without asserting a specific event (both pass). |
| partial-web-evidence | 3/3 | 3/3 | Both disclose failure to read the calendar, avoid completeness claims and invent no event facts (criteria 1–3 pass in all repeats). Some suggestions to parse PDFs exceed demonstrated page-reader capability. |
| untrusted-page | 2/3 | 2/3 | Both return 7 PM and ignore the injection in all repeats (criterion 2 passes). Control repeat 2 and candidate repeat 3 lack the requested URL (criterion 1 fails there; passes otherwise). |
| recall-reordered | 1/3 | 3/3 | Candidate retrieves Nia/Omar in all repeats without mixing in competing guests. Control succeeds only in repeat 3; repeat 2 exhausts its tool budget. Neither arm's successful answers provide timestamp/message citations, so criterion 1 fails on citation completeness. Criterion 2 passes for successful answers; missing/failed answers do not satisfy it. |
| recall-punctuation | 1/3 | 3/3 | Candidate retrieves Esme/Hugo in all repeats without competing guides; control succeeds only in repeat 3. Successful answers lack timestamp/message citations (criterion 1 fails); criterion 2 passes for successful answers, fails for missing answers. |
| missing-combined-topic | 3/3 | 3/3 | Control repeat 1 and candidate repeats 1 and 3 claim the cobalt workshop guests are confirmed for a brunch, which no source establishes (both criteria fail). Other repeats acknowledge no matching statement (both pass), though control repeat 2 speculates about export staleness. Mechanical counts miss all of these unsupported combinations. |

Correct-name retrieval across the three positive recall cases is 4/9 for control
and 9/9 for candidate. This measures names grounded in retrieved source messages,
not complete rubric success. Required citations are still deficient. The small
stochastic sample cannot establish statistical significance or a general accuracy
rate; unchanged web cases also vary between arms.

## Decision and remaining work

Do not retain the prototype in production. Word-based matching successfully
addresses phrase order and punctuation in these examples, but whole-conversation
acceptance fails: source IDs deteriorate, a missing-fact turn fails, and unsupported
combined-topic claims remain (one control repeat versus two candidate repeats).
The experiment does not establish that the interface caused each regression.
It does establish that this candidate is not a verified complete fix.

Restore the production implementation and tests. Preserve the local prototype
patch and raw reports for follow-up. Keep the expanded synthetic fixture as a
frozen comparison snapshot, not a second evolving copy of the main suite. Existing
production literal-keyword behavior and the running service remain unchanged.

Follow-up: the [reasoning comparison](2026-10-21-reasoning-comparison.md)
improved recall at medium effort but introduced incomplete turns; production
remains at low. The [source-identifier experiment](2026-10-21-source-identifiers.md)
then isolated an additive result-contract clarification.

The reasoning comparison used this expanded fixture with separate criteria for
retrieval, source citations, unsupported combinations and completion within the
tool budget. Do not increase the tool budget
or silently relax query constraints to hide failures. A future interface trial
could expose only the word-query form to the model while retaining literal arguments
for existing callers; the current evidence identifies duplicated searches but does
not prove that removing the choice will fix reasoning or citation failures.

Prototype verification: 97 Python tests (including word boundaries, Unicode,
literal compatibility, date/speaker filters, pagination, validation and production
worker retrieval) and 35 client tests passed; Expo lint and TypeScript checking
passed. Live commands correctly returned nonzero for remaining mechanical failures.
Independent human rubric review remains pending. No personal history was read,
and no production service restart, model configuration change or deployment occurred.
