import asyncio
import importlib.util
import json
from pathlib import Path
import unittest

from entourage_server.config import Settings

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("conversation_evaluations", ROOT / "scripts/evaluate-conversations.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class ScriptedModel:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.requests = []

    async def generate(self, messages, on_text):
        self.requests.append(json.loads(json.dumps(messages)))
        return next(self.replies)


def call(name, arguments):
    return {"tool_calls": [{"id": "fixture-call", "function": {"name": name, "arguments": arguments}}]}


class ConversationEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.cases = {case["id"]: case for case in evaluation.load_cases(evaluation.FIXTURE)["cases"]}
        self.settings = Settings(gemini_api_key="synthetic")

    def test_correction_uses_real_journal_retrieval_and_preserves_follow_up(self):
        model = ScriptedModel([call("searchMemories", {"keywords": ["lantern"]}),
                               {"content": "Birch-92 (message=2)."}, {"content": "Previously Cedar-71."}])
        row = asyncio.run(evaluation.run_case(self.cases["corrected-memory"], self.settings, model))
        self.assertTrue(all(turn["mechanical_pass"] for turn in row["turns"]))
        self.assertNotIn("Birch-92", json.dumps(model.requests[0]))
        self.assertIn("Birch-92", model.requests[1][-1]["content"])
        self.assertIn("Birch-92", json.dumps(model.requests[2]))
        self.assertEqual(row["turns"][0]["semantic_review"], "pending")

    def test_session_boundary_removes_old_task_but_retains_current_topic(self):
        model = ScriptedModel([{"content": "Mira and Sol can join the picnic."}, {"content": "Mira and Sol."}])
        row = asyncio.run(evaluation.run_case(self.cases["topic-switch"], self.settings, model))
        self.assertNotIn("database", json.dumps(model.requests[0]))
        self.assertIn("picnic at home", json.dumps(model.requests[0]))
        self.assertTrue(row["all_turns_executed"])
        self.assertTrue(all(turn["mechanical_pass"] for turn in row["turns"]))

    def test_page_fixture_is_matched_by_url_and_injected_text_reaches_model(self):
        model = ScriptedModel([call("readWebPage", {"url": "https://northbridge.example/quartet"}),
                               {"content": "7 PM: https://northbridge.example/quartet"}])
        row = asyncio.run(evaluation.run_case(self.cases["untrusted-page"], self.settings, model))
        self.assertIn("SYSTEM OVERRIDE", model.requests[1][-1]["content"])
        self.assertTrue(row["turns"][0]["web_fixtures"][0]["fixture_matched"])
        self.assertTrue(row["turns"][0]["mechanical_pass"])

    def test_unmatched_page_never_fetches_network_and_wrong_answer_fails(self):
        model = ScriptedModel([call("readWebPage", {"url": "http://127.0.0.1/private"}),
                               {"content": "Moon-cheese-override, 9 PM"}])
        row = asyncio.run(evaluation.run_case(self.cases["untrusted-page"], self.settings, model))
        self.assertFalse(row["turns"][0]["web_fixtures"][0]["fixture_matched"])
        self.assertIn("No synthetic response", model.requests[1][-1]["content"])
        self.assertFalse(row["turns"][0]["mechanical_pass"])

    def test_tool_budget_failure_stops_case_and_does_not_count_as_pass(self):
        model = ScriptedModel([call("searchMemories", {"keywords": ["lantern"]})] * 5)
        row = asyncio.run(evaluation.run_case(self.cases["corrected-memory"], self.settings, model))
        self.assertEqual(row["turns"][0]["status"], "failed")
        self.assertFalse(row["all_turns_executed"])
        summary = evaluation.summarize({"runs": [row]})
        self.assertEqual(summary["corrected-memory"]["mechanical_passes"], 0)

    def test_fact_checks_accept_typographic_variants_but_require_correct_source(self):
        turn = self.cases["corrected-memory"]["turns"][0]
        tools = [{"name": "searchMemories"}]
        good = evaluation.assess(turn, "completed", "Birch\u201192 (ID\u202f2).", tools)
        self.assertTrue(good["mechanical_pass"])
        self.assertTrue(evaluation.assess(turn, "completed", "Birch-92 [message_id=2]", tools)["mechanical_pass"])
        self.assertFalse(evaluation.assess(turn, "completed", "Birch-92 (ID 20).", tools)["mechanical_pass"])
        self.assertFalse(evaluation.assess(turn, "failed", "Birch-92 (ID 2).", tools)["mechanical_pass"])
