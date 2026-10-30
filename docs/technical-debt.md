# Remaining technical work

Status: Engineering backlog; items are not scheduled commitments.
Reviewed: October 30, 2026.

Follow [current priorities](ongoing-work-streams.md) when selecting work. Operational
behavior belongs in [service operations](../server/EXECUTION.md); dated results
belong in the [experiment index](experiments/README.md).

## Execution and client limits

- Browser/device tool execution currently assumes one active tab per device. Only
  read-only device capabilities, calculator, journal/reviewed-import retrieval,
  public-page reading and optionally Google-backed web search are exposed;
  no side-effecting tools exist.
- Web experiments still show unsupported answer details and overclaimed coverage.
  Use the conversation suite to isolate answering behavior; its fixed web evidence
  does not measure actual public-search coverage or website accessibility.
- Journals refresh automatically with execution enabled, with retry/restart catchup.
  Large-history export efficiency and timezone-change migration remain future work. Literal keyword search
  returns five messages per page, defaults to user evidence, and supports oldest/newest
  ordering and direct source-message reads; semantic recall and automatic correction
  resolution remain future work. Conversation results expose numeric source IDs;
  imported records use string IDs and snapshot-bound reads.
- Inventory and date reading support coverage questions and topic summaries.
  Long ranges need pagination; the four-call budget limits a single-turn overview.
  Persisted summaries and a larger-corpus index remain future work.
- One worker serializes turns, including device waits. Consider concurrency only
  with explicit resource limits and per-conversation ordering.
- Interrupted running/waiting work becomes needs_review. Users can dismiss it and
  explicitly retry; safe checkpoint continuation and side-effecting tools need a
  stronger execution/idempotency contract before implementation.
- The client currently fetches full paginated history while polling. Incremental
  message loading and bounded rendering will matter for long-lived conversations.
- Authentication is single-owner via direct localhost or the owner's Tailscale Serve
  identity. Diagnostic-token rotation remains future work; device IDs are not authentication.
- Display/export uses explicit message kinds. Legacy ID decoding is confined to
  saved-chat conversion and import; preserve those boundaries during future work.
- Browser submission/poll coordination remains in one hook; import and device
  handling have separate helpers. Further lifecycle changes need reconnect and
  ambiguous-submission coverage, not just file splitting.
- Shared-chat compatibility projection still runs during resolution/reads and
  refresh. Keep its timing until later writes through old APIs are accounted for.
- Stored tool-loop checkpoints support inspection, not automatic replay or a
  complete inference-input log. Changing that contract requires a separate decision.
- Native inference is deferred. Native runtime failures sometimes return explanatory
  text; align these with the server error contract when native work resumes.
- The existing one-screen entry point is App.tsx. Introduce Expo Router as required
  when navigation is added; keep shared components outside route directories.

## Memory and evaluation gaps

- Answers can confuse source identity, record dates, activity dates and correction
  order even with complete evidence. Plans and reservations can become unsupported
  completion or current-status claims. Evaluate whole conversations and nearby
  positive cases before adopting retrieval or prompt changes.
- Broad summaries have no demonstrated significance-selection mechanism. Index
  entries are discovery leads, not inspected evidence. Automatic synthesis,
  importance ranking and consolidation remain deferred proposals.
- The reviewed import pilot is manually curated. Reliable automatic extraction,
  synthesis and incremental publication are unproven. Resumable ingestion,
  larger-corpus indexing, attachments and additional source adapters are absent.
  See [ingestion boundaries](memory-ingestion.md).
- Existing memory cases informed development. Untouched real topics with
  independently prepared expectations are needed before claiming generalization.
  Mechanical scoring and unblinded coding-agent review are incomplete measures;
  see the [evaluation protocol](experiments/conversation-evaluations.md#memory-experiments-and-holdout-separation).
- Initial history selection uses an approximate character budget. llama.cpp has
  actual-token preflight and bounded answer-only recovery, but oversized evidence
  and provider behavior can still prevent completion. The four-call tool budget
  can constrain useful retrieval; disabling tools for finalization does not
  guarantee that every provider will finish successfully.

Run the checks in the [project README](../README.md). Python regressions use
simulated inference and temporary stores; client tests cover refresh, rendering
and retry behavior. Automated pixel comparison is absent. `scripts/check-agent.py`
checks real authenticated inference separately from these regressions.
