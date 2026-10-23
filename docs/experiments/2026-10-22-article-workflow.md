# Article structure, support review and end-to-end pilot

Status: Completed experimental increment; autonomous publication remains unsupported.
Date: October 22, 2026.
Review: Coding-agent review, unblinded; independent human review pending.

## Structure and citations

The runner now has optional `--structured` and `--citations spans` modes.
Schema constraints enforce article/claim/evidence shapes and enumerate known source
IDs. Local validation still checks the plan, links and actual source evidence.

llama.cpp's [server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
describes schema-constrained responses; the
[request parser](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/server-common.cpp)
distinguishes `json_object` with `schema` from `json_schema` with a nested wrapper.
An initial incorrect wrapper was only constraining JSON syntax and produced missing
fields. Its two attempts remain recorded separately and are not counted as schema
successes. The verified `json_object` plus `schema` shape was then tested on the
actual configured server. The prompt and output cap otherwise stayed unchanged.

| Method and sample | Repeats | Structurally valid output | Full local plan/evidence validation |
| --- | ---: | ---: | ---: |
| Corrected schema, literal quotes, original synthetic sample | 2 | 2 | 2 |
| Corrected schema, literal quotes, original real sample | 2 | 2 | 0 |
| Schema and source spans, original real sample | 2 | 2 | 2 |
| Schema and source spans, development fixtures | 2 | 2 | 2 |
| Schema and source spans, held-out fixtures | 2 | 2 | 2 |

In literal-quote mode, real-mail quotes were reformatted by the model. Source-span
mode changes citation selection instead of loosening the quote check: deterministic
paragraph slices, at most 500 Unicode code points, get opaque IDs. The model selects
IDs, and a compiler inserts the exact original source substrings into the existing
plan contract. A span map is reproducible from the frozen records and runner.
Blank paragraph separators are not sent as separate spans. Raw model responses and
compiled plans remain separate. A span does not assert that a claim follows from it.

Examples:

```powershell
server/.venv/Scripts/python.exe ingestion/src/propose_articles.py --records ingestion/fixtures/article-accuracy-development.jsonl --config server/data/inference.json --output ingestion/data/reports/new-article-trial --repeats 2 --structured --citations spans
```

## Source inspection and semantic findings

Inspection verified the original message hash and found that its plain-text MIME
part already listed every order-progress stage. The HTML alternative also contained
those labels. The presence of a status label was not evidence of the corresponding
completed action. The new implementation does not parse a vendor-specific shipping
state or change the generic normalizer based on that one message.

The real span-mode drafts still included unsupported delivery claims, including in
an article description. The development and held-out fixtures distinguished proposed
from completed events and retained positive completion controls in the observed
outputs, but descriptions still used current/upcoming language and unknowns were
usually empty. Narrow fixture success is not an overall publication-quality score.

Reusable synthetic development/held-out records and criteria are in
`ingestion/fixtures/article-accuracy-*.jsonl` and `article-accuracy-rubric.json`.
The rubric is not sent to the model. It checks progress displays, proposals versus
attendance, explicit completion reports, conditions versus established account
features, correction history and reported returns. No prompt changes were made
after inspecting the held-out output. These records and labels were authored by
the same coding agent and are not an independent benchmark.

## Separate support triage

`ingestion/src/review_articles.py` checks all displayed article language: titles,
descriptions, claims and unknowns. It supplies the original source context as well
as the cited excerpts, requires one verdict for every check, and rejects missing,
duplicate or invented check IDs. Verdicts are supported, unsupported or uncertain.
It never edits, approves or publishes articles.

Sixteen labeled synthetic checks include eight supported controls and eight
unsupported assertions. The negative cases include an authentic but irrelevant
citation, a listed status mistaken for delivery, a proposal mistaken for service
completion, and a historical setting mistaken for current state. Expected verdicts
are withheld from requests. Calibration uses two repeats per model:

| Reviewer | Supported controls retained | Unsupported claims flagged | False support |
| --- | ---: | ---: | ---: |
| Configured local gpt-oss-20b MXFP4 | 16/16 | 14/16 | 2/16 |
| Existing hosted Gemini 4 Argon reference | 16/16 | 16/16 | 0/16 |

Denominators pool two correlated repeats, not independent cases. The local reviewer
falsely accepted the ambiguous delivery assertion in both. On the real negative
draft, local review missed the delivery claim in both repeats; one also falsely
rejected title paraphrases, while the other flagged nothing. This is evidence
against using local-model agreement as approval.

