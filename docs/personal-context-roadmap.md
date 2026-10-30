# Personal context and memory roadmap

Status: Deferred proposals; current behavior is described in the linked references.
Updated: October 30, 2026.

## Intended experience

One continuous conversation should provide useful recall across devices and pauses.
The agent should connect relevant history to the current decision, preserve detail,
and distinguish past plans, reported outcomes and present requirements. Memory
organization should stay behind the conversation.

A guiding use case is planning a recurring trip from prior years' correspondence:
recover organizers, bookings, transport and lessons where supported, then help plan
the next trip using current evidence for new requirements. The existing curated
trip examples are development cases, not proof of automatic reconstruction.

## Existing foundation

Python owns durable conversations and execution. SQLite is authoritative for
conversation history; refreshed Markdown journals provide a readable projection.
Reviewed imported records and article plans are authoritative JSON in immutable
bundles; rendered Markdown is an inspection view.

Recent conversation context is selected within a bounded inactivity window.
Older conversation and imported evidence is accessible through memory tools.
See [journal behavior](reference/memory-journals.md),
[ingestion boundaries](memory-ingestion.md) and [service operations](../server/EXECUTION.md).

## Possible extensions

- Incremental article updates that preserve source evidence and corrections.
- Background consolidation into useful concepts and recurring-event instances,
  allowing structure to emerge from content rather than imposing a fixed taxonomy.
- Better discovery and bounded retrieval as the reviewed corpus grows.
- Broad synthesis that selects what matters to the question while retaining detail.
- Additional source formats and attachments after small reviewed format trials.

These are hypotheses, not a committed architecture or scheduled sequence. There
is no selected importance score, automatic splitting threshold, background
consolidation process or automatic publication gate. Local inference is attractive
for cost and control; hosted inference remains an option, with no automatic routing.

## Boundary for resuming work

Start from a concrete everyday-use failure and the [current priorities](ongoing-work-streams.md).
Separate evidence discovery, extraction, article synthesis and conversational
answering; improved retrieval alone does not establish faithful answers.

Use the [acceptance criteria](personal-memory-development.md) and independently
prepared expectations on untouched real topics before claiming generalization.
Preserve source roles, chronology, uncertainty and correction provenance through
follow-ups. Keep candidate generation, advisory review and explicit publication
separate. Further ingestion volume and model comparisons remain deferred.
