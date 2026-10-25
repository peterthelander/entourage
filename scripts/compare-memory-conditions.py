"""Summarize explicitly reviewed memory conditions without judging answers."""

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from memory_validation import read, summarize_review, write_new


def compare(report_path, expected_path, review_path, *, manifest_path=None):
    validation = summarize_review(report_path, expected_path, review_path, manifest_path=manifest_path)
    report, review = read(report_path), read(review_path)
    groups = defaultdict(lambda: {"rows": [], "turns": [], "cases": defaultdict(list)})
    for row in review["rows"]:
        group = groups[(row["provider"], row.get("mode", "retrieval"))]
        group["rows"].append(row)
        group["cases"][(row["repeat"], row["case"])].append(row)
    for run in report["runs"]:
        group = groups[(run["provider"], run.get("mode", "retrieval"))]
        group["turns"].extend(run["turns"])
    conditions = []
    for (provider, mode), group in sorted(groups.items()):
        turns = group["turns"]
        for turn in turns:
            seconds = turn.get("seconds")
            if type(seconds) not in (float, int) or not 0 <= seconds < float("inf"):
                raise ValueError("Every attempted turn needs a finite nonnegative duration")
        durations = [t["seconds"] for t in turns]
        completed = [t["seconds"] for t in turns if t["status"] == "completed"]
        conditions.append({
            "provider": provider, "mode": mode,
            "reviewed_case_runs": len(group["cases"]),
            "full_case_passes": sum(all(r["verdict"] == "pass" for r in rows)
                                    for rows in group["cases"].values()),
            "planned_turns_in_reviewed_runs": len(group["rows"]), "attempted_turns": len(turns),
            "execution_counts": dict(Counter(r["execution_status"] for r in group["rows"])),
            "semantic_counts": dict(Counter(r["verdict"] for r in group["rows"])),
            "attempt_seconds_median": median(durations) if durations else None,
            "completed_seconds_median": median(completed) if completed else None,
            "total_attempt_seconds": round(sum(durations), 3),
        })
    return {"version": 1, "validation": validation, "conditions": conditions,
            "scope": "Explicit report-bound review, not automatic grading. Completed latency excludes failures; "
                     "inspect attempted latency, skipped turns and missing runs alongside it. "
                     "Unblinded development findings do not establish generalization."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("report", "expected", "review", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    value = compare(args.report, args.expected, args.review, manifest_path=args.manifest)
    write_new(args.output, value)
    print(args.output)


if __name__ == "__main__":
    main()
