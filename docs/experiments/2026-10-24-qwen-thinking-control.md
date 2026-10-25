# Qwen thinking-disabled comparison

Status: completed exploratory comparison; current live default unchanged. Date: 2026-10-24.

The intervention adds `chat_template_kwargs.enable_thinking=false` to every
request. No Mac restart is required. The model, 16,384-token context, 2,048-token
output budget, prompts, fixtures and tool definitions remain unchanged.

| Comparison | Thinking low | Thinking disabled |
| --- | --- | --- |
| Source-binding control turns passing review | 15/16 | 15/16 |
| Control median turn latency | 27.63 s | 22.10 s |
| Broader cases passing frozen rubrics | 25/30 | 24/30 |
| Broader completed turns | 44/45 | 44/45 |
| Broader median turn latency | 20.027 s | 11.642 s |
| Broader answers leaking a closing thinking marker | 1 | 4 |

The broader disabled run was faster, but introduced regressions in combined-topic
memory, ambiguous-person retrieval and required calculator use. Venue clarification
and place-disambiguation improved. Both arms missed conflicting meeting evidence
and the puzzle in a final planning recap. Both retain the original finalization
failure on missing-memory; the separately repaired live harness should not be
credited to the thinking setting. Additional issues outside the frozen rubrics
include duplicated answers, an invented booking date, and provisional incorrect
arithmetic before tool results.

The control arms each had one contradictory time-window answer. These results do
not establish that disabling thinking preserves reliability. Keep thinking low
for now; latency alone does not justify adopting this setting.

## Reproducibility and limits

Private reports, full request audits and report-bound semantic reviews are under
ignored `scratch/qwen-comparison-20261024/`. An original-harness snapshot matches
the baseline source hashes. Fixture, runner, adapter, source, initial inputs,
tools and before/after engine metadata match across the broader arms. All 85
requests in the disabled broader run include the intervention and max_tokens=2048.

This is one sequential broader repeat with an unblinded coding-agent review of
all 30 cases against the existing frozen rubrics, not independent validation or
a statistically reliable performance estimate. The control has two repeats.
Mechanical keyword checks alone are not the semantic score. Public documentation
contains no personal experiment transcripts.

See [browser failure diagnosis and recovery](2026-10-24-browser-inference-recovery.md)
for the live harness fixes and regression coverage.
