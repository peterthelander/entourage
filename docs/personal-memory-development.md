# Personal memory acceptance criteria

Status: Reference for future memory changes; no active experiment.
Updated: October 30, 2026.

Entourage should use personal history naturally through follow-ups, corrections
and pauses. Detailed evidence should remain available alongside useful broad
summaries. The user should not need to manage the memory's organization.

A proposed improvement should:

- Recover supported facts without inventing identities, chronology, attendance,
  completion, current circumstances or priorities.
- Preserve the difference between source statements, assistant recollections and
  inference. Honest uncertainty should not erase facts the evidence establishes.
- Maintain corrections and their provenance across the whole conversation.
- Keep targeted detail accessible; article count, index position and recurrence
  alone do not establish personal significance.
- Survive nearby successful cases, topic changes and untrusted-source controls.
- Report execution completion, answer quality, latency and coverage separately.

Choose a bounded question and stop rule before changing behavior. Preserve the
baseline and first failures; compare repeated runs under matched settings when
assessing variable model behavior. Authored regression cases are development
material, not independent validation. Follow the
[evaluation protocol](experiments/conversation-evaluations.md#memory-experiments-and-holdout-separation)
and run the checks in the [project README](../README.md).

The [latest context experiment](experiments/2026-10-30-memory-milestone.md) is
closed without adoption. Its candidate is diagnostic only. See the
[current priorities](ongoing-work-streams.md) and [deferred roadmap](personal-context-roadmap.md)
before starting further work.
