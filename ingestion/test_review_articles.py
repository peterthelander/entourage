import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from review_articles import plan_checks, prepare, validate_response  # noqa: E402


class ArticleSupportReviewTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent / "fixtures"
        self.records = [json.loads(line) for line in (root / "memory-records.jsonl").read_text().splitlines()]
        self.plan = json.loads((root / "memory-plan.json").read_text())

    def test_reviews_titles_descriptions_claims_and_unknowns(self):
        records, checks = plan_checks(self.records, self.plan)
        kinds = {row["kind"] for row in checks}
        self.assertTrue({"title", "description", "source_statement", "suggestion", "unknown"} <= kinds)
        messages = prepare(records, checks)
        self.assertNotIn('"source":', messages[1]["content"])
        payload = json.loads(messages[1]["content"])
        self.assertIn("garden-invite", payload["sources"])

    def test_complete_reviews_only_and_no_duplicate_ids(self):
        _, checks = plan_checks(self.records, self.plan)
        result = {"checks": [{"id": c["id"], "verdict": "uncertain", "reason": "Needs review"} for c in checks]}
        self.assertEqual(validate_response(json.dumps(result), checks), result)
        for bad in ([result["checks"][0]] * len(checks), result["checks"][:-1], [None] * len(checks)):
            with self.assertRaises(ValueError):
                validate_response(json.dumps({"checks": bad}), checks)
        with self.assertRaises(ValueError):
            validate_response("[]", checks)

    def test_rejects_cross_record_or_invented_quotes(self):
        records, checks = plan_checks(self.records, self.plan)
        checks = [c for c in checks if "evidence" in c]
        bad = copy.deepcopy(checks)
        bad[0]["evidence"][0]["quote"] = "They attended and paid."
        with self.assertRaises(ValueError):
            prepare(records, bad)
        bad = copy.deepcopy(checks)
        bad[0]["record_ids"] = ["bicycle-repair"]
        with self.assertRaises(ValueError):
            prepare(records, bad)

    def test_calibration_has_positive_and_negative_controls_with_literal_evidence(self):
        root = Path(__file__).parent / "fixtures"
        records = {r["id"]: r for r in map(json.loads, (root / "article-support-records.jsonl").read_text().splitlines())}
        cases = json.loads((root / "article-support-cases.json").read_text())["checks"]
        self.assertEqual({case["expected"] for case in cases}, {"supported", "unsupported"})
        checks = [{key: value for key, value in case.items() if key != "expected"} for case in cases]
        payload = json.loads(prepare(records, checks)[1]["content"])
        self.assertTrue(all("expected" not in c for c in payload["checks"]))
