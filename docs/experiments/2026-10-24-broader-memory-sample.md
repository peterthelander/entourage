# Broader source-first memory sample

Status: Published and verified live; broader conversational reliability remains unresolved.
Date: October 24, 2026 (comparison resumed October 24 local time).

## Question and scope

Does broader historical correspondence make open-ended personal-memory
conversations more useful than the previous topic-guided pilot?

The user requested expansion after a personal-overview response mostly reflected
the curated recurring-trip examples and a handful of recent notices. This is a
bounded exploratory expansion, not a full-archive ingestion or independent
accuracy study. No model, production prompt, retrieval algorithm or service code
was changed for this experiment.

## Discovery and sampling

The existing streaming header catalog read both available mailbox exports to
EOF: 239,329 Inbox records and 18,631 Sent records, spanning 2005–2026.
These 257,960 counts include overlapping exports; they are not unique-message
counts or proof of complete Gmail/calendar/contact coverage. Originals remained
read-only. The exact Gmail label `Category Promotions` was excluded before
normalization; other categories were not globally excluded.

Within each mailbox/year, messages were ranked by SHA256 of a fixed seed and
message ID, with source/offset fallback for missing IDs. Four readable records
per stratum were selected, without topic keywords: 176 draws, 151 distinct
normalized records after cross-export deduplication. The bounded review sample
omitted attachments, raw messages over 2 MiB and bodies over 50,000 characters.
Decision logs retain skips; this convenience sample is not a representative
personal profile. Existing completed catalogs and normalized samples are reusable
stage outputs; full catalog scanning itself still lacks checkpoint orchestration.

The Sent label did not reliably establish authorship: several older records were
received replies containing quoted first-person correspondence. Review used
sender fields and attribution inside quoted threads, not the mailbox label.
Generic newsletters and third-party social activity were not treated as personal
interests or actions merely because the user received them.

## Reviewed candidate

Coding-agent review selected 36 new source records and authored 18 additional
articles. The candidate has 69 sources and 27 articles, retaining all original
33 sources and nine articles unchanged. The additional themes include work,
international moves, family correspondence, books, exercise, technical notes,
travel, housing research and activities.

Claims preserve historical dates and distinguish first-person statements,
provider notices, invitations, planned events, purchases and reported outcomes.
Quoted fiction remains fiction. Interviews do not establish employment; research
does not establish a move; invitations and purchases do not establish attendance.
Attachments were not read and cannot substantiate their claimed contents.
Credentials and incidental medical correspondence were not selected for this
exploratory batch. All 69 retained source byte ranges passed SHA256 verification
against the original mailbox files. Cross-export matches are not independent
corroboration.

Private sample scripts, evidence, candidate articles, acceptance review, integrity
checks, rollback pointer and conversation traces remain in ignored
`ingestion/data/reports/broad-memory-20261024/`. The accepted review is bound to
the exact candidate snapshot. Curation and semantic review were performed by the
same coding agent; independent human review remains pending. No automatic model
triage was substituted for publication review.

## Comparison and verification

The old-bundle baseline uses the same two-turn personal-overview fixture twice,
through the production worker and local Qwen inference in isolated stores. Both
first answers completed, but both follow-ups failed during execution. At least
one completed answer also overstated attendance evidence. These failures are
retained and do not imply that memory availability alone fixes answer quality.

The initial expanded-bundle run was interrupted before a complete trial was
written. Its partial trace is preserved separately from the resumed run. The
candidate, questions, source-backed expectations, production code and inference
settings were frozen before expanded-bundle inference. Two overview repeats and
two focused one-turn cases were attempted. These are exploratory, authored cases;
neither model agreement nor successful execution counts as independent semantic
validation. Ordinary shared-chat history is excluded from the isolated trials.

Both resumed expanded-overview first turns failed during generation after
successful retrieval; their follow-ups were not run. Report-bound review records
these failures explicitly. The trace reports an upstream model error in one
diagnostic replay; a subsequent replay completed with a tool request. This does
not establish a specific parser, tool-limit or context defect, and no runtime
fix or inference-setting change was made on that evidence.

The focused career answer recovered the requested historical role change and
correctly distinguished interview records from employment. It also added an
overconfident assertion about a separate employment-verification attachment,
whose contents were not processed. Correct main findings therefore do not
establish complete answer faithfulness. The Scarsdale answer correctly recovered
dated research and the tour request while withholding claims of a completed move,
tour or enrollment. Both focused turns completed; explicit review records one
pass and one failure for evidence qualification. Focused-case review is retained
separately from the overview comparison.

The reviewed candidate was published as `broad-history-20261024`. The previous
immutable bundle and a copy of its active pointer remain available for rollback.
A service-verification conversation through the phone's Tailscale HTTPS route
successfully retrieved the active snapshot and reported 27 articles and 69 source
records, with historical source dates spanning March 2005–October 2026. It is
excluded from shared-chat consolidation. All articles, all sources with snapshot
pagination, and five literal-search controls also passed direct reader checks.

This establishes broader available memory and live retrieval, not improved
open-ended summary accuracy. Lint, TypeScript checking and all 46 ingestion tests
passed during candidate preparation; no application or service code was changed.

## Subsequent live feedback: breadth versus significance

Observed: October 25, 2026, 02:12–02:14 UTC (October 24 local time).
Status: User-reviewed finding; synthesis/prioritization experiment agreed but not implemented.

The user repeated a natural request for the major areas of knowledge about them.
The live answer completed and covered substantially more subjects than the old
pilot. Its trace contained one `getMemoryInventory` call, exposing the 27 article
titles/descriptions and conversation-journal coverage. No article, source or
conversation-message reads were recorded in this exchange. This successful live
turn is additional evidence; it does not erase the earlier controlled failures.

The user found the answer scattered: durable life themes and incidental events
received similar prominence. The response largely followed a flat article index,
where a dinner instance and a broad career article occupy similar space. That
trace supports the diagnosis of index-level summarization; it does not establish
the model's internal importance rule or prove that it has a significance ranking.
Article existence/count and index order are not measures of personal importance.

The answer also claimed to draw on recent conversations although the sole tool
result provided journal counts/dates, not their contents. This call does not
support that attribution; the copied exchange alone cannot exclude relevant
earlier context. Other overstatements included combining interview years under
the wrong employer, treating housing research as a more recent geographic base,
and describing planned wedding arrangements as confirmed events. A general
closing caveat did not qualify those individual claims adequately.

The agreed next experiment uses the existing reviewed memory before another
volume increase. Inspect supporting articles, group episodes into broader themes,
and compare summaries that select meaningful life areas while preserving access
to details for specific questions. Candidate significance signals include explicit
user emphasis, lasting relevance, recurrence and consequences; these are
hypotheses to evaluate, not implemented scores or a fixed personal taxonomy.
A one-off event can matter greatly when the question or user makes it relevant.

Evaluate broad overviews, targeted event questions and follow-ups together. Check
theme coherence, proportional detail, attribution, historical/current distinctions
and unsupported inference, alongside successful execution and latency. Preserve
the current flat-index response as a development baseline; use separate fresh
questions and independent review for any generalization claim. No synthesis
layer, importance-ranking mechanism, new prompt rule or memory revision was
implemented following this feedback.
