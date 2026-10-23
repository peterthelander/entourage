"""Deterministic readable projections of source records and article plans."""

from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path

from .knowledge_contracts import validate_plan, validate_records


def quoted(text):
    return "\n".join("> " + line for line in text.splitlines())


def render(records, plan, *, accepted=False):
    """Return relative file paths and content; validate everything before writing."""
    by_id = validate_records(records)
    articles = validate_plan(plan, by_id)
    files = {}
    days = defaultdict(list)
    for record in records:
        # This is the source timestamp's calendar date, never the event date.
        days[datetime.fromisoformat(record["observed_at"]).date().isoformat()].append(record)
    for day, entries in sorted(days.items()):
        status = ("Status: Generated projection of reviewed imports; source statements are not independently verified events."
                  if accepted else "Status: Generated candidate; source statements are untrusted evidence, not verified events.")
        lines = [f"# Imported source journal: {day}", "", status, ""]
        for record in sorted(entries, key=lambda r: (datetime.fromisoformat(r["observed_at"]), r["id"])):
            lines += [f"## {record['id']}", "", f"Observed: {record['observed_at']}",
                      f"Event date: {record.get('event_date') or 'not established'}", "",
                      quoted(record["title"]), "", quoted(record["text"]), "",
                      "Source locator:", "", quoted(json.dumps(record["source"], sort_keys=True)), ""]
        files[f"journals/{day}.md"] = "\n".join(lines)
    index = ["# Imported memory index" if accepted else "# Memory candidate index", "",
             "Status: Published reviewed source-grounded memory." if accepted else "Status: Reviewed-plan rendering; not published to agent memory.", ""]
    for article in sorted(articles, key=lambda a: a["slug"]):
        source_ids = {e["record_id"] for claim in article["claims"] for e in claim["evidence"]}
        times = sorted((by_id[identity]["observed_at"] for identity in source_ids),
                       key=lambda value: (datetime.fromisoformat(value), value))
        timeframe = f"{times[0]} to {times[-1]}" if times else "no source timestamps"
        index += [f"- [{article['title']}](articles/{article['slug']}.md): {article['description']} (source timestamps: {timeframe})"]
        status = "Status: Reviewed imported memory; source-grounded, not independently verified." if accepted else "Status: Candidate; semantic accuracy still requires review."
        lines = [f"# {article['title']}", "", status, "",
                 f"Type: {article['type']}", "", f"Source timestamps: {timeframe}", "",
                 "Statements below describe dated source evidence; present-day state has not been verified.", "",
                 article["description"], ""]
        if "activity_period" in article:
            period = article["activity_period"]
            lines += [f"Activity period: {period['start_date']} to {period['end_date']} (associated activity dates, not source timestamps or proof of completion).", ""]
        if "series_slug" in article:
            lines += [f"Series: [{article['series_slug']}]({article['series_slug']}.md)", ""]
        for kind, heading in (("source_statement", "Source statements"), ("inference", "Interpretations"), ("suggestion", "Suggested next steps")):
            lines += [f"## {heading}", ""]
            for claim in article["claims"]:
                if claim["type"] != kind:
                    continue
                lines += [quoted(claim["text"]), ""]
                for evidence in claim["evidence"]:
                    identity = evidence["record_id"]
                    day = datetime.fromisoformat(by_id[identity]["observed_at"]).date().isoformat()
                    lines += [f"Evidence: [{identity}](../journals/{day}.md#{identity}) — source timestamp {by_id[identity]['observed_at']}", "", quoted(evidence["quote"]), ""]
            lines += [""]
        lines += ["## Unknowns", ""]
        lines += [quoted(item) + "\n" for item in article["unknowns"]]
        lines += ["", "## Related articles", ""]
        lines += [f"[[{link}]] — [{link}]({link}.md)" for link in article["links"]]
        files[f"articles/{article['slug']}.md"] = "\n".join(lines).rstrip() + "\n"
    files["index.md"] = "\n".join(index) + "\n"
    files["records.jsonl"] = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in sorted(records, key=lambda r: r["id"]))
    files["plan.json"] = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    return files


def build(records_path, plan_path, output):
    records = [json.loads(line) for line in Path(records_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    files = render(records, plan)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for relative, content in files.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return files
