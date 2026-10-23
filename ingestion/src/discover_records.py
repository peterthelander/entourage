"""Select bounded header leads and normalize full messages for offline review."""

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path

from normalize_mail import normalize


def matching_rules(item, rules):
    text = (item["subject"] + "\n" + item["sender"]).casefold()
    matches = []
    for rule in rules:
        any_terms, all_terms = rule.get("any_terms", []), rule.get("all_terms", [])
        if not any_terms and not all_terms:
            raise ValueError("Discovery rules need literal terms")
        if not all(isinstance(t, str) and t.strip() for t in [*any_terms, *all_terms]):
            raise ValueError("Terms must be nonempty strings")
        if (not any_terms or any(t.casefold() in text for t in any_terms)) and all(t.casefold() in text for t in all_terms):
            matches.append(rule["name"])
    return matches


def run(catalogs, rules_path, output, *, max_records=1500, max_source_bytes=64 * 1024 * 1024):
    rules_path, output = Path(rules_path), Path(output)
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    if not rules.get("rules") or max_records <= 0 or max_source_bytes <= 0:
        raise ValueError("Provide rules and positive discovery bounds")
    output.mkdir(parents=True, exist_ok=False)
    counts, seen, source_bytes = Counter(), set(), 0
    report = {"version": 1, "status": "running", "scope": "Header-selected leads, not exhaustive event membership",
              "rules_sha256": hashlib.sha256(rules_path.read_bytes()).hexdigest(),
              "limits": {"max_records": max_records, "max_source_bytes": max_source_bytes, "max_message_bytes": 8 * 1024 * 1024}}
    (output / "rules.json").write_bytes(rules_path.read_bytes())
    try:
        with (output / "records.jsonl").open("x", encoding="utf-8", newline="\n") as records, (output / "decisions.jsonl").open("x", encoding="utf-8", newline="\n") as decisions:
            for catalog in map(Path, catalogs):
                manifest = json.loads((catalog / "report.json").read_text(encoding="utf-8"))
                if manifest["status"] != "complete":
                    raise ValueError("Catalog is incomplete")
                fingerprints = {r["source"]: r for r in manifest["sources"]}
                for path, fingerprint in fingerprints.items():
                    stat = Path(path).stat()
                    if (stat.st_size, stat.st_mtime_ns) != (fingerprint["size"], fingerprint["mtime_ns"]):
                        raise ValueError("Catalog source has changed")
                with (catalog / "headers.jsonl").open(encoding="utf-8") as headers:
                    for line in headers:
                        item = json.loads(line)
                        if (item.get("source") not in fingerprints
                                or type(item.get("offset")) is not int or item["offset"] < 0
                                or type(item.get("length")) is not int or item["length"] <= 0
                                or item["offset"] + item["length"] > fingerprints[item["source"]]["size"]):
                            raise ValueError("Invalid catalog source range")
                        counts["catalog_messages"] += 1
                        if item["excluded"] or item["oversized_headers"]:
                            counts["excluded_or_oversized_headers"] += 1
                            continue
                        observed = item.get("observed_at")
                        if not observed:
                            counts["unknown_message_date"] += 1
                            continue
                        day = datetime.fromisoformat(observed).date().isoformat()
                        if day < rules.get("start_date", "0001-01-01") or day > rules.get("end_date", "9999-12-31"):
                            continue
                        matched = matching_rules(item, rules["rules"])
                        if not matched:
                            continue
                        decision = {"source": item["source"], "offset": item["offset"], "length": item["length"], "rules": matched}
                        record = None
                        if item["length"] > 8 * 1024 * 1024:
                            reason = "message_size_limit"
                        elif counts["normalized"] >= max_records or source_bytes + item["length"] > max_source_bytes:
                            reason = "discovery_budget"
                        else:
                            with Path(item["source"]).open("rb") as source:
                                source.seek(item["offset"])
                                raw = source.read(item["length"])
                            if len(raw) != item["length"]:
                                raise ValueError("Source range is incomplete")
                            source_bytes += len(raw)
                            record, reason = normalize(raw, item["source"], item["offset"])
                            if record and record["id"] in seen:
                                record, reason = None, "duplicate_exact_raw"
                        if record:
                            record["discovery"] = {"rules": matched, "membership": "unreviewed_lead"}
                            seen.add(record["id"])
                            records.write(json.dumps(record, ensure_ascii=False) + "\n")
                            reason = "normalized"
                        counts[reason] += 1
                        decisions.write(json.dumps({**decision, "decision": reason, "record_id": record["id"] if record else None}) + "\n")
                for path, fingerprint in fingerprints.items():
                    stat = Path(path).stat()
                    if (stat.st_size, stat.st_mtime_ns) != (fingerprint["size"], fingerprint["mtime_ns"]):
                        raise ValueError("Catalog source changed during discovery")
        report["status"] = "complete"
    except Exception:
        report["status"] = "failed"
        raise
    finally:
        report.update(counts=dict(counts), decoded_source_bytes=source_bytes)
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogs", nargs="+", type=Path)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-records", type=int, default=1500)
    parser.add_argument("--max-source-mib", type=int, default=64)
    args = parser.parse_args()
    print(json.dumps(run(args.catalogs, args.rules, args.output, max_records=args.max_records,
                         max_source_bytes=args.max_source_mib * 1024 * 1024)))


if __name__ == "__main__":
    main()
