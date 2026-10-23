"""Local, bounded discovery pilot for source-backed ski-trip history."""

import argparse
from email import policy
from email.parser import BytesParser
from html import unescape
import json
from pathlib import Path
import re
import zipfile

from filter_mail import scan


def relevant(text):
    text = text.casefold()
    return bool(re.search(r"\bski(?:ing)?\b", text)) and (
        "chapin" in text or bool(re.search(r"(?:daddy|father|dad).{0,30}daughter", text))
    )


def message_text(message):
    parts = [part for part in message.walk()
             if part.get_content_type() in ("text/plain", "text/html")
             and part.get_content_disposition() != "attachment"]
    plain = [p for p in parts if p.get_content_type() == "text/plain"]
    texts = []
    for part in plain or parts:
        try:
            content = part.get_content()
        except (LookupError, UnicodeError):
            content = (part.get_payload(decode=True) or b"").decode("utf-8", "replace")
        if part.get_content_type() == "text/html":
            content = unescape(re.sub(r"<[^>]+>", " ", content))
        texts.append(content)
    return "\n".join(texts)


class Discovery:
    def __init__(self, source, output):
        self.source = source
        self.output = output
        self.matches = 0
        self.oversized = 0

    def write(self, line):
        record = json.loads(line)
        if record["decision"] != "retained":
            return
        if record["length"] > 8 * 1024 * 1024:
            self.oversized += 1
            return
        self.source.seek(record["offset"])
        raw = self.source.read(record["length"])
        message = BytesParser(policy=policy.default).parsebytes(raw.split(b"\n", 1)[1])
        body = message_text(message)
        subject = str(message.get("Subject", ""))
        if relevant(subject + "\n" + body):
            self.matches += 1
            self.output.write(json.dumps({
                **record, "subject": subject, "date": str(message.get("Date", "")),
                "from": str(message.get("From", "")),
                "text": body[:48000], "text_truncated": len(body) > 48000,
                "attachments": [p.get_filename() for p in message.walk() if p.get_filename()],
            }) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    reports = []
    sources = [(args.downloads / "Inbox-003.mbox", 256),
               (args.downloads / "Sent-002.mbox", 256)]
    with zipfile.ZipFile(args.downloads / "takeout-20261015T003759Z-2-001.zip") as archive:
        starred = args.output / "Starred.mbox"
        with archive.open("Takeout/Mail/Starred.mbox") as source, starred.open("xb") as target:
            while block := source.read(1024 * 1024):
                target.write(block)
        sources.append((starred, 64))
    with (args.output / "matches.jsonl").open("x", encoding="utf-8") as output:
        for path, mib in sources:
            with path.open("rb") as source:
                discovery = Discovery(source, output)
                report = scan(path, mib * 1024 * 1024, discovery)
            report.update(matches=discovery.matches, oversized_retained_not_searched=discovery.oversized)
            reports.append(report)
            print(path.name, "matches", discovery.matches, "oversized skipped", discovery.oversized, flush=True)
    calendar_matches = []
    with zipfile.ZipFile(args.downloads / "takeout-20261015T003759Z-1-001.zip") as archive:
        for name in archive.namelist():
            if not name.endswith(".ics"):
                continue
            text = archive.read(name).decode("utf-8", "replace")
            text = re.sub(r"\r?\n[ \t]", "", text)
            for event in re.findall(r"BEGIN:VEVENT.*?END:VEVENT", text, re.S):
                if relevant(event):
                    calendar_matches.append({"archive": str(archive.filename), "entry": name, "event": event})
    (args.output / "calendar-matches.json").write_text(json.dumps(calendar_matches, indent=2), encoding="utf-8")
    (args.output / "scan-report.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print("calendar matches", len(calendar_matches))


if __name__ == "__main__":
    main()
