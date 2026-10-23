import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from memory_candidates import build  # noqa: E402
from memory_preview import MemoryPreview  # noqa: E402


class MemoryPreviewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "candidate"
        fixtures = Path(__file__).parent / "fixtures"
        build(fixtures / "memory-records.jsonl", fixtures / "memory-plan.json", self.root)
        self.preview = MemoryPreview(self.root)

    def test_unrelated_topics_and_missing_information(self):
        for query, slug in ((["garden"], "community-garden"), (["bicycle"], "bicycle-maintenance"), (["reading"], "reading-circle-june-2025")):
            result = self.preview.search(query)
            self.assertEqual(result["results"][0]["slug"], slug)
            self.assertEqual(result["status"], "unpublished_candidate")
            article = self.preview.read_article(slug)
            self.assertTrue(article["source_timestamps"])
        self.assertEqual(self.preview.search(["never-mentioned-allergen"])["total_matches"], 0)

    def test_search_read_and_source_pagination_preserve_evidence(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir() if p.is_file()}
        matches = self.preview.search(["moved"], scope="sources")
        identity = matches["results"][0]["record_id"]
        chunk = self.preview.read_source(identity, limit=10)
        parts = [chunk["text"]]
        while chunk["next_offset"] is not None:
            chunk = self.preview.read_source(identity, offset=chunk["next_offset"], limit=10, snapshot=chunk["snapshot"])
            parts.append(chunk["text"])
        self.assertEqual("".join(parts), self.preview.records[identity]["text"])
        self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir() if p.is_file()})
        with self.assertRaises(ValueError):
            self.preview.read_source(identity, offset=10)
        with self.assertRaises(ValueError):
            self.preview.read_source(identity, offset=10, snapshot="wrong")

    def test_tampered_evidence_fails_validation(self):
        path = self.root / "plan.json"
        plan = json.loads(path.read_text())
        plan["articles"][0]["claims"][0]["evidence"][0]["quote"] = "An invented source quote"
        path.write_text(json.dumps(plan))
        with self.assertRaises(ValueError):
            MemoryPreview(self.root)

    def test_changed_bundle_has_new_snapshot_and_unknown_ids_never_become_paths(self):
        path = self.root / "plan.json"
        plan = json.loads(path.read_text())
        plan["articles"][0]["description"] = "Revised description"
        path.write_text(json.dumps(plan))
        self.assertNotEqual(self.preview.snapshot, MemoryPreview(self.root).snapshot)
        with self.assertRaises(ValueError):
            self.preview.read_article("../../server/data")
        with self.assertRaises(ValueError):
            self.preview.read_source("../../server/data")
