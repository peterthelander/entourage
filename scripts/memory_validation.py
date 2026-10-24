"""Frozen memory experiments and explicit, report-bound semantic review.

These checks establish artifact identity and review completeness, not truth.
No model judges answers here, and no live memory is read or published.
"""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(value, file, indent=2, ensure_ascii=False)
        file.write("\n")


def freeze(root, bundle, fixture, expected, settings, *, providers, repeats, gemini_model="gemini-4-argon"):
    from entourage_server.knowledge import ReviewedKnowledge

    root, bundle = Path(root).resolve(), Path(bundle).resolve()
    knowledge = ReviewedKnowledge(bundle)
    cases, expectations = read(fixture), read(expected)
    if cases.get("version") != 1 or expectations.get("version") != 1:
        raise ValueError("Expected version 1 fixture and expectations")
    case_ids = [case["id"] for case in cases["cases"]]
    expected_ids = [case["id"] for case in expectations["cases"]]
    if (len(set(case_ids)) != len(case_ids) or set(case_ids) != set(expected_ids)
            or len(set(expected_ids)) != len(expected_ids)):
        raise ValueError("Expectations must cover each fixture case exactly once")
    by_id = {case["id"]: case for case in cases["cases"]}
    for case in expectations["cases"]:
        criteria = case["criteria"]
        turns = [criterion["turn"] for criterion in criteria]
        if (any(type(turn) is not int for turn in turns)
                or sorted(turns) != list(range(1, len(by_id[case["id"]]["turns"]) + 1))):
            raise ValueError("Expected criteria must cover every turn exactly once")
        for criterion in criteria:
            if (not isinstance(criterion.get("expected"), str) or not criterion["expected"].strip()
                    or not criterion.get("source_ids")
                    or any(identity not in knowledge.records for identity in criterion["source_ids"])):
                raise ValueError("Expected criteria need findings and valid source references")
    if (not providers or len(set(providers)) != len(providers)
            or set(providers) - {"local", "gemini"} or type(repeats) is not int or not 1 <= repeats <= 3):
        raise ValueError("Invalid planned providers or repeats")
    if (expectations.get("created_before_inference") is not True
            or type(expectations.get("independent_review")) is not bool):
        raise ValueError("Declare source-first preparation and reviewer independence")
    paths = [Path(fixture).resolve(), Path(expected).resolve()]
    paths += [bundle / name for name in ("records.jsonl", "plan.json", "review.json")]
    paths += sorted((root / "server/entourage_server").glob("*.py"))
    paths += [root / "scripts" / name for name in
              ("evaluate-knowledge.py", "evaluate-conversations.py", "memory_validation.py")]
    # Deliberately exclude credentials, endpoint addresses and arbitrary config fields.
    effective = {name: getattr(settings, name) for name in (
        "inference_provider", "model", "context_tokens", "max_output_tokens", "context_session_gap_minutes")}
    return {"version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
            "bundle_snapshot": knowledge.snapshot, "fixture_sha256": digest(fixture),
            "expected_path": str(Path(expected).resolve()), "settings": effective,
            "independent_review": expectations["independent_review"],
            "scope": expectations.get("scope"),
            "files": {str(path): digest(path) for path in paths},
            "planned_runs": {"providers": providers, "repeats": repeats, "case_ids": case_ids,
                             "gemini_model": gemini_model if "gemini" in providers else None}}


def verify(manifest, settings=None):
    if manifest.get("version") != 1 or not manifest.get("files"):
        raise ValueError("Invalid freeze manifest")
    for path, expected in manifest["files"].items():
        if digest(path) != expected:
            raise ValueError("Frozen experiment artifact changed: " + path)
    if settings is not None:
        for name, value in manifest["settings"].items():
            if getattr(settings, name) != value:
                raise ValueError("Frozen inference setting changed: " + name)


