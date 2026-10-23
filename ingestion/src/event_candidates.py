"""Suggest event links from reviewed dated observations, never accept membership."""

import argparse
from datetime import date
import json
from pathlib import Path

from memory_candidates import validate_records
from entourage_server.knowledge_contracts import require


def interval(item):
    start, end = item.get("start_date"), item.get("end_date")
    require((start is None) == (end is None), "Provide both event dates or neither")
    if start is None:
        return None
    start, end = date.fromisoformat(start), date.fromisoformat(end)
    require(start <= end, "Reversed event dates")
    return start, end


def tokens(item, field):
    values = item.get(field, [])
    require(isinstance(values, list) and all(isinstance(v, str) and v.strip() for v in values), "Invalid linking terms")
    return {v.strip().casefold() for v in values}


def suggest(records, observations, events):
    """Dates describe activity, not message receipt. Review extraction separately.

    Literal excerpts prove presence only. An explicit extraction review is required
    because mapping those excerpts to dates/places is a semantic judgment.
    """
    by_id = validate_records(records)
    require(type(observations.get("version")) is int and observations["version"] == 1 and observations.get("status") == "reviewed"
            and isinstance(observations.get("reviewer"), str) and observations["reviewer"].strip(),
            "Observations need explicit extraction review")
    facts = observations.get("facts")
    require(isinstance(facts, list) and isinstance(events, list), "Invalid observations/events")
    seen = set()
    for fact in facts:
        require(isinstance(fact, dict) and isinstance(fact.get("id"), str) and fact["id"] not in seen, "Invalid/duplicate observation ID")
        seen.add(fact["id"])
        require(fact.get("record_id") in by_id, "Unknown observation source")
        evidence = fact.get("quotes")
        require(isinstance(evidence, list) and evidence and all(isinstance(q, str) and q.strip()
                and q in by_id[fact["record_id"]]["text"] for q in evidence), "Observation needs exact source excerpts")
        require(isinstance(fact.get("status"), str) and fact["status"].strip(), "Observation needs source status")
        interval(fact)
        for field in ("places", "entities", "references"):
            tokens(fact, field)
    results, event_ids = [], set()
    for event in events:
        require(isinstance(event, dict) and isinstance(event.get("id"), str) and event["id"] not in event_ids, "Invalid/duplicate event ID")
        event_ids.add(event["id"])
        dates = interval(event)
        require(dates is not None, "Event needs an activity date range")
        anchors = event.get("source_ids", [])
        require(isinstance(anchors, list) and all(i in by_id for i in anchors), "Unknown event anchors")
        for fact in facts:
            fact_dates = interval(fact)
            overlap = bool(fact_dates and dates[0] <= fact_dates[1] and fact_dates[0] <= dates[1])
            shared = {field: sorted(tokens(event, field) & tokens(fact, field)) for field in ("places", "entities", "references")}
            anchor = fact["record_id"] in anchors
            # A shared merchant/location alone cannot join recurring years.
            if not (anchor or shared["references"] or overlap):
                continue
            reasons = (["explicit_anchor"] if anchor else []) + (["activity_dates_overlap"] if overlap else [])
            conflict = bool(fact_dates and not overlap and shared["references"])
            if conflict:
                reasons.append("activity_dates_conflict")
            reasons += ["shared_" + field for field, values in shared.items() if values]
            if conflict:
                strength = "conflicting_lead"
            elif anchor:
                strength = "anchor"
            elif shared["references"] or (overlap and (shared["places"] or shared["entities"])):
                strength = "strong_lead"
            else:
                strength = "date_only_lead"
            results.append({"event_id": event["id"], "observation_id": fact["id"], "record_id": fact["record_id"],
                            "source_status": fact["status"], "strength": strength, "reasons": reasons,
                            "shared": shared, "membership": "pending_review"})
    return {"version": 1, "status": "candidates", "links": results,
            "guidance": "All links require membership review. Date overlap is a lead, not proof. Cancellation/charge/reservation/attendance statuses must remain distinct. Unmatched records do not prove absence."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.records.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = suggest(records, json.loads(args.observations.read_text(encoding="utf-8")), json.loads(args.events.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)


if __name__ == "__main__":
    main()
