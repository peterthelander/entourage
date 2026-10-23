# Python agent server

The Python-backed browser is now the default. See [execution setup](EXECUTION.md) for
credentials, the new browser client, device tools, and recovery limitations.
The setup below defaults to persistence-only mode for API exploration.

This is the sole browser agent service. It stores
conversations, imported history, and turn records in SQLite. With execution enabled,
it also owns the full agent loop. Use `scripts/start-agent.py` for the normal service;
the low-level commands below run persistence-only API exploration unless configured.

## Setup (Python 3.11 or newer)

From the repository root on Windows:

```powershell
python -m venv server/.venv
.\server\.venv\Scripts\python.exe -m pip install -r server/requirements-dev.txt
.\server\.venv\Scripts\python.exe -m uvicorn entourage_server.app:create_app --factory --app-dir server --host 127.0.0.1 --port 8000
```

On macOS/Linux:

```sh
python3 -m venv server/.venv
server/.venv/bin/python -m pip install -r server/requirements-dev.txt
server/.venv/bin/python -m uvicorn entourage_server.app:create_app --factory --app-dir server --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/api/v1/health`. Interactive API documentation is at
`http://127.0.0.1:8000/docs`; the implemented OpenAPI schema is `/openapi.json`.
Health is process liveness, not an Ollama connectivity check. The capabilities
list advertises persistence features, not agent execution. Submitted turns remain
`queued` unless execution is explicitly enabled. Use test conversations for API exploration.

Server-only configuration is read at startup:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ENTOURAGE_OLLAMA_UPSTREAM` | `http://127.0.0.1:11434` | Local or remote Ollama HTTP(S) origin |
| `ENTOURAGE_INFERENCE_PROVIDER` | `ollama` | `ollama`, `llama_cpp` or `gemini`; see [selection examples](EXECUTION.md#start-python) |
| `ENTOURAGE_LLAMA_CPP_UPSTREAM` | `http://127.0.0.1:8080` | llama.cpp origin without `/v1`; launcher also reads ignored `data/inference.json` |
| `ENTOURAGE_MODEL` | `qwen3.5:4b` | Server-owned model selection |
| `ENTOURAGE_GEMINI_API_KEY` | empty | Server-only Gemini inference/search credential; also accepts `GEMINI_API_KEY`, then ignored `server/data/gemini-api-key.txt` |
| `ENTOURAGE_WEB_SEARCH_MODEL` | `gemini-2.5-flash-lite` | Gemini model used only for Google Search research; main inference selection is unchanged |
| `ENTOURAGE_CONTEXT_TOKENS` | `8192` | Application context budget; integer 2048–262144, subject to model/hardware limits; does not change hosted model context capacity |
| `ENTOURAGE_MAX_OUTPUT_TOKENS` | `1536` | Maximum generated tokens per model call; positive, at most half the context window |
| `ENTOURAGE_CONTEXT_SESSION_GAP_MINUTES` | `60` | Start fresh active context after a longer gap between user messages; integer 1–1440. Older conversations remain available through memory tools. |
| `ENTOURAGE_KNOWLEDGE_ENABLED` | `0` | Set to `1` to include explicitly reviewed imported bundles in memory search/inventory and enable bounded article/source reads. See [publication and rollback](EXECUTION.md#reviewed-imported-memory). |
| `ENTOURAGE_DATABASE_PATH` | `server/data/entourage.sqlite3` | SQLite file; default is anchored to the server directory, independent of working directory |

Persistence-only mode makes no inference requests; the normal launcher enables
execution and memory retrieval. Relative custom database paths resolve
against the process working directory. Dependencies are constrained to the versions
tested in `constraints.txt`.
The Python server does not read the browser's `EXPO_PUBLIC_*` variables or load
`.env` files automatically. Keep persistence-only exploration on loopback; remote
exposure should use private Tailscale HTTPS and identity checks as described in
execution setup. Persistence-only mode without a token is for loopback development. Personal runtime data lives under
ignored `server/data/`; stop the Python service before copying that directory for a
backup. Custom database paths must also be kept out of Git.

## Persistence API

Use `/docs` to inspect the exact request/response schemas. Creation IDs must be UUIDs.

- `PUT /api/v1/conversations/{id}` with `{"title":"Personal"}` creates a conversation.
- `GET /api/v1/conversations?after=0&limit=50` lists conversations in creation order.
- `GET /api/v1/conversations/{id}/messages?after=0&limit=50` reads ordered messages.
- `PUT /api/v1/conversations/{id}/turns/{turn_id}` with `{"text":"Hello","device_id":"<uuid>"}` stores a queued turn and its user message atomically.
- `GET /api/v1/turns/{turn_id}` retrieves durable task status after reconnect/restart.
- `POST /api/v1/import-preview` with `{"messages":[...]}` previews legacy message kinds without writing.
- `PUT /api/v1/conversations/{id}/imports/{import_id}` with the same body imports into an empty conversation.

Conversation/import creation returns 201; new turns return 202. Identical retries
return 200 without adding messages. Conflicting retries and a second active turn
return 409. A queued turn blocks another turn in that conversation until execution
is enabled. Pagination uses the last
returned sequence as `next_after` when more records exist; limits are 1–100.
JSON uploads are capped at 1 MiB, turn text at 16,000 characters, imports at 1,000
messages. Errors use `{error: {code, message}}` without echoing submitted text.

For imports, use the browser storage object's `messages` array (not its outer
`version` field). Preview first, then explicitly commit to a new conversation. The
welcome placeholder is skipped; `toolresult-` and `error-` IDs become explicit tool
and error kinds. Existing timestamps are converted to UTC; missing ones use import
time. Source localStorage is not changed. These conversation-specific endpoints
support API exploration and compatibility; the current browser uses `/chat` and
`/chat/imports/{id}` to append explicitly imported history to the shared chat.
Keep the same import ID for retries, including after restart.
Unfinished old replies are not included in the committed history import. Their
original browser recovery data remains intact; copy the old request into a draft
and explicitly send it if desired.

## Verify

```powershell
Push-Location server
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Pop-Location
```

On macOS/Linux: `cd server && .venv/bin/python -m unittest discover -s tests -v`.
Tests do not need Ollama or network access. The generated virtual environment and
personal runtime data must never be committed.

See [service operations](EXECUTION.md) for current behavior and
[the migration record](../docs/archive/server-migration.md) for historical design context.
Journal memory retrieval is implemented; MCP integration remains future work.
