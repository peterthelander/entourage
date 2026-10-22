import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from entourage_server.agent import Ollama, build_context, calculate
from entourage_server.app import create_app
from entourage_server.config import Settings
from entourage_server.gemini import Gemini
from entourage_server.execution_store import ExecutionStore
from entourage_server.worker_lock import worker_lock
from entourage_server.journals import export_journals
from entourage_server.storage import SINGLE_CHAT_ID

TOKEN = "test-owner-token-" * 3
KEY = "test-device-key-" * 3


class ScriptedModel:
    def __init__(self, name="calculate", arguments=None):
        self.name = name
        self.arguments = arguments if arguments is not None else {"operation": "multiply", "a": 12, "b": 13}
        self.requests = []

    async def generate(self, messages, on_text):
        self.requests.append(json.loads(json.dumps(messages)))
        if len(self.requests) == 1:
            return {"tool_calls": [{"function": {"name": self.name, "arguments": self.arguments}}]}
        on_text("The answer ")
        await asyncio.sleep(0.02)
        return {"content": "The answer is 156."}


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "agent.db"
        self.settings = Settings(database_path=self.path, execution_enabled=True, api_token=TOKEN, device_timeout_seconds=1)
        self.model = ScriptedModel()

    def client(self, model=None):
        return TestClient(create_app(self.settings, model or self.model), headers={"Authorization": f"Bearer {TOKEN}"})

    def submit(self, client, conversation=None):
        self.device, self.conversation, self.turn = map(str, (uuid4(), uuid4(), uuid4()))
        self.conversation = conversation or self.conversation
        self.assertEqual(client.put(f"/api/v1/devices/{self.device}", json={"key": KEY}).status_code, 200)
        client.put(f"/api/v1/conversations/{self.conversation}", json={})
        self.url = f"/api/v1/conversations/{self.conversation}/turns/{self.turn}"
        self.body = {"text": "Calculate 12 times 13", "device_id": self.device}
        self.assertEqual(client.put(self.url, json=self.body).status_code, 202)

    def wait(self, client, statuses):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            response = client.get(f"/api/v1/turns/{self.turn}")
            self.assertEqual(response.status_code, 200)
            snapshot = response.json()
            if snapshot["status"] in statuses:
                return snapshot
            time.sleep(0.02)
        self.fail(f"Timed out waiting for {statuses}: {snapshot}")

    def test_entire_calculator_loop_finishes_without_polling_client_and_retries_do_not_repeat(self):
        with self.client() as client:
            self.submit(client)
            # No outstanding browser request while the complete agent loop runs.
            time.sleep(0.3)
            result = self.wait(client, {"completed", "failed"})
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["answer"], "The answer is 156.")
            self.assertGreater(result["revision"], 1)
            self.assertNotIn("checkpoint", result)
            self.assertEqual(client.put(self.url, json=self.body).status_code, 200)
            self.assertEqual(len(self.model.requests), 2)
            self.assertEqual(json.loads(self.model.requests[-1][-1]["content"])["result"], 156)
            items = client.get(f"/api/v1/conversations/{self.conversation}/messages").json()["items"]
            self.assertEqual([item["kind"] for item in items], ["user", "tool", "assistant"])
        # Model must not be called again for the persisted completed turn.
        with self.client(ScriptedModel()) as restarted:
            self.assertEqual(restarted.get(f"/api/v1/turns/{self.turn}").json()["answer"], result["answer"])

    def test_configured_gemini_runs_persisted_calculator_loop(self):
        from dataclasses import replace
        settings = replace(self.settings, inference_provider="gemini", model="gemini-test", gemini_api_key="private-test-key")
        requests = []
        signature = {"google": {"thought_signature": "opaque"}}
        def handle(request):
            body = json.loads(request.content)
            requests.append(body)
            self.assertEqual(body["model"], "gemini-test")
            if len(requests) == 1:
                message = {"tool_calls": [{"id": "c1", "type": "function", "extra_content": signature,
                    "function": {"name": "calculate", "arguments": '{"operation":"multiply","a":12,"b":13}'}}]}
                finish = "tool_calls"
            else:
                self.assertEqual(body["messages"][-2]["tool_calls"][0]["extra_content"], signature)
                self.assertEqual(json.loads(body["messages"][-1]["content"])["result"], 156)
                message, finish = {"content": "The answer is 156."}, "stop"
            return httpx.Response(200, json={"choices": [{"finish_reason": finish, "message": message}]})
        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
        with patch("entourage_server.app.Gemini", side_effect=lambda config, _: Gemini(config, mock_client)) as selected:
            with TestClient(create_app(settings), headers={"Authorization": f"Bearer {TOKEN}"}) as client:
                self.submit(client)
                result = self.wait(client, {"completed", "failed"})
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["answer"], "The answer is 156.")
                self.assertEqual(client.get("/api/v1/health").json()["model"], "gemini-test")
                selected.assert_called_once()
                self.assertNotIn("private-test-key", json.dumps(result))
        asyncio.run(mock_client.aclose())

    def test_memory_tool_retrieves_old_evidence_and_persists_result(self):
        store = ExecutionStore(self.path)
        store.initialize()
        store.single_chat()
        with store.connect(write=True) as db:
            for text in ["Ski trip: Vermont", "Correction: ski trip: Maine", *["Unrelated recent message"] * 15]:
                db.execute("INSERT INTO messages(conversation_id,role,kind,text,created_at) VALUES(?,'user','user',?,?)",
                           (SINGLE_CHAT_ID, text, "2026-10-16T12:00:00+00:00"))
        export_journals(self.path, self.path.parent / "vault/journals", "UTC")
        model = ScriptedModel("searchMemories", {"keywords": ["ski"]})
        with self.client(model) as client:
            self.submit(client)
            result = self.wait(client, {"completed", "failed"})
            self.assertEqual(result["status"], "completed")
            self.assertNotIn("Vermont", json.dumps(model.requests[0]))
            evidence = json.loads(model.requests[-1][-1]["content"])
            self.assertEqual(evidence["status"], "matches")
            self.assertIn("Maine", evidence["results"][0]["excerpt"])
            self.assertIn("message=2", evidence["results"][0]["source"])
            rows = client.get(f"/api/v1/conversations/{self.conversation}/messages").json()["items"]
            self.assertTrue(any(row["kind"] == "tool" and "searchMemories" in row["text"] for row in rows))

    def test_web_search_results_reach_model_and_saved_history(self):
        model = ScriptedModel("searchWeb", {"query": "Harvest orchard town"})
        evidence = {"status": "results", "results": [{"title": "Orchard", "url": "https://example.com"}],
                    "summary": "Cider", "search_suggestions_html": "<div>Google</div>"}
        with patch("entourage_server.agent.search_web", new=AsyncMock(return_value=evidence)) as search:
            with self.client(model) as client:
                self.submit(client)
                self.assertEqual(self.wait(client, {"completed", "failed"})["status"], "completed")
                model_evidence = dict(evidence)
                model_evidence.pop("search_suggestions_html")
                self.assertEqual(json.loads(model.requests[-1][-1]["content"]), model_evidence)
                rows = client.get(f"/api/v1/conversations/{self.conversation}/messages").json()["items"]
                self.assertTrue(any(row["kind"] == "tool" and "searchWeb" in row["text"] for row in rows))
                self.assertTrue(any("<div>Google</div>" in row["text"] for row in rows))
            search.assert_awaited_once_with({"query": "Harvest orchard town"}, "", model="gemini-2.5-flash-lite")

    def test_search_then_calendar_then_event_uses_same_persisted_tool_loop(self):
        class ResearchModel:
            def __init__(self):
                self.requests = []

            async def generate(model, messages, on_text):
                model.requests.append(json.loads(json.dumps(messages)))
                step = len(model.requests)
                if step == 1:
                    name, arguments = "searchWeb", {"query": "official venue schedule October 20"}
                elif step == 2:
                    self.assertIn("https://example.com/calendar", messages[-1]["content"])
                    name, arguments = "readWebPage", {"url": "https://example.com/calendar"}
                elif step == 3:
                    self.assertIn("https://example.com/dawkins", messages[-1]["content"])
                    name, arguments = "readWebPage", {"url": "https://example.com/dawkins"}
                else:
                    self.assertIn("7:00 PM", messages[-1]["content"])
                    return {"content": "Richard Dawkins at 7:00 PM. Source: https://example.com/dawkins"}
                return {"tool_calls": [{"id": f"lookup_{step}", "function": {"name": name, "arguments": arguments}}]}

        model = ResearchModel()
        pages = [{"status": "read", "text": "October 20 events", "links": [{"text": "Richard Dawkins", "url": "https://example.com/dawkins"}]},
                 {"status": "read", "url": "https://example.com/dawkins", "text": "Richard Dawkins, October 20, 7:00 PM"}]
        with patch("entourage_server.agent.search_web", new=AsyncMock(return_value={"status": "results", "results": [{"url": "https://example.com/calendar"}]})), \
             patch("entourage_server.agent.read_web_page", new=AsyncMock(side_effect=pages)) as read:
            with self.client(model) as client:
                self.submit(client)
                result = self.wait(client, {"completed", "failed"})
                self.assertEqual(result["status"], "completed")
                self.assertIn("Richard Dawkins", result["answer"])
                rows = client.get(f"/api/v1/conversations/{self.conversation}/messages").json()["items"]
                tools = [row["text"].split("\n")[0] for row in rows if row["kind"] == "tool"]
                self.assertEqual(tools, ["searchWeb", "readWebPage", "readWebPage"])
            self.assertEqual(read.await_count, 2)

    def test_blocked_page_result_reaches_answering_model(self):
        model = ScriptedModel("readWebPage", {"url": "https://example.com/calendar"})
        with patch("entourage_server.agent.read_web_page", new=AsyncMock(return_value={
            "status": "unavailable", "error": "Page returned HTTP 403; contents were not verified."})):
            with self.client(model) as client:
                self.submit(client)
                self.assertEqual(self.wait(client, {"completed", "failed"})["status"], "completed")
                result = json.loads(model.requests[-1][-1]["content"])
                self.assertEqual(result["status"], "unavailable")
                self.assertNotIn("text", result)

    def test_worker_sends_current_session_without_timestamps_or_old_requests(self):
        store = ExecutionStore(self.path)
        store.initialize()
        store.single_chat()
        instant = datetime.now(timezone.utc)
        with store.connect(write=True) as db:
            for text, role, age in [("Suggest coding improvements", "user", timedelta(days=1)),
                                    ("Apple picking", "user", timedelta(minutes=10)),
                                    ("Which friends?", "assistant", timedelta(minutes=9))]:
                db.execute("INSERT INTO messages(conversation_id,role,kind,text,created_at) VALUES(?,?,?,?,?)",
                           (SINGLE_CHAT_ID, role, role, text, (instant - age).isoformat()))
        with self.client() as client:
            self.submit(client, conversation=SINGLE_CHAT_ID)
            self.assertEqual(self.wait(client, {"completed", "failed"})["status"], "completed")
        sent = self.model.requests[0]
        self.assertEqual([m["content"] for m in sent[1:]],
                         ["Apple picking", "Which friends?", self.body["text"]])
        self.assertTrue(all(set(m) == {"role", "content"} for m in sent))
        self.assertEqual(len(store.context_history(SINGLE_CHAT_ID)), 5)

    def test_inventory_and_date_read_tools_execute_server_side(self):
        store = ExecutionStore(self.path)
        store.initialize()
        store.single_chat()
        with store.connect(write=True) as db:
            db.execute("INSERT INTO messages(conversation_id,role,kind,text,created_at) VALUES(?,'user','user',?,?)",
                       (SINGLE_CHAT_ID, "A Shakespeare sonnet about independence", "2026-10-15T12:00:00+00:00"))
        export_journals(self.path, self.path.parent / "vault/journals", "UTC")
        for name, args in [("getMemoryInventory", {}), ("readMemories", {"start_date": "2026-10-15"})]:
            model = ScriptedModel(name, args)
            with self.client(model) as client:
                self.submit(client)
                self.assertEqual(self.wait(client, {"completed", "failed"})["status"], "completed")
                found = json.loads(model.requests[-1][-1]["content"])
                self.assertEqual(found["status"], "ready")
                self.assertEqual(found["coverage"]["mode"], "automatic")
                if name == "getMemoryInventory":
                    self.assertEqual(found["earliest_date"], "2026-10-15")
                else:
                    self.assertIn("Shakespeare", found["results"][0]["excerpt"])

    def test_device_tool_is_bound_to_device_key_and_result_is_idempotent(self):
        model = ScriptedModel("getCurrentLocation", {})
        with self.client(model) as client:
            self.submit(client)
            snapshot = self.wait(client, {"waiting_for_device"})
            request = snapshot["device_requests"][0]
            url = f"/api/v1/turns/{self.turn}/device-results/{request['id']}"
            body = {"device_id": self.device, "content": "Location permission was denied."}
            self.assertEqual(client.put(url, json=body, headers={"X-Device-Key": "wrong" * 10}).status_code, 403)
            self.assertEqual(client.put(url, json=body, headers={"X-Device-Key": KEY}).status_code, 200)
            self.assertEqual(client.put(url, json=body, headers={"X-Device-Key": KEY}).status_code, 200)
            self.assertEqual(client.put(url, json={**body, "content": "different"}, headers={"X-Device-Key": KEY}).status_code, 409)
            self.assertEqual(self.wait(client, {"completed", "failed"})["status"], "completed")
            self.assertIn("denied", model.requests[-1][-1]["content"])

    def test_unavailable_device_expires_and_server_reports_tool_failure_to_model(self):
        model = ScriptedModel("getCurrentTime", {})
        with self.client(model) as client:
            self.submit(client)
            self.assertEqual(self.wait(client, {"completed", "failed"})["status"], "completed")
            self.assertIn("did not respond", model.requests[-1][-1]["content"])

    def test_shutdown_during_device_wait_is_not_replayed(self):
        with self.client(ScriptedModel("getDeviceContext", {})) as client:
            self.submit(client)
            self.wait(client, {"waiting_for_device"})
        with self.client(ScriptedModel()) as restarted:
            snapshot = restarted.get(f"/api/v1/turns/{self.turn}").json()
            self.assertEqual(snapshot["status"], "needs_review")
            self.assertEqual(restarted.put(self.url, json=self.body).status_code, 200)

    def test_auth_origin_and_device_registration_checks(self):
        with self.client() as client:
            self.assertEqual(client.get("/api/v1/conversations", headers={"Authorization": "Bearer wrong"}).status_code, 401)
            self.assertEqual(client.get("/api/v1/conversations", headers={"Origin": "https://untrusted.example"}).status_code, 403)
            preflight = client.options("/api/v1/conversations", headers={"Origin": "http://localhost:8081", "Access-Control-Request-Method": "PUT", "Access-Control-Request-Headers": "authorization,content-type"})
            self.assertEqual(preflight.status_code, 200)
            self.assertEqual(preflight.headers["access-control-allow-origin"], "http://localhost:8081")
            conv = str(uuid4())
            client.put(f"/api/v1/conversations/{conv}", json={})
            result = client.put(f"/api/v1/conversations/{conv}/turns/{uuid4()}", json={"text": "hello", "device_id": str(uuid4())})
            self.assertEqual(result.status_code, 403)

    def test_failed_generation_is_durable_and_not_committed_as_an_answer(self):
        class BrokenModel:
            async def generate(self, messages, on_text):
                on_text("Incomplete answer")
                raise RuntimeError("private upstream exception")

        with self.client(BrokenModel()) as client:
            self.submit(client)
            result = self.wait(client, {"failed"})
            self.assertIsNone(result["answer"])
            self.assertNotIn("private upstream", result["error"])
            latest = client.get(f"/api/v1/conversations/{self.conversation}/latest-turn").json()
            self.assertEqual(latest["status"], "failed")
            items = client.get(f"/api/v1/conversations/{self.conversation}/messages").json()["items"]
            self.assertEqual([item["kind"] for item in items], ["user"])

    def test_tool_budget_bounds_a_model_that_keeps_requesting_tools(self):
        class LoopingModel:
            async def generate(self, messages, on_text):
                return {"tool_calls": [{"function": {"name": "calculate", "arguments": {"operation": "add", "a": 1, "b": 2}}}]}

        with self.client(LoopingModel()) as client:
            self.submit(client)
            self.assertIn("limit", self.wait(client, {"failed"})["error"])
            items = client.get(f"/api/v1/conversations/{self.conversation}/messages").json()["items"]
            self.assertEqual(sum(item["kind"] == "tool" for item in items), 4)

    def test_schema_one_history_is_preserved_during_upgrade(self):
        store = ExecutionStore(self.path)
        store.initialize()
        conversation = str(uuid4())
        store.create_conversation(conversation, "Existing history")
        # Recreate the exact differences from the previous schema.
        with store.connect(write=True) as db:
            db.execute("DROP TABLE device_requests")
            db.execute("DROP TABLE devices")
            db.execute("ALTER TABLE turns DROP COLUMN checkpoint")
            db.execute("PRAGMA user_version=1")
        store.initialize()
        self.assertEqual(store.list_conversations(0, 50)["items"][0]["title"], "Existing history")
        store.register_device(str(uuid4()), KEY)
        with store.connect() as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 2)

    def test_lock_and_crash_recovery(self):
        store = ExecutionStore(self.path)
        store.initialize()
        with worker_lock(self.path):
            with self.assertRaises(RuntimeError):
                with worker_lock(self.path):
                    pass
        with worker_lock(self.path):
            pass
        conv, turn = str(uuid4()), str(uuid4())
        store.create_conversation(conv, "Crash recovery")
        store.create_turn(conv, turn, "hello", str(uuid4()))
        store.claim()
        store.recover()
        self.assertEqual(store.get_turn(turn)["status"], "needs_review")

    def test_stop_cancels_inference_and_worker_handles_next_request(self):
        class SlowModel:
            def __init__(self):
                self.started, self.cancelled = False, False

            async def generate(self, messages, on_text):
                if not self.started:
                    self.started = True
                    try:
                        await asyncio.sleep(30)
                    except asyncio.CancelledError:
                        self.cancelled = True
                        raise
                return {"content": "Next request completed"}

        model = SlowModel()
        with self.client(model) as client:
            self.submit(client)
            deadline = time.monotonic() + 3
            while not model.started and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(model.started)
            cancel_url = f"/api/v1/turns/{self.turn}/cancellation"
            self.assertEqual(client.put(cancel_url).json()["status"], "failed")
            self.assertEqual(client.put(cancel_url).status_code, 200)
            self.turn = str(uuid4())
            client.put(f"/api/v1/conversations/{self.conversation}/turns/{self.turn}", json=self.body)
            self.assertEqual(self.wait(client, {"completed", "failed"})["status"], "completed")
            self.assertTrue(model.cancelled)
            self.assertEqual(client.put(f"/api/v1/turns/{self.turn}/cancellation").status_code, 409)

    def test_dismiss_review_unblocks_conversation_and_late_device_result_is_rejected(self):
        with self.client(ScriptedModel("getCurrentTime", {})) as client:
            self.submit(client)
            request = self.wait(client, {"waiting_for_device"})["device_requests"][0]
        with self.client(ScriptedModel()) as restarted:
            self.assertEqual(restarted.get(f"/api/v1/turns/{self.turn}").json()["status"], "needs_review")
            restarted.put(f"/api/v1/turns/{self.turn}/cancellation")
            late = restarted.put(f"/api/v1/turns/{self.turn}/device-results/{request['id']}",
                                 json={"device_id": self.device, "content": "late"}, headers={"X-Device-Key": KEY})
            self.assertEqual(late.status_code, 409)
            self.turn = str(uuid4())
            self.assertEqual(restarted.put(f"/api/v1/conversations/{self.conversation}/turns/{self.turn}", json=self.body).status_code, 202)
            self.assertEqual(self.wait(restarted, {"completed", "failed"})["status"], "completed")


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_streaming_options_unicode_tool_calls_and_final_line(self):
        captured = []

        def handle(request):
            captured.append(json.loads(request.content))
            return httpx.Response(200, content=(
                '{"message":{"content":"Hello 🌍"}}\n'
                '{"message":{"tool_calls":[{"function":{"name":"getCurrentTime","arguments":{}}}]},"done":true}'
            ).encode())

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            updates = []
            reply = await Ollama(Settings(), client).generate([], updates.append)
        self.assertEqual(reply["content"], "Hello 🌍")
        self.assertEqual(reply["tool_calls"][0]["function"]["name"], "getCurrentTime")
        self.assertEqual(captured[0]["options"], {"num_ctx": 8192, "num_predict": 1536})
        self.assertFalse(captured[0]["think"])
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            await Ollama(Settings(context_tokens=16384, max_output_tokens=2048), client).generate([], lambda _: None)
        self.assertEqual(captured[-1]["options"], {"num_ctx": 16384, "num_predict": 2048})

    async def test_incomplete_and_error_streams_fail(self):
        for body in [b'{"message":{"content":"partial"}}\n', b'{"error":"private details"}\n', b'not json\n']:
            async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body))) as client:
                with self.assertRaises(Exception):
                    await Ollama(Settings(), client).generate([], lambda _: None)

    def test_context_and_calculator_limits(self):
        context = build_context("latest", [{"role": "assistant", "text": "orphan"}, {"role": "user", "text": "prior"}])
        self.assertEqual([message["content"] for message in context[1:]], ["prior", "latest"])
        self.assertEqual(json.loads(calculate({"operation": "percentage", "a": 18, "b": 250}))["result"], 45)
        for args in [{"operation": "add", "a": True, "b": 1}, {"operation": "divide", "a": 1, "b": 0}]:
            with self.assertRaises((ValueError, ZeroDivisionError)):
                calculate(args)

    def test_larger_context_retains_more_than_twelve_messages_and_respects_budget(self):
        history = [{"role": "user" if i % 2 == 0 else "assistant", "text": f"{i}:" + "x" * 600}
                   for i in range(60)]
        small = build_context("latest", history, Settings(context_tokens=4096, max_output_tokens=768))
        large = build_context("latest", history, Settings(context_tokens=16384, max_output_tokens=2048))
        self.assertGreater(len(large), 14)
        self.assertGreater(sum(len(m["content"]) for m in large[1:]), 6000)
        self.assertGreater(len(large), len(small))
        self.assertEqual(large[1]["role"], "user")
        self.assertEqual(large[-1], {"role": "user", "content": "latest"})
        self.assertEqual(large[-2]["content"], history[-1]["text"])
        self.assertLessEqual(sum(len(m["content"]) for m in large[1:]), 20480)

    def test_context_storage_fetches_older_completed_messages(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        store = ExecutionStore(Path(directory.name) / "context.db")
        store.initialize()
        store.create_conversation("context-test", "Context test")
        with store.connect(write=True) as db:
            for i in range(140):
                db.execute("INSERT INTO messages(conversation_id,role,kind,text,created_at) VALUES(?,?,?,?,?)",
                           ("context-test", "user", "user", str(i), "2026-10-17T12:00:00+00:00"))
        history = store.context_history("context-test")
        self.assertEqual(len(history), 128)
        self.assertEqual(history[0]["text"], "12")
        self.assertEqual(history[-1]["text"], "139")
