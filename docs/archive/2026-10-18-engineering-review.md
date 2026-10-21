# Development and engineering review — October 18, 2026

Status: Archived review and subsequent cleanup record. Review: October 18, 2026.

The findings below describe the reviewed baseline. The subsequent cleanup is
recorded at the end; use that section to distinguish completed work from remaining
decisions.

Review against [design principles](../design-principles.md), with existing behavior
as the baseline. This is a review snapshot, not a second ongoing backlog; existing
work remains tracked in [technical debt](../technical-debt.md).

## Assessment

The primary ownership split is sound: Python owns durable browser conversations,
context assembly and agent execution; the browser owns presentation and device
capabilities; inference adapters handle provider transport. Generated TypeScript
API types already give the browser/service boundary a shared contract. The service
has meaningful tests for persistence, cancellation, restart recovery, journals,
access control and context selection.

The code does not need a general rewrite. The main opportunities are to contain
compatibility mechanisms, separate browser responsibilities, and make development
evidence and documentation easier to trust. Deferred native inference is an
intentional separate runtime, not an obsolete duplicate to delete.

## Findings and recommended scope

### 1. Current documentation contradicts the implemented architecture

Evidence:

- `docs/inference-limits.md` describes 12-message / 6000-character history as the
  current service behavior; Python uses up to 128 messages, a configurable budget,
  and session selection.
- `server/README.md` says memory retrieval is future work and that no inference
  requests are made "in this stage", although the normal launcher enables both.
- `README.md` describes the larger context window without the new session rule;
  `server/EXECUTION.md` describes the session rule.
- `handoff.md` says remote Mac inference remains untested; subsequent experiments
  in this session used it. The handoff is dated, but is not marked as superseded.

Why it matters: investigations can start from the wrong architectural assumptions,
as happened when the old 12-message policy was mistaken for the active path.

Recommendation: make README the entry point, EXECUTION the current operational
reference, and label dated migration/verification/handoff material as historical
where appropriate. Link to current settings rather than repeating values across
several documents. This can be done without changing runtime behavior.

### 2. Explicit server message kinds are converted back into legacy ID conventions

Evidence: `src/hooks/useServerChat.ts` maps server tools/errors to assistant-role
messages with `toolresult-` / `error-` IDs. `ChatMessages.tsx` and
`exchangeExport.ts` then infer message kinds from those prefixes. Tool identity
and output are also encoded into a newline-delimited text field.

Why it matters: a reliable server contract becomes an implicit presentation
protocol. Rendering, copying exchanges and import compatibility must all remember
the same conventions. Adding another message producer can silently bypass them.

Recommendation: use an explicit presentation message kind and one conversion
function at each legacy boundary. First preserve text, order, labels, timestamps,
tool counts and copy output exactly. Keep old-storage import interpretation at the
import boundary. A database migration or native feature parity is not required.

### 3. The browser hook owns too many independent lifecycles

Evidence: `src/hooks/useServerChat.ts` handles connection setup, polling, the
durable pending submission, device credentials/results, history import, message
conversion, draft recovery and presentation state. Its guards are serving real
purposes; the pending-send race has a regression test in
`tests/server-client.test.cjs`.

Why it matters: changes to one responsibility can disturb another through shared
refs and polling. Merely shortening this file would not resolve that coupling.

Recommendation: extract message conversion and legacy import first, then device
request handling. Keep one owner for submission/poll coordination. Before moving
that coordination, cover reconnect/unmount during requests, ambiguous submission
retries, permanent rejection and repeated device-result delivery. Preserve stable
IDs, existing storage keys, retry semantics and cancellation behavior. Avoid a
general event framework or multiple competing pollers.

### 4. Compatibility migration runs as part of ordinary reads and refreshes

Evidence: `Store.single_chat()` combines resolving the shared chat with copying
messages from older conversations. `list_messages()` calls it for each shared-chat
page, and `JournalRefresh.refresh()` calls it about every two seconds. The copy
query scans eligible source messages and relies on `INSERT OR IGNORE` for repeated
execution. API routes also query turn state directly alongside store methods.

Why it matters: read paths perform migration writes; migration cost and policy
remain coupled to polling, journal refresh and history size. Persistence ownership
is less clear when API routes contain their own state queries.

