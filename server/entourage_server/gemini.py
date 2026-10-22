"""Gemini Chat Completions transport for the server-owned agent."""

import asyncio
from copy import deepcopy
import json

from .agent import available_tools


class GeminiHTTPError(RuntimeError):
    def __init__(self, status):
        self.http_status = status
        super().__init__(f"Gemini inference returned HTTP {status}.")


class Gemini:
    def __init__(self, settings, client, *, model=None, api_key=None, reasoning_effort="low"):
        self.settings, self.client = settings, client
        if reasoning_effort not in ("low", "medium", "high"):
            raise ValueError("reasoning_effort must be low, medium or high.")
        self.model = model or settings.model
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        if not self.api_key.strip():
            raise ValueError("Gemini inference requires a server-side API key.")
        self.reasoning_effort = reasoning_effort

    @staticmethod
    def wire_messages(messages):
        # Preserve provider extensions on tool calls, including thought signatures.
        result = deepcopy(messages)
        for message in result:
            message.pop("tool_name", None)
            for call in message.get("tool_calls", []):
                args = call["function"]["arguments"]
                if not isinstance(args, str):
                    call["function"]["arguments"] = json.dumps(args)
        return result

    async def generate(self, messages, on_text):
        body = {"model": self.model, "messages": self.wire_messages(messages),
                "tools": available_tools(self.settings), "stream": False,
                "max_tokens": self.settings.max_output_tokens, "reasoning_effort": self.reasoning_effort}
        async with asyncio.timeout(300):
            async with self.client.stream("POST", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                                          headers={"Authorization": "Bearer " + self.api_key}, json=body,
                                          timeout=300) as response:
                if response.status_code != 200:
                    raise GeminiHTTPError(response.status_code)
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > 2 * 1024 * 1024:
                        raise RuntimeError("Gemini response exceeded the size limit.")
        payload = json.loads(data)
        choices = payload.get("choices", [])
        if len(choices) != 1 or choices[0].get("finish_reason") not in ("stop", "tool_calls"):
            raise RuntimeError("Gemini output was blocked, truncated or incomplete.")
        message = choices[0]["message"]
        content, calls = message.get("content") or "", message.get("tool_calls") or []
        if not isinstance(content, str) or not isinstance(calls, list):
            raise RuntimeError("Gemini returned malformed content or calls.")
        for call in calls:
            if not call.get("id") or not call.get("function", {}).get("name"):
                raise RuntimeError("Gemini returned an incomplete tool call.")
            arguments = call["function"].get("arguments")
            arguments = json.loads(arguments) if isinstance(arguments, str) else arguments
            if not isinstance(arguments, dict):
                raise RuntimeError("Gemini tool arguments must be an object.")
        on_text(content)
        return {"content": content, "tool_calls": calls,
                "inference_metadata": {"provider": "gemini", "model": payload.get("model"),
                                       "usage": payload.get("usage")}}
