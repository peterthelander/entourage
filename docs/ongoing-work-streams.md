# Project status and next priorities

Status: Current development overview.
Updated: October 30, 2026.

## What works

Entourage is a personal agent with one continuous conversation across phone and
desktop browsers. Python owns SQLite history, durable turns, context selection and
the tool loop. The requesting client owns device permissions and device tools.
The supported prototype connects through Tailscale to Python on Windows, with
llama.cpp inference on the Mac over home Wi-Fi. Ollama and hosted Gemini are also
supported. Native on-device inference remains on hold.

The service provides calculation, device context, public-page reading, optional
web search, conversation-memory retrieval and reviewed imported-memory retrieval.
Daily journals refresh from saved conversations. Reviewed imports use immutable
bundles with source references and snapshot-bound readers. The current curated
pilot contains 69 sources and 27 articles; it is not autonomous archive ingestion.

Qwen3.5-122B-A10B UD-IQ3_S is the selected local model for now. Model selection is
closed. Actual inference settings live in ignored `server/data/inference.json`;
startup and recovery are documented in [service operations](../server/EXECUTION.md).

## Known limits

Memory is useful but not consistently faithful. Answers can misassociate sources,
dates and corrections, promote plans to outcomes, or overstate coverage. Broad
summaries have no demonstrated importance-selection mechanism. Automatic article
updates, consolidation and publication are not implemented.

The latest context candidate was not adopted and remains opt-in diagnostic code.
No new retrieval or synthesis layer is active. See the
[closed decision](experiments/2026-10-30-memory-milestone.md) for evidence.

Current service availability has not been reverified since that experiment's
inference connection failure. Passing local regressions does not establish live
Windows-to-Mac availability or model answer quality.

## Next priorities

1. Confirm ordinary browser/service/inference availability before everyday use.
2. Use the existing agent in natural conversations. Capture concrete failures and
   nearby successes, including latency and relevant tool evidence.
3. Diagnose each demonstrated problem and make the smallest coherent improvement.
   Use representative whole-conversation checks before adopting behavior changes.

Keep the existing model and memory volume stable during this feedback cycle.
Further model comparisons, archive expansion and synthesis experiments are deferred
until a concrete need warrants them. Independent real-topic validation is required
before claiming general memory reliability.

## Where to go

- [Technical backlog](technical-debt.md): current engineering limitations.
- [Memory roadmap](personal-context-roadmap.md): deferred capabilities and goals.
- [Memory acceptance criteria](personal-memory-development.md): how to judge a future improvement.
- [Memory ingestion](memory-ingestion.md): implemented boundaries and ownership.
- [Experiment index](experiments/README.md): findings, decisions and reproduction tools.

Update this page when current behavior or priorities change. Keep chronological
results in experiment records and machine-specific details in ignored `docs/local/`.
