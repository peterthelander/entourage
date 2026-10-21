from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from entourage_server.app import create_app
from entourage_server.config import Settings
from entourage_server.storage import Store, StoreError


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "nested" / "agent.db"
        self.settings = Settings(database_path=self.path)
        self.client = self.enterContext(TestClient(create_app(self.settings)))
        self.conversation = str(uuid4())
        self.base = f"/api/v1/conversations/{self.conversation}"
        self.assertEqual(self.client.put(self.base, json={"title": "Personal"}).status_code, 201)

    def test_conversation_and_turn_survive_a_new_server_instance(self):
        turn_id, device_id = str(uuid4()), str(uuid4())
        body = {"text": "Remember this", "device_id": device_id}
        url = f"{self.base}/turns/{turn_id}"
        first = self.client.put(url, json=body)
        self.assertEqual(first.status_code, 202)
        self.assertEqual(first.json()["status"], "queued")
        self.assertNotIn("text", first.json())
        # New app, new store object, new SQLite connections; same physical database.
        with TestClient(create_app(self.settings)) as restarted:
            self.assertEqual(restarted.put(self.base, json={"title": "Personal"}).status_code, 200)
            self.assertEqual(restarted.put(url, json=body).status_code, 200)
            self.assertEqual(restarted.get(f"/api/v1/turns/{turn_id}").json(), first.json())
            messages = restarted.get(f"{self.base}/messages").json()["items"]
            self.assertEqual(len(messages), 1)
            self.assertEqual((messages[0]["text"], messages[0]["kind"]), ("Remember this", "user"))

    def test_conflicting_retries_and_second_active_turn_do_not_append_messages(self):
        turn_id = str(uuid4())
        body = {"text": "Original", "device_id": str(uuid4())}
        url = f"{self.base}/turns/{turn_id}"
        self.client.put(url, json=body)
        self.assertEqual(self.client.put(self.base, json={"title": "Changed"}).status_code, 409)
        for changed in [{**body, "text": "Other"}, {**body, "device_id": str(uuid4())}]:
            self.assertEqual(self.client.put(url, json=changed).json()["error"]["code"], "id_conflict")
        second = self.client.put(f"{self.base}/turns/{uuid4()}", json=body)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(len(self.client.get(f"{self.base}/messages").json()["items"]), 1)

    def test_concurrent_turn_submission_is_serialized(self):
        store = Store(self.path)

        def submit(_):
            try:
                store.create_turn(self.conversation, str(uuid4()), "Concurrent", str(uuid4()))
                return "accepted"
            except StoreError as error:
                return error.code

        with ThreadPoolExecutor(max_workers=4) as executor:
            outcomes = list(executor.map(submit, range(4)))
        self.assertEqual(outcomes.count("accepted"), 1)
        self.assertEqual(outcomes.count("turn_active"), 3)
        self.assertEqual(len(store.list_messages(self.conversation, 0, 100)["items"]), 1)

    def test_turn_and_message_commit_is_atomic_when_message_write_fails(self):
        store = Store(self.path)
        with store.connect(write=True) as db:
            db.execute("""CREATE TRIGGER fail_message BEFORE INSERT ON messages
                BEGIN SELECT RAISE(ABORT, 'simulated disk write failure'); END""")
        turn_id = str(uuid4())
        with self.assertRaises(sqlite3.IntegrityError):
            store.create_turn(self.conversation, turn_id, "Hello", str(uuid4()))
        with self.assertRaises(StoreError) as raised:
            store.get_turn(turn_id)
        self.assertEqual(raised.exception.status, 404)
        self.assertEqual(store.list_messages(self.conversation, 0, 50)["items"], [])
        with store.connect(write=True) as db:
            db.execute("DROP TRIGGER fail_message")
        self.assertTrue(store.create_turn(self.conversation, turn_id, "Hello", str(uuid4()))[1])

    def test_pagination_is_stable_and_bounded(self):
        for index in range(3):
            self.client.put(f"/api/v1/conversations/{uuid4()}", json={"title": f"Chat {index}"})
        first = self.client.get("/api/v1/conversations?limit=2").json()
        second = self.client.get(f"/api/v1/conversations?limit=2&after={first['next_after']}").json()
        self.assertEqual(len(first["items"]), 2)
        self.assertEqual(len(second["items"]), 2)
        self.assertIsNone(second["next_after"])
        self.assertEqual(len({item["id"] for item in first["items"] + second["items"]}), 4)
        for query in ["limit=0", "limit=101", "after=-1", f"after={2**64}"]:
            self.assertEqual(self.client.get(f"/api/v1/conversations?{query}").status_code, 422)

    def legacy_history(self):
        return {"messages": [
            {"id": "welcome", "role": "assistant", "text": "Welcome"},
            {"id": "user-1", "role": "user", "text": "Where am I?", "createdAt": "2026-10-17T12:00:00-04:00"},
            {"id": "toolresult-2", "role": "assistant", "text": "getCurrentLocation\nLocation"},
            {"id": "error-3", "role": "assistant", "text": "Interrupted"},
            {"id": "assistant-4", "role": "assistant", "text": "Answer"},
        ]}

    def test_import_preview_commit_retry_and_message_kinds(self):
        body = self.legacy_history()
        preview = self.client.post("/api/v1/import-preview", json=body)
        self.assertEqual(preview.json(), {"total": 5, "users": 1, "assistants": 1, "tools": 1, "errors": 1, "skipped": 1})
        self.assertEqual(self.client.get(f"{self.base}/messages").json()["items"], [])
        url = f"{self.base}/imports/{uuid4()}"
        self.assertEqual(self.client.put(url, json=body).status_code, 201)
        self.assertEqual(self.client.put(url, json=body).status_code, 200)
        first = self.client.get(f"{self.base}/messages?limit=2").json()
        second = self.client.get(f"{self.base}/messages?after={first['next_after']}&limit=2").json()
        items = first["items"] + second["items"]
        self.assertEqual([item["kind"] for item in items], ["user", "tool", "error", "assistant"])
        self.assertEqual(items[1]["role"], "tool")
        self.assertTrue(items[0]["created_at"].endswith("16:00:00Z"))
        self.assertIsNone(second["next_after"])
        self.assertEqual(self.client.put(f"{self.base}/imports/{uuid4()}", json=body).status_code, 409)
        body["messages"][1]["text"] = "Different"
        self.assertEqual(self.client.put(url, json=body).status_code, 409)
        self.assertEqual(len(self.client.get(f"{self.base}/messages").json()["items"]), 4)

    def test_import_survives_restart_and_ids_cannot_be_reused_in_another_conversation(self):
        import_id = str(uuid4())
        url = f"{self.base}/imports/{import_id}"
        body = self.legacy_history()
        self.client.put(url, json=body)
        with TestClient(create_app(self.settings)) as restarted:
            self.assertEqual(restarted.put(url, json=body).status_code, 200)
            other = f"/api/v1/conversations/{uuid4()}"
            restarted.put(other, json={})
            self.assertEqual(restarted.put(f"{other}/imports/{import_id}", json=body).status_code, 409)
            self.assertEqual(restarted.get(f"{other}/messages").json()["items"], [])

    def test_invalid_and_missing_resources_have_safe_errors(self):
        self.assertEqual(self.client.get(f"/api/v1/turns/{uuid4()}").status_code, 404)
        missing = f"/api/v1/conversations/{uuid4()}"
        self.assertEqual(self.client.get(f"{missing}/messages").status_code, 404)
        body = {"text": "private text", "device_id": str(uuid4()), "model": "untrusted"}
        result = self.client.put(f"{self.base}/turns/{uuid4()}", json=body)
        self.assertEqual(result.status_code, 422)
        self.assertNotIn("private text", result.text)
        self.assertIn("error", result.json())
        duplicate = self.legacy_history()
        duplicate["messages"].append(duplicate["messages"][1])
        self.assertEqual(self.client.post("/api/v1/import-preview", json=duplicate).status_code, 422)
        self.assertEqual(self.client.put(self.base, content=b"x" * (1024 * 1024 + 1)).status_code, 413)
        chunks = (b"x" * (256 * 1024) for _ in range(5))
        self.assertEqual(self.client.put(self.base, content=chunks).status_code, 413)
        self.assertEqual(self.client.put(self.base, content=b"{").status_code, 422)

    def test_failed_write_rolls_back_and_newer_schema_is_rejected(self):
        store = Store(self.path)
        with self.assertRaises(RuntimeError):
            with store.connect(write=True) as db:
                db.execute("UPDATE conversations SET title='Uncommitted'")
                raise RuntimeError("Simulated failure")
        self.assertEqual(store.list_conversations(0, 50)["items"][0]["title"], "Personal")
        with store.connect(write=True) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 2)
            db.execute("PRAGMA user_version=99")
        with self.assertRaisesRegex(RuntimeError, "newer"):
            Store(self.path).initialize()


if __name__ == "__main__":
    unittest.main()
