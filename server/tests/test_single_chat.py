from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from entourage_server.app import create_app
from entourage_server.config import Settings
from entourage_server.models import HistoryImport
from entourage_server.storage import Store


class SingleChatTests(unittest.TestCase):
    def test_later_legacy_writes_still_project_into_shared_chat_once(self):
        with TemporaryDirectory() as directory:
            store = Store(Path(directory) / "test.db")
            store.initialize()
            old = str(uuid4())
            store.create_conversation(old, "Previous chat")
            chat = store.single_chat()
            for text in ["First", "Later"]:
                store.import_history(old, str(uuid4()), HistoryImport(messages=[
                    {"id": text, "role": "user", "text": text},
                ]), append=True)
                store.list_messages(chat["id"], 0, 100)
            rows = store.list_messages(chat["id"], 0, 100)["items"]
            self.assertEqual([row["text"] for row in rows], ["First", "Later"])
            self.assertEqual(len(store.list_messages(old, 0, 100)["items"]), 2)

    def test_every_device_and_restart_resolves_same_thread_and_preserves_previous_history(self):
        with TemporaryDirectory() as directory:
            settings = Settings(database_path=Path(directory) / "test.db")
            with TestClient(create_app(settings)) as client:
                store = Store(settings.database_path)
                old = str(uuid4())
                store.create_conversation(old, "Previous chat")
                store.import_history(old, str(uuid4()), HistoryImport(messages=[
                    {"id": "user-1", "role": "user", "text": "Remember my old question"},
                    {"id": "assistant-1", "role": "assistant", "text": "Remembered"},
                ]))
                first = client.put("/api/v1/chat").json()
                second = client.put("/api/v1/chat").json()
                self.assertEqual(first["id"], second["id"])
                url = f"/api/v1/conversations/{first['id']}/messages"
                self.assertEqual(len(client.get(url).json()["items"]), 2)
                self.assertEqual(len(client.get(url).json()["items"]), 2)
                self.assertEqual(len(store.list_messages(old, 0, 100)["items"]), 2)
            with TestClient(create_app(settings)) as restarted:
                self.assertEqual(restarted.put("/api/v1/chat").json()["id"], first["id"])
                self.assertEqual(len(restarted.get(url).json()["items"]), 2)

    def test_import_appends_to_single_chat_without_creating_threads_or_duplicate_retries(self):
        with TemporaryDirectory() as directory, TestClient(create_app(Settings(database_path=Path(directory) / "test.db"))) as client:
            chat = client.put("/api/v1/chat").json()
            for text in ["First source", "Second source"]:
                url = f"/api/v1/chat/imports/{uuid4()}"
                body = {"messages": [{"id": "same-legacy-id", "role": "user", "text": text}]}
                self.assertEqual(client.put(url, json=body).status_code, 201)
                self.assertEqual(client.put(url, json=body).status_code, 200)
            rows = client.get(f"/api/v1/conversations/{chat['id']}/messages").json()["items"]
            self.assertEqual([row["text"] for row in rows], ["First source", "Second source"])
            self.assertEqual(len(client.get("/api/v1/conversations").json()["items"]), 1)
