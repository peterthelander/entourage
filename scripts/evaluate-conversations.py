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
sys.path.insert(0, str(ROOT / "scripts"))

from entourage_server.agent import Worker, Ollama, build_context, available_tools
from entourage_server.config import Settings
from entourage_server.execution_store import ExecutionStore
from entourage_server.journals import export_journals
from entourage_server.llama_cpp import LlamaCpp
from entourage_server.storage import SINGLE_CHAT_ID
from evaluation_gemini import GeminiEvaluation, evaluation_key

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
            for field in ("checks", "diagnostic_checks"):
                for kind, patterns in turn.get(field, {}).items():
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
    diagnostics = {}
    for kind, patterns in turn.get("diagnostic_checks", {}).items():
        for pattern in patterns:
            found = bool(re.search(pattern, normalized, re.I))
            diagnostics[f"{kind}:{pattern}"] = found if kind == "contains" else not found
    return {"checks": checks, "mechanical_pass": all(checks.values()), "diagnostics": diagnostics,
            "semantic_review": "pending"}


class RecordingModel:
    def __init__(self, model):
        self.model, self.requests, self.responses, self.failures = model, [], [], []
        self.on_change = None

    def changed(self, phase):
        if self.on_change is not None:
            self.on_change(phase)

    def __getattr__(self, name):
        if name == "finalize" and hasattr(self.model, "finalize"):
            return self._finalize
        raise AttributeError(name)

    async def _finalize(self, messages, on_text):
        self.requests.append(deepcopy(messages))
        self.changed("finalizing")
        try:
            reply = await self.model.finalize(messages, on_text)
        except Exception as error:
            self.failures.append({"error_type": type(error).__name__, "http_status": getattr(error, "http_status", None)})
            self.changed("inference_failed")
            raise
        self.responses.append(deepcopy(reply))
        self.changed("finalized")
        return reply

    async def generate(self, messages, on_text):
        self.requests.append(deepcopy(messages))
        self.changed("generating")
        try:
            reply = await self.model.generate(messages, on_text)
        except Exception as error:
            self.failures.append({"error_type": type(error).__name__, "http_status": getattr(error, "http_status", None)})
            self.changed("inference_failed")
            raise
        self.responses.append(deepcopy(reply))
        self.changed("generated")
        return reply


