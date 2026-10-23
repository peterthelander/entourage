"""Normalize bounded MBOX samples into generic source records, without inference."""

import argparse
from collections import Counter
import csv
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path

from filter_mail import PROMOTIONS, scan
from memory_candidates import validate_records


class ReadableHTML(HTMLParser):
    """Extract visible text, excluding scripts, styling and document metadata."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head"):
            self.hidden.append(tag)
        if not self.hidden and tag in ("br", "p", "div", "li", "tr", "h1", "h2", "h3"):
            self.chunks.append("\n")

    def handle_endtag(self, tag):
        if self.hidden and tag == self.hidden[-1]:
            self.hidden.pop()
        if not self.hidden and tag in ("p", "div", "li", "tr"):
            self.chunks.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.chunks.append(data)


def extract_text(message, warnings, omitted):
    # Reject an entire attached subtree, including nested forwarded messages.
    if message.get_content_disposition() == "attachment" or message.get_filename():
        omitted.append({"type": message.get_content_type(), "filename": message.get_filename()})
        return ""
    if message.get_content_maintype() == "message":
        omitted.append({"type": message.get_content_type(), "filename": None})
        return ""
    if message.is_multipart():
        children = list(message.iter_parts())
        if message.get_content_subtype() == "alternative":
            # Prefer a nonempty plain alternative, but keep all visible parts of
            # a mixed message instead of globally discarding HTML siblings.
            children.sort(key=lambda p: p.get_content_type() != "text/plain")
            for part in children:
                text = extract_text(part, warnings, omitted)
                if text.strip():
                    return text
            return ""
        return "\n\n".join(text for part in children if (text := extract_text(part, warnings, omitted)).strip())
    if message.get_content_type() not in ("text/plain", "text/html"):
        omitted.append({"type": message.get_content_type(), "filename": None})
        return ""
    try:
        text = message.get_content()
    except (LookupError, UnicodeError):
        warnings.append("charset_decode_fallback_utf8_replacement")
        text = (message.get_payload(decode=True) or b"").decode("utf-8", "replace")
    if "\ufffd" in text:
        warnings.append("replacement_characters_present")
    if message.get_content_type() == "text/html":
        parser = ReadableHTML()
        parser.feed(text)
        parser.close()
        text = "".join(parser.chunks)
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def normalize(raw, source, offset):
    """Return (record, rejection reason). Hash covers the complete MBOX byte range."""
    message = BytesParser(policy=policy.default).parsebytes(raw.split(b"\n", 1)[1])
    labels = set()
    for value in message.get_all("X-Gmail-Labels", []):
        labels.update(item.strip() for item in next(csv.reader([str(value)])) if item.strip())
    if PROMOTIONS in labels:
        return None, "promotions_label"
    dates = message.get_all("Date", [])
    if len(dates) != 1:
        return None, "missing_or_multiple_dates"
    try:
        observed = parsedate_to_datetime(str(dates[0]))
        if observed.utcoffset() is None:
            return None, "date_without_timezone"
    except (TypeError, ValueError, OverflowError):
        return None, "invalid_date"
    warnings = []
    omitted = []
    text = extract_text(message, warnings, omitted)
    if not text:
        return None, "no_readable_body"
    warnings += sorted({type(defect).__name__ for part in message.walk() for defect in part.defects})
    digest = hashlib.sha256(raw).hexdigest()
    record = {
        "version": 1, "id": "mail-" + digest, "kind": "email",
        "title": str(message.get("Subject", "")).strip() or "(No subject)",
        "text": text, "observed_at": observed.isoformat(), "event_date": None,
        "labels": sorted(labels),
        "source": {"uri": Path(source).resolve().as_uri(),
                   "locator": f"mbox offset={offset} length={len(raw)}",
                   "sha256": digest},
        "email": {"message_id": str(message.get("Message-ID", "")),
                  "from": str(message.get("From", "")),
                  "to": str(message.get("To", "")),
                  "date_header": str(dates[0])},
        "extraction": {"version": 1, "method": "mime-readable-body",
                       "text_truncated": False, "attachments_included": False,
                       "omitted_parts": omitted, "warnings": sorted(set(warnings))},
    }
    validate_records([record])
    return record, None


class Normalizer:
    def __init__(self, source, path, records, decisions, seen, max_message_bytes):
        self.source, self.path = source, path
        self.records, self.decisions, self.seen = records, decisions, seen
        self.max_message_bytes = max_message_bytes
        self.counts = Counter()

    def write(self, line):
        entry = json.loads(line)
        record = None
        identity = None
        if entry["decision"] == "excluded":
            reason = "promotions_label"
        elif entry["oversized_headers"]:
            reason = "oversized_headers"
        elif entry["length"] > self.max_message_bytes:
            reason = "message_size_limit"
        else:
            self.source.seek(entry["offset"])
            raw = self.source.read(entry["length"])
            if len(raw) != entry["length"]:
                raise RuntimeError("Source changed: incomplete byte range")
            record, reason = normalize(raw, self.path, entry["offset"])
            identity = record["id"] if record else None
            if record and record["id"] in self.seen:
                record, reason = None, "duplicate_exact_raw"
        if record:
            self.seen.add(record["id"])
            payload = json.dumps(record, ensure_ascii=False) + "\n"
            self.records.write(payload)
            self.counts["normalized_source_bytes"] += entry["length"]
            self.counts["normalized_text_utf8_bytes"] += len(record["text"].encode("utf-8"))
            self.counts["normalized_jsonl_utf8_bytes"] += len(payload.encode("utf-8"))
            reason = "normalized"
        self.counts[reason + "_messages"] += 1
        entry.update(normalization=reason, record_id=identity)
        self.decisions.write(json.dumps(entry) + "\n")


def run(sources, output, max_bytes, max_message_bytes):
    paths = [Path(path).resolve(strict=True) for path in sources]
    if len(set(paths)) != len(paths):
        raise ValueError("Duplicate input paths")
    if max_bytes <= 0 or max_message_bytes <= 0:
        raise ValueError("Byte limits must be positive")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    reports, seen = [], set()
    with (output / "records.jsonl").open("x", encoding="utf-8", newline="\n") as records, (output / "decisions.jsonl").open("x", encoding="utf-8", newline="\n") as decisions:
        for path in paths:
            before = path.stat()
            with path.open("rb") as source:
                worker = Normalizer(source, path, records, decisions, seen, max_message_bytes)
                report = scan(path, max_bytes, worker)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError("Source changed during normalization; discard this run")
            report["normalization"] = dict(worker.counts)
            reports.append(report)
    summary = {"status": "complete", "adapter_version": 1, "sources": reports,
               "limits": {"max_bytes_per_source": max_bytes, "max_message_bytes": max_message_bytes},
               "scope": "Bounded source normalization only; no article synthesis or live publication"}
    (output / "report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-mib", type=int, default=64)
    parser.add_argument("--max-message-mib", type=int, default=8)
    args = parser.parse_args()
    result = run(args.sources, args.output, args.max_mib * 1024 * 1024, args.max_message_mib * 1024 * 1024)
    for source in result["sources"]:
        print(Path(source["source"]).name, json.dumps(source["normalization"]))


if __name__ == "__main__":
    main()
