# Remaining technical work

Reviewed: October 25, 2026. Current evaluation baseline:
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

- The [October 24 browser diagnosis](experiments/2026-10-24-browser-inference-recovery.md)
  reproduced Qwen finalization failure from a late system message and a separate
  real context overflow. Finalization now uses the initial system message; large
  llama.cpp transcripts have actual-token preflight and bounded answer-only
  recovery. Configured versus loaded model status and safe error causes are
  visible in the UI, with refresh/render regressions. Approximate initial history
  selection and oversized evidence remain limits; successful execution does not
  establish semantic answer correctness.
- The [Qwen follow-up](experiments/2026-10-24-qwen-transfer-and-conversations.md)
  improves source-binding controls (15/16 passing) and the broader first-pass
  rubric score (25/30 versus historical gpt-oss 21/30), with materially slower
  observed responses. It still misses unresolved venue alternatives and required
  source links, omits part of a requested plan recap, and leaks a literal thinking
  marker with duplicated text in one answer. The original failed experiment
  remains preserved; the later live reproduction established and repaired a
  strict-template finalization defect. Known context/output limits, template
  failures, connection errors, timeouts and interrupted streams now have separate
  safe messages, including measured context counts when available. The
  [thinking-disabled comparison](experiments/2026-10-24-qwen-thinking-control.md)
  reduced latency but scored 24/30 with more presentation leaks; thinking remains
  low. Repeated evaluation and independent review remain work. The live deployment
  now uses Qwen, without claiming that one pass establishes general reliability.
- The [evidence-versus-answering comparison](experiments/2026-10-23-memory-faithfulness.md)
  still finds local chronology, estimate/settlement and object-identity errors
  with complete source evidence. Reconciliation-prompt and bounded-source-context
  trials did not justify production adoption; the broader context comparison was
  13 passing/8 failing/3 unclear turns versus 14/8/2 in its matched control.
  Empty model replies now fail execution explicitly instead of becoming completed
  placeholder answers. Semantic answer failures remain distinct.
- The live 69-source/27-article pilot is hand-curated. The original 33-source/
  nine-article bundle used private topic selectors, user hints and reviewed
  observations; the October 24 expansion used seeded mailbox/year sampling.
  Coding-agent review still supplied article synthesis and acceptance;
  reliable automatic extraction, synthesis and incremental publication are not
  established. Larger-corpus indexing, resumable ingestion, attachment processing
  and real bank/card adapters remain unimplemented.
- Broad memory summaries currently have no demonstrated significance-selection
  mechanism. A subsequent live answer summarized the flat article inventory,
  mixing durable life themes with incidental episodes, claiming conversation
  grounding without recorded message reads and overstating dated evidence.
  The agreed next experiment is evidence-backed synthesis and question-appropriate
  prioritization over existing memory, preserving targeted detail retrieval.
  No importance score, synthesis layer or automatic consolidation has been
  implemented. See the [expansion and live-feedback record](experiments/2026-10-24-broader-memory-sample.md#subsequent-live-feedback-breadth-versus-significance).
  An [offline overview experiment](experiments/2026-10-24-memory-overview.md) now
  compares inventory-only, full selected evidence and editorial thematic grouping.
  Its first full-evidence attempt exceeded the actual model context; normalized
  packets and a smaller selection preserve complete selected articles. This is
  experimental infrastructure, not production retrieval or automatic significance.
  The completed comparison retained source-binding errors with inspected evidence
  and 180-second follow-up timeouts. The thematic candidate was not adopted;
  fictional unnamed-participant and unread-attachment controls now preserve these
  failures as development material.
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
- The [fresh-topic study](experiments/2026-10-23-fresh-memory-validation.md)
  additionally shows correct tables followed by reversed chronology, unsupported
  timezone conversions and overstated archive coverage. Expanded source excerpts
  improve payment qualifications on a small local comparison, but do not fix
  chronology. Article generation can omit source exceptions despite valid literal
  citations; automatic acceptance remains unjustified. Fictional source-binding
  regression inputs and explicit freeze/review tooling now exist.
- The four executed-call budget now has an answer-only finalization pass. A hosted
  reference still requested tools after finalization disabled them and failed;
  this recovery path does not guarantee completion. Execution success and semantic
  correctness must remain separate findings. See the
  [recurring-event record](experiments/2026-10-23-recurring-event-reconstruction.md).

Run the checks documented in README.md. Python tests exercise temporary databases
and simulated inference; hook and rendered-component tests cover refresh, model
identity, errors and retry controls. Automated pixel screenshot comparison is
not implemented. scripts/check-agent.py checks real authenticated inference.
