"""Synthetic conversation evaluations through the production worker; offline by default."""
import argparse
import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import json
import hashlib
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import time
import unicodedata
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from entourage_server.agent import Worker, Ollama, build_context, available_tools
from entourage_server.config import Settings
from entourage_server.execution_store import ExecutionStore
from entourage_server.journals import export_journals
from entourage_server.llama_cpp import LlamaCpp
from entourage_server.storage import SINGLE_CHAT_ID

FIXTURE = ROOT / "server/tests/fixtures/conversation-evaluations.json"


def load_cases(path):
    fixture = json.loads(path.read_text(encoding="utf-8"))
    if fixture.get("version") != 1 or not fixture.get("cases"):
        raise ValueError("Expected version 1 and nonempty cases.")
    ids = set()
    for case in fixture["cases"]:
        if case["id"] in ids:
            raise ValueError("Duplicate case ID.")
        ids.add(case["id"])
        if not case["turns"] or not case["rubric"]:
            raise ValueError("Each case needs turns and a review rubric.")
        for turn in case["turns"]:
            if datetime.fromisoformat(turn["created_at"]).tzinfo is None:
                raise ValueError("Turn timestamps must include a timezone.")
            for kind, patterns in turn.get("checks", {}).items():
                if kind not in {"contains", "excludes"}:
                    raise ValueError("Unknown check kind.")
                for pattern in patterns:
                    re.compile(pattern)
    return fixture


def assess(turn, status, answer, tools):
    """Narrow observable assertions, never a semantic correctness verdict."""
    checks = {"completed": status == "completed"}
    names = [tool["name"] for tool in tools]
    normalized = unicodedata.normalize("NFKC", answer or "").translate(str.maketrans({
        "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2212": "-"}))
    for name in turn.get("required_tools", []):
        checks[f"tool:{name}"] = name in names
    for name in turn.get("forbidden_tools", []):
        checks[f"no_tool:{name}"] = name not in names
    for kind, patterns in turn.get("checks", {}).items():
        if kind not in {"contains", "excludes"}:
            raise ValueError("Unknown check kind.")
        for pattern in patterns:
            found = bool(re.search(pattern, normalized, re.I))
            checks[f"{kind}:{pattern}"] = found if kind == "contains" else not found
    return {"checks": checks, "mechanical_pass": all(checks.values()),
            "semantic_review": "pending"}


class RecordingModel:
    def __init__(self, model):
        self.model, self.requests, self.responses = model, [], []

    async def generate(self, messages, on_text):
        self.requests.append(deepcopy(messages))
        reply = await self.model.generate(messages, on_text)
        self.responses.append(deepcopy(reply))
        return reply


async def run_case(case, settings, model):
    # No production store, refresh process, device, public website or Google API.
    with TemporaryDirectory(prefix="entourage-eval-") as directory:
        settings = replace(settings, database_path=Path(directory) / "evaluation.sqlite3",
                           device_timeout_seconds=1)
        store = ExecutionStore(settings.database_path)
        store.initialize()
        store.single_chat()
        store.create_conversation("evaluation", "Synthetic evaluation")
        with store.connect(write=True) as db:
            for group, conversation in (("memories", SINGLE_CHAT_ID), ("history", "evaluation")):
                for row in case.get(group, []):
                    db.execute("INSERT INTO messages(conversation_id,role,kind,text,created_at) VALUES(?,?,?,?,?)",
                               (conversation, row["role"], row["role"], row["text"], row["created_at"]))
        export_journals(settings.database_path, Path(directory) / "vault/journals", "UTC")
        recorder = RecordingModel(model)
        runs, fixture_calls = [], []

        async def web(name, args):
            matched = next((item for item in case.get("web", []) if item["name"] == name
                            and all(args.get(k) == v for k, v in item.get("arguments", {}).items())), None)
            fixture_calls.append({"name": name, "arguments": args, "fixture_matched": matched is not None})
            return deepcopy(matched["result"]) if matched else {
                "status": "unavailable", "error": "No synthetic response for these arguments."}

        async def search(args, *unused, **kwargs):
            return await web("searchWeb", args)

        async def read(args, **kwargs):
            return await web("readWebPage", args)

        with patch("entourage_server.agent.search_web", search), patch("entourage_server.agent.read_web_page", read):
            for index, turn in enumerate(case["turns"]):
                turn_id = f"evaluation-{index}"
                store.create_turn("evaluation", turn_id, turn["text"], "synthetic-device")
                with store.connect(write=True) as db:
                    db.execute("UPDATE turns SET created_at=? WHERE id=?", (turn["created_at"], turn_id))
                    db.execute("UPDATE messages SET created_at=? WHERE turn_id=?", (turn["created_at"], turn_id))
                before = len(recorder.requests)
                response_before = len(recorder.responses)
                web_before = len(fixture_calls)
                started = time.monotonic()
                await Worker(store, settings, recorder).execute(store.claim())
                result = store.get_turn(turn_id)
                with store.connect(write=True) as db:
                    tools = [{"name": row["text"].split("\n", 1)[0],
                              "result": row["text"].split("\n", 1)[1]} for row in db.execute(
                        "SELECT text FROM messages WHERE turn_id=? AND kind='tool' ORDER BY sequence", (turn_id,))]
                    # Keep synthetic time consistent for the next production context selection.
                    db.execute("UPDATE messages SET created_at=? WHERE turn_id=?", (turn["created_at"], turn_id))
                runs.append({"turn": index + 1, "prompt": turn["text"], "status": result["status"],
                             "answer": result["answer"], "error": result["error"],
                             "seconds": round(time.monotonic() - started, 3),
                             "inputs": recorder.requests[before:], "responses": recorder.responses[response_before:], "tools": tools,
                             "web_fixtures": fixture_calls[web_before:],
                             **assess(turn, result["status"], result["answer"], tools)})
                if result["status"] != "completed":
                    break
        return {"case": case["id"], "rubric": case["rubric"], "turns": runs,
                "all_turns_executed": len(runs) == len(case["turns"])}


