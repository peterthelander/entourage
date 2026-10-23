"""Explicit hosted reference for experiments via the existing production adapter."""

import asyncio
from dataclasses import replace
import json
from pathlib import Path
import sys


def complete_reference(messages, model, output, repeat):
    import httpx
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "server"))
    from entourage_server.config import Settings
    from entourage_server.gemini import Gemini

    async def generate():
        settings = Settings.from_environment()
        # Keep all credentials confined to the existing settings/adapter. Never
        # serialize settings, headers or exceptions containing a request object.
        settings = replace(settings, max_output_tokens=4096, context_tokens=16384)
        async with httpx.AsyncClient(timeout=300, trust_env=False) as client:
            class Recorder:
                def stream(self, *args, **kwargs):
                    (output / "request.json").write_text(json.dumps(kwargs["json"], indent=2, ensure_ascii=False), encoding="utf-8")
                    return client.stream(*args, **kwargs)
            adapter = Gemini(settings, Recorder(), model=model)
            reply = await adapter.generate(messages, lambda _: None)
            (output / f"adapter-response-{repeat}.json").write_text(json.dumps(reply, indent=2, ensure_ascii=False), encoding="utf-8")
            return {"choices": [{"finish_reason": "tool_calls" if reply["tool_calls"] else "stop", "message": reply}],
                    "usage": reply["inference_metadata"].get("usage")}
    return asyncio.run(generate())
