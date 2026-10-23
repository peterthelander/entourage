# Memory ingestion development

Status: Experimental pipeline with a small reviewed memory pilot connected to the live Python service.
Updated: October 23, 2026.

The goal is generic memory from personal activity and historical exports: dated
evidence, organically organized concept articles, event/project instances and a
compact index. The [memory roadmap](personal-context-roadmap.md) describes the
intended experience. The ski-trip example is an evaluation case, not a subject
embedded in the pipeline.

## Current pipeline

1. **Read and filter.** Stream a bounded prefix of each MBOX, excluding the exact
   Gmail label `Category Promotions`. Preserve originals and log every complete
   message decision. Partial trailing records are outside the sample.
2. **Normalize.** Produce generic source records with readable body text, original
   timestamp, labels, original byte ranges and hashes. Report skipped oversized
   records, unknown dates, exact duplicates and omitted attachments.
3. **Select an experiment sample.** Rank eligible records by a seeded hash, without
   topic keywords. The current orchestration selects three complete bodies between
   100 and 3,000 characters. This is a bounded convenience sample, not representative
   sampling or a new ingestion exclusion policy.
4. **Draft articles.** Ask the configured local model for schema-constrained concept
   or instance plans. In source-span mode, the model selects source slice IDs;
   deterministic compilation inserts the original text and preserves literal-quote
   validation. Structure/citation validity does not imply claim validity.
5. **Triage support.** A separate model pass checks article titles, descriptions,
   claims and unknowns against the sources. Results are advisory. Tests found that
   the local reviewer can approve the same mistake as the drafting model.
6. **Render candidates.** Write isolated dated journals, articles, an index and
   input sidecars. Source timestamps are explicit in articles, citations and index
   entries. All outputs remain candidates with pending semantic review.
7. **Preview retrieval.** A read-only candidate reader supports literal article/source
   search, article reads and snapshot-checked source pagination. It validates source
   references and labels every preview result as unpublished.
8. **Review, publish and retrieve live.** A semantic reviewer accepts an exact
   candidate snapshot. The separate administrative publisher creates an immutable
   bundle and switches the active pointer. Opt-in service tools retrieve the
   reviewed sources/articles. Automatic publication and incremental updates remain
   unimplemented.

The pipeline creates detailed reports and hashes, has explicit failure states, and
refuses to reuse an output directory. It is not yet resumable. A successful run
means processing completed, not that the content was approved.

## Run a bounded pilot

From the repository root with the existing Python server environment:

```powershell
server/.venv/Scripts/python.exe ingestion/src/run_memory_pilot.py C:/path/to/Inbox.mbox C:/path/to/Sent.mbox --config server/data/inference.json --output ingestion/data/reports/new-memory-pilot --max-mib 64 --repeats 2
```

The wrapper uses local llama.cpp only. It does not restart or reconfigure the
running agent. Its output directory contains:

```text
pilot-report.json       # Stage outcomes, sampling, code/config/content hashes
normalized/            # Source records, message decisions and coverage
sample.jsonl           # Exact complete records selected for this experiment
proposals/             # Requests, responses and validated article plans
support-1/             # Advisory model support assessments
candidate-1/           # Unpublished journals, articles, index and sidecars
support-2/
candidate-2/
```

The completed local run is under ignored
`ingestion/data/reports/generic-memory-pilot-20261022/`. A subsequent dated render
is in `ingestion/data/candidates/generic-pilot-dated-preview-20261022/`. Generated
data and personal review notes remain outside Git. Raw source files stay in Downloads.

## What the experiments establish

Schema constraints and source-span references improved mechanical reliability on
the small trials. They did not solve overconfident claims, stale current-state
language, unsupported statements in descriptions, or what deserves a lasting article.

On a 16-case synthetic support check, the local reviewer falsely accepted one of
eight unsupported claims in both repeats. The existing hosted reference caught all
eight and preserved all eight supported controls in each repeat. That comparison
used synthetic records only and does not establish a reliable automatic gate on
personal mail. No automatic model selection or hosted fallback was added.

