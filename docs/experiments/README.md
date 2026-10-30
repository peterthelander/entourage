# Experiment index

Status: Research reference; listed records preserve their dated findings.
Updated: October 30, 2026.

Consult [current priorities](../ongoing-work-streams.md) before resuming an old
experiment. Historical next steps and settings are not active instructions.
Model selection and the latest memory-context round are closed; no additional
memory experiment is scheduled.

## Records

- [Bounded memory-context acceptance decision, October 30 (closed)](2026-10-30-memory-milestone.md)
- [Memory coverage, return/correction and index controls, October 28](2026-10-28-personal-memory.md)
- [Current-model personal-memory diagnostics and context trials](2026-10-26-personal-memory.md)
- [Qwen122 selection decision and comparison (closed)](2026-10-26-qwen122-comparison.md)
- [Current-service Qwen27 baseline versus Coder-Next](2026-10-26-qwen-current-baseline.md)
- [Coder-Next versus earlier inference setups](2026-10-25-coder-next-comparison.md)
- [Evidence-backed personal overview controls](2026-10-24-memory-overview.md)
- [Broader historical memory sample and synthesis feedback](2026-10-24-broader-memory-sample.md)
- [Qwen thinking-disabled comparison](2026-10-24-qwen-thinking-control.md)
- [Browser inference failure diagnosis, display tests and recovery](2026-10-24-browser-inference-recovery.md)
- [Qwen source-binding controls and broader conversation comparison](2026-10-24-qwen-transfer-and-conversations.md)
- [Qwen versus gpt-oss memory comparison](2026-10-24-qwen-memory-comparison.md)
- [Memory faithfulness: evidence availability versus answering](2026-10-23-memory-faithfulness.md)
- [Fresh-topic memory validation and evidence-excerpt comparison](2026-10-23-fresh-memory-validation.md)
- [Recurring event reconstruction across years and sources](2026-10-23-recurring-event-reconstruction.md)
- [Reviewed memory integration and live pilot, October 23](2026-10-23-reviewed-memory-integration.md)
- [October 22 structure, support review and full ingestion pilot](2026-10-22-article-workflow.md)
- [October 22 initial article-generation trials](2026-10-22-article-generation.md)
- [October 22 generic mail normalization](2026-10-22-mail-normalization.md)
- [Generic memory candidate contracts and multi-topic pilot](memory-candidate-contracts.md)
- [October 22 ski-trip discovery pilot](2026-10-22-ski-trip-discovery.md)
- [October 22 initial mail filtering](2026-10-22-ingestion-filtering.md)
- [Conversation evaluation suite and memory holdout protocol](conversation-evaluations.md)
- [October 21 conversation baseline and findings](2026-10-21-conversation-baseline.md)
- [October 21 literal-search guidance trials](2026-10-21-retrieval-guidance.md)
- [October 21 word-search interface comparison](2026-10-21-word-search.md)
- [October 21 reasoning-effort comparison](2026-10-21-reasoning-comparison.md)
- [October 21 explicit source-identifier experiment](2026-10-21-source-identifiers.md)
- [October 22 broader suite and local/Gemini comparison](2026-10-22-model-comparison.md)
- [Context selection experiments and runner](context-experiments.md)
- [Web lookup and page-reading evaluations](web-lookup-evaluation.md)


## Reusable tools

- `scripts/evaluate-conversations.py`: representative agent/conversation checks.
- `scripts/diagnose-memory.py`: retrieval versus supplied-evidence controls and
  the explicitly opted-in context candidate in `scripts/memory_context.py`.
- `scripts/diagnose-memory-context.py` and `memory_source_context.py`: the older
  source-excerpt comparison, retained to reproduce its separate rejected trial.
- `scripts/memory_overview.py` and `preview-memory-overview.py`: offline editorial
  grouping and evidence controls; no production synthesis layer.
- `scripts/memory_source_coverage.py`: diagnostic coverage metadata.
- `scripts/memory_validation.py`, `validate-memory-experiment.py` and
  `compare-memory-conditions.py`: frozen inputs and report-bound review utilities.

Retain distinct experimental mechanisms only while they support a recorded
comparison or useful regression. Production does not import the context candidates.
New investigations should reuse these entry points rather than add parallel wrappers.
Private results belong in ignored `scratch/`; older reports may remain in ignored
`.expo/` to preserve recorded paths. Fictional memory fixtures live in
`ingestion/fixtures/` and Python regressions in `server/tests/`.
