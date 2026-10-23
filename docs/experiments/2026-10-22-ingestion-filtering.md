# Initial deterministic mail filtering

Status: Completed bounded pilot; full-corpus effects remain unmeasured.
Date: October 22, 2026.

## Method

Read the first 64 MiB of each of the Inbox and Sent MBOX exports, without modifying
sources or sending content to inference. Count only complete message records.
Exclude records whose parsed `X-Gmail-Labels` contains the exact label
`Category Promotions`. Preserve all other records, including missing labels.
Byte counts include the original envelope, headers, MIME body and attachments.
The scanner and reproduction instructions live in [ingestion](../../ingestion/README.md).
Private reports and source-offset manifests are in ignored `ingestion/data/reports/`.

## Results

| Sample | Complete messages | Excluded | Retained | Excluded bytes | Retained bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Inbox prefix | 435 | 259 | 176 | 22,458,770 | 44,586,078 |
| Sent prefix | 149 | 1 | 148 | 13,888 | 64,263,682 |

Promotions filtering removed 59.5% of Inbox records and 33.5% of counted Inbox
bytes. Sent exclusions were 0.7% of records and approximately 0.02% of bytes.
The Inbox sample ended with 64,016 bytes of an incomplete record; Sent ended with
2,831,294 bytes. Those bytes are excluded from the result denominators. No counted
record had missing labels or oversized headers. There were no unassigned bytes.

## Interpretation and next questions

The selected filter substantially reduces this Inbox sample, with little effect
on Sent. Large non-promotional messages and attachments can keep byte volume high
even after many messages are excluded. This pilot did not quantify attachment
versus body sizes or extracted text volume, and did not inspect retained content
for usefulness.

Sequential prefixes are not representative random samples. Do not project these
percentages onto the full archive. The two mailboxes can contain overlapping mail;
these counts are not unique messages across sources. This pass creates decisions
and byte-range manifests, not a materialized filtered dataset or agent memory.

Next experiments can measure MIME/attachment overhead and inspect small retained
samples before choosing further rules. Additional categories are not excluded by
this experiment. Before full ingestion, add source identity validation,
deduplication and resumable processing.
