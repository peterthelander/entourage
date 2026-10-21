# Server-owned agent execution

Memory searches default to original user messages. `searchMemories` supports
`speaker` (`user`, `assistant`, `all`), `order` (`oldest`, `newest`), and pagination
using `next_offset` with `snapshot`. Assistant recollections are secondary leads;
verify their citations using `readMemories` with a numeric `message_id` instead of
dates. Returned source timestamps establish when a message was recorded. Imported
completion uncertainty remains visible; user statements are evidence of what was
said, not independent verification of their contents.

**Current setup:** the Python-backed browser is the default. Start from the repository root:
`server/.venv/Scripts/python.exe scripts/start-agent.py`
(use `server/.venv/bin/python` on macOS/Linux). For private phone access, pass
`--origin https://<your-tailscale-host>` and route `/` to Expo on 8081 and `/agent`
to Python on loopback:8000 through Tailscale Serve.

The launcher enables execution, stores a persistent diagnostic credential in
ignored `server/data/access-token.txt`, and never prints it. Browser access is
automatic through localhost or the owner's Serve identity. It uses localhost:8000
locally and the current origin plus `/agent` remotely, without a token in the URL
or browser bundle.

Machine-local inference selection lives in ignored `server/data/inference.json`,
loaded by the launcher at startup; explicit environment variables take precedence.
Record host addresses and restart details in ignored `docs/local/machine-runbook.md`.
Native inference remains deferred. The environment-based setup below is an
alternative for other machines or ports.

The Python service now builds context, calls the selected inference server, executes the calculator, requests
device tools, and commits answers independently of browser connectivity. The retired
Node proxy and browser agent have been removed.

## Start Python

For llama.cpp, set `ENTOURAGE_INFERENCE_PROVIDER=llama_cpp`,
`ENTOURAGE_LLAMA_CPP_UPSTREAM=http://<mac-ip>:8080` and `ENTOURAGE_MODEL` to an ID
returned by `/v1/models`. The adapter handles streamed Chat Completions and tool
calls. Reasoning content is excluded from displayed answers. The service considers
up to 128 recent messages from the current session, within an approximate text
budget reserving room for tools and output.
A gap longer than 60 minutes between user messages starts fresh active context;
set `ENTOURAGE_CONTEXT_SESSION_GAP_MINUTES` (1–1440) to adjust it. The comparison
uses the latest message's saved creation time, so queue delays do not reset context.
Midnight alone does not split a session. Timestamp metadata is used only for
selection and is not added to model conversation text. Historical messages are
preserved, and the existing memory tools can retrieve discussions from prior
sessions when the user refers back to them. For longer
context, restart the llama.cpp engine with a larger `-c` value before raising the service setting.
Ollama remains available by selecting provider `ollama` and its existing upstream.

The normal launcher discovers its own Tailscale login and DNS name using the local
Tailscale daemon. It permits that login through Tailscale Serve, and direct localhost
access for the local browser. Python stays bound to loopback. It accepts Serve identity
headers only from the actual loopback socket peer and an expected Host; forwarded
headers do not grant direct-local access. Uvicorn proxy-header rewriting is disabled
so the socket peer remains verifiable. Other Tailscale users do not inherit access.
Exact origin checks and separate device-result credentials remain in place.

Install requirements using [server setup](README.md). For a low-level diagnostic
deployment using uvicorn directly instead of the normal launcher, generate a private token
in your own terminal: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
Keep it out of Git, URLs, screenshots, and public Expo environment variables.
In the terminal starting Python, from the repository root:

```powershell
$env:ENTOURAGE_EXECUTION_ENABLED = '1'
$env:ENTOURAGE_API_TOKEN = '<your private token>'
$env:ENTOURAGE_ALLOWED_ORIGINS = 'http://localhost:8082,http://127.0.0.1:8082'
$env:ENTOURAGE_OLLAMA_UPSTREAM = 'http://127.0.0.1:11434'
.\server\.venv\Scripts\python.exe -m uvicorn entourage_server.app:create_app --factory --app-dir server --host 127.0.0.1 --port 8000
```

