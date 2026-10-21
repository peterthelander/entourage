"""Live static-page and multi-step checks, isolated from saved conversations."""

import argparse
import asyncio
from dataclasses import replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

import httpx
from entourage_server.agent import SYSTEM_PROMPT
from entourage_server.config import Settings
from entourage_server.llama_cpp import LlamaCpp
from entourage_server.web_pages import read_web_page
from entourage_server.web_search import search_web


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["pages", "agent"])
    args = parser.parse_args()
    rows = []
    path = ROOT / f".expo/page-reading-{args.stage}.json"

    def save(row):
        rows.append(row)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in row.items() if k not in {"result", "messages"}}, ensure_ascii=True), flush=True)

    if args.stage == "pages":
        for url in ["https://www.carnegiehall.org/Calendar", "https://www.lincolncenter.org/lincoln-center-at-home/calendar", "https://www.nyphil.org/concerts-tickets/"]:
            result = await read_web_page({"url": url})
            save({"url": url, "status": result["status"], "error": result.get("error"),
                  "characters": len(result.get("text", "")), "link_count": len(result.get("links", [])), "result": result})
        return
    settings = Settings.from_environment()
    inference = json.loads((ROOT / "server/data/inference.json").read_text())
    settings = replace(settings, model=inference["ENTOURAGE_MODEL"],
                       llama_cpp_upstream=inference["ENTOURAGE_LLAMA_CPP_UPSTREAM"], max_output_tokens=1536)
    async with httpx.AsyncClient(timeout=120, trust_env=False) as client:
        model = LlamaCpp(settings, client)
        for question in ["I'm seeing a show at Carnegie Hall on October 20, 2026. What events are listed that day? Inspect the official schedule before answering.",
                         "Can you check the official Lincoln Center calendar for events on October 20, 2026?",
                         "Verify the Richard Dawkins event at Carnegie Hall on October 20, 2026 using its event page."]:
            for repeat in range(2):
                messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
                used, names = 0, []
                for _ in range(5):
                    reply = await model.generate(messages, lambda text: None)
                    calls = reply.get("tool_calls", [])
                    if not calls or used + len(calls) > 4:
                        save({"question": question, "repeat": repeat + 1, "status": "answered" if not calls else "tool_limit",
                              "tools": names, "answer": reply.get("content"), "messages": messages})
                        break
                    used += len(calls)
                    messages.append({"role": "assistant", "content": reply.get("content", ""), "tool_calls": calls})
                    for call in calls:
                        function = call["function"]
                        name, tool_args = function["name"], function["arguments"]
                        if isinstance(tool_args, str):
                            tool_args = json.loads(tool_args)
                        names.append(name)
                        if name == "searchWeb":
                            result = await search_web(tool_args, settings.gemini_api_key, model=settings.web_search_model, client=client)
                            result.pop("search_suggestions_html", None)
                        elif name == "readWebPage":
                            result = await read_web_page(tool_args)
                        else:
                            result = {"status": "unavailable", "error": "This isolated public-research check has no requesting device or personal memory."}
                        messages.append({"role": "tool", "name": name, "tool_call_id": call["id"], "content": json.dumps(result)})


if __name__ == "__main__":
    asyncio.run(main())
