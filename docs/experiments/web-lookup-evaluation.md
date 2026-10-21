# Web lookup: preserving the question

Status: Experiment record; unresolved behavior is noted below. Experiments: October 20, 2026.

Small experiment, October 20, 2026. The observed failure was a request about
"Harvest Apple Orchard in upstate New York" becoming a directory of orchards,
followed by unsupported details in the local model's table.

The handoff supplied keyword-like text to Gemini. Both repeated baseline searches
returned general orchard lists. The revisions keep a self-contained research
question in the tool schema, ask research to establish the named subject before
describing it, and ask the answering model to preserve uncertainty and cite the
returned source URLs. No orchard-specific matching or retry rules were added.

Repeated revised searches still sometimes broadened the request. Supplying the
full original question focused the beginning of the research on Harvest-named
venues, but did not consistently prevent unrelated alternatives. The local
gpt-oss-20b model also still introduced unsupported details and sometimes omitted
real citation links. These trials do not establish a reliable behavioral fix.
General comparison requests continued to return comparisons. Results are variable;
these are small qualitative trials, not a measured accuracy estimate.

Local comparison inputs and outputs are in ignored `.expo/lookup-*.json`, with the
isolated runner in `.expo/lookup-comparison.py`. No test conversation was added to
the user's saved chat. The credential was loaded privately, never printed.

Separately, copied exchanges now omit only `search_suggestions_html`, with an
explicit omission marker. Queries, summaries, source links, claim/source mappings,
and timestamps remain available; saved results and the Google widget are unchanged.
An export regression test verifies retained evidence and unchanged original data.

Next everyday check: does the agent identify the intended venue or ask a useful
town/name question? Do its specific claims have support in the lookup and clickable
citations? Treat these as open evaluation questions rather than solved behavior.

## Carnegie Hall: isolate research from answering

The reported October 20 exchange omitted the Richard Dawkins event, merged
performers from separate concerts, and selected a concert without knowing the
user's ticket. Zankel Hall itself is part of Carnegie Hall; it was not evidence
that the agent searched the wrong institution.

The reproducible runner is `scripts/evaluate-web-lookup.py`. It reads the existing
credential and local inference selection privately, calls the providers directly,
and saves reports under ignored `.expo/`. It never submits turns to the service
or writes conversation history.

### Research comparison

Same production research instructions and output limits, three runs per question
per model, 18 calls total. Questions covered the original broad date/venue request,
the correction naming Dawkins, and a specific Knights/Emanuel Ax request.

| Question | Gemini 2.5 Flash-Lite | Gemini 2.5 Flash |
| --- | --- | --- |
| Broad Carnegie Hall schedule: Dawkins included | 0/3 | 0/3 |
| Dawkins explicitly named: event found | 3/3 | 3/3 |
| Knights explicitly named: event found | 3/3 | 3/3 |

Both models used essentially the same broad search queries and confidently
summarized two performances while omitting Dawkins. This does not establish that
the underlying search index lacked the event: naming Dawkins retrieved it.
Changing to Flash alone did not solve coverage. Do not use these small counts
as population-level accuracy estimates.

### Answering comparison

Controlled replays use identical facts with two representations: the existing
JSON-style evidence and a short source-linked brief. Each representation is
repeated three times for four cases: partial findings, three separate events,
a specific single event, and the user's correction after an earlier wrong answer.
The three-event fixture intentionally leaves one event's time/auditorium unresolved;
it is not an assertion that the live calendar was independently fetched in full.

Source links are isolated to the events present in each fixture. An initial
exploratory replay accidentally included the Dawkins link in the partial fixture;
those results are excluded. The final replay also aligns each tool query with its
follow-up question. Final reports are `web-evaluation-replay-json.json` and
`web-evaluation-replay-brief.json`; research is `web-evaluation-research.json`.

With clean evidence, the local model still sometimes chose a particular event
without identifying the user's ticket and added details not present in the input.
Examples across the trials included ticket prices, extra performers, and incorrect
weekdays. The shorter representation sometimes yielded better links but did not
reliably fix factual fidelity or uncertainty. Corrections naming Dawkins were
easier than the original ambiguous request.

### Decision

No production model or evidence-format change is justified by these trials. Keep
the runner and findings; do not add venue-specific matching, automatic query
expansion, or another set of prompt prohibitions. The two remaining questions have
different owners:

- Research: can primary-calendar/source inspection establish coverage better than
  a synthesized search summary? Source access may fail, which must remain visible.
- Answering: can the selected local model follow the supplied evidence faithfully
  under a different supported reasoning/model configuration? Compare the same
  saved inputs before changing the live conversation engine.

These findings diagnose why a better research summary alone is insufficient;
they do not establish a reliable fix for either stage.

## Bounded static-page reader

Added `readWebPage` to the existing tool loop. It reads public static HTML/text,
extracts links, supports literal text finding and excerpt pagination, and reports
truncation/access failures. It does not run a browser or interact with calendars.
The four-call turn limit is unchanged. No venue-specific code was added.

`scripts/evaluate-page-reading.py pages` tested three sites: Carnegie Hall's
calendar hit the redirect limit, Lincoln Center's calendar exceeded the 1 MiB
response cap, and the New York Philharmonic concerts page returned text and links.
The Philharmonic text included navigation and client-rendering placeholders, so
this is successful extraction, not verification of a complete schedule.

The isolated Mac-model `agent` run repeated three requests twice: the original
Carnegie Hall schedule, Lincoln Center's calendar, and the Dawkins event page.
All six invoked search and page reading. Three final answers acknowledged inability
to verify official source contents, two exhausted the four-call budget, and one
still incorrectly described findings as the only official events. This verifies
tool selection and multi-step execution, not reliable research judgment.

Saved inputs, tool results, and answers are in ignored
`.expo/page-reading-agent.json`; direct reads are in `page-reading-pages.json`.
Unit/integration checks separately verify public-network restrictions, redirect
handling, extraction, output limits, and a persisted search → calendar → event
sequence. The latter uses scripted model decisions and does not establish that
the live model reliably chooses or answers that sequence.
