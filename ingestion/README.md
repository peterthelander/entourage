# Personal data ingestion

Status: Bounded ingestion experiments and explicit reviewed publication implemented;
a small reviewed pilot is live. Automatic synthesis/publication remains future work.
Updated: October 23, 2026.

This workspace is for Python batch-ingestion experiments with Google Takeout,
MBOX mail, calendars and contacts. The Python service remains the owner of live
agent memory. Batch experiments produce unpublished candidates. Only the separate administrative
publisher activates an explicitly reviewed bundle in the service knowledge store.

## Layout

- `src/`: reusable parsing, filtering and batch-processing code as it is developed.
- `data/raw/`: optional local source archives and exports.
- `data/normalized/`: parsed records with source references, before filtering.
- `data/filtered/`: records retained after deterministic filtering.
- `data/candidates/`: proposed concept articles and other derived memory.
- `data/reviewed/`: private bundles with explicit semantic review records.
- `data/reports/`: inventories, filter counts, checkpoints and experiment outputs.

The whole `data/` directory is ignored by Git. Keep private records, generated
articles, filenames and personal experiment reports there. Synthetic fixtures can
be committed with future code. Record methods and conclusions without personal
data in `docs/experiments/`.

Source files can remain in Downloads and be read by path; do not copy the large
mailboxes just to populate `raw/`. Treat originals as read-only. These folders
describe logical stages, not a requirement to duplicate the full corpus at every
stage. Stream records and retain only the intermediate outputs an experiment needs.

## Initial experiment rules

