"""Session selection keeps old requests out without changing model messages."""
from datetime import datetime, timedelta, timezone
import unittest

from entourage_server.agent import build_context
from entourage_server.config import Settings


class ContextSessionTests(unittest.TestCase):
    def context(self, history, created_at="2026-10-18T11:17:00+00:00", settings=None):
        return build_context("Going with Tate and Starr", history, settings, created_at=created_at)

    def row(self, text, at, role="user"):
        return {"role": role, "text": text, "created_at": at}

    def test_overnight_gap_excludes_old_request_and_keeps_current_exchange(self):
        context = self.context([
            self.row("Suggest coding improvements", "2026-10-17T20:22:00+00:00"),
            self.row("Here are improvements", "2026-10-17T20:23:00+00:00", "assistant"),
            self.row("Good morning", "2026-10-18T11:04:00+00:00"),
            self.row("Hello", "2026-10-18T11:05:00+00:00", "assistant"),
            self.row("Apple picking at the harvest farm", "2026-10-18T11:06:00+00:00"),
        ])
        self.assertEqual([m["content"] for m in context[1:]],
                         ["Good morning", "Hello", "Apple picking at the harvest farm", "Going with Tate and Starr"])
        self.assertTrue(all(set(m) == {"role", "content"} for m in context))

    def test_same_day_long_gap_starts_fresh(self):
        self.assertEqual(len(self.context([
            self.row("Morning topic", "2026-10-18T09:00:00+00:00"),
            self.row("Old reply", "2026-10-18T09:01:00+00:00", "assistant"),
        ])), 2)

    def test_crossing_midnight_and_offsets_preserve_continuity(self):
        context = self.context([
            self.row("Trip tomorrow", "2026-10-17T23:50:00-04:00"),
            self.row("Which friends?", "2026-10-18T03:55:00+00:00", "assistant"),
        ], created_at="2026-10-18T00:10:00-04:00")
        self.assertEqual(context[1]["content"], "Trip tomorrow")
        self.assertEqual(context[2]["content"], "Which friends?")

    def test_gap_is_between_adjacent_user_messages_not_total_session_age(self):
        history = [self.row(str(hour), f"2026-10-18T{hour:02}:00:00+00:00") for hour in range(7, 12)]
        self.assertEqual(len(self.context(history)), 7)
        # An assistant's late reply cannot extend a user's inactivity window.
        self.assertEqual(len(self.context([
            self.row("Old task", "2026-10-18T09:00:00+00:00"),
            self.row("Delayed response", "2026-10-18T11:16:00+00:00", "assistant"),
        ])), 2)

    def test_configurable_threshold_and_exact_boundary(self):
        history = [self.row("Recent", "2026-10-18T10:17:00+00:00")]
        self.assertEqual(len(self.context(history)), 3)
        self.assertEqual(len(self.context(history, created_at="2026-10-18T11:17:01+00:00")), 2)
        self.assertEqual(len(self.context(history, settings=Settings(context_session_gap_minutes=30))), 2)

    def test_bad_or_missing_history_times_do_not_reactivate_older_messages(self):
        for at in [None, "invalid", "2026-10-18T10:00:00", "2026-10-19T10:00:00+00:00"]:
            with self.subTest(at=at):
                history = [self.row("Old", "2026-10-18T10:00:00+00:00"),
                           self.row("Bad time", at),
                           self.row("Recent", "2026-10-18T11:16:00+00:00")]
                self.assertEqual([m["content"] for m in self.context(history)[1:]],
                                 ["Recent", "Going with Tate and Starr"])
        self.assertEqual(len(self.context([{"role": "user", "text": "No timestamp"}])), 2)

    def test_session_selection_still_obeys_character_and_message_limits(self):
        instant = datetime(2026, 10, 18, 11, 17, tzinfo=timezone.utc)
        history = [self.row(str(i) + "x" * 600, (instant - timedelta(seconds=140 - i)).isoformat(),
                            "user" if i % 2 == 0 else "assistant") for i in range(140)]
        context = self.context(history, settings=Settings(context_tokens=4096, max_output_tokens=768))
        self.assertLessEqual(sum(len(m["content"]) for m in context[1:]), 2560)
        self.assertLessEqual(len(context), 130)
        self.assertEqual(context[1]["role"], "user")
        self.assertEqual(context[-2]["content"], history[-1]["text"])


if __name__ == "__main__":
    unittest.main()
