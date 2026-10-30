import importlib.util
from pathlib import Path
import sys
import unittest

from entourage_server.agent import build_context
from entourage_server.config import Settings

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from memory_validation import freeze, verify


class MemoryReturnFixtureTests(unittest.TestCase):
    def test_return_case_crosses_session_boundary_and_has_frozen_per_turn_expectations(self):
        spec = importlib.util.spec_from_file_location("return_evaluation", ROOT / "scripts/evaluate-conversations.py")
        evaluation = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evaluation)
        fixtures = ROOT / "ingestion/fixtures"
        path = fixtures / "memory-return-conversations.json"
        case = evaluation.load_cases(path)["cases"][0]
        settings = Settings(knowledge_enabled=True)
        first = case["turns"][0]
        context = build_context(first["text"], case["history"], settings, created_at=first["created_at"])
        self.assertEqual([m["role"] for m in context], ["system", "user"])
        self.assertNotIn("planting", context[-1]["content"])
        self.assertEqual(len(case["turns"]), 4)
        self.assertIn("planting", case["memories"][-1]["text"])
        manifest = freeze(ROOT, fixtures / "memory-overview-memory", path,
                          fixtures / "memory-return-expectations.json", settings,
                          providers=["local"], repeats=1)
        verify(manifest)
        self.assertFalse(manifest["independent_review"])
        self.assertEqual(manifest["planned_runs"]["case_ids"], ["return-and-correct-attendance"])


if __name__ == "__main__":
    unittest.main()
