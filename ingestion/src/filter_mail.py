"""Bounded, read-only MBOX filtering; only headers are buffered."""

import argparse
import csv
import json
from collections import Counter
from email import policy
from email.parser import BytesHeaderParser
from pathlib import Path


PROMOTIONS = "Category Promotions"
HEADER_LIMIT = 256 * 1024


def scan(path, max_bytes, manifest=None):
    path = Path(path)
    size = path.stat().st_size
    limit = min(max_bytes, size)
    totals = Counter()
    label_counts = Counter()
    offset = 0
    start = None
    headers = bytearray()
    in_headers = False
    oversized = False

    def finish(end):
        if start is None:
            return
        message = BytesHeaderParser(policy=policy.default).parsebytes(bytes(headers))
        labels = set()
        for value in message.get_all("X-Gmail-Labels", []):
            labels.update(label.strip() for label in next(csv.reader([str(value)])))
        # Incomplete/oversized headers are retained conservatively.
        excluded = not oversized and PROMOTIONS in labels
        group = "excluded" if excluded else "retained"
        length = end - start
        totals[group + "_messages"] += 1
        totals[group + "_bytes"] += length
        totals["messages_without_labels"] += not bool(labels)
        totals["oversized_headers"] += oversized
        label_counts.update(labels)
        if manifest:
            manifest.write(json.dumps({
                "source": str(path.resolve()), "offset": start, "length": length,
                "message_id": str(message.get("Message-ID", "")),
                "labels": sorted(labels), "decision": group,
                "reason": "promotions_label" if excluded else "no_exclusion",
                "oversized_headers": oversized,
            }) + "\n")

    with path.open("rb") as source:
        line_start = True
        while offset < limit:
            chunk = source.readline(min(1024 * 1024, limit - offset))
            if not chunk:
                break
            if line_start and chunk.startswith(b"From "):
                finish(offset)
                start = offset
                headers = bytearray()
                in_headers = True
                oversized = False
            elif start is not None and in_headers:
                if chunk in (b"\n", b"\r\n"):
                    in_headers = False
                elif len(headers) + len(chunk) <= HEADER_LIMIT:
                    headers.extend(chunk)
                else:
                    oversized = True
                    in_headers = False
            offset += len(chunk)
            line_start = chunk.endswith(b"\n")
    if offset == size:
        finish(offset)
        partial = 0
    else:
        partial = offset - start if start is not None else 0
    counts = {key: totals[key] for key in (
        "retained_messages", "excluded_messages", "retained_bytes", "excluded_bytes",
        "messages_without_labels", "oversized_headers",
    )}
    return {
        "source": str(path.resolve()), "source_bytes": size,
        "read_bytes": offset, "complete_file": offset == size,
        "trailing_partial_bytes_not_counted": partial,
        "unassigned_bytes": offset - partial - totals["retained_bytes"] - totals["excluded_bytes"],
        **counts, "labels": dict(label_counts.most_common()),
        "byte_measure": "Original MBOX bytes including envelope, headers, body and attachments",
        "sampling": "Sequential prefix; trailing partial message excluded unless source EOF reached",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--max-mib", type=int, default=64)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.max_mib <= 0:
        parser.error("--max-mib must be positive")
    paths = [*args.sources, args.report] + ([args.manifest] if args.manifest else [])
    resolved = [p.resolve() for p in paths]
    if len(set(resolved)) != len(resolved):
        parser.error("Sources and output paths must be distinct")
    outputs = [args.report] + ([args.manifest] if args.manifest else [])
    for output in outputs:
        if output.exists():
            parser.error(f"Output already exists: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
    manifest = args.manifest.open("x", encoding="utf-8") if args.manifest else None
    try:
        reports = [scan(p, args.max_mib * 1024 * 1024, manifest) for p in args.sources]
    finally:
        if manifest:
            manifest.close()
    args.report.write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
