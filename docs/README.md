# Documentation

Start with the [project README](../README.md). Coding agents also follow [AGENTS.md](../AGENTS.md).

## Ongoing development

- [Project status and next priorities](ongoing-work-streams.md)
- [Design principles](design-principles.md)
- [Technical debt and remaining work](technical-debt.md)
- [Personal context and memory roadmap](personal-context-roadmap.md)
- [Personal memory acceptance criteria](personal-memory-development.md)
- [Memory ingestion boundaries](memory-ingestion.md)
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

See the [experiment index](experiments/README.md) for dated decisions, findings
and reproduction tools. Closed investigations are reference material.

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
