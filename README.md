# Entourage

A personal agent with a phone/desktop browser interface, a Python agent service,
and local inference through Ollama or llama.cpp. The browser handles display, input and device permissions;
Python owns conversations, durable turns, model requests and the tool loop.

See [design principles](docs/design-principles.md) for how we investigate problems and
keep changes simple and coherent. Browse the [documentation index](docs/README.md)
for current references, proposals, experiments, and historical records.

## Run

Install the JavaScript dependencies using the existing package lock (`npm ci`),
then follow [Python setup](server/README.md) to create its virtual environment.
From the repository root on Windows:

```powershell
.\server\.venv\Scripts\python.exe scripts/start-agent.py
```

On macOS/Linux: `server/.venv/bin/python scripts/start-agent.py`.
In a second terminal: `npm run web` (uses port 8081; phone access uses Tailscale).
Open `http://localhost:8081`; the browser connects automatically. The launcher trusts
direct localhost requests and your own Tailscale Serve identity over the private link.
No copied token or browser sign-in is required. SQLite data stays excluded from Git.

For phone access, configure private Tailscale routing as described in
[service operations](server/EXECUTION.md). Machine-specific addresses, model settings,
and restart steps belong in ignored `docs/local/machine-runbook.md`.

## Configuration and data

See [server configuration](server/README.md) for supported environment variables
and defaults, and [service operations](server/EXECUTION.md#start-python) for context
selection. The launcher reads ignored `server/data/inference.json`; explicit
environment variables override it. See [inference limits](docs/reference/inference-limits.md)
for budgeting and engine-capacity limitations.

Agent conversations live in SQLite under ignored `server/data/`. Stop Python before
copying that directory for a backup. Never commit personal data, model weights, or tokens.

Saved history from the earlier browser version can be previewed and explicitly
imported into the shared chat. The source copy stays intact. Every device opens
the same continuous thread, without conversation tabs or a new-chat control.
Unfinished old requests can be copied into a draft; they do not run automatically.
Use Stop request for queued/running work, Dismiss interruption after a service
restart, and Copy request to retry for an explicit new submission.

See [service operations](server/EXECUTION.md), [architecture](docs/archive/server-migration.md)
and [verification](docs/archive/2026-10-17-execution-verification.md) for details and limitations.

## Verify

```powershell
Push-Location server
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Pop-Location
node --test tests/*.test.cjs
npm run lint
npx --no-install tsc --noEmit
```

The authenticated live smoke check is
`server/.venv/Scripts/python.exe scripts/check-agent.py` (use `bin/python` on Mac).
Pass `--endpoint https://<your-tailscale-host>/agent` to check the private phone route.
It creates a service-verification conversation and checks a real calculator exchange.

## Daily memory journals

Export shared history using
`server/.venv/Scripts/python.exe scripts/export-journals.py --timezone America/New_York`
after updating Python requirements. See [journal configuration and limits](docs/reference/memory-journals.md).
With execution enabled, Python refreshes journals automatically about every two
seconds and catches up after restart. Set `ENTOURAGE_JOURNAL_TIMEZONE` consistently
for your deployment. `searchMemories` searches journals by keywords/date,
returns source references and reports refresh status. Automatic summaries remain future work.
`getMemoryInventory` reports covered dates/counts; `readMemories` reads dated
entries without keywords for topic summaries, with pagination and explicit partial coverage.

## Native direction

The Expo/React Native app, native model loading, local chat storage, and `llama.rn`
inference are retained but on hold. The native-only tool loop and its tests remain.
Native feature parity/testing is not required for current browser work. Device tools
can later support a native client while inference stays on the home computer.
