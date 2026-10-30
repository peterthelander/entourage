# Memory ingestion

Status: Experimental candidate pipeline; reviewed pilot available to the service.
Updated: October 30, 2026.

## Current state and ownership

The curated pilot contains 69 source records and 27 articles. It demonstrates
retrieval over reviewed personal history, not autonomous reconstruction or full
archive coverage. Coding-agent curation and acceptance were used; independent
human validation remains pending. No model training or fine-tuning occurred.

Python owns shared source/article contracts, validation, rendering, bounded
readers and administrative publication. The service reads an explicitly accepted
immutable bundle through `server/data/vault/knowledge/current.json` when imported
memory is enabled. Rendered Markdown is a view of authoritative JSON inputs.
The service does not ingest these development documents as personal memory.

`searchMemories` and `getMemoryInventory` expose conversation and imported memory
separately. Imported article/source reads require the returned snapshot. Literal
search can fall back to labeled word-overlap leads. Bounded recent tool evidence
supports immediate follow-ups; stale snapshots are excluded. Imported journals
remain separate from conversation journals.

## Candidate pipeline

1. Read bounded MBOX inputs, preserving originals and logging decisions. The exact
   Gmail label `Category Promotions` is excluded; partial trailing records are
   outside the sample.
2. Normalize source text, timestamps, labels, original byte ranges and hashes.
   Report oversized records, missing dates, duplicates and omitted attachments.
3. Select a bounded experiment sample and draft source-backed article plans.
4. Validate structure and literal evidence references, then run advisory support
   checks. Valid citations and model agreement do not establish claim accuracy.
5. Render unpublished candidates for inspection and read-only retrieval preview.
6. Accept an exact snapshot through explicit semantic review. The separate
   publisher creates an immutable bundle and atomically switches the pointer.

The batch wrapper currently uses a seeded three-record convenience sample and
local llama.cpp. It does not restart or reconfigure the agent. It refuses reused
output directories and is not resumable. Commands, output layout and discovery
utilities are documented in the [ingestion workspace](../ingestion/README.md).
Private catalogs, candidates and reports stay in ignored `ingestion/data/`.

## Read-only candidate preview

```powershell
server/.venv/Scripts/python.exe ingestion/src/memory_preview.py --bundle <candidate-directory> search deadline --scope sources
server/.venv/Scripts/python.exe ingestion/src/memory_preview.py --bundle <candidate-directory> article <slug>
server/.venv/Scripts/python.exe ingestion/src/memory_preview.py --bundle <candidate-directory> source <id>
```

Search accepts 1–6 literal strings and returns at most five results. Source reads
return 1,200 characters by default, up to 6,000 with `--limit`. Continue using
`--offset <next_offset> --snapshot <returned snapshot>`. Article reads include
cited source evidence. The reader validates JSON inputs and evidence references;
it does not verify original archive bytes or read edited Markdown back into plans.
Every preview remains labeled unpublished.

## Reviewed live pilot

The recorded active bundle is `broad-history-20261024`. Publication binds review
to the exact source/article snapshot and preserves prior immutable bundles.
Actual activation is machine configuration; see [service configuration](../server/README.md).

Source records retain observation dates. Instance articles can carry reviewed
activity periods and series links. A booking does not establish attendance or
present status. Topic selectors and curated facts belong in experiment inputs
and personal knowledge, not production rules. The exploratory
`ingestion/src/find_ski_trip.py` is isolated from production.

## Limits and future work

Automatic extraction and synthesis can omit qualifications or introduce unsupported
claims despite mechanically valid evidence. Retrieval success does not guarantee
faithful model answers. Semantic review remains required for publication.

Automatic acceptance, incremental updates, consolidation, full-archive ingestion,
attachment extraction and real bank/card adapters are unimplemented. Existing
fictional transaction fixtures do not implement those adapters. Further expansion
and synthesis experiments are deferred; see [current priorities](ongoing-work-streams.md)
and the [memory roadmap](personal-context-roadmap.md).

For findings and historical verification, use the [experiment index](experiments/README.md).
Future validation should separate discovery, extraction, event membership,
synthesis and conversational answering under the
[evaluation protocol](experiments/conversation-evaluations.md#memory-experiments-and-holdout-separation).
