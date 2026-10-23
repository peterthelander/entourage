# Remaining technical work

Reviewed: October 23, 2026. Current evaluation baseline:
[conversation suite](experiments/conversation-evaluations.md). Prioritize repeated
conversation evidence before choosing retrieval, model or prompt changes.

The supported path is browser -> Python agent service -> Mac llama.cpp (or Ollama). The retired Node
proxy and browser-owned orchestration have been removed. Model hardware and agent
state remain independently deployable.

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
  Citations, source dates and unsupported combinations still fail in live model
  evaluations despite successful retrieval. See the
  [source-identifier experiment](experiments/2026-10-21-source-identifiers.md).
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

## Reviewed memory and evaluation gaps

- The live 33-source/nine-article pilot is hand-curated. Private topic selectors,
  user hints and reviewed observations supplied discovery and membership decisions;
  reliable automatic extraction, synthesis and incremental publication are not
  established. Larger-corpus indexing, resumable ingestion, attachment processing
  and real bank/card adapters remain unimplemented.
- The running code is generic, but the recurring-event cases informed development
  and cannot serve as untouched validation. Freeze code/settings and use fresh
  real topics with independently prepared expected findings; evaluate ingestion
  stages separately from retrieval/answering. See the
  [memory evaluation protocol](experiments/conversation-evaluations.md#memory-experiments-and-holdout-separation).
- Local answers still mix source/activity years, confuse car and ski-equipment
  rentals, and turn dated reservations into current-status claims. Better article
  structure and retrieval help some cases but have not established reliable
  multi-turn source binding. Preserve failed traces and use controlled comparisons
  before choosing further model, context or retrieval changes.
- The four executed-call budget now has an answer-only finalization pass. A hosted
  reference still requested tools after finalization disabled them and failed;
  this recovery path does not guarantee completion. Execution success and semantic
  correctness must remain separate findings. See the
  [recurring-event record](experiments/2026-10-23-recurring-event-reconstruction.md).

Run the checks documented in README.md. Python tests exercise temporary databases
and simulated inference; scripts/check-agent.py checks real authenticated inference.
