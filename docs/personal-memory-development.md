# Dependable personal memory

Status: October 30 milestone closed; candidate not adopted; broader roadmap deferred.
Started: October 26, 2026.
Updated: October 30, 2026.

## Outcome

The [bounded acceptance run](experiments/2026-10-30-memory-milestone.md) closed
with an execution-gate failure: three answers completed, the recap timed out,
and the second repeat failed connection. The remaining live-model controls were
not started. No inference repair or further candidate tuning is pending in this
milestone. Default worker activation was withdrawn; the combined candidate is
an opt-in diagnostic only. This closes the experiment, not dependable memory.

## October 30 completion contract

Close the interrupted context experiment with a decision, rather than continue
searching for a generally reliable memory architecture. Assess the existing
combined candidate (active user-message record times and bounded original-source
paragraphs for follow-ups); do not introduce another candidate during this round.

Completion requires:

1. Run the existing four-turn return-after-pause fixture twice through the
   configured Mac llama.cpp adapter and actual Python worker, using isolated
   temporary stores. Review every answer against the existing frozen expectations:
   recover the newer user report, distinguish invitation from attendance, accept
   watering instead of planting, and retain the correction's provenance in recap.
2. Run the existing topic-switch, ordinary-update, active-date-correction,
   recall-after-pause and untrusted-memory controls once, plus the original-source
   instruction fixture once. If those pass, finish the interrupted detailed-memory
   check with the two existing grocery cases once (four turns), including full-answer
   chronology and payment qualifications. Require complete execution and
   full-conversation rubric passes. Record latency and engine identity before/after.
3. Keep runtime activation only if both return conversations and all controls
   pass. Otherwise withdraw activation, preserve the candidate and failed evidence
   for reproducibility, and close this round without further tuning. A rejected
   candidate completes the experiment; it does not complete dependable memory.
4. Run Python and JavaScript regressions, lint and typecheck. Reconcile current
   behavior, experiment results and ongoing-work documentation.

The first failure is retained. No extra repeats to seek a passing answer, prompt
patches, new retrieval mechanisms, model changes, archive expansion or automatic
ingestion enter this milestone. Fresh real-topic independent validation is deferred
and must not be claimed from these authored regression fixtures. Everyday feedback
can justify a separately scoped next task after this decision is complete.

Earlier work: the [first baseline and paragraph trial](experiments/2026-10-26-personal-memory.md)
are recorded. Paragraph enrichment was rejected after chronology regressions;
the transfer run was interrupted and preserved. A changed engine template/context
led to [fresh matched coverage and continuity controls](experiments/2026-10-28-personal-memory.md),
now reconciled in the October 30 decision.
The live reader, prompt and published memory remain unchanged.

## Intended experience

Entourage should use personal history to help with an ongoing decision, preserve
the difference between plans and outcomes, and maintain those distinctions through
follow-ups, corrections and pauses. Broad questions should receive a useful
synthesis; detailed episodes must remain available. Users should not have to
manage memory organization or supervise source attribution.

This work follows the [design principles](design-principles.md) and
[memory roadmap](personal-context-roadmap.md). Qwen3.5-122B-A10B remains fixed at
the selected configuration. Model selection is closed; these experiments assess
the agent's memory behavior, not alternative models.

## Broader sequence (deferred)

1. Preserve a current-model baseline on the existing real-memory diagnostics:
   normal retrieval, supplied articles, complete original sources, and broad
   overviews with inventory/flat/thematic controls. Keep first failures and
   exact inputs, settings, source snapshots and engine metadata.
2. Prepare source-backed transfer expectations before candidate changes. These
   questions use existing curated records; coding-agent authorship/review does
   not constitute an independent holdout. A separately prepared and reviewed
   real-topic holdout remains an explicit validation boundary.
3. Diagnose evidence discovery separately from evidence interpretation and
   question-appropriate prioritization. Trial the smallest change supported by
   the observed failures, using matched evidence and settings where possible.
4. Adopt only an improvement that survives follow-ups and nearby positive and
   negative controls. A failed candidate should remain an experiment rather than
   add production complexity. Record useful negative findings as well as gains.

## Acceptance

- Recover relevant historical evidence without inventing missing identities,
  chronology, attendance, settlement, current circumstances or priorities.
- Keep confirmed source statements useful: uncertainty must not erase evidence
  that an action was reported or completed when the source establishes that.
- Preserve detail access alongside broad synthesis; do not substitute article
  count, index position or frequency for user importance.
- Evaluate complete conversations, including a correction and a return after an
  inactivity boundary. Record execution failures separately from semantic errors.
- Report attempted/completed latency and partial coverage, not just passing
  answer counts. Compare repeated runs before claiming reliability gains.
- Run relevant Python/JavaScript checks, lint and typecheck before delivery.

## Working artifacts

Private experiment inputs, first-run reports and report-bound reviews belong in
ignored `scratch/personal-memory-20261026/`, `scratch/personal-memory-20261028/`
and `scratch/memory-milestone-20261030/`. Existing comparison artifacts and
the live knowledge bundle remain intact. Reusable tooling and fictional
regressions belong in `scripts/`, `server/tests/` and `ingestion/fixtures/`.

Incremental publication, full-archive ingestion, automatic consolidation and
side-effecting tools remain later milestones. This stage establishes the
evidence needed to choose a practical memory improvement.
