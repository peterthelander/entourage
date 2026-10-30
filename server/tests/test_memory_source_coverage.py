from copy import deepcopy
from pathlib import Path
import sys
import unittest

from entourage_server.knowledge import ReviewedKnowledge

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from memory_source_coverage import article_source_coverage


class SourceCoverageTests(unittest.TestCase):
    def test_discloses_unread_originals_without_changing_article_or_adding_prose(self):
        bundle = ReviewedKnowledge(ROOT / "ingestion/fixtures/source-binding-memory")
        original = bundle.read_article("cedar-pantry")
        before = deepcopy(original)
        result = article_source_coverage(bundle, original)
        self.assertEqual(original, before)
        self.assertEqual({k: v for k, v in result.items() if k != "source_coverage"}, before)
        sources = result["source_coverage"]["sources"]
        self.assertEqual(len(sources), len({e["record_id"] for c in before["article"]["claims"] for e in c["evidence"]}))
        for item in sources:
            record = bundle.records[item["record_id"]]
            self.assertEqual(item["total_characters"], len(record["text"]))
            self.assertEqual(item["observed_at"], record["observed_at"])
            self.assertEqual(set(item), {"record_id", "observed_at", "total_characters", "full_source_text_provided"})

    def test_complete_source_flag_requires_entire_original_in_a_quote(self):
        bundle = ReviewedKnowledge(ROOT / "ingestion/fixtures/source-binding-memory")
        original = bundle.read_article("cedar-pantry")
        evidence = original["article"]["claims"][0]["evidence"][0]
        identity = evidence["record_id"]
        bundle.records[identity]["text"] = "Header\n\n" + evidence["quote"] + "\n\nAdditional qualification."
        incomplete = article_source_coverage(bundle, original)["source_coverage"]["sources"]
        self.assertFalse(next(s for s in incomplete if s["record_id"] == identity)["full_source_text_provided"])
        evidence["quote"] = bundle.records[identity]["text"]
        complete = article_source_coverage(bundle, original)["source_coverage"]["sources"]
        self.assertTrue(next(s for s in complete if s["record_id"] == identity)["full_source_text_provided"])


if __name__ == "__main__":
    unittest.main()