async def run_case(case, settings, model, *, knowledge_bundle=None, on_progress=None):
    # No production store, refresh process, device or real web-tool calls.
    with TemporaryDirectory(prefix="entourage-eval-") as directory:
        settings = replace(settings, database_path=Path(directory) / "evaluation.sqlite3",
                           device_timeout_seconds=1, knowledge_enabled=knowledge_bundle is not None)
        if knowledge_bundle is not None:
            from entourage_server.knowledge import publish_bundle
            publish_bundle(knowledge_bundle, Path(knowledge_bundle) / "review.json",
                           settings.database_path.parent / "vault/knowledge")
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
                failures_before = len(recorder.failures)
                web_before = len(fixture_calls)
                started = time.monotonic()
                if on_progress is not None:
                    def progress(phase):
                        on_progress({"case": case["id"], "completed_turns": deepcopy(runs),
                                     "active_turn": {"turn": index + 1, "prompt": turn["text"],
                                                     "phase": phase,
                                                     "inputs": deepcopy(recorder.requests[before:]),
                                                     "responses": deepcopy(recorder.responses[response_before:]),
                                                     "inference_failures": deepcopy(recorder.failures[failures_before:])}})
                    recorder.on_change = progress
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
                             "inference_failures": recorder.failures[failures_before:],
                             "web_fixtures": fixture_calls[web_before:],
                             **assess(turn, result["status"], result["answer"], tools)})
                if result["status"] != "completed":
                    break
        return {"case": case["id"], "category": case.get("category"), "rubric": case["rubric"],
                "diagnostic_rubric": case.get("diagnostic_rubric", []), "turns": runs,
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
        async def engine_metadata():
            if getattr(args, "gemini_model", None) or settings.inference_provider == "gemini":
                return {"status": "hosted", "provider": "gemini", "requested_model": args.gemini_model or settings.model,
                        "note": "Provider version/usage recorded on each successful response; server internals unavailable."}
            if settings.inference_provider != "llama_cpp":
                return {"status": "not_captured", "provider": settings.inference_provider}
            try:
                response = await client.get(settings.llama_cpp_upstream.rstrip("/") + "/props", timeout=10)
                response.raise_for_status()
                props = response.json()
                return {"status": "captured", **{key: props.get(key) for key in (
                    "build_info", "model_alias", "model_ftype", "total_slots", "chat_template_caps",
                    "default_generation_settings")},
                    "chat_template_sha256": hashlib.sha256(props.get("chat_template", "").encode()).hexdigest()}
            except (httpx.HTTPError, ValueError, TypeError, AttributeError) as error:
                return {"status": "unavailable", "error_type": type(error).__name__}

        report["engine_before"] = await engine_metadata()
        save(args.output, report)
        if getattr(args, "gemini_model", None) or settings.inference_provider == "gemini":
            model = GeminiEvaluation(settings, client, model=args.gemini_model or settings.model, api_key=evaluation_key(ROOT),
                                     reasoning_effort=args.reasoning_effort)
        else:
            model = (LlamaCpp(settings, client, reasoning_effort=args.reasoning_effort)
                     if settings.inference_provider == "llama_cpp" else Ollama(settings, client))
        for repeat in range(1, args.repeats + 1):
            for case in fixture["cases"]:
                row = await run_case(case, settings, model)
                row["repeat"] = repeat
                report["runs"].append(row)
                save(args.output, report)
                print(json.dumps({"case": row["case"], "repeat": repeat,
                                  "mechanical_pass": row["all_turns_executed"] and all(t["mechanical_pass"] for t in row["turns"]),
                                  "semantic_review": "pending"}), flush=True)
                if any(f.get("http_status") for t in row["turns"] for f in t.get("inference_failures", [])):
                    report["aborted"] = "Provider HTTP failure; remaining cases were not run. Inspect inference_failures before comparing quality."
                    report["engine_after"] = await engine_metadata()
                    return
        report["engine_after"] = await engine_metadata()


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
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high"), default="low",
                        help="Evaluation request override for llama.cpp or Gemini; production configuration is unchanged")
    parser.add_argument("--gemini-model", help="Evaluation-only hosted model; uses the existing private Google key in live mode")
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
    if args.live and not args.gemini_model and settings.inference_provider not in ("llama_cpp", "gemini") and args.reasoning_effort != "low":
        parser.error("--reasoning-effort overrides require llama_cpp or gemini")
    report = {"version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "live": args.live,
              "requested_repeats": args.repeats,
              "settings": {key: getattr(settings, key) for key in ("inference_provider", "model", "context_tokens",
                           "max_output_tokens", "context_session_gap_minutes")},
              "transport": f"llama.cpp reasoning effort {args.reasoning_effort}, format deepseek; Ollama uses production defaults. Sampling is server-controlled.",
              "inference_options": {"reasoning_effort": args.reasoning_effort if settings.inference_provider == "llama_cpp" else None,
                                    "reasoning_format": "deepseek" if settings.inference_provider == "llama_cpp" else None},
              "scope": "Synthetic worker/memory evaluation. Web responses are fixtures; no real device or website checks. Mechanical checks do not establish semantic correctness.",
              "tools": available_tools(settings), "fixture": fixture, "runs": []}
    report["fixture_sha256"] = hashlib.sha256(json.dumps(fixture, sort_keys=True).encode()).hexdigest()
    report["runner_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["evaluation_adapter_sha256"] = hashlib.sha256((ROOT / "scripts/evaluation_gemini.py").read_bytes()).hexdigest()
    report["evaluated_model"] = {"provider": "gemini" if args.gemini_model else settings.inference_provider,
                                 "model": args.gemini_model or settings.model}
    if args.gemini_model or settings.inference_provider == "gemini":
        report["transport"] = "Gemini OpenAI-compatible REST; non-streaming; identical application tools and budgets; provider sampling defaults."
        report["inference_options"] = {"reasoning_effort": args.reasoning_effort, "stream": False,
                                       "max_tokens": settings.max_output_tokens}
    report["source_sha256"] = {name: hashlib.sha256((ROOT / "server/entourage_server" / name).read_bytes()).hexdigest()
                               for name in ("agent.py", "memory.py", "llama_cpp.py", "config.py", "journals.py", "gemini.py")}
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
                              "evaluation_adapter_matches": (baseline.get("evaluation_adapter_sha256") == report["evaluation_adapter_sha256"]
                                                             if baseline.get("evaluation_adapter_sha256") else None),
                              "source_matches": (baseline.get("source_sha256") == report["source_sha256"]
                                                 if baseline.get("source_sha256") else None),
                              "inference_options": baseline.get("inference_options"),
                              "settings": baseline["settings"], "summary": summarize(baseline),
                              "note": "Compare matched cases and repeats; these counts do not score semantic quality."}
    save(args.output, report)
    print(f"Saved {args.output}; {len(report['runs'])} case runs. Semantic review remains required.")
    return int(any(not row["all_turns_executed"] or any(not turn["mechanical_pass"] for turn in row["turns"])
                   for row in report["runs"]))


if __name__ == "__main__":
    raise SystemExit(main())
