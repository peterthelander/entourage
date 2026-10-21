"""Prepare synthetic context comparisons offline, or explicitly run live inference.

Never reads personal SQLite history or executes model-requested tools.
"""
import argparse
import asyncio
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from entourage_server.agent import build_context, TOOLS
from entourage_server.config import Settings
from entourage_server.llama_cpp import LlamaCpp


def build_cases(fixture, settings):
    cases = {}
    history = fixture["history"]
    query = fixture["query"]
    probes = {"original": (history, query)}
    if "follow_up" in fixture:
        probes["continuity"] = ([*history, {**query, "role": "user"}], fixture["follow_up"])
    for name, (rows, prompt) in probes.items():
        cases[name + "/full"] = build_context(prompt["text"], rows, settings)
        cases[name + "/session"] = build_context(prompt["text"], rows, settings, created_at=prompt["created_at"])
    return cases


async def compare(report, settings, repeats):
    import httpx

    async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=10), trust_env=False) as client:
        model = LlamaCpp(settings, client)
        for repeat in range(1, repeats + 1):
            for name, messages in report["inputs"].items():
                started = time.monotonic()
                run = {"condition": name, "repeat": repeat}
                try:
                    run.update(await model.generate(messages, lambda _: None))
                except Exception as error:
                    # Keep diagnostics useful without retaining upstream response bodies.
                    run["error"] = type(error).__name__
                run["seconds"] = round(time.monotonic() - started, 3)
                report["runs"].append(run)
                print(json.dumps(run), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=ROOT / "server/tests/fixtures/context-comparison.json")
    parser.add_argument("--output", type=Path, default=ROOT / ".expo/context-comparison.json")
    parser.add_argument("--live", action="store_true", help="Send inference requests; otherwise only prepare inputs")
    parser.add_argument("--upstream", help="Explicit llama.cpp origin, required for --live")
    parser.add_argument("--model", help="Explicit model ID, required for --live")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error("--repeats must be between 1 and 10")
    if args.live and (not args.upstream or not args.model):
        parser.error("--live requires --upstream and --model")
    settings = Settings(inference_provider="llama_cpp", context_tokens=16384, max_output_tokens=2048,
                        llama_cpp_upstream=args.upstream or "http://127.0.0.1:8080", model=args.model or "offline")
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    report = {
        "description": fixture.get("description", ""), "live": args.live,
        "settings": {key: asdict(settings)[key] for key in (
            "inference_provider", "model", "llama_cpp_upstream", "context_tokens",
            "max_output_tokens", "context_session_gap_minutes")},
        "tools": TOOLS, "reasoning_effort": "low", "reasoning_format": "deepseek",
        "note": "Synthetic fixture; server sampling defaults; repeated runs are not deterministic. Tools are never executed. Evaluate outputs manually.",
        "inputs": build_cases(fixture, settings), "runs": [],
    }
    if args.live:
        asyncio.run(compare(report, settings, args.repeats))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {args.output}; {len(report['runs'])} inference requests recorded.")
    return 1 if any("error" in run for run in report["runs"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
