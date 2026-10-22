import json
import unittest

import httpx

from entourage_server.config import Settings
from entourage_server.llama_cpp import LlamaCpp


class LlamaCppTests(unittest.IsolatedAsyncioTestCase):
    async def test_fragmented_stream_tool_arguments_and_followup(self):
        captured = []
        events = [
            {"delta": {"reasoning_content": "private reasoning"}},
            {"delta": {"content": "Hello 🌍"}},
            {"delta": {"tool_calls": [{"index": 0, "id": "call_1", "function": {
                "name": "calculate", "arguments": '{"operation":"multiply",'}}]}},
            {"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '"a":12,"b":13}'}}]}},
            {"delta": {}, "finish_reason": "tool_calls"},
        ]
        wire = "".join("data: " + json.dumps({"choices": [event]}) + "\n\n" for event in events) + "data: [DONE]\n\n"

        class Fragmented(httpx.AsyncByteStream):
            async def __aiter__(self):
                data = wire.encode()
                for index in range(0, len(data), 7):
                    yield data[index:index + 7]

        def handle(request):
            self.assertEqual(str(request.url), "http://mac:8080/v1/chat/completions")
            captured.append(json.loads(request.content))
            return httpx.Response(200, stream=Fragmented())

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            updates = []
            reply = await LlamaCpp(Settings(llama_cpp_upstream="http://mac:8080"), client).generate([], updates.append)
        self.assertEqual(updates, ["Hello 🌍"])
        call = reply["tool_calls"][0]
        self.assertEqual(json.loads(call["function"]["arguments"])["b"], 13)
        messages = LlamaCpp.wire_messages([
            {"role": "assistant", **reply},
            {"role": "tool", "tool_name": "calculate", "name": "calculate", "tool_call_id": "call_1", "content": "156"},
        ])
        self.assertEqual(messages[0]["tool_calls"][0]["id"], "call_1")
        self.assertNotIn("tool_name", messages[1])
        self.assertEqual(messages[1]["tool_call_id"], "call_1")
        self.assertNotIn("options", captured[0])
        self.assertEqual(captured[0]["reasoning_effort"], "low")

    async def test_reasoning_override_changes_wire_effort_without_changing_other_limits(self):
        captured = []
        def handle(request):
            captured.append(json.loads(request.content))
            return httpx.Response(200, text='data: {"choices":[{"delta":{"content":"Done"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n')
        settings = Settings()
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            for effort in ("medium", "high"):
                await LlamaCpp(settings, client, reasoning_effort=effort).generate([], lambda _: None)
            with self.assertRaises(ValueError):
                LlamaCpp(settings, client, reasoning_effort="unlimited")
        self.assertEqual([body["reasoning_effort"] for body in captured], ["medium", "high"])
        self.assertTrue(all(body["max_tokens"] == settings.max_output_tokens for body in captured))
        self.assertTrue(all(body["reasoning_format"] == "deepseek" for body in captured))

    async def test_incomplete_truncated_error_and_bad_tool_streams_fail(self):
        for body in [
            'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n',
            'data: {"choices":[{"delta":{},"finish_reason":"length"}]}\n\n',
            'data: {"error":{"message":"private"}}\n\n',
            'data: [DONE]\n\n',
            'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"x","function":{"name":"calculate","arguments":"{"}}]},"finish_reason":"tool_calls"}]}\n\n',
        ]:
            with self.subTest(body=body):
                async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))) as client:
                    with self.assertRaises(Exception):
                        await LlamaCpp(Settings(), client).generate([], lambda _: None)

    def test_provider_configuration_validation(self):
        with self.assertRaises(ValueError):
            Settings(inference_provider="unknown")
        for url in ["file:///tmp/model", "http://user:pass@mac", "http://mac/v1", "http://mac:0"]:
            with self.assertRaises(ValueError):
                Settings(llama_cpp_upstream=url)
