import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from memory_validation import read, review_template, write_new

spec = importlib.util.spec_from_file_location("memory_conditions", ROOT / "scripts/compare-memory-conditions.py")
conditions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conditions)


class MemoryConditionsTests(unittest.TestCase):
    def test_skipped_and_failed_turns_remain_visible_and_cannot_pass_case(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, expected, review = [root / (name + ".json") for name in ("report", "expected", "review")]
            write_new(expected, {"version": 1, "independent_review": False, "cases": [{"id": "overview", "criteria": [
                {"turn": i, "expected": "Preserve uncertainty", "source_ids": ["fictional"]} for i in (1, 2, 3)]}]})
            write_new(report, {"version": 1, "status": "complete", "diagnostic_modes": ["inventory", "thematic_overview"],
                "planned_runs": {"providers": ["local"], "repeats": 1, "case_ids": ["overview"]}, "runs": [
                    {"provider": "local", "repeat": 1, "case": "overview", "mode": "inventory", "turns": [
                        {"turn": i, "status": "completed", "seconds": i} for i in (1, 2, 3)]},
                    {"provider": "local", "repeat": 1, "case": "overview", "mode": "thematic_overview", "turns": [
                        {"turn": 1, "status": "completed", "seconds": 2},
                        {"turn": 2, "status": "failed", "seconds": 180}]}]})
            template = review_template(report, expected)
            template["reviewer"] = "Fictional test reviewer"
            for row in template["rows"]:
                row.update(verdict="pass" if row["execution_status"] == "completed" else "fail", notes="Fictional finding")
            write_new(review, template)
            summary = conditions.compare(report, expected, review)
            inventory, themed = summary["conditions"]
            self.assertEqual(inventory["full_case_passes"], 1)
            self.assertEqual(themed["full_case_passes"], 0)
            self.assertEqual(themed["attempted_turns"], 2)
            self.assertEqual(themed["planned_turns_in_reviewed_runs"], 3)
            self.assertEqual(themed["execution_counts"], {"completed": 1, "failed": 1, "not_run": 1})
            self.assertEqual(themed["attempt_seconds_median"], 91)
            self.assertEqual(themed["completed_seconds_median"], 2)
            changed = read(review)
            changed["rows"][0]["expected"] = "Changed after review"
            other = root / "changed.json"
            write_new(other, changed)
            with self.assertRaisesRegex(ValueError, "identity or expected finding changed"):
                conditions.compare(report, expected, other)
