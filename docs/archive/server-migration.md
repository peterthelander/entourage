# Server-owned agent migration

Status: Archived migration design and delivery record. Archived: October 21, 2026; original record is undated.

Historical migration design and delivery record. Some proposed features below
have since shipped. For current ownership, setup and limitations, see
[README](../../README.md), [service operations](../../server/EXECUTION.md) and
[technical debt](../technical-debt.md).

Decision: Python for the agent server; TypeScript/Expo for browser and future
native clients. Ollama remains a separate inference service, local or remote.
Use FastAPI for HTTP and generated OpenAPI. Start with SQLite for durable state,
one server process and one worker; no message broker is needed initially.

## Current and target ownership

The earlier browser-built prompts, browser-owned history/tool loop and Node proxy
have been replaced. Ollama performs inference. Browser polling exposes incremental
output roughly once per second.

Python owns conversations, context assembly, complete agent turns, general tools
and durable execution records. Memory retrieval and MCP clients are future additions.
The device owns its UI, permissions, capabilities, and an optional cache.
Ollama owns model weights and inference caches, not authoritative agent memory.

## v1 HTTP contract

Persistence routes, agent execution, and authenticated device results are implemented.
The Python-backed browser is now the default; the old Node proxy is stopped.
See [execution setup](../../server/EXECUTION.md) for authentication, limits,
additional endpoints and current recovery behavior.

All IDs are UUIDs. Clients choose IDs for creation requests so retries can reuse
them. Times are UTC ISO 8601. Request/response schemas will be published through
OpenAPI with each implemented endpoint; generate TypeScript types from that schema
instead of maintaining a second handwritten contract. The retired `/api/jobs`
transport has been removed; use the turn endpoints below.

| Request | Meaning |
| --- | --- |
| `PUT /api/v1/chat` | Resolve the single shared chat used by every client |
| `PUT /api/v1/chat/imports/{import_id}` | Append previewed legacy history to the shared chat idempotently |
| `PUT /api/v1/conversations/{id}` | Create a conversation idempotently |
| `GET /api/v1/conversations?after={sequence}` | List conversations, cursor-paginated by creation order |
| `GET /api/v1/conversations/{id}/messages?after={sequence}` | Read ordered committed messages, cursor-paginated |
| `PUT /api/v1/conversations/{id}/turns/{turn_id}` | Submit `{text, device_id}`; server chooses model/context/tools |
| `GET /api/v1/turns/{turn_id}` | Durable snapshot: status, revision, partial/final answer, error; tool/device progress will be added with execution |
| `POST /api/v1/import-preview` | Preview legacy message classification, without writing |
| `PUT /api/v1/conversations/{id}/imports/{import_id}` | Explicitly import legacy messages into an empty conversation |
| `PUT /api/v1/turns/{turn_id}/device-results/{request_id}` | Submit an authorized device tool result or explicit denial/unavailability |

An identical creation retry returns the existing resource; conflicting content for
the same ID returns 409. New turn acceptance returns 202 only after durable storage.
One active turn per conversation initially; another new turn returns 409. Unknown
IDs return 404. Errors use `{error: {code, message}}`; execution failure appears in
the turn snapshot, not as an assistant answer. Requests have bounded sizes and
pagination has a limit of 1–100 and an exclusive `after` sequence cursor.
Uploads are capped at 1 MiB. New turns run only when the Python worker is explicitly
enabled; persistence-only mode still queues them. The one-active-turn rule includes
`needs_review`. The worker currently serializes turns across conversations.

Turn states: `queued`, `running`, `waiting_for_device`, `completed`, `failed`,
`needs_review`. Snapshots have a monotonic revision. Start with polling; connection
loss must not cancel work. An event stream can be added later without changing turn
ownership. Partial output is marked provisional and must not enter future model
history as a completed answer.

## Device boundary

The server records a device request with a unique request ID, target device ID,
allowlisted capability, validated arguments, and expiry. Only the bound device
session may return its result. Device identity is not authentication by itself.
Transport authentication and conversation/device authorization must be implemented
before remote clients switch over; Tailscale connectivity alone does not establish
application ownership.

Location, device clock/timezone, device metadata, and future Health access remain
device operations. Do not accidentally replace the user's clock/location with the
server's. The calculator can move to the server. An unavailable device leaves the
turn waiting until expiry, then records a tool failure the agent can explain.
The client handles permission prompts; the server cannot force a background phone
to respond. Tool names, arguments and output sizes are checked on both boundaries.
Device results are idempotent; conflicting repeated results return 409.

## Durable execution and recovery

Store ordered typed messages (`user`, `assistant`, `tool` with explicit kind),
turns, checkpoints, and tool execution records in SQLite. Keep the database and
memory files with the agent service, outside Git. Server restart must retain history
and classify unfinished work. Do not claim a database alone makes side effects
exactly-once: a tool can act and the process can crash before recording its result.
Ambiguous side-effecting tool calls become `needs_review`, unless the downstream
tool supports a verified idempotency key. Never silently replay them.

Browser history import will be explicit, previewed, and deduplicated with an import
ID. Preserve original localStorage until successful import is confirmed. Existing
UI tool/error ID prefixes need conversion into explicit message kinds; imported
tool output must not become an authoritative assistant statement. No automatic
merge of independent phone and desktop histories.

## Delivery stages and acceptance

1. **Foundation (complete):** runnable Python service, startup configuration,
   health endpoint, tests, and this design contract. Existing UI/proxy untouched.
2. **Persistence (complete):** SQLite schema version 2, conversation APIs and tests
   that reopen a real temporary database; explicit history import with duplicate
   protection. Turns and user messages commit atomically; concurrent submissions
   cannot create two active turns. Guided browser import now previews and explicitly
   commits saved history while keeping the original browser storage.
3. **Agent execution (complete):** Python context/tool loop, bounded Ollama
   streaming, calculator, credential-bound device bridge, and separate server-backed
   browser client. Limits are preserved. Generated OpenAPI DTOs define the client
   boundary. This is now the default browser path.
4. **Recovery (baseline complete):** disconnect/reconnect, restart review state,
   device timeout, explicit cancellation/dismissal and manual retry. Cancellation
   cannot be overwritten by late worker completion. Interrupted work is not replayed.
   Advanced checkpoint recovery and side-effecting tools remain future work.
5. **Cutover (HP service switched):** existing private web link uses Python; old
   proxy is stopped and `/llm` removed. Browser history remains available for explicit
   import on each originating device. Physical-phone testing remains outstanding.

Keep model/hardware changes independent. Python communicates directly with the
configured Ollama origin; it does not depend on the Node job proxy. Python uses
8000; the old proxy on 11435 is no longer running. Keep device execution on clients.
Add MCP and richer memory after this baseline.
