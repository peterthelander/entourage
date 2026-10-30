# Bounded memory-context acceptance decision

Date: October 30, 2026 (America/New_York).
Status: Closed; candidate not adopted. Dependable memory remains unproven.

## Goal and stop rule

Resolve the interrupted timestamp/source-excerpt candidate with a finite decision.
The [completion contract](../personal-memory-development.md#october-30-completion-contract)
requires two four-turn return/update/correction conversations, existing nearby
controls, and passing engineering checks before runtime adoption. A failed gate
withdraws activation and ends this round; it does not trigger another intervention.
No models, prompts, source records or published memory were changed.

## Reconciliation of earlier work

October 28 reports contain more completed experiments than the prior public record:

- Source-coverage metadata: both conditions passed six of eight turns and two of
  four complete cases. Neither read original sources. Not adopted.
- Record times: seven of eight turns passed versus five of eight in control;
  one timed recap still misbound attendance to invitation evidence. This small
  authored comparison does not establish dependable continuity.
- Withholding uninspected index entries reduced some overreach, but broad-answer
  judgments remained ambiguous and unrepeated. Not adopted.
- Question-directed paragraphs recovered missing payment qualifications, but
  chronology/order-identity failures remained in both conditions. The source
  instruction control retained the benign receipt fact without obeying the attack.

The combined candidate had been wired into the working-tree worker, but its
`combined-detail` run stopped after one completed two-turn case and part of the
next. No process remained from that run. The original report and partial trace
were preserved unchanged; a separate interruption record identifies their hash.
That partial run is not a completed acceptance result. No live service restart
was performed to activate the candidate during this closeout.

## October 30 run

Used the actual Python worker and configured Mac llama.cpp adapter with temporary
SQLite/journal stores and the fictional return fixture. Personal conversations
and the live knowledge pointer were untouched. Two repeats were planned before
inference; the existing source-backed expectations were unchanged.

| Repeat | Outcome |
| --- | --- |
| 1 | First three answers pass: recover newer attendance report, distinguish invitation, accept watering with correct correction date. Final recap fails the 90-second inference deadline. |
| 2 | First turn fails connection to the Mac; remaining three turns do not execute. |

Of eight planned turns, three completed, two failed execution and three were not
run. Neither complete conversation passed. Failed/missing answers have no semantic
accuracy verdict; this is an execution-gate failure, not proof of a reasoning
regression or that the candidate caused the outage. Attempted turn durations were
23.295, 46.842, 8.081, 90.041 and 21.082 seconds; no successful-recap latency exists.

Engine metadata initially matched Qwen3.5-122B-A10B UD-IQ3_S, build
`b11669-620d2225c`, one slot, reporting 65,536 context tokens. The application
remained at 16,384 context/2,048 output tokens. Metadata was unavailable after the
run; engine stability could not be established. Do not pool this with earlier
32,768/16,384-engine-context trials or infer a cause from the context difference.
The Python browser service was already stopped before this experiment.

The nearby, source-instruction and conditional detailed-memory inference checks
were not started after the connection failure. They are explicitly unvalidated
in this round, not passing controls or queued background work. No additional
repeats, timeout increases, prompt patches or infrastructure investigation followed.

## Decision and implementation

Withdraw the candidate's default worker activation. Production `agent.py` is
unchanged from the committed implementation. The candidate remains solely in
`scripts/memory_context.py`, accessible through the explicit `retrieval_context`
diagnostic mode. Ordinary `retrieval` and supplied-evidence controls again use
the unchanged production context builder. A worker-level regression checks both
opt-in evidence insertion and absence of insertion after the diagnostic exits.
No live configuration flag or additional production recovery path was added.

Final validation: 186 Python tests pass after isolation, including opt-in/default
worker separation; 46 JavaScript tests, lint and TypeScript checking pass.
Whitespace checks pass. Production `agent.py` and its original session-context
regression match the committed versions. Live browser/HTTPS smoke checks were
not performed because the service was stopped and inference became unavailable.

Private report, frozen candidate source, report-bound review and prior interruption
record: ignored `scratch/memory-milestone-20261030/`. The review records three
semantic passes and five unavailable/unclear judgments with execution status
separate. It is unblinded coding-agent review, not independent validation.

Reproduction, only when a separately authorized future investigation needs it:

```powershell
.\server\.venv\Scripts\python.exe scripts/diagnose-memory.py `
  --bundle ingestion/fixtures/memory-overview-memory `
  --fixture ingestion/fixtures/memory-return-conversations.json `
  --expected ingestion/fixtures/memory-return-expectations.json `
  --modes retrieval_context --repeats 2 --inference-timeout 90 `
  --output scratch/memory-context-new
```

This milestone closes the experiment and reconciles code/documentation. It does
not deliver dependable memory. No automatic follow-up is scheduled. Model choice,
archive expansion, thematic synthesis, independent real-topic validation and native
inference remain deferred. Restore ordinary service/inference availability before
future everyday use; any recovery work should have its own bounded scope.
