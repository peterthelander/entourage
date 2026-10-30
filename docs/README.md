# Documentation

Start with the [project README](../README.md). Coding agents also follow [AGENTS.md](../AGENTS.md).

## Ongoing development

- [Ongoing work streams](ongoing-work-streams.md)
- [Design principles](design-principles.md)
- [Technical debt and remaining work](technical-debt.md)
- [Personal context and memory roadmap](personal-context-roadmap.md)
- [Personal memory: bounded milestone outcome and deferred roadmap](personal-memory-development.md)
- [Memory ingestion status, ownership and next validation](memory-ingestion.md)
- [Batch ingestion experiment workspace](../ingestion/README.md)
- [Recursive self-improvement ideas](recursive-self-improvement.md)

Keep ongoing development documents directly in `docs/`. Roadmaps and ideas retain
their proposal status until implemented; known engineering limitations stay in the
technical backlog.

## Current references

- [Python setup and configuration](../server/README.md)
- [Service operation, tools, and recovery](../server/EXECUTION.md)
- [Daily memory journals](reference/memory-journals.md)
- [Inference limits and context budgeting](reference/inference-limits.md)

These describe implemented behavior. Keep configuration defaults in the server
configuration table and link to them rather than copying values into several guides.

## Experiments

- [Bounded memory-context acceptance decision, October 30 (closed)](experiments/2026-10-30-memory-milestone.md)
- [Memory coverage, return/correction and index controls, October 28](experiments/2026-10-28-personal-memory.md)
- [Current-model personal-memory diagnostics and context trials](experiments/2026-10-26-personal-memory.md)
- [Qwen122 selection decision and comparison (closed)](experiments/2026-10-26-qwen122-comparison.md)
- [Current-service Qwen27 baseline versus Coder-Next](experiments/2026-10-26-qwen-current-baseline.md)
- [Coder-Next versus earlier inference setups](experiments/2026-10-25-coder-next-comparison.md)
- [Evidence-backed personal overview controls](experiments/2026-10-24-memory-overview.md)
- [Broader historical memory sample and synthesis feedback](experiments/2026-10-24-broader-memory-sample.md)
- [Qwen thinking-disabled comparison](experiments/2026-10-24-qwen-thinking-control.md)
- [Browser inference failure diagnosis, display tests and recovery](experiments/2026-10-24-browser-inference-recovery.md)
- [Qwen source-binding controls and broader conversation comparison](experiments/2026-10-24-qwen-transfer-and-conversations.md)
- [Qwen versus gpt-oss memory comparison](experiments/2026-10-24-qwen-memory-comparison.md)
- [Memory faithfulness: evidence availability versus answering](experiments/2026-10-23-memory-faithfulness.md)
- [Fresh-topic memory validation and evidence-excerpt comparison](experiments/2026-10-23-fresh-memory-validation.md)
- [Recurring event reconstruction across years and sources](experiments/2026-10-23-recurring-event-reconstruction.md)
- [Reviewed memory integration and live pilot, October 23](experiments/2026-10-23-reviewed-memory-integration.md)
- [October 22 structure, support review and full ingestion pilot](experiments/2026-10-22-article-workflow.md)
- [October 22 initial article-generation trials](experiments/2026-10-22-article-generation.md)
- [October 22 generic mail normalization](experiments/2026-10-22-mail-normalization.md)
- [Generic memory candidate contracts and multi-topic pilot](experiments/memory-candidate-contracts.md)
- [October 22 ski-trip discovery pilot](experiments/2026-10-22-ski-trip-discovery.md)
- [October 22 initial mail filtering](experiments/2026-10-22-ingestion-filtering.md)
- [Conversation evaluation suite and memory holdout protocol](experiments/conversation-evaluations.md)
- [October 21 conversation baseline and findings](experiments/2026-10-21-conversation-baseline.md)
- [October 21 literal-search guidance trials](experiments/2026-10-21-retrieval-guidance.md)
- [October 21 word-search interface comparison](experiments/2026-10-21-word-search.md)
- [October 21 reasoning-effort comparison](experiments/2026-10-21-reasoning-comparison.md)
- [October 21 explicit source-identifier experiment](experiments/2026-10-21-source-identifiers.md)
- [October 22 broader suite and local/Gemini comparison](experiments/2026-10-22-model-comparison.md)
- [Context selection experiments and runner](experiments/context-experiments.md)
- [Web lookup and page-reading evaluations](experiments/web-lookup-evaluation.md)

Keep methods, conclusions, and limitations here. Reusable runners belong in
`scripts/`, synthetic fixtures in `tests/`, and new private inputs/results in
ignored `scratch/`. Existing runners still default to ignored `.expo/` outputs;
historical reports stay there so their recorded paths remain valid.
The ingestion workspace keeps private catalogs, source records, curation and
reports in ignored `ingestion/data/`; its fictional fixtures live under
`ingestion/fixtures/`. Keep these data locations separate from reusable code and
from claims of independent validation.

## Archive

- [October 17 development handoff](archive/2026-10-17-handoff.md)
- [Server migration design and delivery record](archive/server-migration.md)
- [October 17 execution verification](archive/2026-10-17-execution-verification.md)
- [October 18 engineering review and subsequent cleanup](archive/2026-10-18-engineering-review.md)

These preserve decisions and evidence from their recorded period. Old settings,
test counts, and outstanding checks are historical; consult current references
before operating the service. File paths quoted inside historical findings refer
to the layout at the time of the review.

## Local notes and maintenance

Machine-specific hosts, ports, model choices, and restart instructions belong in
ignored `docs/local/machine-runbook.md`. It is local-only and will not appear in a
fresh checkout. Actual inference configuration remains in ignored
`server/data/inference.json`; the runbook does not configure the service.
Personal generated journals remain under ignored `server/data/vault/`.

Keep root Markdown limited to the project README and agent instructions. Keep
principles, the technical backlog, roadmaps, and ideas directly in `docs/`. Use lowercase hyphenated names for new docs.
Start proposals, experiment records, and archived snapshots with their status and
date; distinguish the date of an experiment from the date a document was moved.
Update this index and relative links when adding or moving documents.
