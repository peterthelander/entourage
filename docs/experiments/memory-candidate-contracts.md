# Generic memory candidate contracts

Status: Version 1 contracts, deterministic renderer and explicit reviewed service integration implemented; automatic synthesis/publication remains experimental.
Updated: October 23, 2026 (initial contract October 22).

## Purpose and boundaries

Implement the [memory roadmap](../personal-context-roadmap.md) with a small common
record envelope, readable chronological evidence, living concept articles and
event/project instance articles. Topic names and relationships are data. No ski-trip
matching, fixed subject taxonomy or topic-specific code belongs in this renderer.
The ingestion CLI is `ingestion/src/memory_candidates.py`; shared validation and
rendering live in `server/entourage_server/knowledge_contracts.py` and
`knowledge_documents.py`. Python's standard library is sufficient. The service
owns live memory.

## Source records: JSONL version 1

One JSON object per retained logical source record:

| Field | Meaning |
| --- | --- |
| `version` | `1` |
| `id` | Unique lowercase hyphenated identifier, assigned by the adapter and reused on subsequent imports |
| `kind` | Nonempty source type, e.g. email, calendar, receipt or conversation; no fixed enumeration |
| `title`, `text` | Source title and normalized readable content, not model-authored summary |
| `observed_at` | Source timestamp with explicit UTC offset, not ingestion time |
| `event_date` | Optional date explicitly supported by the source, or null; does not assert occurrence |
| `source.uri` | Original source location or immutable object reference |
| `source.locator` | Position within that source, e.g. archive entry plus MBOX byte range |
| `source.sha256` | Lowercase SHA256 of the exact original source unit identified by the locator |
| `labels` | Optional list of original labels, preserved for auditing |

For email, `observed_at` should come from the selected source timestamp, while a
future event date belongs separately in `event_date`. A date mentioned in a quoted
email is not automatically the date of the enclosing message. Sources without a
reliable timestamp need an explicit adapter decision before entering this prototype;
do not silently substitute import time. Multiple event dates can remain in source
text until a richer temporal representation is justified.

The envelope is rigid only about identity, provenance and basic integrity. It does
not impose a taxonomy on people, activities or concepts. Adapters must specify
their source-unit hashing and ID assignment and preserve extraction/truncation
information when introducing partial records. This prototype expects complete
normalized text. The prior topic-search JSONL is not this contract and must not be
silently relabeled as normalized records.

Validation checks shape, unique IDs, timestamp offsets, source locators and hash
syntax. It rejects retained records carrying the exact Promotions exclusion label.
It does not resolve source URIs, verify original bytes against hashes, deduplicate
exports, detect forwarded content or validate source statements as real-world facts.
Those remain adapter/integration responsibilities. A syntactically valid checksum
alone is not proof of source integrity.

## Article plan: JSON version 1

The renderer consumes a separate reviewed plan with `version: 1` and an `articles`
list. This preserves the boundary between evidence and editorial/model decisions.
Each article contains:

Instances can additionally carry an `activity_period` object with ISO
`start_date`/`end_date` and a `series_slug` naming an existing concept article.
Activity dates require semantic review of source evidence; syntax validation
checks ordering, not truth. They do not assert completion. An email sent in one
year can describe an activity in another; its source journal stays on the source
timestamp's day. The deterministic views and retrieval preserve both dates.
The current generation schema does not automatically produce these optional
fields; extraction/curation supplies them before review. Advisory support triage
includes the activity period when present.

- `slug`, `title`, `description`: safe filename stem, human title and short index entry.
- `type`: `concept` for a continuing subject, or `instance` for an event/project occurrence.
- `claims`: text with type `source_statement`, `inference` or `suggestion`.
- Each claim's `evidence`: nonempty list of `record_id` and exact `quote` pairs.
- `unknowns`: explicit unresolved questions rather than invented completeness.
- `links`: other article slugs in this plan; checked for broken references.

Evidence quotes must occur in the cited normalized text. This mechanically prevents
invented quotations and missing references, but cannot establish that the claim is
entailed by the quote. Human semantic review remains necessary. A later model can
propose plans under this same contract; this implementation does not invoke one.
Historical statements, interpretations and suggestions have separate output sections.
An instance article can carry suggested next steps; completion state, assignees and
task synchronization are deliberately not invented in this first contract.

## Output and ownership

Each run requires a new output directory and validates the entire input before
creating it. A failed write can leave a partial experiment directory; it is not a
transactional publish. No existing files are overwritten.

```text
<new candidate directory>/
  records.jsonl           # Retained evidence envelope and source locators
  plan.json               # Editorial decisions retained for inspection
  journals/YYYY-MM-DD.md  # Quoted source text grouped by observed date
  articles/<slug>.md      # Concept or instance, with evidence links
  index.md                # Article titles and short descriptions
```

Journals retain the source timestamp's local date and UTC offset. They show event
dates separately and quote source material as untrusted content. They are evidence
projections, not generated claims about what actually happened. They do not write
to or replace the service's generated conversation journals. Future synthesized
episodic summaries must be distinguishable from these source projections.

Articles cite journal entries; those entries include source locators and hashes.
Related articles use `[[wiki-links]]` alongside standard Markdown links. The index
is a readable registry, not an assumption that every article will fit in context
at archive scale. Retrieval budgets and index partitioning need later evaluation.

Living updates, splitting large articles, background consolidation, duplicate and
correction resolution, model-driven topic discovery, checkpoints and atomic live
publication remain future work. This experiment renders isolated candidate snapshots.

## Synthetic pilot and checks

Run from the repository root, selecting a fresh output path each time:

```powershell
python ingestion/src/memory_candidates.py --records ingestion/fixtures/memory-records.jsonl --plan ingestion/fixtures/memory-plan.json --output ingestion/data/candidates/generic-contract-pilot-20261022
python -m unittest discover -s ingestion -p test_*.py
```

Four fictional records cover a garden workday and later date correction, bicycle
maintenance, and a reading-circle invitation. Three manually written article plans
produce four dated journals, three articles, an index and retained input sidecars.
Fixture source hashes are computed from each complete synthetic UTF-8 source text.

Inspection confirmed that the garden article retains both proposed dates and the
later correction, does not claim attendance, and labels checking for later changes
as a suggestion. The bicycle article reports receipt contents without inventing a
future service interval. The reading-circle instance distinguishes its invitation
date from its event date and does not claim attendance. Tests check these temporal
and provenance boundaries, deterministic rendering, missing/fabricated evidence,
unsafe paths, broken links, duplicate IDs, Promotions and ambiguous timestamps.

These results establish mechanical generality across several topics, not automatic
topic discovery, semantic synthesis quality or agent-level recall. The
[bounded mail adapter](2026-10-22-mail-normalization.md) now bridges retained MBOX
records to this envelope. Next, review model-proposed
plans on a small mixed-topic corpus before introducing live article updates.