The hosted comparison used synthetic records only, through the existing production
Gemini adapter and its existing private credential loading. It was explicitly
selected with `--provider gemini`; there is no fallback and no live model switch.
The shared adapter includes agent tool schemas but no tool loop is run, and any
tool-call response is rejected. Its request is saved without headers or credentials;
its response is the adapter result with provider metadata, rather than the local
transport's raw HTTP JSON. This transport/format difference limits strict timing
and formatting comparisons. No hosted personal-mail review was performed here.

```powershell
server/.venv/Scripts/python.exe ingestion/src/review_articles.py --records ingestion/fixtures/article-support-records.jsonl --cases ingestion/fixtures/article-support-cases.json --config server/data/inference.json --output ingestion/data/reports/new-support-trial --repeats 2
```

Calibration results demonstrate behavior on these explicit checks, not general
semantic accuracy or a reliable publication gate. Stronger-model verdicts also
need review. No automatic routing decision has been made.

## Reproducible complete pilot

`ingestion/src/run_memory_pilot.py` now runs bounded mail normalization, deterministic
three-record sampling, repeated span-based drafts, support triage and candidate
rendering in one command. It preserves run state, selection criteria, original
inputs, requests, responses, code/config hashes in new runs and output content
hashes. A stage failure is recorded explicitly; directories cannot be overwritten.
The first run predates the added top-level code-hash metadata, but its proposal
and review components recorded their runner/request hashes.

The initial two-repeat pilot normalized 297 records and selected three short
records without topic keywords. They covered social notification, school-library
administration and a news newsletter. Both plans validated mechanically and both
support passes completed without flags. Inspection still found source-time state
worded as current and imperfect citation attribution. Notifications and news also
raise a separate relevance question: not every accurately extracted message should
necessarily become an enduring concept article.

Every result remains marked `live_publication: false`, `candidate_review: pending`.
Even all-supported review results cannot change that state. A successful pilot is
process completion, not acceptance. Tests exercise this boundary explicitly.
Rendering now exposes source timestamps in article headers, every evidence link
and index entries, alongside a statement that present-day state is unverified.
This is a provenance improvement, not a semantic fix for a false claim.

The [development guide](../memory-ingestion.md) gives the full command and layout.
Private artifacts live under ignored `ingestion/data/reports/`:

- `article-schema-synthetic-20261022/`: incorrect wrapper attempts.
- `article-schema-corrected-synthetic-20261022/`, `article-schema-real-20261022/`:
  corrected schema with generated quotations.
- `article-spans-real-20261022/`, `article-spans-development-20261022/`,
  `article-spans-holdout-20261022/`: span-based proposal trials.
- `article-support-calibration-20261022/`, `article-support-reference-20261022/`:
  local and hosted synthetic calibration.
- `article-real-support-local-20261022/`: local review of a known-negative draft.
- `generic-memory-pilot-20261022/`: complete bounded pipeline and private review notes.

## Verification and remaining work

Tests cover bounded source slices and round-trip compilation, schema wrapper shape,
withheld rubrics, complete review coverage, quote integrity, response-size and finish
checks, source-independent sampling, failed-stage reporting and refusal to publish
or approve after model agreement. Existing normalization and contract tests remain.

## Read-only retrieval follow-up

`ingestion/src/memory_preview.py` now validates candidate JSON sidecars and provides
literal article/source search, article reads and source pagination. It has bounded
inputs/responses, snapshot identities, mandatory matching snapshots on continuation,
and explicit unpublished status. It never reads or writes the live agent database
or vault, executes source content, or promotes a bundle based on a directory name.
It does not verify original archive bytes or prove semantic correctness.

Three topic lookups in the separately reviewed real-mail candidate bundle resolved
to the expected articles and literal source quotes. Missing-information lookup
returned zero results. Private check output is
`ingestion/data/reports/memory-preview-checks-20261022.json`. Unit tests also cover
unrelated synthetic topics, quote tampering, page reconstruction, snapshot changes,
unknown/path-like IDs and absence of writes to bundle files.

The next milestone is agent-conversation evaluation of that preview, including
usefulness, temporal interpretation and follow-up questions across topics.
Before live publication, establish revision ownership, broader deduplication and
service integration. Background consolidation, large-corpus indexing, attachment
processing and resumable full ingestion remain future work.

## Follow-up, October 23, 2026

The [reviewed integration experiment](2026-10-23-reviewed-memory-integration.md)
records the subsequent agent conversations, explicit publication boundary and
small live pilot. The next-milestone statements above describe the October 22
candidate stage. Large-corpus deduplication and background consolidation remain
unimplemented.
