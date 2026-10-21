import json
import unittest
from dataclasses import replace

import httpx

from entourage_server.agent import available_tools
from entourage_server.config import Settings
from entourage_server.web_search import search_web


class WebSearchTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def grounded():
        return {"candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"text": "Private reasoning", "thought": True}, {"text": "Apples and cider."}]},
            "groundingMetadata": {"webSearchQueries": ["Harvest orchard town"],
                "groundingChunks": [{"web": {"title": "<b>Orchard</b>", "uri": "https://example.com"}},
                                    {"web": {"uri": "javascript:alert(1)"}},
                                    {"web": {"uri": "https://user:secret@example.com"}}],
                "groundingSupports": [{"segment": {"text": "Apples and cider."}, "groundingChunkIndices": [0, 1]}],
                "searchEntryPoint": {"renderedContent": "<div>Google suggestions</div>"}}}]}

    async def run_search(self, handler, args=None):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await search_web(args or {"query": "Harvest orchard town"}, "private-key", client=client)

    async def test_sources_are_bounded_and_unsafe_links_are_excluded(self):
        def respond(request):
            self.assertEqual(request.headers["x-goog-api-key"], "private-key")
            self.assertEqual(request.method, "POST")
            self.assertEqual(str(request.url), "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent")
            body = json.loads(request.content)
            self.assertEqual(body["tools"], [{"googleSearch": {}}])
            self.assertEqual(body["contents"], [{"role": "user", "parts": [{"text": "Harvest orchard town"}]}])
            self.assertNotIn("private-key", str(request.url))
            return httpx.Response(200, json=self.grounded())
        result = await self.run_search(respond)
        self.assertEqual(result["status"], "results")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["title"], "Orchard")
        self.assertEqual(result["summary"], "Apples and cider.")
        self.assertEqual(result["grounding_supports"][0]["source_indices"], [0])
        self.assertEqual(result["search_suggestions_html"], "<div>Google suggestions</div>")
        self.assertNotIn("private-key", json.dumps(result))

    async def test_failures_do_not_leak_provider_body_or_key(self):
        for status in (401, 429, 500):
            result = await self.run_search(lambda request: httpx.Response(status, text="private-key provider error"))
            self.assertEqual(result["status"], "unavailable")
            self.assertNotIn("private-key", json.dumps(result))
        for body in (b"not json", b"[]", b'{"web":null}', b"x" * (512 * 1024 + 1)):
            result = await self.run_search(lambda request: httpx.Response(200, content=body))
            self.assertEqual(result["status"], "unavailable")

    async def test_timeout_and_empty_results(self):
        def timeout(request):
            raise httpx.ReadTimeout("private-key", request=request)
        self.assertEqual((await self.run_search(timeout))["status"], "unavailable")
        payload = self.grounded()
        payload["candidates"][0]["groundingMetadata"] = {}
        result = await self.run_search(lambda r: httpx.Response(200, json=payload))
        self.assertEqual(result["status"], "no_results")
        self.assertNotIn("summary", result)

    async def test_incomplete_and_blocked_research_is_not_success(self):
        for reason in ("MAX_TOKENS", "SAFETY"):
            payload = self.grounded()
            payload["candidates"][0]["finishReason"] = reason
            self.assertEqual((await self.run_search(lambda r: httpx.Response(200, json=payload)))["status"], "unavailable")

    async def test_summary_is_bounded(self):
        payload = self.grounded()
        payload["candidates"][0]["content"]["parts"] = [{"text": "x" * 10000}]
        self.assertEqual(len((await self.run_search(lambda r: httpx.Response(200, json=payload)))["summary"]), 6000)

    async def test_invalid_queries_and_missing_configuration(self):
        for args in ({}, {"query": " "}, {"query": 3}, {"query": "x" * 401}, {"query": "x", "extra": True}):
            with self.assertRaises(ValueError):
                await search_web(args, "")
        self.assertEqual((await search_web({"query": "orchard"}, ""))["status"], "unavailable")

    def test_only_configured_servers_advertise_search(self):
        settings = Settings()
        self.assertNotIn("searchWeb", [t["function"]["name"] for t in available_tools(settings)])
        configured = replace(settings, gemini_api_key="private-key")
        self.assertIn("searchWeb", [t["function"]["name"] for t in available_tools(configured)])
        self.assertNotIn("private-key", repr(configured))

    def test_model_id_cannot_change_request_path(self):
        for model in ("", "../model", "model?key=x", "model:action"):
            with self.assertRaises(ValueError):
                Settings(web_search_model=model)