On macOS/Linux use shell exports and `server/.venv/bin/python`. Ollama may be local
or on the Mac through private Tailscale HTTPS. The upstream must be an HTTP(S) origin
without a path. The configured model defaults to `qwen3.5:4b`; change it server-side
with `ENTOURAGE_MODEL`. The browser's legacy model settings do not apply here.

## Start the browser (custom endpoint example)

In a separate terminal:

```powershell
$env:EXPO_PUBLIC_AGENT_SERVER_URL = 'http://127.0.0.1:8000'
node node_modules/expo/bin/cli start --port 8082
```

Open `http://localhost:8082`; browser access uses the launcher identity checks.
The browser does not send or save an owner bearer token. Device credentials,
pending submissions, and device-result acknowledgements use a separate localStorage
namespace. Saved browser history can be previewed and explicitly imported into the
shared chat; the original copy is never overwritten. Stable import
IDs protect retries, including lost acknowledgements. Old pending requests can be
copied into a draft for an explicit new submission; they never run automatically. Server history is
authoritative. Every client automatically opens the same continuous chat. Earlier
server chats are copied into it without deleting the originals; service-verification
chats are excluded.

For a phone, use a private Tailscale HTTPS URL for Python, and put the exact HTTPS
origin serving the web app into `ENTOURAGE_ALLOWED_ORIGINS`. A phone cannot reach server
services using `127.0.0.1`. Keep Python on loopback behind Tailscale Serve. This is a
single-owner service: the accepted owner identity grants access to all conversations, not multi-user
isolation. Browser storage must be available. Use one active tab per device while
testing device requests; the three current device tools are read-only.

## Tools and limits

Web search uses Gemini with Google Search grounding. To configure your existing
Google AI Studio API key privately, run this from the repository root:

```powershell
.\server\.venv\Scripts\python.exe scripts/configure-gemini.py
```

The prompt hides your key and saves it in ignored `server/data/gemini-api-key.txt`.
This makes no API request and does not enable billing. Restart the Python service
using the normal launcher afterward. Alternatively set `ENTOURAGE_GEMINI_API_KEY`
or `GEMINI_API_KEY` in the service environment; these take precedence over the file.
Never put the key in an `EXPO_PUBLIC_*` variable or commit it. `.env` files are not
loaded automatically. No additional package is needed.

