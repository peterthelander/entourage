from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from event_candidates import suggest


class EventCandidateTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).parent / "fixtures"
        self.records = [json.loads(line) for line in (fixtures / "event-linking-records.jsonl").read_text(encoding="utf-8").splitlines()]
        self.facts = json.loads((fixtures / "event-linking-observations.json").read_text(encoding="utf-8"))
        self.events = json.loads((fixtures / "event-linking-events.json").read_text(encoding="utf-8"))

    def test_activity_dates_link_early_booking_and_other_sources_without_mixing_years(self):
        links = suggest(self.records, self.facts, self.events)["links"]
        self.assertEqual({(r["event_id"], r["record_id"]) for r in links if r["strength"] == "strong_lead"},
                         {("conference-2025", "hotel"), ("conference-2025", "transaction"), ("conference-2026", "cancellation")})
        self.assertTrue(all(r["membership"] == "pending_review" for r in links))
        self.assertEqual(next(r for r in links if r["record_id"] == "cancellation")["source_status"], "cancelled")
        self.assertEqual(next(r for r in links if r["record_id"] == "unrelated")["strength"], "date_only_lead")

    def test_merchant_alone_and_message_date_cannot_establish_membership(self):
        facts = deepcopy(self.facts)
        for fact in facts["facts"]:
            fact.pop("start_date")
            fact.pop("end_date")
        self.assertEqual(suggest(self.records, facts, self.events)["links"], [])

    def test_unreviewed_or_fabricated_extraction_is_rejected(self):
        self.facts["facts"][0]["quotes"] = ["Invented hotel stay"]
        with self.assertRaises(ValueError):
            suggest(self.records, self.facts, self.events)

    def test_same_reference_with_conflicting_dates_is_not_a_strong_match(self):
        self.events[1]["references"] = ["A1"]
        self.facts["facts"][0]["references"] = ["A1"]
        links = suggest(self.records, self.facts, self.events)["links"]
        conflict = next(r for r in links if r["event_id"] == "conference-2026" and r["record_id"] == "hotel")
        self.assertEqual(conflict["strength"], "conflicting_lead")
        self.assertIn("activity_dates_conflict", conflict["reasons"])


if __name__ == "__main__":
    unittest.main()
