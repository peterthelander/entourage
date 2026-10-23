"""Reproducible bounded ingestion-to-candidate experiment; never publishes live memory."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from memory_candidates import build
from normalize_mail import run as normalize_mail
from propose_articles import prepare, run as propose
from review_articles import plan_checks, run as review


def select_sample(records, limit=3, seed="memory-pilot-v1"):
    """Select whole records by stable hash, independent of topic and file order."""
    if not 1 <= limit <= 3:
        raise ValueError("Pilot sample size must be from 1 to 3")
    eligible = [record for record in records if 100 <= len(record["text"]) <= 3000]
    ranked = sorted(eligible, key=lambda r: (hashlib.sha256((seed + "\0" + r["id"]).encode()).hexdigest(), r["id"]))
    selected = []
    for record in ranked:
        try:
            prepare(selected + [record], citations="spans")
        except ValueError:
            continue
        selected.append(record)
        if len(selected) == limit:
            break
    if len(selected) != limit:
        raise ValueError("Not enough eligible complete records for the requested sample")
    return selected, {"method": "ascending SHA256(seed + NUL + record ID)", "seed": seed,
                      "eligible_records": len(eligible), "normalized_records": len(records),
                      "min_text_characters": 100, "max_text_characters": 3000,
                      "selected_ids": [r["id"] for r in selected],
                      "scope": "Convenience sample of bounded short bodies, not a representative corpus estimate"}


def run(sources, config, output, max_mib=64, repeats=2, seed="memory-pilot-v1"):
    output = Path(output)
    if not sources or max_mib <= 0 or not 1 <= repeats <= 3:
        raise ValueError("Provide sources, a positive byte budget and 1 to 3 repeats")
    config = Path(config).resolve(strict=True)
    config_digest = hashlib.sha256(config.read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=False)
    report = {"version": 1, "status": "running", "live_publication": False,
              "started_at": datetime.now(timezone.utc).isoformat(),
              "config_sha256": config_digest, "stages": {}, "candidate_review": "pending"}
    report["code_sha256"] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ("run_memory_pilot.py", "normalize_mail.py", "filter_mail.py",
                                          "propose_articles.py", "review_articles.py", "memory_candidates.py", "local_model.py")}

    def save():
        (output / "pilot-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    save()
    try:
        print("Normalizing bounded mail samples", flush=True)
        normalization = normalize_mail(sources, output / "normalized", max_mib * 1024 * 1024, 8 * 1024 * 1024)
        report["stages"]["normalize"] = {"status": normalization["status"]}
        save()
        records = [json.loads(line) for line in (output / "normalized/records.jsonl").read_text(encoding="utf-8").splitlines()]
        selected, sampling = select_sample(records, seed=seed)
        (output / "sample.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in selected), encoding="utf-8")
        report["stages"]["sample"] = sampling
        save()
        print("Proposing source-span article plans", flush=True)
        proposals = propose(output / "sample.jsonl", config, output / "proposals", repeats,
                            structured=True, citations="spans")
        report["stages"]["propose"] = proposals["runs"]
        report["stages"]["candidates"] = []
        save()
        for trial in proposals["runs"]:
            if not trial["mechanical_pass"]:
                continue
            number = trial["repeat"]
            plan_path = output / f"proposals/plan-{number}.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            by_id, checks = plan_checks(selected, plan)
            print(f"Support triage for proposal {number}", flush=True)
            support = review(by_id, checks, config, output / f"support-{number}", 1)
            candidate = {"proposal": number, "review": "pending", "triage": support["runs"], "published": False}
            candidate["triage_complete"] = all(row["complete"] for row in support["runs"])
            # Rendering is inspectable candidate output regardless of advisory
            # verdicts; model agreement never constitutes approval.
            files = build(output / "sample.jsonl", plan_path, output / f"candidate-{number}")
            candidate["files"] = len(files)
            candidate["content_hashes"] = {name: hashlib.sha256((output / f"candidate-{number}" / name).read_bytes()).hexdigest() for name in files}
            report["stages"]["candidates"].append(candidate)
            save()
        if hashlib.sha256(config.read_bytes()).hexdigest() != config_digest:
            raise RuntimeError("Inference configuration changed during pilot")
        complete = (len(report["stages"]["candidates"]) == repeats
                    and all(row["triage_complete"] for row in report["stages"]["candidates"]))
        report["status"] = "complete" if complete else "complete_with_stage_failures"
    except Exception as error:
        report.update(status="failed", error_type=type(error).__name__)
        save()
        raise
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        save()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-mib", type=int, default=64)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--seed", default="memory-pilot-v1")
    args = parser.parse_args()
    report = run(args.sources, args.config, args.output, args.max_mib, args.repeats, args.seed)
    print(json.dumps({"status": report["status"], "candidate_review": report["candidate_review"], "live_publication": False}))
    if report["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
