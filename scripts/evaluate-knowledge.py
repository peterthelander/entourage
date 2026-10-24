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
from memory_validation import digest, read, verify


async def run(args):
    bundle = ReviewedKnowledge(args.bundle)
    fixture = evaluation.load_cases(args.fixture)
    settings = replace(evaluation.live_settings(), knowledge_enabled=True)
    manifest_path = getattr(args, "freeze_manifest", None)
    manifest = read(manifest_path) if manifest_path else None
    if manifest is not None:
        verify(manifest, settings)
        if (manifest["bundle_snapshot"] != bundle.snapshot
                or manifest["fixture_sha256"] != digest(args.fixture)
                or manifest["planned_runs"] != {"providers": args.providers, "repeats": args.repeats,
                                                "case_ids": [case["id"] for case in fixture["cases"]],
                                                "gemini_model": args.gemini_model if "gemini" in args.providers else None}):
            raise ValueError("Run arguments do not match the frozen experiment")
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"version": 1, "status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
              "bundle_snapshot": bundle.snapshot, "review_sha256": bundle.review_sha256,
              "fixture_sha256": hashlib.sha256(args.fixture.read_bytes()).hexdigest(),
              "production_worker_sha256": hashlib.sha256((ROOT / "server/entourage_server/agent.py").read_bytes()).hexdigest(),
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "service_code_sha256": {name: hashlib.sha256((ROOT / "server/entourage_server" / name).read_bytes()).hexdigest()
                                      for name in ("agent.py", "execution_store.py", "knowledge.py", "knowledge_bundle.py",
                                                   "knowledge_contracts.py", "config.py", "llama_cpp.py", "gemini.py")},
              "scope": "Production worker and tools with isolated databases; no live chat, real device or web calls",
              "freeze_manifest_sha256": digest(manifest_path) if manifest_path else None,
              "settings": {name: getattr(settings, name) for name in (
                  "inference_provider", "model", "context_tokens", "max_output_tokens", "context_session_gap_minutes")},
              "planned_runs": {"providers": args.providers, "repeats": args.repeats,
                               "case_ids": [case["id"] for case in fixture["cases"]],
                               "gemini_model": args.gemini_model if "gemini" in args.providers else None},
              "semantic_review": "pending", "runs": []}
    def save():
        evaluation.save(args.output / "report.json", report)
    save()
    try:
        await run_trials(args, settings, fixture, report, save, manifest)
    except BaseException as error:
        report.update(status="interrupted" if isinstance(error, (KeyboardInterrupt, asyncio.CancelledError)) else "failed",
                      error_type=type(error).__name__, finished_at=datetime.now(timezone.utc).isoformat())
        save()
        raise
    report.update(finished_at=datetime.now(timezone.utc).isoformat())
    save()
    return report


async def run_trials(args, settings, fixture, report, save, manifest):
    import httpx
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
                    if manifest is not None:
                        verify(manifest, settings)
                    def progress(value):
                        report["active_run"] = {"provider": provider, "repeat": repeat, **value}
                        save()
                    row = await evaluation.run_case(case, settings, model, knowledge_bundle=args.bundle,
                                                    on_progress=progress)
                    row.update(provider=provider, repeat=repeat)
                    report["runs"].append(row)
                    report.pop("active_run", None)
                    save()
                    print(json.dumps({"provider": provider, "case": row["case"], "repeat": repeat,
                                      "turns": len(row["turns"]), "completed": row["all_turns_executed"] and all(t["status"] == "completed" for t in row["turns"]),
                                      "mechanical_pass": row["all_turns_executed"] and all(t["mechanical_pass"] for t in row["turns"])}), flush=True)
                    if any(f.get("http_status") for t in row["turns"] for f in t.get("inference_failures", [])):
                        report["status"] = "provider_failure"
                        save()
                        return
    if manifest is not None:
        verify(manifest, settings)
    report["status"] = "complete"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--providers", nargs="+", choices=("local", "gemini"), default=["local"])
    parser.add_argument("--gemini-model", default="gemini-4-argon")
    parser.add_argument("--repeats", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--freeze-manifest", type=Path,
                        help="Require exact frozen code, inputs, inference settings and planned runs")
    args = parser.parse_args()
    report = asyncio.run(run(args))
    if report["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
