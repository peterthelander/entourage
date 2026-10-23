"""Reviewed-memory conversations through the production worker, in isolated stores."""

import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("conversation_evaluation", ROOT / "scripts/evaluate-conversations.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)

from entourage_server.gemini import Gemini
from entourage_server.llama_cpp import LlamaCpp
from entourage_server.knowledge import ReviewedKnowledge
from evaluation_gemini import evaluation_key


async def run(args):
    import httpx
    bundle = ReviewedKnowledge(args.bundle)
    fixture = evaluation.load_cases(args.fixture)
    args.output.mkdir(parents=True, exist_ok=False)
    settings = replace(evaluation.live_settings(), knowledge_enabled=True)
    report = {"version": 1, "status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
              "bundle_snapshot": bundle.snapshot, "review_sha256": bundle.review_sha256,
              "fixture_sha256": hashlib.sha256(args.fixture.read_bytes()).hexdigest(),
              "production_worker_sha256": hashlib.sha256((ROOT / "server/entourage_server/agent.py").read_bytes()).hexdigest(),
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "Production worker and tools with isolated databases; no live chat, real device or web calls",
              "semantic_review": "pending", "runs": []}
    def save():
        evaluation.save(args.output / "report.json", report)
    save()
    async with httpx.AsyncClient(timeout=300, trust_env=False) as client:
        for provider in args.providers:
            if provider == "local":
                if settings.inference_provider != "llama_cpp":
                    raise ValueError("Local comparison requires the configured llama.cpp provider")
                model = LlamaCpp(settings, client, reasoning_effort="low")
            else:
                model = Gemini(settings, client, model=args.gemini_model, api_key=evaluation_key(ROOT), reasoning_effort="low")
            for repeat in range(1, args.repeats + 1):
                for case in fixture["cases"]:
                    row = await evaluation.run_case(case, settings, model, knowledge_bundle=args.bundle)
                    row.update(provider=provider, repeat=repeat)
                    report["runs"].append(row)
                    save()
                    print(json.dumps({"provider": provider, "case": row["case"], "repeat": repeat,
                                      "turns": len(row["turns"]), "completed": row["all_turns_executed"] and all(t["status"] == "completed" for t in row["turns"]),
                                      "mechanical_pass": row["all_turns_executed"] and all(t["mechanical_pass"] for t in row["turns"])}), flush=True)
                    if any(f.get("http_status") for t in row["turns"] for f in t.get("inference_failures", [])):
                        report["status"] = "provider_failure"
                        save()
                        return report
    report.update(status="complete", finished_at=datetime.now(timezone.utc).isoformat())
    save()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--providers", nargs="+", choices=("local", "gemini"), default=["local"])
    parser.add_argument("--gemini-model", default="gemini-4-argon")
    parser.add_argument("--repeats", type=int, choices=(1, 2, 3), default=2)
    args = parser.parse_args()
    report = asyncio.run(run(args))
    if report["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
