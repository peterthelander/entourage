"""llama.cpp Chat Completions transport; agent execution remains on this server."""

import asyncio
import json

from .agent import available_tools


class LlamaCpp:
    def __init__(self, settings, client):
        self.settings, self.client = settings, client

    @staticmethod
    def wire_messages(messages):
        result = []
        for message in messages:
            item = {key: value for key, value in message.items() if key != "tool_name"}
            if "tool_calls" in item:
                item["tool_calls"] = [{
                    "id": call["id"], "type": "function", "function": {
                        "name": call["function"]["name"],
                        "arguments": (call["function"]["arguments"] if isinstance(call["function"]["arguments"], str)
                                      else json.dumps(call["function"]["arguments"])),
                    },
                } for call in item["tool_calls"]]
            result.append(item)
        return result

    async def generate(self, messages, on_text):
        body = {"model": self.settings.model, "messages": self.wire_messages(messages),
                "tools": available_tools(self.settings), "stream": True, "max_tokens": self.settings.max_output_tokens,
                "reasoning_format": "deepseek", "reasoning_effort": "low"}
        content, calls, size, finished = "", {}, 0, False
        async with asyncio.timeout(300):
            async with self.client.stream("POST", self.settings.llama_cpp_upstream.rstrip("/") +
                                          "/v1/chat/completions", json=body) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"llama.cpp returned HTTP {response.status_code}.")
                async for line in response.aiter_lines():
                    size += len(line.encode("utf-8"))
                    if size > 2 * 1024 * 1024:
                        raise RuntimeError("Model response exceeded the size limit.")
                    if not line or line.startswith(":"):
                        continue
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        if not finished:
                            raise RuntimeError("llama.cpp ended without a finish reason.")
                        break
                    chunk = json.loads(payload)
                    if not isinstance(chunk, dict) or chunk.get("error"):
                        raise RuntimeError("llama.cpp returned a model error.")
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue  # Optional usage-only event.
                    choice = choices[0]
                    delta = choice.get("delta", {})
                    text = delta.get("content") or ""
                    if not isinstance(text, str):
                        raise RuntimeError("Malformed model content.")
                    content += text
                    if text:
                        on_text(content)
                    # reasoning_content is deliberately excluded from user-visible output.
                    for part in delta.get("tool_calls", []):
                        index = part.get("index")
                        if type(index) is not int or index < 0 or index > 3:
                            raise RuntimeError("Malformed tool call index.")
                        call = calls.setdefault(index, {"id": "", "type": "function",
                                                       "function": {"name": "", "arguments": ""}})
                        call["id"] += part.get("id", "")
                        function = part.get("function", {})
                        call["function"]["name"] += function.get("name", "")
                        call["function"]["arguments"] += function.get("arguments", "")
                    reason = choice.get("finish_reason")
                    if reason is not None:
                        if reason not in ("stop", "tool_calls"):
                            raise RuntimeError("Model output was truncated or could not finish.")
                        finished = True
        if not finished:
            raise RuntimeError("llama.cpp stream ended before completion.")
        ordered = [calls[index] for index in sorted(calls)]
        for call in ordered:
            if not call["id"] or not call["function"]["name"]:
                raise RuntimeError("Incomplete model tool call.")
            # Validate before any tool can execute; retain the wire string for follow-up requests.
            if not isinstance(json.loads(call["function"]["arguments"]), dict):
                raise RuntimeError("Tool arguments must be an object.")
        return {"content": content, "tool_calls": ordered}
