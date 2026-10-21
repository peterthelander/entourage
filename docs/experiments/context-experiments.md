# Context experiments

Status: Experiment record and reusable runner guide. Experiments: October 18, 2026.

`scripts/compare-context.py` uses a synthetic fixture, independent of personal
history, message IDs, credentials and machine-local configuration. It compares
the former full-window policy with current session selection for an update and
a follow-up. It does not change the production policy.

Prepare inputs offline from the repository root:

```powershell
.\server\.venv\Scripts\python.exe scripts/compare-context.py
```

This performs no inference. Inspect the conditions and settings in ignored
`.expo/context-comparison.json`. Use `--fixture` and `--output` to compare other
synthetic conversations and preserve separate experiment reports.

Run a live comparison explicitly, substituting the actual endpoint and model ID:

```powershell
.\server\.venv\Scripts\python.exe scripts/compare-context.py --live --upstream http://MODEL-HOST:8080 --model MODEL-ID
```

On macOS/Linux use `server/.venv/bin/python`. Live mode uses the production
llama.cpp adapter, tools and system prompt. It records three repetitions of each
condition by default (`--repeats` adjusts this). Calls are sequential and model
tool requests are recorded without execution. No chat records are written.

Evaluate whether answers address the latest message, retain the outing and names,
invent details, or request unnecessary tools. A tool request is an intermediate
outcome, not evidence of a successful final answer. Sampling defaults remain
server-controlled; repeated runs cannot guarantee deterministic outputs.

The October 18 experiments with actual history suggested session selection was a
useful direction. Timestamp prefixes sometimes appeared in responses; one full
timestamped input revived an old coding request. The unchanged full-window control
did not reproduce that failure in its three runs. Those limited observations do
not establish universal failure rates or an optimal inactivity threshold. Private
inputs and raw results remain in ignored local scratch files; the synthetic
fixture preserves the scenario, not an exact replay of that incident.
