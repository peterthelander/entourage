import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from entourage_server.execution_store import ExecutionStore
from entourage_server.journal_refresh import JournalRefresh
from entourage_server.memory import search_memories
from entourage_server.storage import SINGLE_CHAT_ID


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = ExecutionStore(Path(self.temp.name) / "test.db")
        self.store.initialize()
        self.store.single_chat()
        self.refresh = JournalRefresh(self.store, "UTC")

    def complete(self, turn_id="turn"):
        self.store.create_turn(SINGLE_CHAT_ID, turn_id, "Remember my amber bicycle", "device")
        turn = self.store.claim()
        self.store.finish(turn, answer="Recorded your amber bicycle")

    def test_completion_refresh_restart_and_no_duplicate_rewrites(self):
        self.refresh.refresh()
        self.store.create_turn(SINGLE_CHAT_ID, "turn", "Remember my amber bicycle", "device")
        self.refresh.refresh()
        self.assertEqual(search_memories(self.refresh.directory, {"keywords": ["amber"], "speaker": "all"})["results"], [])
        turn = self.store.claim()
        self.store.finish(turn, answer="Recorded your amber bicycle")
        self.refresh.refresh()
        self.assertEqual(len(search_memories(self.refresh.directory, {"keywords": ["amber"], "speaker": "all"})["results"]), 2)
        with patch("entourage_server.journal_refresh.export_journals") as export:
            self.refresh.refresh()
            export.assert_not_called()
        # Rebuild on restart even without an in-memory completion notification.
        JournalRefresh(self.store, "UTC").refresh()
        self.assertEqual(len(search_memories(self.refresh.directory, {"keywords": ["amber"], "speaker": "all"})["results"]), 2)

    def test_failure_does_not_change_completed_turn_and_retries(self):
        self.complete()
        with patch("entourage_server.journal_refresh.export_journals", side_effect=OSError("private path")):
            self.refresh.refresh()
        self.assertEqual(self.store.get_turn("turn")["status"], "completed")
        self.assertEqual(self.refresh.coverage()["status"], "refresh_failed")
        self.assertIsNone(self.refresh.signature)
        self.refresh.refresh()
        self.assertEqual(self.refresh.coverage()["status"], "ready")
        self.assertEqual(len(search_memories(self.refresh.directory, {"keywords": ["amber"], "speaker": "all"})["results"]), 2)

    def test_background_startup_catchup_and_stop(self):
        self.complete()
        async def run():
            stop = asyncio.Event()
            task = asyncio.create_task(self.refresh.run(stop))
            for _ in range(100):
                if self.refresh.last_success:
                    break
                await asyncio.sleep(0.02)
            stop.set()
            await asyncio.wait_for(task, 3)
        asyncio.run(run())
        self.assertEqual(self.refresh.coverage()["status"], "ready")

    def test_restart_preserves_existing_timezone_without_environment_override(self):
        self.complete()
        JournalRefresh(self.store, "America/New_York").refresh()
        restarted = JournalRefresh(self.store, None)
        restarted.refresh()
        self.assertEqual(restarted.timezone_name, "America/New_York")
        self.assertEqual(restarted.coverage()["status"], "ready")
