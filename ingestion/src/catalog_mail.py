"""Bounded streaming MBOX header catalog; source bodies are never copied."""

import argparse
import csv
from datetime import datetime, timezone
from email import policy
from email.parser import BytesHeaderParser
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import re
import time

from filter_mail import HEADER_LIMIT, PROMOTIONS


def ranges(path, *, max_bytes, start_offset=0, block_size=4 * 1024 * 1024):
    """Yield complete MBOX ranges; a bounded trailing partial is not emitted.

    Resume only at a previously emitted envelope offset. Standard MBOX escaping
    is required: unescaped body lines beginning 'From ' are ambiguous.
    """
    size = path.stat().st_size
    if max_bytes <= 0 or block_size < 8 or not 0 <= start_offset <= size:
        raise ValueError("Invalid scan bounds")
    end = min(size, start_offset + max_bytes)
    previous, tail, position, last = None, b"", start_offset, -1
    with path.open("rb") as source:
        source.seek(start_offset)
        while position < end:
            block = source.read(min(block_size, end - position))
            if not block:
                raise RuntimeError("Source shortened during cataloging")
            data = tail + block
            base = position - len(tail)
            boundaries = ([start_offset] if position == start_offset and block.startswith(b"From ") else [])
            boundaries += [base + match.start() + 1 for match in re.finditer(br"\nFrom ", data)]
            for boundary in boundaries:
                if boundary <= last:
                    continue
                if previous is not None:
                    yield previous, boundary - previous
                previous, last = boundary, boundary
            position += len(block)
            tail = data[-6:]
    if previous is not None and end == size:
        yield previous, size - previous


def headers(source, offset, length):
    source.seek(offset)
    raw = source.read(min(length, HEADER_LIMIT + 1))
    body = raw.split(b"\n", 1)[1] if b"\n" in raw else b""
    separator = re.search(br"\r?\n\r?\n", body)
    oversized = separator is None and length > HEADER_LIMIT
    message = BytesHeaderParser(policy=policy.default).parsebytes(body[:separator.start()] if separator else body)
    labels = set()
    for value in message.get_all("X-Gmail-Labels", []):
        labels.update(label.strip() for label in next(csv.reader([str(value)])) if label.strip())
    observed = None
    try:
        dates = message.get_all("Date", [])
        parsed = parsedate_to_datetime(str(dates[0])) if len(dates) == 1 else None
        observed = parsed.isoformat() if parsed and parsed.utcoffset() is not None else None
    except (ValueError, TypeError, OverflowError):
        pass
    return {"offset": offset, "length": length, "observed_at": observed,
            "subject": str(message.get("Subject", "")), "sender": str(message.get("From", "")),
            "message_id": str(message.get("Message-ID", "")), "labels": sorted(labels),
            "oversized_headers": oversized, "excluded": not oversized and PROMOTIONS in labels}


def run(sources, output, *, max_bytes):
    output = Path(output)
    paths = [Path(p).resolve(strict=True) for p in sources]
    if len(set(paths)) != len(paths) or not paths or max_bytes <= 0:
        raise ValueError("Provide distinct sources and a positive byte budget")
    output.mkdir(parents=True, exist_ok=False)
    report = {"version": 1, "status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Header catalog only; bounded prefixes, no model processing", "sources": []}
    report_path = output / "report.json"
    def save():
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    save()
    try:
        with (output / "headers.jsonl").open("x", encoding="utf-8", newline="\n") as catalog:
            for path in paths:
                before, started = path.stat(), time.monotonic()
                row = {"source": str(path), "size": before.st_size, "mtime_ns": before.st_mtime_ns,
                       "budget_bytes": max_bytes, "messages": 0, "excluded_promotions": 0,
                       "complete_bytes": 0, "earliest": None, "latest": None}
                with path.open("rb") as source:
                    for offset, length in ranges(path, max_bytes=max_bytes):
                        item = headers(source, offset, length)
                        catalog.write(json.dumps({"source": str(path), **item}, ensure_ascii=False) + "\n")
                        row["messages"] += 1
                        row["excluded_promotions"] += item["excluded"]
                        row["complete_bytes"] = offset + length
                        stamp = item["observed_at"]
                        if stamp:
                            for field, compare in (("earliest", min), ("latest", max)):
                                row[field] = compare([row[field], stamp], key=datetime.fromisoformat) if row[field] else stamp
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise RuntimeError("Source changed during cataloging; discard this run")
                row.update(read_bytes=min(max_bytes, before.st_size), complete_file=max_bytes >= before.st_size,
                           seconds=round(time.monotonic() - started, 3))
                report["sources"].append(row)
                save()
                print(json.dumps({"source": path.name, **{k: row[k] for k in ("messages", "earliest", "latest", "seconds")}}), flush=True)
        report["status"] = "complete"
    except Exception:
        report["status"] = "failed"
        raise
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        save()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-mib", type=int, default=1024)
    args = parser.parse_args()
    run(args.sources, args.output, max_bytes=args.max_mib * 1024 * 1024)


if __name__ == "__main__":
    main()