Research defaults to `gemini-2.5-flash-lite`; override with
`ENTOURAGE_WEB_SEARCH_MODEL` if needed for your project's model access.
The API project's quotas and billing tier determine actual cost and availability;
see [Google's pricing](https://ai.google.dev/gemini-api/docs/pricing). The server
does not enable billing or switch models/providers on failure.

Configured servers offer `searchWeb` to llama.cpp and Ollama. The agent can look up
a named outing without an explicit search request when useful, using the town
from context or asking when the place is ambiguous. Only the focused query goes to
Google, not the full conversation or memory history. Gemini's bounded research
summary, source links, and claim/source associations return through the normal
persisted tool loop. These findings do not guarantee today's hours or availability.
Unsearched answers, blocked/truncated generation, missing sources, and provider
failures are reported without raw provider errors or credentials. No automatic
retries are made. The browser shows expandable findings/source links and Google's
search suggestions in a sandboxed frame. Suggestion HTML is saved for display and
excluded from subsequent model context. Native search UI remains deferred.
Without a key the model is not offered web search. Enabling it still requires a
live provider check and repeated conversations on the selected model to evaluate
when it chooses to search; scripted execution tests do not establish that behavior.

`readWebPage` is available to both inference providers even without a search key.
It opens public HTTP(S) pages and returns extracted static text, the final source
URL, fetch time, and links to follow. Use `offset` / `next_offset` for another
8,000-character excerpt, or `find` for a literal phrase with surrounding text.
The output states when text or links were truncated; no match is not proof an
event does not exist. The full extraction is capped at 100,000 characters.

Reads use a separate credential-free HTTP client, a 25-second total deadline,
at most three redirects and a 1 MiB response limit. Every redirect's host is
resolved and checked for public addresses, and connections are pinned to a
validated IP while preserving TLS hostname verification. Private/local addresses,
URL credentials, nonstandard ports, and non-HTML/text responses are rejected.
Cookies or credentials from inference and the requesting browser are not shared.
Scripts are not executed, and hidden/script/style content is omitted where
identified in HTML; CSS and JavaScript visibility are not evaluated.

This adds a tool to the existing four-call loop, not a separate research worker.
Search can discover a calendar, the reader can inspect it and follow an event
link, then the model can answer. Site blocks, JavaScript-only calendars, PDFs,
large pages, and limited excerpts remain explicit limitations; a successful read
is not an assertion that the complete schedule has been verified. Page text and
links are untrusted source material, not agent instructions.

Run `scripts/evaluate-page-reading.py pages` or `agent` with the server Python
environment for isolated live checks. Reports go to ignored `.expo/`; no turns
are added to the user's saved conversation. Unit tests cover extraction, limits,
network boundaries, and the persisted search → calendar → event tool sequence.

The calculator and `searchMemories` journal search run on Python. Search returns
bounded excerpts with source IDs from journals beside the configured database;
see [journal configuration](../docs/reference/memory-journals.md). Restart Python after code
updates to load the new tool. Clock/timezone, location and device metadata run on
the requesting device, with existing permission handling. Devices register their
own random key; only its hash is stored server-side. Device results require both
authorized owner access and the matching device key. No MCP or side-effecting tools exist
in this stage. A missing foreground client causes a device timeout after 120 seconds,
reported to the model as a tool failure rather than a fabricated reading.

One worker processes turns sequentially, including while waiting for device input.
An OS lock prevents two executing services from owning the same database. Run one
uvicorn process without reload for actual tasks. Generation allows five minutes per
model call, 2 MiB of upstream output, and four tool calls per turn. Context and
output token limits are configured at startup; see [configuration](README.md).
History follows the [session selection policy](#start-python); failed turns,
tool rows, and errors are excluded from prior-turn model history.
Current-turn tool results remain in the model context and are stored separately.

SQLite schema version 2 adds device requests, credential hashes and checkpoints,
preserving version-1 history. Incremental output is stored and polled roughly once
per second. Disconnecting does not cancel work. Restart conservatively marks
interrupted running/waiting turns `needs_review`, without replay. Queued turns start
when execution is enabled.
Use Stop request to cancel queued/running work, or Dismiss interruption to release
a review-blocked conversation. Copy request to retry restores the prompt to the
draft; Send creates a new turn with a new ID. Completed turns cannot be cancelled,
and repeating a cancellation is safe. Credential rotation and advanced checkpoint
recovery remain future work.

Checkpoints retain tool-loop state for inspection only. They are written around
tool calls, not for every inference request, and are never replayed automatically.
Changing retention, diagnostic coverage or recovery policy is separate work.

## API additions and validation

- `PUT /api/v1/devices/{id}` registers `{key}` (32–200 characters).
- `PUT /api/v1/turns/{turn_id}/device-results/{request_id}` accepts `{device_id, content}`
  with `X-Device-Key`; repeated identical results succeed, conflicting ones return 409.
- Turn snapshots include device requests and provisional output, never internal checkpoints.
- `GET /api/v1/conversations/{id}/latest-turn` includes completed/failed status.
- `GET /api/v1/conversations/{id}/active-turn` finds unfinished or review-blocked work.
- `PUT /api/v1/turns/{id}/cancellation` stops a turn or dismisses review without replay.

Regenerate TypeScript DTOs from OpenAPI after API changes:
`server/.venv/Scripts/python.exe server/export_types.py` (use `bin/python` on Mac).
Run Python tests from [setup](README.md), plus
`node --test tests/conversation.test.cjs tests/server-client.test.cjs`,
`npm run lint`, and `npx --no-install tsc --noEmit`.

There is no legacy browser/proxy switch. Browser inference always uses Python;
the native on-device path remains separately preserved and deferred.