The guiding outcome is an agent that can review prior Chapin daddy-daughter ski
trips from ingested sources and help plan the upcoming trip. See the
[use case and success criteria](../docs/personal-context-roadmap.md#guiding-use-case-planning-the-chapin-daddy-daughter-ski-trip).
Measure filtering and extraction against useful, source-backed recall as well as
size reduction.

- Begin with bounded samples and report the sampling method and limits.
- Exclude mail with the exact Gmail label `Category Promotions`, parsed from
  `X-Gmail-Labels`, before model processing. Missing labels do not imply promotions.
- Report scanned, excluded and retained record counts and bytes, with an explicit
  definition of the byte measure used.
- Preserve source identity and message identifiers so candidates can be traced
  back to evidence. Account for overlapping exports before counting unique mail.
- Keep source text separate from inferred claims and generated article content.
- Design larger runs to resume from checkpoints; do not load whole MBOX files
  into memory.

## Run the initial filter

From the repository root, using Python's standard library only:

```powershell
python ingestion/src/filter_mail.py C:/path/to/Inbox.mbox --max-mib 64 --report ingestion/data/reports/sample.json --manifest ingestion/data/reports/sample.jsonl
python -m unittest discover -s ingestion -p test_*.py
```

The byte budget applies separately to each source. The scanner reads sequentially,
buffers only bounded headers, and omits the trailing incomplete message when the
budget ends before EOF. It recognizes standard MBOX `From ` envelope lines;
body lines beginning with `From ` must be escaped as in standard MBOX exports.
Oversized headers are retained conservatively and counted for review.

The JSON report measures original MBOX bytes, including attachments and MIME
encoding, rather than extracted text or token counts. The optional JSONL manifest
records source paths, byte ranges, message IDs, labels and decisions. It does not
copy message bodies or create filtered MBOX files. Original sources must remain
unchanged for these offsets to remain valid. Outputs must use new filenames.
Duplicate exports are not deduplicated; counts are per-source records. Resume
support and durable source fingerprints remain future work before full ingestion.

The first [filter experiment](../docs/experiments/2026-10-22-ingestion-filtering.md)
records findings and limits.

The [ski-trip discovery pilot](../docs/experiments/2026-10-22-ski-trip-discovery.md)
adds bounded decoded-body discovery and a privately stored, manually reviewed
candidate history. The later reviewed pilot provides live retrieval of a selected
source, rather than automatically publishing these discovery results.

See the [memory roadmap](../docs/personal-context-roadmap.md) and
[ongoing work streams](../docs/ongoing-work-streams.md).

## Generic memory candidates

[Source-record and article contracts](../docs/experiments/memory-candidate-contracts.md)
define the shared envelope and output ownership. `src/memory_candidates.py` validates
records plus a separately reviewed article plan and renders source journals,
concept/instance articles, evidence references and an index into a fresh directory.
There are no topic-specific rules or model calls in this renderer.

Synthetic multi-topic inputs live in `fixtures/`. To reproduce the pilot with a
new destination:

```powershell
python ingestion/src/memory_candidates.py --records ingestion/fixtures/memory-records.jsonl --plan ingestion/fixtures/memory-plan.json --output ingestion/data/candidates/generic-contract-pilot-20261022
```

Quote validation proves source-text presence, not semantic correctness. Article
plans still require review. Existing discovery outputs need a normalization adapter
before they can enter this format. Rendering does not publish to the live vault.

## Normalize retained mailbox samples

`src/normalize_mail.py` bridges MBOX records to the generic format without topic
matching or model calls. Use a fresh output directory:

```powershell
python ingestion/src/normalize_mail.py C:/path/to/Inbox.mbox C:/path/to/Sent.mbox --max-mib 64 --max-message-mib 8 --output ingestion/data/normalized/mail-sample
```

Outputs are `records.jsonl`, `decisions.jsonl` and a completion `report.json`.
The byte budget applies per source. Decisions cover every complete sampled message,
including exclusions, skipped messages and exact-raw duplicates. A run without the
completion report is unfinished and must not be published. Outputs are experimental
and are not resumable yet. Sources remain read-only.

The adapter preserves original `Date` timestamps with offsets, message IDs, labels,
raw-message SHA256 and byte locators. It does not infer event dates. Plain text is
preferred within MIME alternatives; HTML-only bodies are converted to visible text.
Attached files, attached forwards and nontext parts are omitted and described in
extraction metadata. Whole messages over the size cap are skipped, not truncated.
Missing/ambiguous dates and empty readable bodies are reported for later review.

See [the adapter pilot](../docs/experiments/2026-10-22-mail-normalization.md) for
results, identity semantics and remaining limitations.

## Propose articles with the local model

`src/propose_articles.py` runs a bounded, explicitly selected sample through the
configured llama.cpp server. Use the server virtual environment and a new output
directory; it does not change the running agent's configuration:

```powershell
server/.venv/Scripts/python.exe ingestion/src/propose_articles.py --records ingestion/fixtures/memory-records.jsonl --config server/data/inference.json --output ingestion/data/reports/article-sample --repeats 2
```

It preserves inputs, requests, responses and validation outcomes. A structurally
valid plan remains pending semantic review; it is never automatically rendered or
published. Initial [article-generation trials](../docs/experiments/2026-10-22-article-generation.md)
found unsupported completion claims despite real citations. A separately reviewed
candidate example exists locally, while automatic publication remains unimplemented.

## Run all current stages

The [development guide](../docs/memory-ingestion.md) describes the complete bounded
pipeline and current boundaries. A fresh local run uses:

```powershell
server/.venv/Scripts/python.exe ingestion/src/run_memory_pilot.py C:/path/to/Inbox.mbox C:/path/to/Sent.mbox --config server/data/inference.json --output ingestion/data/reports/new-pilot --max-mib 64 --repeats 2
```

It normalizes, selects three whole short-body records by seeded hash, generates
schema-constrained plans using explicit source spans, runs advisory local support
checks and renders isolated candidates. Outputs retain timestamps, hashes and
reports. It never publishes or marks model agreement as approval; successful
processing still leaves semantic review pending. Sources remain read-only and
the running agent's inference settings and memory are untouched.

For separate proposal trials, add `--structured --citations spans`. For advisory
support checks, use `src/review_articles.py --records <sample.jsonl> --plan <plan.json>
--config server/data/inference.json --output <fresh-directory> --repeats 2`.
It also accepts synthetic `--cases` for calibration. The optional explicit
`--provider gemini` uses the existing server adapter and credentials as a diagnostic
reference, with no automatic fallback. Source bodies sent to a hosted reviewer
would leave the local inference path; the completed comparison used synthetic
records only. See [findings](../docs/experiments/2026-10-22-article-workflow.md).

`src/memory_preview.py` supplies read-only article/source search and paginated source
reads over a candidate bundle. See the [preview commands and boundaries](../docs/memory-ingestion.md#read-only-candidate-preview).
It labels all results as unpublished, checks literal evidence, and does not open
the live memory database or vault. Agent-level conversations have now been evaluated; see the
[reviewed live pilot](../docs/memory-ingestion.md#reviewed-live-pilot).

## Publish a reviewed bundle

The shared contracts, renderer and reader live in `server/entourage_server/`;
ingestion CLIs import that owner. Candidate previews remain unpublished. After
semantic review, use the administrative publisher described in
[service operations](../server/EXECUTION.md#reviewed-imported-memory). It requires
an accepted review tied to the exact candidate snapshot, creates a new immutable
bundle and switches an atomic pointer. Advisory support checks never approve it.

To reproduce isolated conversation checks with fictional reviewed data:

```powershell
server/.venv/Scripts/python.exe scripts/evaluate-knowledge.py --bundle ingestion/fixtures/reviewed-conversation-memory --fixture ingestion/fixtures/knowledge-conversations.json --output ingestion/data/reports/new-conversation-check --providers local --repeats 2
```

`--providers local gemini` also uses hosted reference inference and sends the
supplied source content to that provider. Reports preserve inputs, tool results
and answers; keep personal reports under ignored `data/`. Execution completion
and literal assertions are mechanical checks, not semantic accuracy scores.

`scripts/check-knowledge.py --output <new-private-report>` checks the running
service by creating a service-verification conversation and a device registration;
it does not add the exchange to shared-chat consolidation. This live check writes
verification history and runs inference.
