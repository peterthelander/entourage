import asyncio
import importlib.util
import io
import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import httpx

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

    def test_production_worker_combines_conversations_and_reviewed_imports(self):
        from test_knowledge import reviewed_fixture
        from entourage_server.knowledge_bundle import KnowledgeBundle
        with TemporaryDirectory() as directory:
            bundle = reviewed_fixture(Path(directory) / "bundle")
            snapshot = KnowledgeBundle(bundle).snapshot
            case = {"id": "knowledge-routing", "rubric": ["Read imported evidence"], "turns": [
                {"text": "What changed for the garden workday?", "created_at": "2026-10-22T19:00:00+00:00"}]}
            model = ScriptedModel([
                call("searchMemories", {"keywords": ["community garden workday", "date change"]}),
                call("readKnowledgeArticle", {"slug": "community-garden", "snapshot": snapshot}),
                {"content": "The proposed date changed from May 3 to May 10; attendance is unknown."}])
            row = asyncio.run(evaluation.run_case(case, self.settings, model, knowledge_bundle=bundle))
            self.assertEqual(row["turns"][0]["status"], "completed")
            search = json.loads(model.requests[1][-1]["content"])
            self.assertEqual(search["imported_memory"]["results"][0]["slug"], "community-garden")
            self.assertEqual(search["imported_memory"]["match_mode"], "ranked_partial")
            self.assertIn("conversation_memory", search)
            article = json.loads(model.requests[2][-1]["content"])
            self.assertTrue(article["article"]["unknowns"])
            self.assertEqual([t["name"] for t in row["turns"][0]["tools"]], ["searchMemories", "readKnowledgeArticle"])

    def test_recent_imported_evidence_survives_followup_but_not_inactivity(self):
        from test_knowledge import reviewed_fixture
        from entourage_server.knowledge_bundle import KnowledgeBundle
        with TemporaryDirectory() as directory:
            bundle = reviewed_fixture(Path(directory) / "bundle")
            snapshot = KnowledgeBundle(bundle).snapshot
            case = {"id": "evidence-followup", "rubric": ["Retain evidence within session"], "turns": [
                {"text": "Read garden history", "created_at": "2026-10-22T19:00:00+00:00"},
                {"text": "Did I attend?", "created_at": "2026-10-22T19:01:00+00:00"},
                {"text": "After a pause", "created_at": "2026-10-22T22:00:00+00:00"}]}
            model = ScriptedModel([
                call("readKnowledgeArticle", {"slug": "community-garden", "snapshot": snapshot}),
                {"content": "The proposed date changed."}, {"content": "Attendance is unknown."}, {"content": "A new session."}])
            row = asyncio.run(evaluation.run_case(case, self.settings, model, knowledge_bundle=bundle))
            followup = model.requests[2]
            self.assertTrue(any(m.get("role") == "tool" and "Attendance and whether" in m.get("content", "") for m in followup))
            after_pause = model.requests[3]
            self.assertFalse(any(m.get("role") == "tool" for m in after_pause))
            self.assertTrue(row["all_turns_executed"])

    def test_correction_uses_real_journal_retrieval_and_preserves_follow_up(self):
        model = ScriptedModel([call("searchMemories", {"keywords": ["lantern"]}),
                               {"content": "Birch-92 (message=2)."}, {"content": "Previously Cedar-71."}])
        row = asyncio.run(evaluation.run_case(self.cases["corrected-memory"], self.settings, model))
        self.assertTrue(all(turn["mechanical_pass"] for turn in row["turns"]))
        self.assertNotIn("Birch-92", json.dumps(model.requests[0]))
        self.assertIn("Birch-92", model.requests[1][-1]["content"])
        self.assertEqual(json.loads(model.requests[1][-1]["content"])["results"][0]["message_id"], 2)
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

    def test_comparison_fixture_separates_source_diagnostics_from_product_answers(self):
        fixture = evaluation.load_cases(ROOT / 'server/tests/fixtures/personal-agent-comparison.json')
        self.assertEqual(len(fixture['cases']), 30)
        self.assertGreaterEqual(sum(len(case['turns']) > 1 for case in fixture['cases']), 10)
        case = next(c for c in fixture['cases'] if c['id'] == 'recall-after-pause')
        result = evaluation.assess(case['turns'][0], 'completed', 'Mira and Sol are coming.', [{'name': 'searchMemories'}])
        self.assertTrue(result['mechanical_pass'])
        self.assertFalse(all(result['diagnostics'].values()))

    def test_live_runner_records_engine_and_sends_requested_reasoning_effort(self):
        requests = []
        def handle(request):
            if request.method == "GET":
                return httpx.Response(200, json={"build_info": "test-build", "chat_template": "template",
                                                "default_generation_settings": {"n_ctx": 16384}})
            requests.append(json.loads(request.content))
            return httpx.Response(200, text='data: {"choices":[{"delta":{"content":"Done"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n')

        async def fake_case(case, settings, model):
            await model.generate([], lambda _: None)
            return {"case": case["id"], "all_turns_executed": True,
                    "turns": [{"mechanical_pass": True}]}

        with TemporaryDirectory() as directory:
            args = SimpleNamespace(reasoning_effort="medium", repeats=1, output=Path(directory) / "report.json")
            report = {"runs": []}
            client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
            with patch("httpx.AsyncClient", return_value=client), patch.object(evaluation, "run_case", side_effect=fake_case):
                asyncio.run(evaluation.evaluate(args, {"cases": [{"id": "test"}]},
                                                Settings(inference_provider="llama_cpp"), report))
            self.assertEqual(report["engine_before"]["build_info"], "test-build")
            self.assertEqual(report["engine_after"], report["engine_before"])
            self.assertEqual(requests[0]["reasoning_effort"], "medium")
            self.assertEqual(len(report["runs"]), 1)

    def test_cli_rejects_reasoning_override_for_ollama_before_any_live_call(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            argv = ["evaluate-conversations.py", "--live", "--reasoning-effort", "medium", "--output", str(output)]
            with patch("sys.argv", argv), patch("sys.stderr", io.StringIO()), \
                    patch.object(evaluation, "live_settings", return_value=Settings()), \
                    patch.object(evaluation, "evaluate") as live:
                with self.assertRaises(SystemExit) as error:
                    evaluation.main()
            self.assertEqual(error.exception.code, 2)
            live.assert_not_called()
            self.assertFalse(output.exists())

    def test_provider_http_failure_stops_batch_and_preserves_safe_diagnostics(self):
        class Denied:
            async def generate(self, messages, on_text):
                from evaluation_gemini import GeminiHTTPError
                raise GeminiHTTPError(403)
        with TemporaryDirectory() as directory:
            args = SimpleNamespace(reasoning_effort='low', repeats=3, gemini_model='test',
                                   output=Path(directory) / 'report.json')
            report = {'runs': []}
            with patch.object(evaluation, 'GeminiEvaluation', return_value=Denied()), \
                    patch.object(evaluation, 'evaluation_key', return_value='private-test-key'):
                asyncio.run(evaluation.evaluate(args, {'cases': [self.cases['missing-memory']]}, self.settings, report))
            self.assertEqual(len(report['runs']), 1)
            failure = report['runs'][0]['turns'][0]['inference_failures'][0]
            self.assertEqual(failure['http_status'], 403)
            self.assertIn('aborted', report)
            self.assertNotIn('private-test-key', json.dumps(report))

    def test_offline_gemini_preparation_never_loads_credentials(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'prepared.json'
            with patch('sys.argv', ['evaluate-conversations.py', '--gemini-model', 'test', '--output', str(output)]), \
                    patch.object(evaluation, 'evaluation_key', side_effect=AssertionError('must not read key')), \
                    patch.object(evaluation, 'live_settings', side_effect=AssertionError('must not read config')):
                self.assertEqual(evaluation.main(), 0)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertFalse(report['live'])
            self.assertEqual(report['runs'], [])
