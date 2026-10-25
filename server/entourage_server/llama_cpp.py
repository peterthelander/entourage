"""llama.cpp Chat Completions transport; agent execution remains on this server."""

import asyncio
import json

from .agent import available_tools
from .inference_errors import InferenceError


class LlamaCpp:
    def __init__(self, settings, client, *, reasoning_effort="low"):
        if reasoning_effort not in ("low", "medium", "high"):
            raise ValueError("reasoning_effort must be low, medium or high.")
        self.settings, self.client = settings, client
        self.reasoning_effort = reasoning_effort

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

    async def finalize(self, messages, on_text):
        return await self.generate(messages, on_text, tools_enabled=False)

    @staticmethod
    async def upstream_error(response):
        error_body = bytearray()
        async for chunk in response.aiter_bytes():
            error_body.extend(chunk[:16384 - len(error_body)])
            if len(error_body) >= 16384:
                break
        raw = error_body.decode("utf-8", errors="replace").lower()
        if "system message must be at the beginning" in raw or "jinja exception" in raw:
            raise InferenceError("prompt_template", "The inference server rejected the conversation format. Check model/template compatibility.")
        if "exceed_context_size" in raw or "exceeds the available context" in raw or "exceeds the context size" in raw:
            raise InferenceError("context_limit", "The request exceeds the inference server's context window. Shorten the conversation or increase its context capacity.")
        raise InferenceError("upstream_http", f"The inference server returned HTTP {response.status_code}. Check its model and request settings.")

    async def check_context(self, body):
        # Hash-heavy memory results tokenize much more densely than ordinary
        # prose. For large transcripts, ask this engine's actual template and
        # tokenizer rather than treating four characters as one token.
        if len(json.dumps(body["messages"], ensure_ascii=False).encode("utf-8")) <= self.settings.context_tokens:
            return
        upstream = self.settings.llama_cpp_upstream.rstrip("/")
        rendered = await self.client.post(upstream + "/apply-template", json=body)
        if rendered.status_code != 200:
            await self.upstream_error(rendered)
        measured = await self.client.post(upstream + "/tokenize", json={
            "content": rendered.json()["prompt"], "add_special": False})
        if measured.status_code != 200:
            await self.upstream_error(measured)
        tokens = measured.json()["tokens"]
        if not isinstance(tokens, list):
            raise InferenceError("context_measurement", "Could not measure the inference context. Check the inference server's tokenizer support.")
        if len(tokens) + body["max_tokens"] > self.settings.context_tokens:
            raise InferenceError("context_limit", f"The request needs {len(tokens):,} input tokens plus {body['max_tokens']:,} reserved response tokens, exceeding the {self.settings.context_tokens:,}-token context window. Shorten the request or reduce retrieved history; a larger context requires changing llama-server and the agent settings.")

    async def generate(self, messages, on_text, *, tools_enabled=True):
        body = {"model": self.settings.model, "messages": self.wire_messages(messages),
                "tools": available_tools(self.settings) if tools_enabled else [], "stream": True, "max_tokens": self.settings.max_output_tokens,
                "reasoning_format": "deepseek", "reasoning_effort": self.reasoning_effort}
        content, calls, size, finished = "", {}, 0, False
        async with asyncio.timeout(300):
            await self.check_context(body)
            async with self.client.stream("POST", self.settings.llama_cpp_upstream.rstrip("/") +
                                          "/v1/chat/completions", json=body) as response:
                if response.status_code != 200:
                    await self.upstream_error(response)
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
                            raise InferenceError("interrupted_stream", "The inference response ended before the model finished. No completed answer was saved. Try again; if this repeats, check the inference server.")
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
                        if reason == "length":
                            raise InferenceError("output_limit", "The model reached the response token limit before finishing. Try a shorter request or increase the output limit; thinking also uses that limit.")
                        if reason not in ("stop", "tool_calls"):
                            raise RuntimeError("Model output was truncated or could not finish.")
                        finished = True
        if not finished:
            raise InferenceError("interrupted_stream", "The inference response ended before the model finished. No completed answer was saved. Try again; if this repeats, check the inference server.")
        ordered = [calls[index] for index in sorted(calls)]
        for call in ordered:
            if not call["id"] or not call["function"]["name"]:
                raise RuntimeError("Incomplete model tool call.")
            # Validate before any tool can execute; retain the wire string for follow-up requests.
            if not isinstance(json.loads(call["function"]["arguments"]), dict):
                raise RuntimeError("Tool arguments must be an object.")
        return {"content": content, "tool_calls": ordered}
