# Ski-trip discovery pilot

Status: Completed bounded discovery; agent integration remains proposed.
Date: October 22, 2026.

## Method and scope

The reusable standard-library runner `ingestion/src/find_ski_trip.py` scans the
first 256 MiB of each large mailbox, the full Starred mailbox from the mail ZIP,
and both calendars in the contacts/calendar ZIP. It extracts Starred to a new
ignored output directory while leaving original archives untouched.

Run from the repository root with a new output directory:

```powershell
python ingestion/src/find_ski_trip.py --downloads C:/Users/Owner/Downloads --output ingestion/data/reports/ski-trip-pilot-20261022
```

Mail filtering uses the existing exact Promotions exclusion before body decoding.
The topic rule requires ski/skiing plus Chapin or a father/dad/daddy-daughter
phrase in the decoded subject or text body. Non-attachment plain text is preferred
over HTML. Records larger than 8 MiB are skipped; attachments are not searched.
Matched text is capped at 48,000 characters with a truncation flag. No inference
service is called. Calendar matching applies the same topic rule to unfolded
VEVENT blocks; it is not a complete semantic calendar search.

## Findings and limits

Inbox: 2,481 complete records, 1,411 Promotions exclusions, one topic match.
Sent: 779 complete records, three exclusions, three topic matches.
Starred: all 256 records, six exclusions, no matches. No calendar matches.
Seven retained large messages were skipped. Prefix sampling and exact topic terms
limit recall; no full-archive absence claims are justified.

Human review found that three messages repeated one announcement through forwards.
These must not count as three separate events or independent confirmation. A
fourth result was related school material without an established trip connection.
The initial evidence supports some historical planning questions but does not yet
support a multi-year history or confirmed participation and outcomes.

Private decoded records, source offsets and scan coverage live under ignored
`ingestion/data/reports/ski-trip-pilot-20261022/`. A manually reviewed candidate
article is in ignored `ingestion/data/candidates/chapin-daddy-daughter-ski-trip-pilot.md`.
It separates direct evidence, forwarded copies, recommendations and unknowns.
It has not been added to the live agent vault or evaluated through the agent.

Next: expand evidence coverage for earlier years and missing trip logistics,
deduplicate forwarded content, then evaluate retrieval against explicit questions.
Do not equate a successful topic search or drafted article with agent-level recall.