The deterministic real-mail sample also included social and news notifications.
Filtering Promotions alone does not decide what is useful personal memory. No new
category exclusion or durable-memory relevance policy has been selected.

## Reviewed live pilot

Five reviewed source records and five articles are now published in
`server/data/vault/knowledge/bundles/personal-pilot-20261022/`. The active pointer
is `server/data/vault/knowledge/current.json`; the machine's ignored inference
configuration enables `ENTOURAGE_KNOWLEDGE_ENABLED=1`. This remains opt-in by
default. Original mailbox byte hashes were checked for the selected records.
Review was performed by the coding agent; independent human review is pending.

The Python service owns the shared contracts, renderer, bounded reader and
publisher. Publication requires an accepted review bound to the exact candidate
snapshot, preserves immutable bundle revisions and atomically switches the active
pointer. Model support triage alone cannot approve publication. Rendered Markdown
is a view of the authoritative JSON, not an editable ingestion input.

Existing `searchMemories` and `getMemoryInventory` now expose conversation and
imported memory separately when enabled. Article/source readers require the
returned snapshot. Literal searches can fall back to explicitly labeled ranked
word-overlap leads. Recent source evidence is retained within bounded context for
immediate follow-ups, with stale snapshots excluded. Imported journals stay
separate from conversation journals. The four executed-tool-call limit remains;
a final answer-only model pass can summarize evidence when that budget is spent.

The live API inventory and a two-turn ski planning conversation completed: the
agent recovered historical dinner details and correctly said attendance, payment
and lodging were unknown. This demonstrates access to the small reviewed bundle,
not reliable recall across the full archives. Final local comparisons completed
all eight synthetic and six personal case runs; hosted comparisons completed six
of eight synthetic and all six personal runs. Completion is not a semantic pass:
unsupported general advice and occasional present-state wording remain issues.
No automatic hosted routing was added. Server tests (121), ingestion tests (34),
lint and TypeScript checking passed during integration.

## Next implementation boundary

Keep generation, support triage and publication separate. Broaden semantic review
of actual planning/recall conversations across topics, including follow-ups and
unknowns. Use a stronger model as a diagnostic reference, not proof of correctness.

Python now owns accepted source records, article revisions and indexes alongside
its existing conversation history. Incremental article updates, organic splitting,
larger reviewed coverage and background consolidation remain future work.

## Read-only candidate preview

```powershell
python ingestion/src/memory_preview.py --bundle ingestion/data/candidates/article-real-reviewed-20261022 search amazon
python ingestion/src/memory_preview.py --bundle ingestion/data/candidates/article-real-reviewed-20261022 search deadline --scope sources
```

`article <slug>` returns an article and dated source references. `source <id>` reads
up to 1,200 characters, with `next_offset` and `snapshot`; continuation requires
`--offset <next_offset> --snapshot <returned snapshot>`. Read limits can be set to
at most 6,000 characters. Search takes 1–6 literal strings, requires every string,
and returns at most five results with total counts. It is not semantic retrieval.

The reader loads the bundle's `records.jsonl` and `plan.json`, validates all source
references/quotes and derives a content snapshot. It does not read from SQLite,
load the live vault, write a persistent index or verify original archive bytes.
It treats these JSON sidecars as authoritative for preview; manually edited rendered
Markdown is not ingested back into the plan. Every result stays labeled as an
unpublished candidate even when a local directory name says "reviewed".

Three real-bundle topic lookups and all their cited source quotes passed deterministic
checks; an absent-topic query returned no matches. This establishes mechanical
retrieval and provenance, not agent recall, semantic accuracy or usefulness at scale.

## References

- [Generic contracts](experiments/memory-candidate-contracts.md)
- [Initial filtering](experiments/2026-10-22-ingestion-filtering.md)
- [Mail normalization](experiments/2026-10-22-mail-normalization.md)
- [Initial article generation](experiments/2026-10-22-article-generation.md)
- [Structure, support review and full pilot](experiments/2026-10-22-article-workflow.md)
