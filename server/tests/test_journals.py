from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from entourage_server.journals import export_journals
from entourage_server.storage import Store, SINGLE_CHAT_ID


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = Store(self.root / "test.db")
        self.store.initialize()
        self.store.single_chat()
        self.output = self.root / "journals"

    def message(self, text, timestamp, kind="user", turn=None):
        with self.store.connect(write=True) as db:
            db.execute("""INSERT INTO messages(conversation_id,turn_id,role,kind,text,created_at)
                VALUES(?,?,?,?,?,?)""", (SINGLE_CHAT_ID, turn,
                "tool" if kind == "tool" else kind, kind, text, timestamp))

    def export(self, zone="America/New_York"):
        return export_journals(self.store.path, self.output, zone)

    def test_local_midnight_unicode_provenance_and_repeat_export(self):
        self.message("Café 🐈\n# quoted heading", "2026-10-18T03:59:00+00:00")
        self.message("Later", "2026-10-18T04:01:00+00:00", "assistant")
        self.assertEqual(self.export(), {"days": 2, "messages": 2, "changed": 2})
        first = (self.output / "2026-10-17.md").read_text(encoding="utf-8")
        self.assertIn("> Café 🐈\n> # quoted heading", first)
        self.assertIn("message=1; turn=imported", first)
        self.assertIn("completion unverified", first)
        before = {p.name: p.stat().st_mtime_ns for p in self.output.iterdir()}
        self.assertEqual(self.export()["changed"], 0)
        self.assertEqual(before, {p.name: p.stat().st_mtime_ns for p in self.output.iterdir()})

    def test_completed_only_with_tools_and_backfill(self):
        for index, status in enumerate(["completed", "failed", "running", "needs_review", "queued", "waiting_for_device"]):
            turn = f"turn-{index}"
            with self.store.connect(write=True) as db:
                db.execute("INSERT INTO turns(id,conversation_id,device_id,text,status,created_at) VALUES(?,?,?,?,?,?)",
                           (turn, SINGLE_CHAT_ID, "device", "question", "failed", "2026-10-17T12:00:00+00:00"))
                # Only one unfinished turn is permitted by the production schema.
                db.execute("UPDATE turns SET status=? WHERE id=?", (status, turn))
            self.message(status, "2026-10-17T12:00:00+00:00", turn=turn)
            if status == "completed":
                self.message("calculate\nresult: 4", "2026-10-17T12:01:00+00:00", "tool", turn)
                self.message("Four", "2026-10-17T12:02:00+00:00", "assistant", turn)
            if status not in ("completed", "failed", "waiting_for_device"):
                with self.store.connect(write=True) as db:
                    db.execute("UPDATE turns SET status='failed' WHERE id=?", (turn,))
        self.assertEqual(self.export()["messages"], 3)
        document = (self.output / "2026-10-17.md").read_text(encoding="utf-8")
        self.assertIn("Tool result", document)
        self.assertNotIn("> failed", document)
        self.message("New completed import", "2026-10-17T13:00:00+00:00")
        self.assertEqual(self.export()["messages"], 4)
        self.assertEqual((self.output / "2026-10-17.md").read_text(encoding="utf-8").count("> completed"), 1)

    def test_dst_repeated_hour_keeps_absolute_order(self):
        self.message("first", "2026-11-01T05:30:00+00:00")
        self.message("second", "2026-11-01T06:15:00+00:00")
        self.export()
        document = (self.output / "2026-11-01.md").read_text(encoding="utf-8")
        self.assertLess(document.index("> first"), document.index("> second"))
        self.assertIn("-04:00", document)
        self.assertIn("-05:00", document)

    def test_read_only_missing_database_and_unmanaged_file_protection(self):
        missing = self.root / "missing.db"
        with self.assertRaises(Exception):
            export_journals(missing, self.output, "UTC")
        self.assertFalse(missing.exists())
        self.message("hello", "2026-10-17T12:00:00+00:00")
        self.output.mkdir()
        target = self.output / "2026-10-17.md"
        target.write_text("My handwritten journal", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.export()
        self.assertEqual(target.read_text(encoding="utf-8"), "My handwritten journal")

    def test_invalid_timezone_writes_nothing_and_export_preserves_database(self):
        self.message("hello", "2026-10-17T12:00:00+00:00")
        before = self.store.path.read_bytes()
        with self.assertRaises(Exception):
            self.export("Invalid/Timezone")
        self.assertFalse(self.output.exists())
        self.export()
        self.assertEqual(before, self.store.path.read_bytes())
