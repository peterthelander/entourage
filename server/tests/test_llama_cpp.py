import json
import unittest

import httpx

from entourage_server.config import Settings
from entourage_server.llama_cpp import LlamaCpp
from entourage_server.inference_errors import InferenceError


class LlamaCppTests(unittest.IsolatedAsyncioTestCase):
    async def test_large_transcript_uses_actual_template_and_tokens_before_generation(self):
        for count, should_fit in ((8000, False), (4000, True)):
            requests = []

            def handle(request):
                requests.append(request.url.path)
                body = json.loads(request.content)
                if request.url.path == "/apply-template":
                    self.assertEqual(body["messages"][0]["content"], "source-id-" * 1500)
                    self.assertTrue(body["tools"])
                    return httpx.Response(200, json={"prompt": "engine-formatted transcript including tool definitions"})
                if request.url.path == "/tokenize":
                    self.assertIn("including tool definitions", body["content"])
                    return httpx.Response(200, json={"tokens": [1] * count})
                return httpx.Response(200, text='data: {"choices":[{"delta":{"content":"Grounded answer"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n')

            async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
                model = LlamaCpp(Settings(), client)
                if should_fit:
                    result = await model.generate([{"role": "user", "content": "source-id-" * 1500}], lambda _: None)
                    self.assertEqual(result["content"], "Grounded answer")
                else:
                    with self.assertRaises(InferenceError) as caught:
                        await model.generate([{"role": "user", "content": "source-id-" * 1500}], lambda _: None)
                    self.assertEqual(caught.exception.code, "context_limit")
                    self.assertIn(f"{count:,} input tokens", str(caught.exception))
                    self.assertIn(f"{model.settings.max_output_tokens:,} reserved response tokens", str(caught.exception))
                    self.assertIn(f"{model.settings.context_tokens:,}-token context window", str(caught.exception))
            self.assertEqual(requests, ["/apply-template", "/tokenize"] + (["/v1/chat/completions"] if should_fit else []))

    async def test_inference_failures_report_safe_distinct_causes(self):
        examples = [
            (500, {"error": {"message": "private source text: Jinja Exception: System message must be at the beginning."}}, "prompt_template"),
            (400, {"error": {"type": "exceed_context_size_error", "message": "private input"}}, "context_limit"),
            (503, {"error": {"message": "private URL or token"}}, "upstream_http"),
        ]
        for status, body, expected in examples:
            with self.subTest(expected=expected):
                async with httpx.AsyncClient(transport=httpx.MockTransport(
                        lambda _: httpx.Response(status, json=body))) as client:
                    with self.assertRaises(InferenceError) as caught:
                        await LlamaCpp(Settings(), client).generate([], lambda _: None)
                self.assertEqual(caught.exception.code, expected)
                self.assertNotIn("private", str(caught.exception))
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200,
                text='data: {"choices":[{"delta":{"reasoning_content":"private reasoning"},"finish_reason":"length"}]}\n\n'))) as client:
            with self.assertRaises(InferenceError) as caught:
                await LlamaCpp(Settings(), client).generate([], lambda _: None)
        self.assertEqual(caught.exception.code, "output_limit")
        self.assertIn("response token limit", str(caught.exception))
        self.assertNotIn("private", str(caught.exception))

    async def test_finalization_removes_all_tools(self):
        captured = []
        def handle(request):
            captured.append(json.loads(request.content))
            return httpx.Response(200, text='data: {"choices":[{"delta":{"content":"Unknown from the evidence."},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n')
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            reply = await LlamaCpp(Settings(), client).finalize([], lambda _: None)
        self.assertEqual(captured[0]["tools"], [])
        self.assertEqual(reply["content"], "Unknown from the evidence.")

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
