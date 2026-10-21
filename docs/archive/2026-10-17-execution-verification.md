# Python execution verification — October 17, 2026

Status: Archived verification record. Recorded: October 17, 2026.

Historical verification record. Counts, setup and outstanding work below apply to
the recorded checks. See [current operations](../../server/EXECUTION.md) and
[technical debt](../technical-debt.md) for the current service.

## Retired-code cleanup

Removed the old Node proxy, job transport, browser tool-loop orchestration, legacy
browser switch, obsolete smoke script and their tests. Kept the native inference
path and the minimal old-storage readers needed for explicit history import.
Current checks pass: 26 Python tests, 20 JavaScript tests, lint and typecheck.
The served bundle contains the Python client and no retired browser harness.
The web startup script uses LAN/8081; Tailscale provides phone access.

## Main service cutover

Python now runs on localhost:8000, exposed privately through
`https://hp.taile8e695.ts.net/agent`. Expo on 8081 serves the Python-backed browser
by default. The old proxy was identified by its exact command, stopped, and its
`/llm` Tailscale route removed. Ollama was not restarted.

Verified health through Tailscale, the browser connection form at the existing URL,
and a full authenticated calculator turn through the private route: exactly one
tool call, result 156, and matching final answer. The smoke script read the credential
from its ignored local file without printing it or embedding it in a URL.

Final checks: 26 Python tests, 33 JavaScript tests, lint, and TypeScript passed.
Cancellation tests verify interrupted inference, rejected late device results,
and worker continuation. Dismissing restart review releases the conversation.
History import keeps source storage; the user's phone history still needs importing
from that originating browser. Physical-phone testing remains outstanding.

## Earlier isolated execution tests

The first tests below used an opt-in browser before cutover. See
[execution setup](../../server/EXECUTION.md) for the current startup and credential path.

Live smoke tests used separate Expo/Python ports (8082/8001), a disposable SQLite
database under ignored `.expo/`, and the existing Windows Ollama model `qwen3.5:4b`.

- Submitted a calculator request for 12 × 13 from the browser, then navigated to
  about:blank while inference ran. Returning restored the persisted conversation,
  one recorded calculator result, and the answer 156. Python executed the complete
  tool loop without needing the browser to execute the calculator or start follow-up
  inference.
- Requested the device clock through `getCurrentTime`. The browser handled the
  credential-bound request and returned `09:58:06`, America/New_York, UTC offset
  -240. The final answer matched the recorded local time. This verifies a browser
  device round trip, not native phone permissions or Health access.

Automated coverage includes durable completion, retry deduplication, device keys,
denied/unavailable tools, timeout, interrupted-task review status, single-worker
locking, failed generations, tool-call budget, stream framing, schema upgrades,
and the earlier persistence tests. Client transport tests cover stable retry IDs,
credential headers, pagination and permanent API rejection status.

Location permission on a physical phone, native client integration, remote Mac
inference and Tailscale access to the new Python service remain untested. The normal
browser/Ollama service retains its existing tests and default configuration.
