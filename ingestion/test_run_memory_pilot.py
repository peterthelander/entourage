from contextlib import redirect_stdout
import io
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent / "src"))
import run_memory_pilot as pilot  # noqa: E402


class MemoryPilotTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parent / "fixtures/article-accuracy-development.jsonl"
        self.records = [json.loads(line) for line in path.read_text().splitlines()]
        for record in self.records:
            record["text"] += "\nSource note: this fictional record exercises the bounded ingestion pilot."
            record["source"]["sha256"] = hashlib.sha256(record["text"].encode()).hexdigest()

    def test_sample_is_order_independent_and_bounded(self):
        a, report = pilot.select_sample(self.records)
        b, _ = pilot.select_sample(list(reversed(self.records)))
        self.assertEqual([r["id"] for r in a], [r["id"] for r in b])
        self.assertEqual(len(a), 3)
        self.assertEqual(report["normalized_records"], len(self.records))
        with self.assertRaises(ValueError):
            pilot.select_sample([])

    def normalize(self, sources, output, *args):
        output.mkdir()
        (output / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in self.records))
        return {"status": "complete"}

    def propose(self, records_path, config, output, repeats, **kwargs):
        output.mkdir()
        records = [json.loads(line) for line in records_path.read_text().splitlines()]
        articles = [{"slug": r["id"], "title": r["title"], "description": "Synthetic source statement.",
                     "type": "concept", "claims": [{"type": "source_statement", "text": r["text"],
                     "evidence": [{"record_id": r["id"], "quote": r["text"]}]}], "unknowns": [], "links": []} for r in records]
        for i in range(1, repeats + 1):
            (output / f"plan-{i}.json").write_text(json.dumps({"version": 1, "articles": articles}))
        return {"runs": [{"repeat": i, "mechanical_pass": True} for i in range(1, repeats + 1)]}

    def test_all_supported_reviews_never_publish_or_approve(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.json"
            config.write_text("{}")
            with patch.object(pilot, "normalize_mail", self.normalize), patch.object(pilot, "propose", self.propose), patch.object(pilot, "review", return_value={"runs": [{"complete": True, "flagged": []}]}), redirect_stdout(io.StringIO()):
                report = pilot.run([root / "synthetic.mbox"], config, root / "pilot", repeats=1)
            self.assertEqual(report["status"], "complete")
            self.assertFalse(report["live_publication"])
            self.assertEqual(report["candidate_review"], "pending")
            candidate = report["stages"]["candidates"][0]
            self.assertFalse(candidate["published"])
            self.assertEqual(candidate["review"], "pending")
            self.assertTrue(candidate["content_hashes"])
            with self.assertRaises(FileExistsError):
                pilot.run([root / "synthetic.mbox"], config, root / "pilot")

    def test_stage_failure_leaves_explicit_failed_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.json"
            config.write_text("{}")
            with patch.object(pilot, "normalize_mail", side_effect=RuntimeError("Synthetic failure")), redirect_stdout(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    pilot.run([root / "synthetic.mbox"], config, root / "pilot")
            report = json.loads((root / "pilot/pilot-report.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertFalse(report["live_publication"])
