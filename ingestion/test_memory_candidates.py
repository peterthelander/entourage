import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from memory_candidates import render  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


class MemoryCandidateTests(unittest.TestCase):
    def setUp(self):
        self.records = [json.loads(line) for line in (FIXTURES / "memory-records.jsonl").read_text().splitlines()]
        self.plan = json.loads((FIXTURES / "memory-plan.json").read_text())

    def test_multiple_topics_dates_corrections_and_provenance(self):
        files = render(self.records, self.plan)
        self.assertEqual(len([p for p in files if p.startswith("articles/")]), 3)
        self.assertIn("journals/2025-04-01.md", files)
        self.assertNotIn("journals/2025-05-03.md", files)  # Event is not receipt date.
        garden = files["articles/community-garden.md"]
        self.assertIn("May 3", garden)
        self.assertIn("May 10", garden)
        self.assertIn("garden-correction", garden)
        self.assertIn("Source timestamps:", garden)
        self.assertIn("present-day state has not been verified", garden)
        self.assertIn("source timestamps:", files["index.md"])
        self.assertIn(self.records[0]["source"]["sha256"], files["journals/2025-04-01.md"])
        self.assertEqual(files, render(list(reversed(self.records)), self.plan))

    def test_missing_or_fabricated_evidence_is_rejected(self):
        for evidence in ({"record_id": "missing", "quote": "hello"},
                         {"record_id": "garden-invite", "quote": "We attended and paid."}):
            with self.subTest(evidence=evidence):
                plan = copy.deepcopy(self.plan)
                plan["articles"][0]["claims"][0]["evidence"] = [evidence]
                with self.assertRaises(ValueError):
                    render(self.records, plan)

    def test_path_escape_broken_links_and_duplicate_ids_rejected(self):
        for field, value in (("slug", "../../live-vault"), ("links", ["missing"])):
            plan = copy.deepcopy(self.plan)
            plan["articles"][0][field] = value
            with self.assertRaises(ValueError):
                render(self.records, plan)
        with self.assertRaises(ValueError):
            render(self.records + [self.records[0]], self.plan)

    def test_promotions_and_ambiguous_timestamps_rejected(self):
        for field, value in (("labels", ["Category Promotions"]), ("observed_at", "2025-04-01T12:00:00")):
            records = copy.deepcopy(self.records)
            records[0][field] = value
            with self.assertRaises(ValueError):
                render(records, self.plan)


if __name__ == "__main__":
    unittest.main()
