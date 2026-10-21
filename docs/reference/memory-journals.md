# Daily memory journals

Python owns export and search; SQLite remains authoritative. Journals are a
generated, readable projection. Summaries and article generation remain deferred.

Install updated Python requirements, then run from the repository root:

```powershell
.\server\.venv\Scripts\python.exe scripts/export-journals.py --timezone America/New_York
```

On macOS/Linux use `server/.venv/bin/python`. Output defaults to ignored
`server/data/vault/journals/YYYY-MM-DD.md`. The database defaults to
`server/data/entourage.sqlite3`, respecting `ENTOURAGE_DATABASE_PATH`.
Override paths with `--database` and `--output`; relative paths use the current
working directory. Keep custom output containing personal data outside Git.

`--timezone` overrides `ENTOURAGE_JOURNAL_TIMEZONE`; the fallback is UTC.
Windows uses the declared `tzdata` dependency for IANA timezone rules.
Use the same database and timezone on subsequent exports. To change either,
use a fresh output directory: old files absent from new input are not deleted.

Only the existing shared chat is read. Export never creates/migrates a chat or
modifies SQLite. Open the browser once to resolve the shared chat after migrating
old data. Original conversations and verification chats are not separately exported.

Completed turns include user messages, assistant answers and tool results.
Partial output, failed/unfinished turns and error-kind messages are excluded.
Imported messages have no execution status and are explicitly labeled completion
unverified. Missing original import timestamps represent import time.

Every entry retains its UTC timestamp, local time with UTC offset, conversation
ID, message sequence and available turn ID. Each message belongs to its own local
calendar date; exchanges spanning midnight can appear in two files. Entries sort
by absolute time, then sequence. Source text is blockquoted as untrusted data.

Each run rebuilds represented days from a consistent SQLite snapshot. Repeated
exports leave unchanged files untouched and never duplicate entries. Changed
files are replaced atomically; a crash between files is recoverable by rerunning.
Run one exporter at a time. Files without the generator marker are not overwritten.
Edits to generated files are replaced; keep authored notes/articles separately.
These files are not a complete database backup.

## Search from the assistant

The Python agent also exposes `getMemoryInventory` and `readMemories`:

- `getMemoryInventory({})` reports earliest/latest journal dates, day and message
  counts, and dated counts/timezones in pages of 30 days (`offset`, `next_offset`).
  Counts describe saved messages, not distinct conversations or life events.
- `readMemories({start_date, end_date?})` reads an inclusive local journal-date
  range without keywords. It returns four chunks of up to 600 characters each,
  with speaker labels, dates and source message IDs. Long messages continue across
  chunks. Continue with the returned `next_offset` and `snapshot` token. If journals
  changed between pages, restart at offset zero rather than combine mixed snapshots.

These tools allow questions such as “Which days do your memories cover?” and
“Summarize what we discussed on October 15.” For relative dates, the agent is
instructed to get the requesting device's current time first. Inventory alone
does not supply topics: the agent must read entries before summarizing them.
All memory tools share the existing four-call turn budget, so busy days or long
date ranges may require follow-up requests. Summaries must disclose partial
coverage and cite date/message references; the model's compliance can vary.
Inventory and reading use the same file/byte scan limits as search, flagging
incomplete coverage. Inventory date extent and totals are only for the scanned
subset when those limits apply. Neither tool creates stored summaries.

Restart the Python service after updating code to expose `searchMemories` to
Ollama. No browser changes or new dependencies are needed. The tool reads
`vault/journals` beside the configured SQLite database. Custom export output is
not searched automatically: export to that directory to use the assistant tool.

Arguments are `keywords` (1–6 literal strings, each at most 80 characters) and
optional inclusive `start_date` / `end_date` in `YYYY-MM-DD`. All keywords must
occur in the same message, case-insensitively; there is no semantic search,
stemming or regex. Use short topic words rather than entire natural-language questions.
Keyword search excludes saved outputs from `searchMemories`, `getMemoryInventory`
and `readMemories`, including imported tool results. These copied retrieval payloads
remain in the journals, inventory counts and date-based reading. User messages,
assistant replies and results from other tools retain their existing search behavior.

Up to five newest matching messages return dated excerpts (500 characters each),
speaker labels, journal filenames and SQLite source references. Later corrections
remain alongside earlier statements when both match and fit the result limit;
the model must interpret them. Returned statements are evidence of what was said,
not automatically verified facts. The prompt requests date/message-ID citations.
Existing tool-result display and persisted turn history show the raw evidence.

Only generated date-named files are searched; symlink files are skipped. Search
reads at most 200 eligible files, 2 MiB per file and 16 MiB in total, newest first.
Results indicate truncation and distinguish no matches, unavailable journals and
read failures. Search runs outside the async service event loop. It shares the
existing four-tool-call budget. It does not write files or refresh journals.

With execution enabled, Python now refreshes journals in a separate background
task about every two seconds. It catches up on startup, includes completed and
imported shared-chat history, and retries failures without changing completed
answers. Unchanged source records skip file generation. Persistence-only mode
does not run the refresher. The standalone exporter remains available for inspection.

Set `ENTOURAGE_JOURNAL_TIMEZONE` before starting Python to choose a timezone.
Without it, the service preserves an existing generated journal's timezone,
falling back to UTC for a new vault. Record the deployment timezone in the ignored local runbook. Changing timezone
can leave old day files behind; use a fresh vault when deliberately changing it.
Do not run the standalone exporter concurrently with the service refresher.

Search coverage reports automatic mode, the last successful check timestamp,
timezone, and ready/catching_up/refresh_failed status. During refresh or a failure,
search may still see older journal files. Refreshing multiple days is not a single
atomic operation. SQLite remains authoritative, and restart retries the projection.
Model tool selection and answer quality still depend on the configured model.
Run `server/.venv/Scripts/python.exe scripts/check-memory.py` for an isolated
real-Ollama smoke check (optional `--model`). It creates temporary synthetic
journals and a temporary database, exercises the full worker/tool loop and removes
them afterwards; personal chat history is untouched.
Add `--overview` to test inventory plus date-based topic summarization.
Next steps are improved retrieval and reviewed semantic articles; automatic
dreaming remains deferred.
