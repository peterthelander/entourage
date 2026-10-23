# Conversation evaluation suite

Status: Implemented evaluation harness; model quality remains under evaluation.
Updated: October 23, 2026 (initial guide October 21).

See the [initial repeated baseline](2026-10-21-conversation-baseline.md) for
observed retrieval and unsupported-event-selection failures.

Run from the repository root with the server Python environment (use
`server/.venv/bin/python` on macOS/Linux):

```powershell
.\server\.venv\Scripts\python.exe scripts/evaluate-conversations.py
.\server\.venv\Scripts\python.exe scripts/evaluate-conversations.py --live --repeats 3 --output scratch/conversation-baseline.json
```

The default command validates the synthetic fixture and saves initial inputs
without contacting inference or reading local inference configuration. Live mode
uses the production llama.cpp, Ollama or Gemini adapter, reading inference settings from
ignored `server/data/inference.json` with environment variables taking precedence,
as in the normal launcher. It does not change service settings or the running app.
It never reads personal history or owner credentials. Local runs do not read the
Google API key. Live runs selecting Gemini through configuration or
`--gemini-model` read the existing private
Google key only for synthetic model inference; web/page tools remain fixture-backed.

Select cases with repeatable `--case corrected-memory` options. Keep separate
output files for comparisons; each command replaces its output file. Use
`--baseline scratch/conversation-baseline.json` with a new output path to include
the previous report's mechanical counts, settings and fixture-identity comparison.
Compare the same cases, repeat count and fixture before attributing differences
to a model/configuration change. Sampling remains server-controlled; repeats are
not deterministic. Reports include application settings, source hashes and
llama.cpp engine metadata before/after live runs where available. Engine snapshots
identify the reported build, quantization, template and generation defaults, not
every launch setting or hardware condition. Older reports lack these snapshots.

For llama.cpp, `--reasoning-effort low|medium|high` overrides only evaluation
requests; the production transport still defaults to low. Keep output limits
fixed when testing effort under current operating constraints, and count
truncations as failures. Live non-low overrides with Ollama are rejected.

The frozen broader suite is `server/tests/fixtures/personal-agent-comparison.json`
(30 cases, 45 user turns per complete repeat). Select it with `--fixture`; the
original seven-case default and ten-case snapshot remain for regression/history.
See the [October 22 model-comparison protocol](2026-10-22-model-comparison.md).
In the broader suite, message-ID checks are `diagnostic_checks` and do not affect
the product-level mechanical pass. Product rubrics still require review of the
actual answers and tool evidence. Correct answers can fail a mechanical no-tool
expectation, and incorrect answers can contain every expected token.

`--gemini-model gemini-4-argon --live` selects the shared production Gemini adapter
without changing the service provider. It uses the same prompt, production
worker, tools, context selection and application budgets. Only synthetic inputs
are sent; no provider-built-in tools are enabled. Provider HTTP failures abort
the batch with sanitized diagnostics rather than generate repeated access/quota
failures. Hosted response identity and usage are recorded. Hosted calls return a
complete answer, while local calls stream, so compare total turn times rather
than time to first token. Reasoning/sampling/token accounting are provider-specific.

## Scope and evidence

The maintained fixture is `server/tests/fixtures/conversation-evaluations.json`.
Its seven cases cover topic changes, recall after an inactivity gap, corrections
and follow-ups, missing personal facts, ambiguous events, incomplete source
access, and an instruction injected into untrusted page text. All names, facts,
venues and dates are synthetic. The `.example` URLs are never fetched.

Each case/repeat gets a fresh temporary SQLite database. The production worker,
session selection, tool budget, journal exporter and memory tools execute normally.
Seeded memory is separate from recent context. Multiple turns in a case retain
the model's actual earlier replies. Dates are fixed for reproducible session
selection. Web calls receive fixture responses; unmatched requests return an
explicit unavailable result and are recorded. Unexpected device calls time out
locally after one second; no actual device is contacted. Search is offered even
without a Google key, using a placeholder that is never sent to a provider.

Reports preserve every inference input and successful model reply, saved tool result, fixture match,
final answer, completion status, elapsed time and individual mechanical check.
They are saved after each case/repeat under ignored `scratch/`. No saved user
conversation is modified. These evaluations do not test browser recovery,
phone permissions, actual website access or live Google search quality; existing
integration tests and public-research runners cover other boundaries.

