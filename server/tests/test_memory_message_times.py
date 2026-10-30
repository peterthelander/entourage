from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from memory_context import with_message_times


class MessageTimesTests(unittest.TestCase):
    def test_repeated_user_text_is_bound_to_correct_record_time_without_mutation(self):
        history = [{"role": "user", "text": "Update", "created_at": "2026-10-25T12:00:00+00:00"},
                   {"role": "user", "text": "Update", "created_at": "2026-10-26T12:00:00+00:00"}]
        messages = [{"role": "system", "content": "Instructions"},
                    {"role": "user", "content": "Update"}, {"role": "assistant", "content": "Acknowledged"},
                    {"role": "user", "content": "Update"}, {"role": "user", "content": "Recap?"}]
        original = deepcopy(messages)
        result = with_message_times(messages, history, "2026-10-27T12:00:00+00:00")
        self.assertEqual(messages, original)
        self.assertIn("2026-10-25", result[1]["content"])
        self.assertIn("2026-10-26", result[3]["content"])
        self.assertIn("2026-10-27", result[4]["content"])
        self.assertTrue(result[4]["content"].endswith("Recap?"))
        self.assertEqual(result[2], messages[2])

    def test_tool_pairs_are_unchanged_and_offsets_are_normalized_to_utc(self):
        messages = [{"role": "system", "content": "Instructions"},
                    {"role": "assistant", "tool_calls": [{"id": "call"}], "content": ""},
                    {"role": "tool", "tool_call_id": "call", "content": "Source record date"},
                    {"role": "user", "content": "Correction"}]
        result = with_message_times(messages, [], "2026-10-26T00:30:00+02:00")
        self.assertEqual(result[1:3], messages[1:3])
        self.assertIn("2026-10-25T22:30:00+00:00", result[-1]["content"])
        self.assertIn("not an event date", result[-1]["content"])

    def test_missing_or_invalid_historical_dates_are_not_fabricated(self):
        messages = [{"role": "system", "content": "Instructions"}, {"role": "user", "content": "Old"},
                    {"role": "user", "content": "New"}]
        result = with_message_times(messages, [{"role": "user", "text": "Old", "created_at": "invalid"}],
                                    "2026-10-26T12:00:00+00:00")
        self.assertEqual(result[1], messages[1])
        self.assertEqual(with_message_times(messages, [], None), messages)


if __name__ == "__main__":
    unittest.main()
