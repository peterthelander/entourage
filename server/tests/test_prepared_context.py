import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from entourage_server.config import Settings
from entourage_server.knowledge import ReviewedKnowledge

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from memory_context import prepare_context

BUNDLE = ROOT / "ingestion/fixtures/question-context-memory"


class PreparedContextTests(unittest.TestCase):
    def setUp(self):
        self.bundle = ReviewedKnowledge(BUNDLE)
        self.wire = [
            {"role": "assistant", "content": "", "tool_calls": [{"id": "article", "type": "function", "function": {
                "name": "readKnowledgeArticle", "arguments": json.dumps({"slug": "bicycle-maintenance", "snapshot": self.bundle.snapshot})}}]},
            {"role": "tool", "tool_name": "readKnowledgeArticle", "tool_call_id": "article",
             "content": json.dumps(self.bundle.read_article("bicycle-maintenance"))}]
        self.history = [
            {"role": "user", "text": "Read the bicycle maintenance article.", "created_at": "2026-10-28T12:00:00+00:00"},
            {"role": "assistant", "text": json.dumps(self.wire), "wire_messages": self.wire, "created_at": "2026-10-28T12:00:00+00:00"},
            {"role": "assistant", "text": "Brake pads and chain adjustment.", "created_at": "2026-10-28T12:00:00+00:00"}]

    def test_dates_and_followup_originals_preserve_complete_wire_pairs(self):
        messages = prepare_context("What does the receipt require for a rebate?", self.history, Settings(knowledge_enabled=True),
                                   created_at="2026-10-28T12:01:00+00:00", knowledge_bundle=self.bundle)
        self.assertEqual(messages[2:4], self.wire)
        self.assertIn("2026-10-28T12:01:00+00:00", messages[-1]["content"])
        self.assertIn("Additional original historical evidence", messages[-1]["content"])
        self.assertIn("Rebate requests require the original receipt", messages[-1]["content"])
        no_match = prepare_context("Receipt?", self.history, Settings(knowledge_enabled=True),
                                   created_at="2026-10-28T12:01:00+00:00", knowledge_bundle=self.bundle)
        self.assertNotIn("Additional original historical evidence", no_match[-1]["content"])

    def test_session_boundary_and_disabled_imports_never_add_old_source_context(self):
        paused = prepare_context("What about a rebate?", self.history, Settings(knowledge_enabled=True),
                                 created_at="2026-10-29T12:00:00+00:00", knowledge_bundle=self.bundle)
        self.assertEqual([m["role"] for m in paused], ["system", "user"])
        self.assertNotIn("Additional original historical evidence", paused[-1]["content"])
        disabled = prepare_context("What about a rebate?", self.history, Settings(knowledge_enabled=False),
                                   created_at="2026-10-28T12:01:00+00:00", knowledge_bundle=self.bundle)
        self.assertNotIn("Additional original historical evidence", disabled[-1]["content"])

    def test_budget_drops_whole_old_exchanges_but_preserves_latest_request(self):
        settings = Settings(context_tokens=2048, max_output_tokens=512, knowledge_enabled=True)
        prompt = "What about a rebate?"
        messages = prepare_context(prompt, self.history, settings, created_at="2026-10-28T12:01:00+00:00",
                                   knowledge_bundle=self.bundle)
        self.assertEqual([m["role"] for m in messages], ["system", "user"])
        self.assertTrue(messages[-1]["content"].endswith(prompt))
        self.assertNotIn("Additional original historical evidence", messages[-1]["content"])

    def test_opt_in_diagnostic_adds_followup_evidence_and_default_worker_does_not(self):
        spec = importlib.util.spec_from_file_location("prepared_diagnosis", ROOT / "scripts/diagnose-memory.py")
        diagnosis = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(diagnosis)
        snapshot, assertions = self.bundle.snapshot, self

        class Model:
            calls = 0
            candidate = True

            async def generate(self, messages, on_text):
                self.calls += 1
                user = next(m for m in reversed(messages) if m["role"] == "user")
                if self.candidate:
                    assertions.assertIn("Conversation message recorded at", user["content"])
                else:
                    assertions.assertNotIn("Conversation message recorded at", user["content"])
                    assertions.assertNotIn("Additional original historical evidence", user["content"])
                if self.calls == 1:
                    assertions.assertNotIn("Additional original historical evidence", messages[-1]["content"])
                    return {"content": "", "tool_calls": [{"id": "article", "type": "function", "function": {
                        "name": "readKnowledgeArticle", "arguments": json.dumps({"slug": "bicycle-maintenance", "snapshot": snapshot})}}]}
                if self.calls == 3 and self.candidate:
                    assertions.assertIn("Additional original historical evidence", messages[-1]["content"])
                    assertions.assertIn("Rebate requests require the original receipt", messages[-1]["content"])
                return {"content": "Recorded receipt facts.", "tool_calls": []}

        case = {"id": "prepared-worker", "rubric": ["Use original evidence"], "turns": [
            {"text": "Read the bicycle maintenance article.", "created_at": "2026-10-28T12:00:00+00:00"},
            {"text": "What does the receipt require for a rebate?", "created_at": "2026-10-28T12:01:00+00:00"}]}
        model = Model()
        row = asyncio.run(diagnosis.run_diagnostic(case, Settings(), model, BUNDLE, "retrieval_context"))
        self.assertEqual(model.calls, 3)
        self.assertTrue(all(t["status"] == "completed" for t in row["turns"]))
        self.assertEqual(row["turns"][1]["tools"], [])
        baseline = Model()
        baseline.candidate = False
        row = asyncio.run(diagnosis.run_diagnostic(case, Settings(), baseline, BUNDLE, "retrieval"))
        self.assertEqual(baseline.calls, 3)
        self.assertTrue(all(t["status"] == "completed" for t in row["turns"]))


if __name__ == "__main__":
    unittest.main()
