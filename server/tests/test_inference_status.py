from dataclasses import replace
import unittest

import httpx

from entourage_server.config import Settings
from entourage_server.inference_status import inference_status


class InferenceStatusTests(unittest.IsolatedAsyncioTestCase):
    async def probe(self, reply, *, model="old.gguf", status=200):
        settings = Settings(inference_provider="llama_cpp", execution_enabled=True,
                            trust_local=True, model=model)
        async with httpx.AsyncClient(transport=httpx.MockTransport(
                lambda _: httpx.Response(status, json=reply))) as client:
            return await inference_status(settings, client)

    async def test_loaded_model_is_not_the_configured_label_after_a_model_swap(self):
        result = await self.probe({"data": [{"id": "/Downloads/Qwen-new.gguf"}]})
        self.assertEqual(result.status, "model_mismatch")
        self.assertEqual(result.loaded_model, "/Downloads/Qwen-new.gguf")
        self.assertEqual(result.configured_model, "old.gguf")
        self.assertIn("restart", result.message)

    async def test_exact_id_and_explicit_alias_are_verified(self):
        for metadata in ({"id": "chosen"}, {"id": "actual.gguf", "aliases": ["chosen"]}):
            result = await self.probe({"data": [metadata]}, model="chosen")
            self.assertEqual(result.status, "ready")
            self.assertEqual(result.loaded_model, metadata["id"])

    async def test_offline_and_malformed_metadata_do_not_claim_a_loaded_model(self):
        for reply, status in (({}, 503), ({"data": []}, 200), ({"data": "private"}, 200),
                              ({"data": [{"id": None}]}, 200)):
            result = await self.probe(reply, status=status)
            self.assertEqual(result.status, "unavailable")
            self.assertIsNone(result.loaded_model)
            self.assertNotIn("private", result.message)

    async def test_connection_failure_is_safe_and_other_providers_are_only_configured(self):
        settings = Settings(inference_provider="llama_cpp", execution_enabled=True, trust_local=True)

        def offline(request):
            raise httpx.ConnectError("private address and token", request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(offline)) as client:
            result = await inference_status(settings, client)
        self.assertEqual(result.status, "unavailable")
        self.assertNotIn("private", result.message)
        result = await inference_status(replace(settings, inference_provider="ollama"), None)
        self.assertEqual(result.status, "configured")
        self.assertIsNone(result.loaded_model)
