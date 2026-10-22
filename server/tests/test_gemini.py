from copy import deepcopy
import json
import unittest

import httpx

from entourage_server.config import Settings
from entourage_server.gemini import Gemini


class GeminiTests(unittest.IsolatedAsyncioTestCase):
    def test_production_configuration_and_missing_key(self):
        Settings(inference_provider="gemini", model="gemini-test")
        with self.assertRaisesRegex(ValueError, "API key"):
            Settings(inference_provider="gemini", execution_enabled=True, trust_local=True)
        with self.assertRaisesRegex(ValueError, "API key"):
            Gemini(Settings(), None)
        configured = Settings(inference_provider="gemini", model="gemini-test", gemini_api_key="private-test-key")
        model = Gemini(configured, None)
        self.assertEqual(model.model, "gemini-test")
        self.assertEqual(model.api_key, "private-test-key")
        self.assertNotIn("private-test-key", repr(configured))

    async def test_wire_tools_signatures_usage_and_no_builtin_search(self):
        captured = []
        signature = {'google': {'thought_signature': 'opaque-test-signature'}}
        call = {'id': 'c1', 'type': 'function', 'function': {'name': 'calculate', 'arguments': '{"operation":"add","a":2,"b":3}'}, 'extra_content': signature}
        def handle(request):
            self.assertEqual(request.headers['authorization'], 'Bearer private-test-key')
            self.assertNotIn('private-test-key', str(request.url))
            captured.append(json.loads(request.content))
            message = {'tool_calls': [call]} if len(captured) == 1 else {'content': '5'}
            return httpx.Response(200, json={'model': 'fixed-model-version', 'usage': {'completion_tokens': 12},
                                            'choices': [{'finish_reason': 'tool_calls' if len(captured) == 1 else 'stop', 'message': message}]})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            model = Gemini(Settings(gemini_api_key='fixture'), client, model='gemini-4-argon', api_key='private-test-key')
            reply = await model.generate([{'role': 'user', 'content': 'Add 2 and 3.'}], lambda _: None)
            messages = [{'role': 'assistant', 'content': '', 'tool_calls': reply['tool_calls']},
                        {'role': 'tool', 'tool_name': 'calculate', 'tool_call_id': 'c1', 'content': '{"result":5}'}]
            original = deepcopy(messages)
            final = await model.generate(messages, lambda _: None)
        self.assertEqual(messages, original)
        self.assertEqual(captured[1]['messages'][0]['tool_calls'][0]['extra_content'], signature)
        self.assertNotIn('tool_name', captured[1]['messages'][1])
        self.assertEqual(final['inference_metadata']['model'], 'fixed-model-version')
        self.assertEqual(captured[0]['max_tokens'], Settings.max_output_tokens)
        self.assertTrue(all(t['type'] == 'function' for t in captured[0]['tools']))

    async def test_errors_and_truncation_never_become_successful_answers(self):
        for status, payload in [(429, {'error': {'message': 'private-test-key'}}),
                                (200, {'choices': [{'finish_reason': 'length', 'message': {'content': 'partial'}}]}),
                                (200, {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
                                    {'id': 'c', 'function': {'name': 'calculate', 'arguments': '[]'}}]}}]})]:
            with self.subTest(status=status, payload=payload):
                async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(status, json=payload))) as client:
                    with self.assertRaises((RuntimeError, ValueError)) as error:
                        await Gemini(Settings(), client, model='test', api_key='private-test-key').generate([], lambda _: None)
                    self.assertNotIn('private-test-key', str(error.exception))
