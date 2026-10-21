# Entourage: Recursive Self-Improvement & Autonomous Loop Specification

Status: Proposal; autonomous development loop is not implemented. Updated: October 21, 2026.

The paths and schemas below describe intended work. `tests/eval_scenarios.yaml`
does not exist; the implemented baseline instead uses synthetic JSON fixtures and
the [conversation evaluation runner](experiments/conversation-evaluations.md).
It records mechanical checks separately from required human semantic review;
it does not guarantee hallucination-free answers or authorize autonomous commits.
The autonomous loop has not been enabled. The current
memory design proposal is [the personal context roadmap](personal-context-roadmap.md);
current journal behavior is documented in [the reference](reference/memory-journals.md).
The proposed log format below is not the existing generated-journal format.

## 1. Objective
Establish a safe, autonomous local development loop to iterate on the *Entourage* codebase and knowledge base without human babysitting, leveraging local high-memory hardware (M2 Max, 64GB) and free local LLM inference.

---

## 2. The Core Risk: Test-Green Hallucination Laundering
* **The Problem:** A passing unit test suite only proves mechanical correctness. An autonomous loop can easily pass all technical assertions while quietly drifting away from architectural intent, introducing weird abstractions, or corrupting vault semantics.
* **The Solution:** A dual-layer evaluation architecture combining hard deterministic linters with semantic golden test suites.

---

## 3. The Dual-Layer Evaluation Architecture

### Layer 1: Deterministic Guardrails (The Floor)
* **Syntax & Linting:** Code must pass standard linters and type checkers.
* **Schema Validation:** Markdown vaults and log formats (`[timestamp] [[source]] | description | #keywords`) must strictly adhere to vault schemas.
* **Action:** If Layer 1 fails, the iteration halts instantly and rolls back.

### Layer 2: Semantic Regression Testing & Self-Judgment (The Compass)
* **The Golden Test Suite (`tests/eval_scenarios.yaml`):** A static file containing 5–10 baseline queries and expected retrieval behaviors (e.g., historical lookups, concept queries, constraint checks).
* **Evaluation Pass:** After a code change, a test runner feeds the queries to the local model, verifying:
  1. Accurate citation of source files.
  2. Complete absence of unsupported hallucinated details.
  3. Alignment with core architectural goals.
* **Action:** If the semantic score drops compared to baseline, the iteration is rejected.

---

## 4. Execution Workflow for Local Coding Agents
1. **Pull Context:** Read current codebase, [personal context roadmap](personal-context-roadmap.md), and [technical backlog](technical-debt.md).
2. **Implement Increment:** Propose a single, tightly scoped modification.
3. **Run Layer 1 (Deterministic):** Verify compilation, tests, and formatting.
4. **Run Layer 2 (Semantic Eval):** Execute the golden test prompts against the updated system.
5. **Commit or Revert:** If both layers pass, commit the change with a descriptive message. If either fails, analyze the failure, revert, and retry.
