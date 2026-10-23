from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from entourage_server.agent import available_tools, build_context
from entourage_server.config import Settings
from entourage_server.knowledge import knowledge_operation, load_current, publish_bundle
from entourage_server.knowledge_bundle import KnowledgeBundle


ROOT = Path(__file__).resolve().parents[2]


def reviewed_fixture(directory):
    directory.mkdir()
    fixtures = ROOT / "ingestion/fixtures"
    (directory / "records.jsonl").write_bytes((fixtures / "memory-records.jsonl").read_bytes())
    (directory / "plan.json").write_bytes((fixtures / "memory-plan.json").read_bytes())
    bundle = KnowledgeBundle(directory)
    review = {"version": 1, "status": "accepted", "snapshot": bundle.snapshot,
              "reviewer": "Synthetic fixture author", "reviewer_kind": "coding_agent",
              "reviewed_at": datetime.now(timezone.utc).isoformat(),
              "notes": "Synthetic source-grounded test bundle; no live data."}
    (directory / "review.json").write_text(json.dumps(review))
    return directory


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.candidate = reviewed_fixture(self.root / "candidate")
        self.vault = self.root / "vault/knowledge"

    def publish(self, identity="test-bundle"):
        return publish_bundle(self.candidate, self.candidate / "review.json", self.vault, bundle_id=identity)

    def test_only_reviewed_exact_content_can_be_activated(self):
        pointer = self.publish()
        self.assertEqual(load_current(self.vault).snapshot, pointer["snapshot"])
        self.assertTrue((self.vault / "bundles/test-bundle/articles/community-garden.md").is_file())
        self.assertIn("Published reviewed", (self.vault / "bundles/test-bundle/index.md").read_text())
        review = json.loads((self.candidate / "review.json").read_text())
        review["snapshot"] = "wrong"
        (self.candidate / "bad-review.json").write_text(json.dumps(review))
        with self.assertRaises(ValueError):
            publish_bundle(self.candidate, self.candidate / "bad-review.json", self.vault, bundle_id="bad")
        self.assertEqual(json.loads((self.vault / "current.json").read_text()), pointer)
        with self.assertRaises(FileExistsError):
            self.publish()

    def test_generated_triage_is_not_semantic_acceptance(self):
        (self.candidate / "triage.json").write_text(json.dumps({"version": 1, "status": "complete", "triage_only": True}))
        with self.assertRaises(ValueError):
            publish_bundle(self.candidate, self.candidate / "triage.json", self.vault)
        self.assertFalse((self.vault / "current.json").exists())

    def test_portable_conversation_fixture_review_matches_bytes(self):
        fixture = ROOT / "ingestion/fixtures/reviewed-conversation-memory"
        publish_bundle(fixture, fixture / "review.json", self.vault)
        self.assertEqual(len(load_current(self.vault).articles), 3)

    def test_search_read_and_snapshot_guard(self):
        pointer = self.publish()
        result = knowledge_operation(self.vault, "searchKnowledge", {"keywords": ["garden"]})
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["coverage"]["source_count"], 4)
        article = knowledge_operation(self.vault, "readKnowledgeArticle", {"slug": "community-garden", "snapshot": pointer["snapshot"]})
        self.assertIn("unknowns", article["article"])
        self.assertEqual(knowledge_operation(self.vault, "readKnowledgeArticle", {"slug": "community-garden", "snapshot": "old"})["status"], "knowledge_changed")
        source = knowledge_operation(self.vault, "readKnowledgeSource", {"record_id": "garden-invite", "snapshot": pointer["snapshot"], "limit": 10})
        self.assertEqual(source["next_offset"], 10)
        self.assertEqual(source["observed_at"], "2025-04-01T10:00:00-04:00")

    def test_overspecific_phrases_produce_labeled_partial_leads(self):
        self.publish()
        result = knowledge_operation(self.vault, "searchKnowledge", {"keywords": ["community garden workday", "date change"]})
        self.assertEqual(result["match_mode"], "ranked_partial")
        self.assertEqual(result["results"][0]["slug"], "community-garden")
        self.assertIn("date", result["results"][0]["missing_tokens"])
        self.assertEqual(knowledge_operation(self.vault, "searchKnowledge", {"keywords": ["never-mentioned-allergen"]})["total_matches"], 0)

    def test_inventory_is_a_bounded_article_index_not_full_archive_coverage(self):
        self.publish()
        result = knowledge_operation(self.vault, "getKnowledgeInventory", {})
        self.assertEqual(result["article_count"], 3)
        self.assertEqual(result["source_count"], 4)
        self.assertEqual(len(result["articles"]), 3)
        self.assertIsNone(result["next_offset"])
        self.assertIn("not event dates", result["coverage"])

    def test_tampering_or_path_escape_fails_closed(self):
        self.publish()
        pointer_path = self.vault / "current.json"
        pointer = json.loads(pointer_path.read_text())
        pointer["bundle_id"] = "../../candidate"
        pointer_path.write_text(json.dumps(pointer))
        self.assertEqual(knowledge_operation(self.vault, "searchKnowledge", {"keywords": ["garden"]})["status"], "knowledge_unavailable")
        self.assertEqual(knowledge_operation(self.root / "absent", "searchKnowledge", {"keywords": ["garden"]})["status"], "knowledge_unavailable")

    def test_post_review_edit_invalidates_activation(self):
        self.publish()
        path = self.vault / "bundles/test-bundle/plan.json"
        plan = json.loads(path.read_text())
        plan["articles"][0]["description"] = "Changed after review"
        path.write_text(json.dumps(plan))
        self.assertEqual(knowledge_operation(self.vault, "searchKnowledge", {"keywords": ["garden"]})["status"], "knowledge_unavailable")

    def test_malformed_active_pointer_is_unavailable(self):
        self.publish()
        for pointer in ([], None, {"version": True, "bundle_id": "test-bundle"}):
            with self.subTest(pointer=pointer):
                (self.vault / "current.json").write_text(json.dumps(pointer))
                result = knowledge_operation(self.vault, "getKnowledgeInventory", {})
                self.assertEqual(result["status"], "knowledge_unavailable")

    def test_tools_and_prompt_are_opt_in(self):
        disabled = Settings()
        enabled = replace(disabled, knowledge_enabled=True)
        self.assertNotIn("searchKnowledge", [t["function"]["name"] for t in available_tools(disabled)])
        self.assertIn("readKnowledgeArticle", [t["function"]["name"] for t in available_tools(enabled)])
        self.assertNotIn("searchKnowledge", [t["function"]["name"] for t in available_tools(enabled)])
        self.assertNotIn("searchKnowledge", build_context("Hello", [], disabled)[0]["content"])
        self.assertIn("imported_memory", build_context("Hello", [], enabled)[0]["content"])

    def test_context_budget_never_leaves_orphaned_cached_tool_messages(self):
        wire = [{"role": "assistant", "content": "", "tool_calls": [{"id": "cached", "type": "function", "function": {"name": "readKnowledgeArticle", "arguments": "{}"}}]},
                {"role": "tool", "content": "source data", "tool_call_id": "cached"}]
        history = [{"role": "user", "text": "x" * 6000},
                   {"role": "assistant", "text": json.dumps(wire), "wire_messages": wire},
                   {"role": "assistant", "text": "answer"}]
        settings = Settings(context_tokens=2048, max_output_tokens=512, knowledge_enabled=True)
        messages = build_context("Follow up", history, settings)
        self.assertEqual([m["role"] for m in messages], ["system", "user"])


if __name__ == "__main__":
    unittest.main()
