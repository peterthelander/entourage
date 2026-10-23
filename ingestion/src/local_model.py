"""Bounded local inference for offline ingestion experiments, with no live agent state."""

import json
from pathlib import Path
from urllib.parse import urlsplit


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("ENTOURAGE_INFERENCE_PROVIDER") != "llama_cpp":
        raise ValueError("This experiment requires the configured llama.cpp provider")
    origin, model = config["ENTOURAGE_LLAMA_CPP_UPSTREAM"], config["ENTOURAGE_MODEL"]
    url = urlsplit(origin)
    if (url.scheme not in ("http", "https") or not url.hostname or url.username or url.password
            or url.path not in ("", "/") or url.query or url.fragment):
        raise ValueError("Expected an inference origin without path or credentials")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("Missing model ID")
    return origin, model


def complete(client, origin, body, response_path):
    chunks, length = [], 0
    with client.stream("POST", origin.rstrip("/") + "/v1/chat/completions", json=body) as response:
        response.raise_for_status()
        for chunk in response.iter_bytes():
            length += len(chunk)
            if length > 2 * 1024 * 1024:
                raise ValueError("Response exceeds 2 MiB")
            chunks.append(chunk)
    raw = b"".join(chunks)
    Path(response_path).write_bytes(raw)
    data = json.loads(raw)
    return data


def completed_content(data):
    choice = data["choices"][0]
    if choice.get("finish_reason") != "stop" or choice["message"].get("tool_calls"):
        raise ValueError("Expected completed content without tool calls")
    content = choice["message"].get("content")
    if not isinstance(content, str):
        raise ValueError("Expected string completion content")
    return content
