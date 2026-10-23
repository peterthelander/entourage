# Generic mail normalization pilot

Status: Completed bounded adapter pilot; synthesis and live integration remain future work.
Date: October 22, 2026.

## Implementation

`ingestion/src/normalize_mail.py` consumes standard MBOX sources with the existing
streaming scanner. It applies the exact Promotions exclusion before reading bodies,
then converts all eligible topics into the [generic source envelope](memory-candidate-contracts.md).
No topic searches, model calls or event-date inference are used.

The adapter prefers plain text within MIME alternatives, converts HTML-only text
with an HTML parser, and omits scripts, styles and document metadata. It preserves
all readable sibling sections in mixed messages while excluding attachments,
attached-message subtrees and nontext parts. Extraction metadata reports omitted
parts, charset fallback and parser warnings. Quoted inline forwards remain text;
the adapter does not assert they are independent corroboration.

Records preserve decoded subject, sender/recipient, original Date and Message-ID,
labels, source file URI, byte offset/length and a hash. The SHA256 and `mail-<hash>`
ID cover the exact MBOX byte range including its envelope, MIME encoding and
attachments, not just extracted text. Unchanged raw records retain identity when
moved. Changed labels or export envelopes may create different IDs for the same
logical email. Message-ID alone is not trusted as a deduplication key. Exact raw
duplicates are suppressed within a run and logged; semantic/thread deduplication
and aggregation of multiple source locations remain future work.

Missing/multiple dates, invalid dates, dates with unknown offsets, oversized
messages, oversized headers and messages with no readable body are skipped with
explicit decision reasons. The adapter never substitutes import time. Body-only
extraction is not a promise to preserve attachment contents or HTML appearance.
Records retain the complete selected normalized body without character truncation.

Outputs use a fresh directory. `report.json` is written only after successful
completion; without it, partial outputs are unfinished. Source size and modification
time are checked before/after each scan to catch ordinary concurrent edits. Hashes
can validate a record's byte range later; no full-file snapshot/fingerprint or
transactional source lock is provided. Resume is not implemented.

## Reproduction

Run from repository root with a fresh destination:

```powershell
python ingestion/src/normalize_mail.py C:/Users/Owner/Downloads/Inbox-003.mbox C:/Users/Owner/Downloads/Sent-002.mbox --max-mib 64 --output ingestion/data/normalized/mail-prefix-64mib-20261022
python -m unittest discover -s ingestion -p test_*.py
```

Private outputs: ignored `ingestion/data/normalized/mail-prefix-64mib-20261022/`
contains records, per-message decisions and coverage reports. An empty article plan
was used with the generic renderer to verify journal production; generated files
live in ignored `ingestion/data/candidates/mail-prefix-journals-20261022/`.
This did not synthesize articles or publish anything to the service's live vault.

## Results

Read the first 64 MiB from each source; trailing partial messages were not processed.

| Decision | Inbox | Sent |
| --- | ---: | ---: |
| Complete sampled messages | 435 | 149 |
| Promotions excluded | 259 | 1 |
| Normalized | 171 | 126 |
| Unknown date offset | 1 | 3 |
| Above 8 MiB message cap | 2 | 2 |
| No readable body | 2 | 8 |
| Exact-raw duplicates suppressed | 0 | 9 |

The 297 emitted records correspond to 36,130,082 original bytes. Their selected
normalized text totals 1,017,667 UTF-8 bytes (about 0.97 MiB); full JSONL with
provenance and extraction metadata is 1,317,526 bytes (about 1.26 MiB). These are
measures for the emitted subset only, not a claim of equivalent information
retention across the whole 128 MiB sample. Skipped large messages explain a
substantial part of the difference from the filter's retained byte totals.

Twenty-two emitted records describe omitted parts; none reported decoder/parser
warnings. The generic renderer accepted all records and produced 39 dated source
journals plus its three input/index sidecars. Spot checks found a readable service
notification and a newsletter body with encoded formatting noise. Thus normalization
does not imply all retained material is useful or clean. No extra categories or
newsletter rules were enabled.

## Verification and next step

Tests cover original-byte hash/locator semantics, timestamp preservation, generic
journal compatibility, MIME alternatives, HTML scripts/styles, attached forwards,
charset fallback, Promotions, malformed/unknown dates, missing bodies, size limits,
exact duplicates and refusal to overwrite output. Source fixtures are synthetic.

The bounded adapter establishes a bridge to the generic format, not full-corpus
coverage, complete semantic deduplication or memory quality. Next, inspect mixed-topic
record samples and evaluate model-proposed article plans with evidence quotes and
unknowns. Attachment extraction, date recovery and fuller noise filtering need
separate experiments before broad ingestion.
