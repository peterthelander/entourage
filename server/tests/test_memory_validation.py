import asyncio
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from entourage_server.config import Settings
from test_knowledge import reviewed_fixture

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from memory_validation import freeze, read, review_template, summarize_review, verify, write_new


class MemoryValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bundle = reviewed_fixture(self.root / "bundle")
        self.fixture = self.root / "fixture.json"
        self.expected = self.root / "expected.json"
        write_new(self.fixture, {"version": 1, "cases": [{"id": "garden", "rubric": ["Preserve correction"],
                  "turns": [{"text": "When?", "created_at": "2026-10-23T10:00:00+00:00"},
                            {"text": "Did I attend?", "created_at": "2026-10-23T10:01:00+00:00"}]}]})
        write_new(self.expected, {"version": 1, "created_before_inference": True, "independent_review": False,
                  "cases": [{"id": "garden", "criteria": [
                      {"turn": 1, "expected": "Corrected date", "source_ids": ["garden-correction"]},
                      {"turn": 2, "expected": "Attendance unknown", "source_ids": ["garden-invite"]}]}]})
        self.settings = Settings()

    def manifest(self):
        return freeze(ROOT, self.bundle, self.fixture, self.expected, self.settings,
                      providers=["local"], repeats=2)

    def test_committed_source_binding_regression_is_reviewed_and_fully_specified(self):
        fixtures = ROOT / "ingestion/fixtures"
        manifest = freeze(ROOT, fixtures / "source-binding-memory",
                          fixtures / "source-binding-conversations.json",
                          fixtures / "source-binding-expectations.json", self.settings,
                          providers=["local"], repeats=2)
        verify(manifest, self.settings)
        self.assertFalse(manifest["independent_review"])
        self.assertEqual(len(manifest["planned_runs"]["case_ids"]), 3)

    def test_freeze_rejects_changed_sources_settings_and_incomplete_expectations(self):
        manifest = self.manifest()
        verify(manifest, self.settings)
        self.assertNotIn("gemini_api_key", manifest["settings"])
        from dataclasses import replace
        with self.assertRaisesRegex(ValueError, "setting changed"):
            verify(manifest, replace(self.settings, context_tokens=16384))
        self.fixture.write_text('{}')
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            verify(manifest)
        expected = read(self.expected)
        expected["cases"][0]["criteria"].pop()
        self.expected.write_text(json.dumps(expected))
        write_new(self.root / "replacement.json", {"version": 1, "cases": [{"id": "garden", "turns": [{}, {}]}]})
        with self.assertRaisesRegex(ValueError, "every turn"):
            freeze(ROOT, self.bundle, self.root / "replacement.json", self.expected, self.settings,
                   providers=["local"], repeats=2)

    def report(self):
        path = self.root / "report.json"
        write_new(path, {"status": "failed", "runs": [{"provider": "local", "repeat": 1, "case": "garden",
                  "turns": [{"turn": 1, "status": "failed", "answer": None}]}]})
        return path

    def test_review_preserves_failed_and_unattempted_turns_and_binds_report(self):
        report = self.report()
        template = review_template(report, self.expected)
        self.assertEqual([r["execution_status"] for r in template["rows"]], ["failed", "not_run"])
        template["reviewer"] = "Test reviewer"
        template["rows"][0].update(verdict="pass", notes="Cannot pass")
        review = self.root / "review.json"
        write_new(review, template)
        with self.assertRaisesRegex(ValueError, "cannot pass"):
            summarize_review(report, self.expected, review)
        template["rows"][0]["verdict"] = "fail"
        review.write_text(json.dumps(template))
        result = summarize_review(report, self.expected, review)
        self.assertFalse(result["review_complete"])
        self.assertEqual(result["semantic_counts"], {"fail": 1, "pending": 1})
        report.write_text(json.dumps({"status": "complete", "runs": []}))
        with self.assertRaisesRegex(ValueError, "does not match"):
            summarize_review(report, self.expected, review)

    def test_missing_planned_runs_cannot_be_hidden_by_completed_review(self):
        from memory_validation import digest
        manifest = self.manifest()
        manifest_path = self.root / "freeze.json"
        write_new(manifest_path, manifest)
        report = self.report()
        data = read(report)
        data["freeze_manifest_sha256"] = digest(manifest_path)
        report.write_text(json.dumps(data))
        template = review_template(report, self.expected, manifest_path=manifest_path)
        template["reviewer"] = "Test reviewer"
        for row in template["rows"]:
            row.update(verdict="fail", notes="Execution did not complete")
        review = self.root / "review.json"
        write_new(review, template)
        result = summarize_review(report, self.expected, review, manifest_path=manifest_path)
        self.assertFalse(result["review_complete"])
        self.assertEqual(result["missing_runs"], [{"provider": "local", "repeat": 2, "case": "garden"}])

    def test_report_plan_preserves_missing_runs_without_a_freeze_manifest(self):
        report = self.report()
        data = read(report)
        data["planned_runs"] = {"providers": ["local"], "repeats": 2, "case_ids": ["garden"]}
        report.write_text(json.dumps(data))
        template = review_template(report, self.expected)
        template["reviewer"] = "Reviewer"
        for row in template["rows"]:
            row.update(verdict="fail", notes="Execution did not complete")
        review = self.root / "review.json"
        write_new(review, template)
        result = summarize_review(report, self.expected, review)
        self.assertFalse(result["review_complete"])
        self.assertEqual(len(result["missing_runs"]), 1)

    def test_duplicate_runs_and_review_identity_changes_are_rejected(self):
        report = self.report()
        data = read(report)
        data["runs"].append(data["runs"][0])
        report.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "Duplicate case run"):
            review_template(report, self.expected)
        data["runs"].pop()
        report.write_text(json.dumps(data))
        template = review_template(report, self.expected)
        template["reviewer"] = "Reviewer"
        template["rows"][0]["expected"] = "Changed expectation"
        review = self.root / "review.json"
        write_new(review, template)
        with self.assertRaisesRegex(ValueError, "identity"):
            summarize_review(report, self.expected, review)

    def test_runner_persists_failures_and_retains_completed_cases(self):
        spec = importlib.util.spec_from_file_location("knowledge_runner", ROOT / "scripts/evaluate-knowledge.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        args = SimpleNamespace(bundle=self.bundle, fixture=self.fixture, output=self.root / "run",
                               providers=["local"], repeats=2, freeze_manifest=None)

        async def trials(args, settings, fixture, report, save, manifest):
            report["runs"].append({"case": "garden", "repeat": 1})
            report["active_run"] = {"case": "garden", "repeat": 2, "active_turn": {"inputs": [[{"role": "user", "content": "Pending question"}]]}}
            save()
            raise RuntimeError("Simulated transport setup failure")

        with patch.object(runner, "run_trials", trials):
            with self.assertRaises(RuntimeError):
                asyncio.run(runner.run(args))
        result = read(args.output / "report.json")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertEqual(len(result["runs"]), 1)
        self.assertEqual(result["active_run"]["repeat"], 2)
        self.assertIn("finished_at", result)

    def test_runner_rejects_frozen_argument_drift_before_creating_output(self):
        spec = importlib.util.spec_from_file_location("knowledge_runner_frozen", ROOT / "scripts/evaluate-knowledge.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        settings = runner.evaluation.live_settings()
        manifest = freeze(ROOT, self.bundle, self.fixture, self.expected, settings,
                          providers=["gemini"], repeats=2, gemini_model="frozen-reference")
        path = self.root / "manifest.json"
        write_new(path, manifest)
        args = SimpleNamespace(bundle=self.bundle, fixture=self.fixture, output=self.root / "rejected",
                               providers=["gemini"], repeats=2, gemini_model="different-reference", freeze_manifest=path)
        with self.assertRaisesRegex(ValueError, "arguments do not match"):
            asyncio.run(runner.run(args))
        self.assertFalse(args.output.exists())


if __name__ == "__main__":
    unittest.main()