Recommendation: first give shared-chat migration and turn lookups named store
operations while retaining call order and transactional behavior. Deciding when
migration should run is a separate change: the old conversation APIs still exist,
so moving it to startup alone could stop later messages from appearing in shared
history. Test that compatibility contract before altering its lifecycle. Treat
incremental polling as a separately measured optimization, not incidental cleanup.

### 5. Stored checkpoints have no recovery consumer

Evidence: `ExecutionStore.checkpoint()` and `tool_result()` serialize the growing
model conversation into SQLite around tool calls. Repository code does not read
those saved messages to resume execution. Recovery deliberately marks interrupted
turns `needs_review`, and `get_turn()` removes checkpoints from the API response.
Ordinary turns with no tool call do not save their model input this way.

Why it matters: checkpoint writes add work and retained state, but do not provide
the recovery capability their name might suggest or a consistent diagnostic input
record. This does not make the current no-replay recovery policy wrong.

Recommendation: decide whether checkpoints are intended for diagnostics or future
recovery. Document that purpose and consolidate serialization if retained. Do not
remove storage or add replay as a mechanical refactor; either changes a durability
or diagnostic contract. Preserve the current explicit-retry policy.

### 6. Useful context experiments live only in ignored runtime scratch space

Evidence: the context comparison runner and detailed results from this session
are in `.expo/`, which Git ignores. The runner contains a specific local message
number and reads machine-local inference configuration.

Why it matters: current findings are useful, but another checkout cannot repeat
the comparison without reconstructing the local setup and source conversation.

Recommendation: retain a small reusable runner and synthetic conversation fixtures
in maintained development tooling. Keep actual personal history and raw private
outputs in ignored data. Separate deterministic selection assertions from optional
live model comparisons; record model/settings, conditions and limitations with
each comparison. Avoid introducing a large evaluation framework at this stage.

## Suggested order

1. Correct current documentation and label historical material.
2. Make presentation message conversion explicit with unchanged output.
3. Extract browser import/device responsibilities behind their existing contracts.
4. Clarify migration and checkpoint ownership before changing their lifecycles.
5. Make the small context experiment reproducible with synthetic fixtures.

Keep context policy, system prompts, tools, authentication, API compatibility,
native inference and visible interaction behavior unchanged during this cleanup.
There is no demonstrated need to merge the two inference runtimes, add navigation,
or introduce a new orchestration framework.

## Verification and limits

- 65 Python tests passed, using temporary databases and simulated inference.
- 23 JavaScript tests passed, covering native/shared helpers, the browser API
  client and the pending-send polling regression.
- Expo lint and TypeScript checking passed.
- No application code, live data, running service or inference configuration was
  changed during this review. Only this report was added.
- This was a source-and-test review. It did not benchmark long histories or rerun
  physical-phone permissions and live model behavior.

## Subsequent cleanup

- Corrected current documentation and marked migration/handoff/verification
  snapshots as historical.
- Added explicit presentation message kinds and boundary conversion. Existing
  IDs, visible text, ordering and latest-exchange export format are preserved.
- Extracted browser history import and device-result handling. Storage keys,
  credentials, acknowledgement reuse, pending-send coordination and retries keep
  their existing contracts.
- Moved turn lookup SQL into the store and named the compatibility projection.
  Resolution timing and transactions are unchanged; later legacy writes are
  covered by a regression test.
- Consolidated checkpoint serialization and documented its inspection-only role.
  Storage, visibility, retention and restart behavior are unchanged.
- Added `scripts/compare-context.py`, a synthetic fixture and experiment guidance.
  Preparation is offline by default; optional inference uses the production
  llama.cpp adapter without executing tools or writing chat history.

Further migration scheduling, incremental polling and checkpoint policy decisions
remain in TECHNICAL_DEBT.md. This cleanup does not change context selection,
prompts, tool capabilities, authentication or the deferred native inference path.

Cleanup verification: 67 Python tests, 29 JavaScript tests, Expo lint, TypeScript
checking, offline experiment preparation, and the production web export passed.
The live service and personal data were not changed; physical-phone checks and
new live model comparisons were not part of this structural cleanup.
