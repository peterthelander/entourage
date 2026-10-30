from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from entourage_server.knowledge import ReviewedKnowledge

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from memory_overview import MAX_PLAN_BYTES, load_overview, overview_evidence, validate_overview


class MemoryOverviewTests(unittest.TestCase):
    def setUp(self):
        self.bundle = ReviewedKnowledge(ROOT / "ingestion/fixtures/memory-overview-memory")
        self.plan = json.loads((ROOT / "ingestion/fixtures/memory-overview.json").read_text())

    def test_controls_have_identical_evidence_and_preserve_unknowns_and_dates(self):
        flat = overview_evidence(self.bundle, self.plan, "flat_overview")[0]["result"]
        themed = overview_evidence(self.bundle, self.plan, "thematic_overview")[0]["result"]
        self.assertEqual(flat, {k: v for k, v in themed.items() if k not in {
            "themes", "detail_only", "grouping_author", "grouping_status"}})
        article = themed["articles"]["community-garden"]
        self.assertEqual(article["unknowns"], self.bundle.articles["community-garden"]["unknowns"])
        evidence_id = article["claims"][0]["evidence"][1]
        self.assertEqual(themed["evidence"][evidence_id]["observed_at"], "2025-04-02T10:00:00-04:00")
        self.assertEqual(flat["evidence_coverage"]["index_only_articles"], ["bicycle-maintenance"])
        inventory = overview_evidence(self.bundle, self.plan, "inventory")[0]["result"]
        self.assertNotIn("articles", inventory)
        self.assertIn("index only; no article or source text", inventory["scope"])

    def test_plan_loader_bounds_input_before_parsing(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "overview.json"
            path.write_bytes(b" " * (MAX_PLAN_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "size limit"):
                load_overview(path)
            path.write_text(json.dumps(self.plan), encoding="utf-8")
            self.assertEqual(load_overview(path), self.plan)

    def test_selected_overview_withholds_index_without_losing_inspected_evidence(self):
        flat = overview_evidence(self.bundle, self.plan, "flat_overview")[0]["result"]
        selected = overview_evidence(self.bundle, self.plan, "selected_overview")[0]["result"]
        self.assertEqual(selected["inventory"], [])
        self.assertIn("uninspected index entries are withheld", selected["scope"])
        self.assertEqual({k: v for k, v in flat.items() if k not in {"inventory", "scope"}},
                         {k: v for k, v in selected.items() if k not in {"inventory", "scope"}})

    def test_detail_control_adds_complete_evidence_in_both_conditions(self):
        for mode in ("flat_overview", "thematic_overview"):
            result = overview_evidence(self.bundle, self.plan, mode, ["bicycle-maintenance"])[0]["result"]
            self.assertEqual(result["evidence_coverage"]["index_only_articles"], [])
            self.assertEqual(self.expand_article(result, "bicycle-maintenance"),
                             self.bundle.read_article("bicycle-maintenance")["article"])

    @staticmethod
    def expand_article(packet, slug):
        article = deepcopy(packet["articles"][slug])
        for claim in article["claims"]:
            claim["evidence"] = [packet["evidence"][identity] for identity in claim["evidence"]]
        return article

    def test_normalization_preserves_every_selected_claim_and_evidence_byte(self):
        result = overview_evidence(self.bundle, self.plan, "thematic_overview")[0]["result"]
        for slug in result["articles"]:
            self.assertEqual(self.expand_article(result, slug), self.bundle.read_article(slug)["article"])
        excerpts = list(result["evidence"].values())
        self.assertEqual(len(excerpts), len({(e["record_id"], e["quote"]) for e in excerpts}))

    def test_stale_plan_missing_duplicate_and_unknown_articles_fail_closed(self):
        for update in ({"snapshot": "stale"}, {"detail_only": []},
                       {"detail_only": ["bicycle-maintenance", "community-garden"]},
                       {"detail_only": ["not-real"]}, {"version": True}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                validate_overview({**self.plan, **update}, self.bundle)

    def test_significance_is_bound_to_source_claims(self):
        for ref in ({"slug": "community-garden", "claim": 1},
                    {"slug": "community-garden", "claim": True},
                    {"slug": "bicycle-maintenance", "claim": 0},
                    {"slug": "community-garden", "claim": 100}):
            plan = deepcopy(self.plan)
            plan["themes"][0]["signals"][0]["supports"] = [ref]
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                validate_overview(plan, self.bundle)

    def test_size_budget_is_utf8_bytes_and_never_silently_truncates(self):
        with patch("memory_overview.MAX_BYTES", 100), self.assertRaisesRegex(ValueError, "budget"):
            overview_evidence(self.bundle, self.plan, "thematic_overview")

    def test_runner_uses_same_plan_for_broad_and_detail_followups(self):
        spec = importlib.util.spec_from_file_location("overview_diagnostic", ROOT / "scripts/diagnose-memory.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        evidence = runner.supplied_evidence(self.bundle, {"diagnostic_articles": ["bicycle-maintenance"]},
                                            "thematic_overview", self.plan)
        self.assertIn("bicycle-maintenance", evidence[0]["result"]["articles"])
        with self.assertRaises(ValueError):
            runner.supplied_evidence(self.bundle, {}, "thematic_overview")

    def test_fictional_questions_have_source_backed_per_turn_expectations(self):
        from entourage_server.config import Settings
        from memory_validation import freeze, verify
        fixtures = ROOT / "ingestion/fixtures"
        manifest = freeze(ROOT, fixtures / "memory-overview-memory",
                          fixtures / "memory-overview-conversations.json",
                          fixtures / "memory-overview-expectations.json", Settings(),
                          providers=["local"], repeats=2)
        verify(manifest)
        self.assertFalse(manifest["independent_review"])
        self.assertEqual(manifest["planned_runs"]["case_ids"],
                         ["broad-to-specific", "importance-challenge", "attribution-and-current-status"])

    def test_new_summary_prose_and_unsupported_significance_fields_are_rejected(self):
        for key in ("summary", "importance_score"):
            plan = deepcopy(self.plan)
            plan["themes"][0][key] = "unsupported factual assertion"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "theme fields"):
                validate_overview(plan, self.bundle)

    def test_preview_exports_inspectable_packet_and_refuses_to_overwrite(self):
        import contextlib
        import io
        spec = importlib.util.spec_from_file_location("overview_preview", ROOT / "scripts/preview-memory-overview.py")
        preview = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preview)
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "preview.json"
            args = ["preview", "--bundle", str(ROOT / "ingestion/fixtures/memory-overview-memory"),
                    "--overview", str(ROOT / "ingestion/fixtures/memory-overview.json"), "--output", str(output)]
            with patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
                preview.main()
            original = output.read_bytes()
            self.assertEqual(json.loads(original)[0]["result"]["snapshot"], self.bundle.snapshot)
            with patch.object(sys, "argv", args), self.assertRaises(FileExistsError):
                preview.main()
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