def live_settings():
    # Same inference precedence as start-agent.py, without loading owner credentials.
    path = ROOT / "server/data/inference.json"
    local = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    fields = {"inference_provider": "ENTOURAGE_INFERENCE_PROVIDER", "model": "ENTOURAGE_MODEL",
              "llama_cpp_upstream": "ENTOURAGE_LLAMA_CPP_UPSTREAM", "ollama_upstream": "ENTOURAGE_OLLAMA_UPSTREAM",
              "context_tokens": "ENTOURAGE_CONTEXT_TOKENS", "max_output_tokens": "ENTOURAGE_MAX_OUTPUT_TOKENS",
              "context_session_gap_minutes": "ENTOURAGE_CONTEXT_SESSION_GAP_MINUTES"}
    values = {}
    for field, env in fields.items():
        value = os.environ.get(env, local.get(env, getattr(Settings, field)))
        values[field] = int(value) if field in {"context_tokens", "max_output_tokens", "context_session_gap_minutes"} else value
    # Enables the production search schema only; search is always intercepted above.
    return Settings(**values, gemini_api_key="synthetic-evaluation-only")


async def evaluate(args, fixture, settings, report):
    import httpx
    async with httpx.AsyncClient(timeout=300, trust_env=False) as client:
        model = LlamaCpp(settings, client) if settings.inference_provider == "llama_cpp" else Ollama(settings, client)
        for repeat in range(1, args.repeats + 1):
            for case in fixture["cases"]:
                row = await run_case(case, settings, model)
                row["repeat"] = repeat
                report["runs"].append(row)
                save(args.output, report)
                print(json.dumps({"case": row["case"], "repeat": repeat,
                                  "mechanical_pass": row["all_turns_executed"] and all(t["mechanical_pass"] for t in row["turns"]),
                                  "semantic_review": "pending"}), flush=True)


def save(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def summarize(report):
    summary = {}
    for row in report["runs"]:
        item = summary.setdefault(row["case"], {"runs": 0, "mechanical_passes": 0, "semantic_review": "pending"})
        item["runs"] += 1
        item["mechanical_passes"] += int(row["all_turns_executed"] and all(t["mechanical_pass"] for t in row["turns"]))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=FIXTURE)
    parser.add_argument("--output", type=Path, default=ROOT / "scratch/conversation-evaluation.json")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--baseline", type=Path, help="Compare mechanical counts with an earlier report; inspect answers separately")
    parser.add_argument("--case", action="append", dest="cases", help="Select case ID; repeatable")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error("--repeats must be between 1 and 10")
    fixture = load_cases(args.fixture)
    if args.cases:
        known = {case["id"] for case in fixture["cases"]}
        if set(args.cases) - known:
            parser.error("Unknown case ID")
        fixture["cases"] = [case for case in fixture["cases"] if case["id"] in args.cases]
    settings = live_settings() if args.live else Settings(gemini_api_key="synthetic-evaluation-only")
    report = {"version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "live": args.live,
              "requested_repeats": args.repeats,
              "settings": {key: getattr(settings, key) for key in ("inference_provider", "model", "context_tokens",
                           "max_output_tokens", "context_session_gap_minutes")},
              "transport": "Production adapter defaults; llama.cpp reasoning effort low, format deepseek. Sampling is server-controlled.",
              "scope": "Synthetic worker/memory evaluation. Web responses are fixtures; no real device or website checks. Mechanical checks do not establish semantic correctness.",
              "tools": available_tools(settings), "fixture": fixture, "runs": []}
    report["fixture_sha256"] = hashlib.sha256(json.dumps(fixture, sort_keys=True).encode()).hexdigest()
    report["runner_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["initial_inputs"] = {case["id"]: build_context(case["turns"][0]["text"], case.get("history", []),
                               settings, created_at=case["turns"][0]["created_at"]) for case in fixture["cases"]}
    save(args.output, report)
    if args.live:
        asyncio.run(evaluate(args, fixture, settings, report))
    report["summary"] = summarize(report)
    if args.baseline:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        report["baseline"] = {"fixture_matches": baseline.get("fixture_sha256") == report["fixture_sha256"],
                              "runner_matches": baseline.get("runner_sha256") == report["runner_sha256"],
                              "settings": baseline["settings"], "summary": summarize(baseline),
                              "note": "Compare matched cases and repeats; these counts do not score semantic quality."}
    save(args.output, report)
    print(f"Saved {args.output}; {len(report['runs'])} case runs. Semantic review remains required.")
    return int(any(not row["all_turns_executed"] or any(not turn["mechanical_pass"] for turn in row["turns"])
                   for row in report["runs"]))


if __name__ == "__main__":
    raise SystemExit(main())
