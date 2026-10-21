import importlib.util
import json
from pathlib import Path
import unittest

from entourage_server.config import Settings

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("compare_context", ROOT / "scripts/compare-context.py")
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


class ContextComparisonTests(unittest.TestCase):
    def test_synthetic_comparison_preserves_the_update_and_follow_up_without_old_task(self):
        fixture = json.loads((ROOT / "server/tests/fixtures/context-comparison.json").read_text())
        cases = comparison.build_cases(fixture, Settings(context_tokens=16384, max_output_tokens=2048))
        self.assertIn("coding agent", cases["original/full"][1]["content"])
        self.assertEqual(cases["original/session"][1]["content"], "Good morning")
        self.assertEqual(cases["original/session"][-1]["content"], fixture["query"]["text"])
        self.assertEqual(cases["continuity/session"][-2]["content"], fixture["query"]["text"])
        self.assertEqual(cases["continuity/session"][-1]["content"], fixture["follow_up"]["text"])
        for messages in cases.values():
            self.assertTrue(all(set(message) == {"role", "content"} for message in messages))
