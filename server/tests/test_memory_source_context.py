from copy import deepcopy
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from entourage_server.knowledge import ReviewedKnowledge
from entourage_server.knowledge_bundle import KnowledgeBundle
from entourage_server.config import Settings

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from memory_source_context import article_source_context


class SourceContextTests(unittest.TestCase):
    def setUp(self):
        self.bundle = ReviewedKnowledge(ROOT / "ingestion/fixtures/source-binding-memory")
        self.original = self.bundle.read_article("cedar-pantry")

    def test_preserves_canonical_article_and_exact_original_offsets(self):
        before = deepcopy(self.original)
        result = article_source_context(self.bundle, self.original)
        self.assertEqual(self.original, before)
        self.assertEqual({k: v for k, v in result.items() if k != "source_context"}, before)
        for passage in result["source_context"]["passages"]:
            record = self.bundle.records[passage["record_id"]]
            self.assertEqual(passage["text"], record["text"][passage["offset"]:passage["end_offset"]])
            self.assertEqual(passage["observed_at"], record["observed_at"])
            self.assertEqual(passage["partial"], passage["offset"] > 0 or passage["end_offset"] < len(record["text"]))

    def test_keeps_qualification_at_end_of_paragraph_and_merges_overlapping_quotes(self):
        first = self.original["article"]["claims"][0]["evidence"][0]
        identity, quote = first["record_id"], first["quote"]
        paragraph = quote + " " + "Additional terms. " * 30 + "Subject to final confirmation."
        self.bundle.records[identity]["text"] = "Header\n\n" + paragraph + "\n\nFooter"
        self.original["article"]["claims"] = [{"evidence": [first, {**first, "quote": "Subject to final confirmation."}]}]
        result = article_source_context(self.bundle, self.original)["source_context"]
        self.assertEqual(len(result["passages"]), 1)
        self.assertEqual(result["passages"][0]["text"], paragraph)
        self.assertTrue(result["passages"][0]["partial"])

    def test_ambiguous_quotes_and_oversized_paragraphs_are_explicit_omissions(self):
        first = self.original["article"]["claims"][0]["evidence"][0]
        identity, quote = first["record_id"], first["quote"]
        self.original["article"]["claims"] = [{"evidence": [first]}]
        for text, reason in ((quote + "\n\n" + quote, "quote_not_unique"),
                             (quote + "é" * 3000, "paragraph_exceeds_budget")):
            self.bundle.records[identity]["text"] = text
            context = article_source_context(self.bundle, self.original)["source_context"]
            self.assertEqual(context["passages"], [])
            self.assertEqual(context["omitted_count"], 1)
            self.assertEqual(context["omitted"][0]["reason"], reason)

    def test_total_budget_includes_utf8_passages_and_omission_metadata(self):
        with patch("memory_source_context.MAX_CONTEXT_BYTES", 650):
            context = article_source_context(self.bundle, self.original)["source_context"]
        self.assertLessEqual(len(json.dumps(context, ensure_ascii=False).encode("utf-8")), 650)
        self.assertGreater(context["omitted_count"], 0)

    def test_index_treatment_preserves_identical_evidence_and_coverage(self):
        from memory_overview import load_overview, overview_evidence
        spec = importlib.util.spec_from_file_location("context_diagnosis", ROOT / "scripts/diagnose-memory-context.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        bundle = ReviewedKnowledge(ROOT / "ingestion/fixtures/memory-overview-memory")
        plan = load_overview(ROOT / "ingestion/fixtures/memory-overview.json")
        for mode in ("flat_overview", "thematic_overview"):
            packet = overview_evidence(bundle, plan, mode)
            before = deepcopy(packet)
            treatment = runner.omit_overview_index(packet)
            self.assertEqual(packet, before)
            self.assertEqual(treatment[0]["result"]["inventory"], [])
            self.assertEqual({k: v for k, v in treatment[0]["result"].items() if k not in {"inventory", "scope"}},
                             {k: v for k, v in packet[0]["result"].items() if k not in {"inventory", "scope"}})
        with self.assertRaises(ValueError):
            runner.omit_overview_index(overview_evidence(bundle, plan, "inventory"))

    def test_original_passages_reach_worker_answer_and_immediate_followup(self):
        spec = importlib.util.spec_from_file_location("passage_evaluation", ROOT / "scripts/evaluate-conversations.py")
        evaluation = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evaluation)
        snapshot, assertions = self.bundle.snapshot, self

        class Model:
            calls = 0

            async def generate(self, messages, on_text):
                self.calls += 1
                if self.calls == 1:
                    return {"content": "", "tool_calls": [{"id": "read", "type": "function", "function": {
                        "name": "readKnowledgeArticle", "arguments": json.dumps({"slug": "cedar-pantry", "snapshot": snapshot})}}]}
                evidence = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
                assertions.assertEqual(len(evidence), 1)
                assertions.assertGreater(len(evidence[0]["source_context"]["passages"]), 0)
                return {"content": "Delivery and final payment remain unknown.", "tool_calls": []}

        original = KnowledgeBundle.read_article

        def read(bundle, slug):
            return article_source_context(bundle, original(bundle, slug))

        model = Model()
        case = {"id": "passage-retention", "rubric": ["Preserve original evidence"], "turns": [
            {"text": "What changed?", "created_at": "2026-10-26T10:00:00+00:00"},
            {"text": "Was it completed?", "created_at": "2026-10-26T10:01:00+00:00"}]}
        with patch.object(KnowledgeBundle, "read_article", read):
            row = asyncio.run(evaluation.run_case(case, Settings(), model,
                knowledge_bundle=ROOT / "ingestion/fixtures/source-binding-memory"))
        self.assertEqual(model.calls, 3)
        self.assertTrue(all(t["status"] == "completed" for t in row["turns"]))
        self.assertEqual(len(row["turns"][0]["tools"]), 1)
        self.assertEqual(row["turns"][1]["tools"], [])


if __name__ == "__main__":
    unittest.main()
