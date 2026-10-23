# Reviewed imported memory integration

Status: Small live pilot implemented; broader semantic evaluation and ingestion remain experimental.
Updated: October 23, 2026.

## Question and scope

Can the production agent use reviewed imported records for recall and planning,
preserve historical qualifications on follow-up, and acknowledge missing evidence?
The implementation is generic. Topic-specific searches and curated mail selection
are experiment inputs, not rules embedded in retrieval or publication.

The private pilot contains five reviewed source records and five articles across
event planning, transaction notices, school and account notifications. Original
MBOX byte-range hashes were verified for these selections. A coding agent reviewed
the claims, descriptions, source excerpts and unknowns; independent human review
is pending. This is a deliberately small convenience sample, not representative
coverage or a full-archive ingestion run.

## Implementation and findings

Python owns shared source/article validation, deterministic Markdown projections,
bounded retrieval and explicit publication. Ingestion CLIs call that shared owner.
An accepted review must match the exact candidate snapshot; model support triage
alone cannot publish. Immutable bundles retain authoritative JSON, with an atomic
active pointer. Generated imported journals stay separate from chat journals.

Early conversation trials frequently searched only chat history or missed exact
phrases. Unified `searchMemories` and inventory now expose chat and imported results
separately. Explicitly labeled partial word-overlap leads improve discovery when
literal phrases miss. Article/source reads remain bound to the returned snapshot.

Follow-ups sometimes lost source qualifications after the initial answer. Bounded
reuse of recent complete source-reader tool pairs gives the next turn the original
evidence, subject to session/context limits and active-snapshot checks. The four
executed-tool-call budget is preserved; an answer-only pass can summarize existing
evidence if another requested batch would exceed it. No automatic hosted fallback
or background article rewriting was introduced.

## Conversation checks

The evaluation runner uses production transports, worker and tools with isolated
temporary stores. Device and web results are controlled fixtures. Four fictional
cases cover a corrected event date, a repair receipt, a reading invitation and
missing booking information; three private cases cover planning and historical
transaction/current-state questions. Each case ran twice per provider.

| Final comparison | Local completed case runs | Hosted reference completed case runs |
| --- | --- | --- |
| Fictional reviewed bundle | 8/8 (14 turns) | 6/8 (12 turns attempted) |
| Private reviewed bundle | 6/6 (12 turns) | 6/6 (12 turns) |

The two hosted fictional failures were inference timeouts before a response.
These are execution completion counts, not semantic pass rates. The local model
recovered historical details and usually preserved unknown attendance, payment,
delivery and lodging, but still sometimes added unsupported general advice or
wording suggesting current state. The hosted reference was useful diagnostically
but did not establish correctness. Reports retain pending semantic-review labels;
there is no blinded or independently scored quality benchmark here. Repeats use
small authored fixtures; overlapping runs are unsuitable for latency comparisons.

Private reports live in ignored `ingestion/data/reports/` under
`knowledge-conversations-final-synthetic-20261022/` and
`knowledge-conversations-final-personal-20261022/`. The names reflect the start
date; runs completed October 23 UTC. Hosted personal trials sent the selected
source evidence to that provider. The deployed inference selection remains local.

## Live verification and boundaries

The reviewed pilot was activated beside the live database and enabled through
the machine's ignored inference configuration. Consistent SQLite and configuration
backups were saved first. A live inventory check confirmed five articles/five
sources. A two-turn planning check recovered dated historical dinner details and
correctly declined to infer attendance, payment or lodging. Verification turns
use the service-verification conversation excluded from shared-chat consolidation.

Private reports are `live-knowledge-smoke-20261022.json` and
`live-knowledge-conversation-20261022.json`. Service publication, flag settings and
rollback are documented in [service operations](../../server/EXECUTION.md#reviewed-imported-memory).

The final tidy-up also enforces LF bytes for snapshot-bound fictional fixtures,
tests their review after checkout, and treats malformed active pointers as
unavailable. Remaining work includes broader semantic scoring, reviewed coverage,
resumable archive processing, deduplication beyond exact raw messages, incremental
article updates and organic splitting. Automatic synthesis/publication remains
unimplemented.
