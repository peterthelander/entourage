"""Retryable journal projection independent of durable turn execution."""

import asyncio
import logging
import re
from datetime import datetime, timezone

from .journals import MARKER, export_journals
from .storage import SINGLE_CHAT_ID


class JournalRefresh:
    def __init__(self, store, timezone_name):
        self.store, self.timezone_name = store, timezone_name
        self.directory = store.path.parent / "vault/journals"
        self.signature = None
        self.last_success = None
        self.failed = False

    def refresh(self):
        try:
            if self.timezone_name is None:
                # Preserve journal day boundaries across ordinary service restarts.
                zone = "UTC"
                for path in sorted(self.directory.glob("????-??-??.md")):
                    if path.is_symlink():
                        continue
                    with path.open(encoding="utf-8") as file:
                        header = file.read(512)
                    match = re.search(r"^Timezone: `([^`\n]+)`$", header, re.MULTILINE)
                    if header.startswith(MARKER) and match:
                        zone = match[1]
                        break
                self.timezone_name = zone
            # Resolve migrated/imported history just as the browser does.
            self.store.single_chat()
            with self.store.connect() as db:
                signature = tuple(db.execute("""SELECT count(*), max(m.sequence) FROM messages m
                    LEFT JOIN turns t ON t.id=m.turn_id WHERE m.conversation_id=?
                    AND m.kind IN ('user','assistant','tool')
                    AND (m.turn_id IS NULL OR t.status='completed')""", (SINGLE_CHAT_ID,)).fetchone())
            if self.signature != signature:
                export_journals(self.store.path, self.directory, self.timezone_name)
                self.signature = signature
            self.last_success = datetime.now(timezone.utc).isoformat()
            self.failed = False
        except Exception:
            # Retry without marking success or exposing private paths/content.
            if not self.failed:
                logging.getLogger(__name__).warning("Journal refresh failed; completed chats remain in SQLite. Retrying.")
            self.failed = True

    def coverage(self):
        return {"mode": "automatic", "status": "refresh_failed" if self.failed else
                "ready" if self.last_success else "catching_up", "last_checked_at": self.last_success,
                "timezone": self.timezone_name,
                "note": "Completed shared-chat history refreshes about every two seconds. Failed or unfinished turns are excluded."}

    async def run(self, stop):
        while not stop.is_set():
            await asyncio.to_thread(self.refresh)
            try:
                await asyncio.wait_for(stop.wait(), timeout=2)
            except TimeoutError:
                pass
