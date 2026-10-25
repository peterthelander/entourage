# Evidence-backed personal overviews

Date: October 24, 2026 (local time).
Continuation: October 25, 2026.
Status: Comparison complete; thematic candidate not adopted in production.

## Question

The [broader-memory feedback](2026-10-24-broader-memory-sample.md#subsequent-live-feedback-breadth-versus-significance)
showed an answer organized around a flat article inventory, with no recorded
article/source reads. Does supplying inspected article evidence help, and does
an editorial thematic organization add value beyond the same evidence?

This experiment does not add automatic importance ranking, consolidate memory,
change the live prompt, or publish a new knowledge bundle.

## Implemented controls

`scripts/memory_overview.py` validates a versioned editorial plan bound to an
exact reviewed-bundle snapshot. Every article belongs exactly once to a theme
or `detail_only`. Themes are content-derived, with no required personal taxonomy.
Significance hypotheses use lasting relevance, recurrence, explicit emphasis or
consequences, with references to existing source-statement claims. Suggestions
and inferred claims cannot support these references. Structural validation
does not establish that a theme matters to the user, or that a source actually
supports the chosen significance signal. These judgments require review.

The builder copies complete selected articles, including claim types, quoted
evidence, source timestamps and unknowns. It introduces no new factual prose.
Repeated article envelopes and timestamp maps are removed. Identical source
excerpts appear once in an evidence map, with each claim referencing their IDs;
record IDs and dates stay adjacent to each exact quotation. A reconstruction
test verifies that normalization preserves every claim and excerpt byte.
Unselected articles remain in a separately identified index; their contents are
not claimed as inspected. Packets fail above 64,000 UTF-8 bytes rather than
silently dropping qualifications. This byte limit is an experiment bound, not
a guarantee that a model context will fit; transport preflight still applies.

`scripts/diagnose-memory.py` now supports three additional conditions:

- `inventory`: titles/descriptions for the frozen imported bundle, without article evidence.
- `flat_overview`: complete selected articles and the full index, without thematic grouping.
- `thematic_overview`: exactly the same article evidence and index, with editorial theme assignments and significance hypotheses.

The last two conditions have identical factual evidence. Their difference is
grouping metadata and its additional prompt length. Comparison with `inventory`
tests evidence availability separately from this grouping treatment. The inventory
condition approximates the observed index-only failure, not a production retrieval
score. All conditions supply evidence as untrusted user data and disable tools;
they bypass the worker's discovery/call budget. No condition proves that the
agent can independently retrieve this packet. Existing `retrieval`, `articles`
and `sources` diagnostic modes remain available.

The same plan is reused across all questions and follow-ups. Explicit
`diagnostic_articles` selectors may add a detailed episode to both evidence
conditions. That is an oracle control for detail retention, not proof of automatic
drill-down. The experimental plan, builder, runner, fixture, source-backed expected
findings, service code and effective settings are frozen before inference.
Reports retain failed turns, partial progress and evidence inputs. Existing
report-bound review tooling distinguishes execution from semantic findings.

## Reproduce with fictional data

Validate and export an inspectable packet before inference:

```powershell
.\server\.venv\Scripts\python.exe scripts/preview-memory-overview.py `
  --bundle ingestion/fixtures/memory-overview-memory `
  --overview ingestion/fixtures/memory-overview.json `
  --output scratch/memory-overview-preview.json
```

This reads reviewed data without inference or publication and refuses to overwrite
an existing output. It validates structural support, not the meaning of a theme.

From the repository root on Windows:

```powershell
.\server\.venv\Scripts\python.exe scripts/diagnose-memory.py `
  --bundle ingestion/fixtures/memory-overview-memory `
  --fixture ingestion/fixtures/memory-overview-conversations.json `
  --expected ingestion/fixtures/memory-overview-expectations.json `
  --overview ingestion/fixtures/memory-overview.json `
  --modes inventory flat_overview thematic_overview `
  --repeats 2 --output scratch/memory-overview-fictional
```

Use `server/.venv/bin/python` on macOS/Linux. This uses configured local llama.cpp
inference and isolated temporary databases; no live chat or knowledge pointer is
changed. The output directory must be new. Private plans, inputs and reports belong
in ignored `scratch/`. Fictional fixtures are authored development material.
The fictional bundle includes an unnamed camp participant, a separate school
note naming Alex, and an unread employment-verification attachment. These are
development regressions derived from observed attribution/current-status failures,
not untouched validation. Their source statements, dates and explicit unknowns
remain separate in the evidence packet. The earlier shared conversation fixture
is unchanged.

Judge broad overviews, specific details and follow-ups together: coherence,
proportionate detail, individual qualifications, dated/current distinctions,
attribution, uncertainty, execution and latency. Frequency or number of articles
does not establish importance. A one-off event can be important. Coding-agent
curation/review is explicitly distinct from independent validation.

Prepare and complete a report-bound review using the existing
[freeze/review workflow](conversation-evaluations.md#freezing-and-reviewing-a-memory-experiment).
Then compare conditions without automatic grading:

```powershell
.\server\.venv\Scripts\python.exe scripts/compare-memory-conditions.py `
  --report scratch/memory-overview-fictional/report.json `
  --expected ingestion/fixtures/memory-overview-expectations.json `
  --review scratch/memory-overview-fictional/review.json `
  --manifest scratch/memory-overview-fictional/freeze.json `
  --output scratch/memory-overview-fictional/conditions.json
```

The comparison validates review identity first, then reports each provider/mode's
whole-case passes, attempted/completed/failed/skipped turns, semantic verdicts and
latency. Attempted latency includes failures; completed-only latency explicitly
excludes them. Entirely missing runs remain visible in the validation result.

## Real local-model comparison

Private inputs and reports: `scratch/memory-overview-20261024/`.
The compact plan uses the existing 69-source/27-article snapshot. Eight complete
articles are organized into four provisional areas; nineteen remain index-only. The
separate dinner-detail question supplies its article in both evidence conditions.
No original article, source, review or active pointer is modified.

The comparison has two cases, four planned turns per condition, three conditions
and one repeat. Expectations were prepared from source-backed articles before
inference. The comparison is exploratory and manually curated, without independent
review. Results and the adoption decision are recorded below.

The first attempt (`run/`) used ten complete articles in five areas. The inventory
overview completed but made unsupported relationship/current-status assertions;
its first follow-up timed out at 90 seconds. All four full-evidence case runs
failed actual-token preflight: 18,759–20,615 input tokens exceeded the configured
16,384-token context, even before the 2,048-token response reserve. The source-bound
plan, questions, expectations and complete failed traces are retained. Exact first
input bytes were recovered from recorded packets and verified against their frozen
hashes after preparing the next candidate. These failures are not semantic scores.

The compact rerun (`compact-run/`) deduplicates evidence and reduces the selected
article set while retaining the full index and complete selected articles. This
is a revised candidate, not a matched normalization-only comparison with the
first attempt. Direct template/tokenizer preflight measured 9,649/10,266 tokens
for the flat/thematic overview and 10,553/11,170 for the detail question, before
the response reserve. The timeout is increased to 180 seconds for all conditions;
the live model, context capacity and output allowance are unchanged. The first
attempt remains a separate failed development run.

The compact run stopped overnight during the thematic overview's second turn.
The runner was no longer present when work resumed on October 25. Its exact
last saved report is archived at `continued-run/interrupted-report.json`; the
original report is now explicitly marked interrupted. The saved partial thematic
answer is preserved as an interrupted attempt, not a completed conversation.

The continuation verifies the original frozen code, inputs and effective settings,
plus the loaded model alias, template hash and engine build. Completed case runs
are retained, including the failed flat-evidence follow-up. The unfinished thematic
case restarts from turn one in a new isolated database; no model stream or live
turn is replayed. The remaining dinner controls then run under the same frozen
plan. `continued-run/continuation.json` binds the source report and continuation
script hashes. The overnight gap is a further limitation on latency comparisons.

## Completed findings and decision, October 25

All six planned case/condition runs have a result in `continued-run/report.json`.
Of twelve planned turns, eight completed, two timed out and two follow-ups were
not run after those timeouts. Report-bound unblinded coding-agent review is complete;
independent review remains absent. Execution completion is separate from the
predeclared semantic criteria.

| Condition | Completed / failed / skipped turns | Whole cases passing review | Specific dinner question | Median attempted turn time |
| --- | --- | --- | --- | --- |
| Inventory only | 4 / 0 / 0 | 0 of 2 | Fail: printed an unexecuted tool call | 67.2 s |
| Flat selected evidence | 2 / 1 / 1 | 1 of 2 | Pass: correct details, attendance unknown | 140.8 s |
| Thematic selected evidence | 2 / 1 / 1 | 0 of 2 | Fail: correct details, then inferred likely attendance | 149.0 s |

The medians include attempted turns that failed; skipped turns have no invented
duration. Small samples, an overnight interruption, different response contents,
and unmeasured engine load prevent treating these figures as general performance
estimates or a causal measurement of grouping overhead.

The inventory overview already used coherent headings. Its failures were more
substantial than flat organization: unsupported current circumstances, completed
events inferred from plans, and confidence in uninspected descriptions. Its
importance-challenge follow-up correctly denied that frequency establishes user
priorities, but that did not repair the whole conversation.

Complete selected articles improved the specific dinner answer: exact reservation
details and the declined overnight invitation were recovered while attendance
remained unknown. This is supplied-evidence performance, not autonomous retrieval.
The thematic answer recovered the same details but ended by saying the dinner
likely took place. The predeclared criterion required withholding an attendance
inference; review records this as a narrow qualification failure, not a failure
to find the main facts. That distinction matters when interpreting the table.

Neither full-evidence condition produced a passing broad overview. The thematic
answer assigned a camp purchase to a named child despite an explicit blank
participant field and unknowns. Both added unsupported current or lasting traits
to dated evidence. Both first follow-ups exceeded the 180-second inference
deadline; their third turns were correctly skipped. The earlier interrupted
thematic answer also overclaimed, and remains separately preserved rather than
silently counted as another successful run.

Decision: retain the bounded packet builder, offline preview, condition comparison
and fictional attribution regressions. Do not deploy this editorial grouping as
a synthesis layer, impose a personal taxonomy, add an importance score, or change
the live prompt/model/bundle on this evidence. No service restart or publication
was performed. Grouping alone has not demonstrated a reliability benefit.

The next bounded question is source binding: compare the same selected evidence
with and without uninspected index descriptions in the answer context, while
retaining positive and negative attribution controls. That may isolate some
index-derived additions, but cannot by itself explain the named-child error from
an inspected article. Further model/context comparisons, latency limits and fresh
independent review remain necessary. More archive ingestion is not the immediate
remedy demonstrated by these results.

Verification: 162 service tests passed, with focused memory tests rerun after the
fictional fixture additions; 46 ingestion tests and 46 JavaScript tests passed.
Lint, TypeScript checking and whitespace checks passed. These checks establish
implementation behavior, not answer correctness. The fictional model cases have
not themselves been claimed as a passing inference benchmark.

Post-study review, October 25: corrected the inventory-only packet's scope text
to state explicitly that it contains no article/source contents. The original
shared scope wording incorrectly described selected articles as supplied in full
even in that condition. Recorded inputs, reviews and timings above retain their
original frozen wording; the corrected baseline has not been rerun. Both preview
and diagnostic commands now use the same 256,000-byte plan-input limit. These
implementation corrections do not establish an improvement in model answers.
