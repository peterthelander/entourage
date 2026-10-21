"""Isolated research and answer comparisons. Writes no conversation history.

Run with the server Python environment. Credentials are loaded privately and never
written to the report. Reports live under ignored .expo/ by default.
"""

import argparse
import asyncio
from dataclasses import replace
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

import httpx
from entourage_server.agent import SYSTEM_PROMPT
from entourage_server.config import Settings
from entourage_server.llama_cpp import LlamaCpp
from entourage_server.web_search import search_web

CASES = {
    "original": "What shows are at Carnegie Hall tonight, October 20, 2026?",
    "correction": "Richard Dawkins at Carnegie Hall tonight October 20, 2026: verify the event, auditorium and start time.",
    "specific": "The Knights with Emanuel Ax at Carnegie Hall October 20, 2026: verify auditorium, start time and performers.",
}
SOURCES = [
    {"source_index": 0, "title": "Carnegie Hall: Richard Dawkins", "url": "https://www.carnegiehall.org/Calendar/2026/10/20/Richard-Dawkins---Genes-and-The-Meaning-of-Life-0700PM"},
    {"source_index": 1, "title": "Carnegie Hall: The Knights", "url": "https://www.carnegiehall.org/Calendar/2026/10/20/The-Knights-0730PM"},
    {"source_index": 2, "title": "Carnegie Hall: Elmira Darvarova", "url": "https://www.carnegiehall.org/Calendar/2026/10/20/Elmira-Darvarova-Violin-0730PM"},
]
EVENTS = [
    "Richard Dawkins — Genes and the Meaning of Life. October 20, 2026, 7:00 PM, Stern Auditorium / Perelman Stage.",
    "The Knights with Emanuel Ax. October 20, 2026, 7:30 PM, Zankel Hall. Mozart Piano Concertos Nos. 17 and 25.",
    "Elmira Darvarova, violin. A separate event on October 20, 2026; this fixture does not establish its auditorium or time.",
]


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["research", "replay"])
    parser.add_argument("--models", nargs="+", default=["gemini-2.5-flash-lite", "gemini-2.5-flash"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--handoff", choices=["json", "brief"], default="json")
    args = parser.parse_args()
    config = Settings.from_environment()
    output = args.output or ROOT / f".expo/web-evaluation-{args.stage}.json"
    rows = []

    def save(row):
        rows.append(row)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({key: value for key, value in row.items() if key not in {"evidence", "messages", "answer"}}, ensure_ascii=False), flush=True)

    async with httpx.AsyncClient(timeout=120, trust_env=False) as client:
        if args.stage == "research":
            for model in args.models:
                for case, query in CASES.items():
                    for repeat in range(args.repeats):
                        started = time.monotonic()
                        result = await search_web({"query": query}, config.gemini_api_key, model=model, client=client)
                        result.pop("search_suggestions_html", None)
                        save({"case": case, "model": model, "repeat": repeat + 1,
                              "seconds": round(time.monotonic() - started, 2), "status": result["status"],
                              "mentions_dawkins": "dawkins" in result.get("summary", "").lower(),
                              "error": result.get("error"), "evidence": result})
        else:
            inference = json.loads((ROOT / "server/data/inference.json").read_text())
            config = replace(config, llama_cpp_upstream=inference["ENTOURAGE_LLAMA_CPP_UPSTREAM"],
                             model=inference["ENTOURAGE_MODEL"], max_output_tokens=1536)
            model = LlamaCpp(config, client)
            for case in ("partial", "three_events", "single_event", "correction"):
                indices = [1, 2] if case == "partial" else [0, 1, 2] if case == "three_events" else [1] if case == "single_event" else [0]
                question = ("I'm going to The Knights tonight. What are the details?" if case == "single_event" else
                            "I'm actually seeing Richard Dawkins. Can you check that event instead?" if case == "correction" else
                            "I'm getting ready to see a show at Carnegie Hall tonight. Can you tell me what the show is?")
                query = CASES["specific"] if case == "single_event" else CASES["correction"] if case == "correction" else CASES["original"]
                evidence = {"status": "results", "query": query, "summary": "\n".join(EVENTS[i] for i in indices),
                            "results": [SOURCES[i] for i in indices], "limitations": "These are search findings, not a complete verified schedule."}
                content = json.dumps(evidence)
                if args.handoff == "brief":
                    content = "Search findings (coverage not established):\n\n" + "\n\n".join(
                        f"{EVENTS[i]}\nSource: [{SOURCES[i]['title']}]({SOURCES[i]['url']})" for i in indices)
                messages = [{"role": "system", "content": SYSTEM_PROMPT + " The local date for this replay is October 20, 2026."}]
                if case == "correction":
                    messages += [{"role": "user", "content": "I'm going to Carnegie Hall tonight. What show is it?"},
                                 {"role": "assistant", "content": "The Knights with Emanuel Ax in Zankel Hall."}]
                messages += [{"role": "user", "content": question},
                             {"role": "assistant", "content": "", "tool_calls": [{"id": "lookup_1", "type": "function", "function": {"name": "searchWeb", "arguments": {"query": evidence["query"]}}}]},
                             {"role": "tool", "name": "searchWeb", "tool_call_id": "lookup_1", "content": content}]
                for repeat in range(args.repeats):
                    try:
                        answer = await model.generate(messages, lambda text: None)
                        save({"case": case, "handoff": args.handoff, "repeat": repeat + 1, "status": "answered", "messages": messages, "answer": answer})
                    except (httpx.HTTPError, RuntimeError, TimeoutError):
                        save({"case": case, "repeat": repeat + 1, "status": "inference_failed"})


if __name__ == "__main__":
    asyncio.run(main())
