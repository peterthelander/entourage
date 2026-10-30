# Current-service Qwen27 baseline versus Coder-Next

Date: October 26, 2026 (America/New_York).
Status: Three repeats complete; unblinded coding-agent review complete; independent review absent.

Follow-up: the [Qwen122 comparison](2026-10-26-qwen122-comparison.md) adds the
larger model at 77/90 with the same current worker and three-repeat fixture.
The 27B results below remain unchanged.

Qwen3.8-27B Q4_K_M with low thinking passes 75/90 case runs on the current
service, compared with Coder-Next Q4_K_M's 65/90. It is stronger on corrections,
preferences and person disambiguation, but slower and unreliable on several
uncertainty cases. This supports using 27B as the local personal-agent baseline;
it does not establish coding performance or eliminate source-faithfulness failures.

## Activation and protocol

The Mac inference server was switched by the owner to
`/Users/pthelander/Downloads/Qwen3.8-27B-Q4_K_M.gguf`. Entourage's ignored local
model setting was aligned and its scheduled agent task restarted after confirming
no active turns. Authenticated model readiness and the private Tailscale calculator
smoke passed: exactly one executed calculator call, final answer 156. The smoke
writes a service-verification conversation excluded from ordinary shared history.

The broader experiment uses the unchanged 30-scenario
`server/tests/fixtures/personal-agent-comparison.json`, three sequential repeats,
90 case runs and 135 user turns. All 135 turns complete; none are omitted or
reclassified as successful merely for finishing. Each case has an isolated
temporary store; web and device calls receive fixtures. Personal histories and
the active knowledge pointer are not changed by the broader evaluation.

Compared with the [three-repeat Coder-Next result](2026-10-25-coder-next-comparison.md),
fixture, runner, evaluation adapter, production source hashes, initial conversation
inputs and application tool definitions match exactly. Application context is
16,384 tokens, output 2,048, session gap 60 minutes and tool budget four calls.
Both adapters request low reasoning effort, but Coder-Next does not implement a
thinking mode, so this is not matched reasoning compute. Engine build is
`b11669-620d2225c`. The 27B engine reports four slots with 16,384 context per slot;
Coder-Next reported one. Templates and sampling differ by setup. Neither hardware
load nor thermal conditions were controlled. Engine metadata and frozen source
identities remain stable throughout the 27B run.

The expected behavior and rubrics predate inference. Review is unblinded
coding-agent assessment of full answers and available tool evidence, not a new
independent holdout or population accuracy estimate. Mechanical checks, semantic
case success and additional presentation defects remain separate. Private plan,
raw report, report-bound review and paired summary are in ignored
`scratch/qwen27-current-20261026/`. Original historical reports are unchanged.

## Results

| Measure | Qwen3.8-27B Q4, low thinking | Coder-Next Q4 |
| --- | --- | --- |
| Distinct scenarios / repeats | 30 / 3 | 30 / 3 |
| Full-case rubric passes | 75/90 | 65/90 |
| Passes by repeat | 24, 25, 26 | 22, 22, 21 |
| Completed user turns | 135/135 | 135/135 |
| Median turn time, all repeats | 15.439 s | 2.489 s |
| Per-repeat median seconds | 15.715, 14.906, 16.384 | 2.553, 2.207, 2.564 |
| Actual tool calls | 122 | 84 |
| Answers containing literal tool-call markup | 3 | 0 |
| Answers containing a closing thinking marker | 2 | 0 |

Times cover whole turns, including tool activity, not tokens per second or first
token latency. Some Coder-Next failures skip required retrieval entirely, so its
latency advantage is not purely a comparison of inference engines doing the same
work. Mechanical 27B case passes are 28, 29 and 29; these exceed semantic passes.

| Category | Qwen27 passes | Coder-Next passes |
| --- | --- | --- |
| Continuity | 17/18 | 16/18 |
| Corrections | 12/12 | 7/12 |
| Recall | 17/18 | 15/18 |
| Uncertainty | 4/12 | 6/12 |
| Web evidence | 7/12 | 6/12 |
| Untrusted data | 9/9 | 9/9 |
| Tool use | 9/9 | 6/9 |

The strongest repeatable gains are changed-seat preference (3/3 versus 0/3),
ambiguous person (3/3 versus 0/3), historical code correction (3/3 versus 1/3),
punctuation-sensitive guide recall (2/3 versus 0/3), and a calculator follow-up
without invented currency (3/3 versus 0/3).

## Failures and limits

All three missing-allergy cases finish with literal XML-style tool calls after
executed searches, rather than a useful uncertainty answer. These are semantic
failures despite completed execution and mechanical passes. The result is not a
fabricated allergy claim, but still fails the user's request. The trace establishes
repeated bad final output; it does not alone isolate parser, template, finalization
instruction or model behavior as the cause. Do not assume higher weight precision
will fix it.

All three conflicting-venue answers retrieve one tentative Library Room proposal
and miss the Station Cafe alternative, answering too definitively. The combined
occasion test passes once: one repeat conflates the guest list, and another returns
the actual workshop list without resolving the user's workshop/brunch ambiguity.
The hyphenated guide lookup fails once, despite succeeding twice.

The museum follow-up omits its required source link in all three repeats. Two
ambiguous-event answers also omit links for factual listings. The third asks for
identifying information without asserting listing facts: it passes the existing
product rubric despite a mechanical missing-web-tool check, consistent with
earlier clarification-only grading. Do not change the rubric to require research
where a useful clarification suffices.

One final planning recap loses the puzzle and quiet-at-home activity. Two other
long replies duplicate content around a literal closing thinking marker, while
retaining the required final plan; those presentation defects remain outside the
frozen content score, as in the earlier reviews. Other additional issues include
redundant unavailable-page reads, unnecessary injection narration and dollar
notation in the separate bounded-calculation case. The latter remains outside
that case's frozen rubric; currency invention explicitly fails the distinct
calculator-follow-up rubric.

The original 27B historical result was 25/30. Its average is reproduced here as
75/90, but matching aggregate rates do not mean the exact same cases always pass.
This run removes the earlier prompt/service-version mismatch with Coder-Next;
it still compares different models, templates, reasoning behavior and engine
settings on authored development cases. The thinking-disabled 27B condition
remains historical and has not been expanded to three current-service repeats.

## Historical follow-up proposals (deferred)

The owner subsequently selected Qwen122 and closed model selection on October 26;
see the [decision record](2026-10-26-qwen122-comparison.md). The proposals below
are retained as historical context and are not active work. 27B remains a measured
comparison baseline. If a Q8 comparison is reopened, it should
hold worker, prompts, fixture, sampling, reasoning effort and budgets fixed before
changing reasoning or context settings in a separate condition. The repeated
literal-tool-output failure warrants a focused finalization investigation, with
its first failed traces retained. A repair should receive its own regression and
comparison record rather than overwrite these scores.

Coding remains untested here. Evaluate real repository tasks through the intended
coding client, including patch correctness, tests, unintended edits, recovery and
human intervention. The personal agent's four-tool execution budget is not a
surrogate for a coding client's longer execution loop. Neither the new baseline
nor the earlier source-supplied controls establish reliable long-running coding.

Lint, TypeScript checking and whitespace checks passed. Review coverage, source
hashes, initial-input identities and unchanged live knowledge pointer were
verified. These checks validate execution/artifact consistency, not semantic truth.