def review_template(report_path, expected_path, *, manifest_path=None):
    report, expected = read(report_path), read(expected_path)
    if manifest_path is not None:
        manifest = read(manifest_path)
        # Review may happen after implementation changes; bind inputs/results,
        # without requiring the working tree still to equal the original code.
        if (report.get("freeze_manifest_sha256") != digest(manifest_path)
                or digest(expected_path) != manifest["files"].get(str(Path(expected_path).resolve()))):
            raise ValueError("Report/expectations do not match the frozen experiment")
        if report.get("diagnostic_modes") != manifest.get("diagnostic_modes"):
            raise ValueError("Report diagnostic modes do not match the frozen experiment")
    by_id = {case["id"]: case for case in expected["cases"]}
    rows, seen = [], set()
    modes = report.get("diagnostic_modes")
    if modes is not None and (not modes or len(set(modes)) != len(modes)):
        raise ValueError("Invalid diagnostic mode plan")
    for run in report["runs"]:
        key = (run["provider"], run["repeat"], run["case"])
        if modes is not None:
            if run.get("mode") not in modes:
                raise ValueError("Run has an unplanned diagnostic mode")
            key += (run["mode"],)
        if key in seen:
            raise ValueError("Duplicate case run in report")
        seen.add(key)
        case = by_id[run["case"]]
        turns = {turn["turn"]: turn for turn in run["turns"]}
        if len(turns) != len(run["turns"]):
            raise ValueError("Duplicate turn in report")
        for criterion in case["criteria"]:
            turn = turns.get(criterion["turn"])
            rows.append({"provider": key[0], "repeat": key[1], "case": key[2],
                         **({"mode": key[3]} if modes is not None else {}),
                         **criterion, "execution_status": turn["status"] if turn else "not_run",
                         "verdict": "pending", "notes": ""})
    return {"version": 1, "report_sha256": digest(report_path),
            "expected_sha256": digest(expected_path),
            "independent_review": expected["independent_review"],
            "reviewer": "", "reviewer_kind": "coding_agent", "rows": rows}


def summarize_review(report_path, expected_path, review_path, *, manifest_path=None):
    template = review_template(report_path, expected_path, manifest_path=manifest_path)
    review = read(review_path)
    if any(review.get(key) != template[key] for key in
           ("version", "report_sha256", "expected_sha256", "independent_review")):
        raise ValueError("Review does not match report and expectations")
    if not review.get("reviewer", "").strip() or review.get("reviewer_kind") not in ("coding_agent", "human"):
        raise ValueError("Explicit reviewer required")
    if len(review.get("rows", [])) != len(template["rows"]):
        raise ValueError("Review must cover all attempted runs and planned turns")
    counts = Counter()
    for row, original in zip(review["rows"], template["rows"]):
        if any(row.get(key) != value for key, value in original.items() if key not in ("verdict", "notes")):
            raise ValueError("Review row identity or expected finding changed")
        verdict = row.get("verdict")
        if verdict not in ("pass", "fail", "unclear", "pending"):
            raise ValueError("Invalid semantic verdict")
        if verdict != "pending" and not row.get("notes", "").strip():
            raise ValueError("Reviewed verdicts need evidence notes")
        if row["execution_status"] != "completed" and verdict == "pass":
            raise ValueError("Unexecuted or failed turns cannot pass")
        counts[verdict] += 1
    report = read(report_path)
    missing = []
    plan = read(manifest_path)["planned_runs"] if manifest_path is not None else report.get("planned_runs")
    if plan is not None:
        modes = report.get("diagnostic_modes")
        seen = {(r["provider"], r["repeat"], r["case"], r.get("mode")) for r in report["runs"]}
        missing = [{"provider": p, "repeat": n, "case": c,
                    **({"mode": mode} if modes is not None else {})} for p in plan["providers"]
                   for n in range(1, plan["repeats"] + 1) for c in plan["case_ids"]
                   for mode in (modes if modes is not None else [None])
                   if (p, n, c, mode) not in seen]
    return {"version": 1, "report_status": report["status"], "semantic_counts": dict(counts),
            "review_complete": not counts["pending"] and not missing,
            "independent_review": review["independent_review"], "missing_runs": missing,
            "execution_counts": dict(Counter(r["execution_status"] for r in review["rows"])),
            "scope": "Explicit reviewer findings; artifact checks do not establish semantic truth"}
