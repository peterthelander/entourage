# Personal memory: coverage, continuity and index controls

Date: October 28, 2026 (America/New_York).
Status: Closed and reconciled October 30; no live memory or prompt change adopted.

The coverage, return, index and subsequent timestamp/question-context trials have
completed or been explicitly identified as interrupted. See the
[October 30 acceptance decision](2026-10-30-memory-milestone.md) for their outcomes,
the combined candidate's execution failure and withdrawal of runtime activation.
The descriptions below preserve the original experiment plan; no background runs
or automatic continuation remain pending.

## Continuation boundary

The [October 26 baseline and paragraph trial](2026-10-26-personal-memory.md)
remain historical results. The paragraph intervention is rejected for production:
it recovers omitted payment qualifications but introduces chronology regressions.
Its subsequent transfer run was interrupted and is preserved explicitly.

The running model is still Qwen3.5-122B-A10B UD-IQ3_S, engine build
`b11669-620d2225c`, one slot. Engine metadata now reports 32,768 context tokens
and a different chat-template hash. Application context remains 16,384 tokens
with a 2,048-token output allowance. No configuration was changed for this study.
Run fresh matched controls rather than attributing cross-date differences to
the memory intervention. Engine metadata is captured before/after each batch.

## Comparisons

`scripts/diagnose-memory.py` now exposes two additional opt-in modes. Its original
default modes and live service behavior are unchanged. The runner interleaves
conditions within each case and rotates their order between repeats. Freeze
manifests include context-builder/runner code and exact evidence/expectations.

- `retrieval_coverage`: normal retrieval, with article responses additionally
  disclosing which original sources are not fully supplied, their dates and
  character counts. No additional source prose or generated claims enter the
  article. Requested qualifications absent from selected quotations may require
  an original-source read; absence from an article is not absence from its source.
- `selected_overview`: the same complete selected articles and source evidence as
  `flat_overview`, withholding only uninspected index entries and adjusting the
  scope statement. Coverage metadata remains intact. This is supplied evidence,
  not an autonomous retrieval score or a production significance mechanism.

Private reports are in ignored `scratch/personal-memory-20261028/`:

1. `coverage-paired`: two existing real two-turn cases, both normal-retrieval
   conditions, two repeats (16 planned turns). Check full-answer chronology,
   omitted payment qualifications, actual source reads, uncertainty and latency.
2. `return-paired`: one new fictional four-turn conversation in both normal
   retrieval conditions (eight planned turns). Start after an inactivity boundary,
   recover a later user-reported attendance update, distinguish it from the
   invitation, accept a new correction, and preserve it in a final recap.
3. `index-paired`: the existing broad three-turn overview plus a detail episode,
   flat/index-withheld conditions, one repeat (eight planned turns). Selected
   factual evidence is identical; preserve first failures and qualifications.

The new committed `memory-return-conversations.json` and expectations are wholly
fictional. Older uncertainty appears in seeded history; a later report appears in
conversation memory. The unit test verifies that old history actually falls
outside active context. User reports establish what the user said, not external
verification, while original invitation unknowns must not erase a newer user
report. The seeded correction is not an automatically exported earlier model
turn, and this fixture does not validate background journal-refresh operation.

These are authored development/regression cases, not untouched independent
validation. Source curation, fixture authorship and answer review are explicit;
there is no independent reviewer. Mechanical checks and full-answer judgments
remain separate. Do not infer durable personal importance, full-archive recall,
automatic ingestion or general reliability from these small comparisons.

## Reproduce

Use a fresh output directory and the configured local inference service:

```powershell
.\server\.venv\Scripts\python.exe scripts/diagnose-memory.py `
  --bundle ingestion/fixtures/memory-overview-memory `
  --fixture ingestion/fixtures/memory-return-conversations.json `
  --expected ingestion/fixtures/memory-return-expectations.json `
  --modes retrieval retrieval_coverage --repeats 1 `
  --output scratch/memory-return-new
```

For index controls use the overview fixture/plan from the
[overview study](2026-10-24-memory-overview.md), with
`--modes flat_overview selected_overview`. The preview command also accepts
`--mode selected_overview` for inspecting the packet without inference.