## Reading results

Mechanical checks cover completion, required/forbidden tool names, selected fact
tokens, source IDs and known failure strings.
Fact checks normalize Unicode compatibility spacing and common hyphens, and
accept `message=2`, `message_id=2` and `ID 2` source labels; they do not validate every citation.
These checks are intentionally narrow: negation and paraphrases can fool them,
and a token may appear in a wrong answer.
A zero exit code means these checks passed, not that answers are correct. A
nonzero exit code flags a mechanical failure. Offline preparation has no model
score. An interrupted run retains completed case reports; it has no resume mode.

Every turn remains `semantic_review: pending`. Review each case against its
recorded rubric and actual tool evidence, marking each criterion pass/fail/unclear
in a separate dated review record with the report filename and case/repeat/turn.
Check especially:

- Does the answer follow current intent and preserve corrections across turns?
- Are personal claims grounded in original messages and accurate citations?
- Are unsupported details absent and missing information left unresolved?
- Does it disclose partial coverage or access failure without claiming completeness?
- Does it ask a useful clarifying question when the evidence cannot identify the event?

Report mechanical counts and rubric findings separately. Do not turn a model's
self-rating or a keyword match into a factuality guarantee. A scripted-model
harness test establishes execution and scoring behavior, not local-model quality.
Use repeated live runs before accepting a behavioral improvement, and retain
nearby successful cases when investigating a failure.

## Memory experiments and holdout separation

The [recurring-event pilot](2026-10-23-recurring-event-reconstruction.md) separates
generic service code, private experiment inputs and published personal knowledge.
It does not yet separate development from independent real-topic validation.
User hints guided discovery; a coding agent selected records, reviewed observations
and links, authored/refined articles and evaluated answers. The same trip questions
informed retrieval/date changes. Those cases are development/regression material,
not a holdout. Fictional unrelated fixtures test mechanics, not real-corpus
generalization. No model weights were trained or fine-tuned.

The next validation protocol is proposed, not yet executed:

1. Freeze the implementation, prompts, inference settings and evaluation rubric;
   record code/configuration identities without credentials. For a retrieval-only
   check, also freeze the reviewed source bundle. For an ingestion check, freeze
   raw inputs and the acceptance procedure before producing candidates.
2. Choose previously untouched real topics, including multiple event instances,
   unrelated records, missing evidence and corrections. An independent reviewer
   should prepare expected findings and acceptable uncertainty from original
   sources before the developer sees model answers. Record any user hints.
3. Score stages separately: source discovery, observation/date extraction, event
   membership, article synthesis and conversational use. Label supplied manual
   annotations explicitly so they do not count as automatic extraction success.
4. Preserve every planned run, failure and partial result. Keep first-run findings
   separate from results after interventions; do not report repeated tuning against
   the same cases as an independent validation gain.
5. Once a case informs code, prompts, source selection or article curation, move it
   into development/regression and choose a fresh holdout for the next claim.

Sources used to answer a question are legitimate retrieval inputs. Leakage arises
when expected answers or unsupported developer knowledge enter source curation,
prompts, special-case code or scoring without being declared. Topic-specific
published facts are expected personal data; topic-specific service behavior is
not the intended architecture. Accurate hand-curated articles establish neither
automatic ingestion quality nor model-wide generalization.

`scripts/evaluate-knowledge.py` publishes the supplied reviewed bundle only inside
each temporary evaluation store. It can send selected private evidence to hosted
inference when explicitly selected; the synthetic-only assurances above describe
the base conversation runner's normal fixtures. These isolated stores do not read
or modify live chat. Live smoke checks instead create service-verification
conversations excluded from shared-chat consolidation; they do write verification
history. Ordinary user interactions remain production history, with assistant
answers treated as secondary evidence rather than accepted imported facts.

Source acceptance and answer scoring are separate decisions. A fabricated answer
must not be promoted into imported knowledge to make a later test pass. Preserve
the exact reviewed source snapshot, original provenance, and contradictory/missing
evidence. A stronger model can expose differences in source use but is not an
independent ground-truth author or reviewer merely by being stronger.
