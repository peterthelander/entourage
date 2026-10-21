"""SQLite authority for conversations and tasks; no inference or side effects here."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import sqlite3

from .models import HistoryImport, legacy_kind

SINGLE_CHAT_ID = "476aa9d6-ddac-4911-a081-973062858de6"


class StoreError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connect(self, *, write: bool = False):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect(write=True) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > 2:
                raise RuntimeError("Database schema is newer than this server supports.")
            if version == 2:
                return
            # Execute separately: executescript would implicitly commit the transaction.
            statements = [
                """CREATE TABLE conversations (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL UNIQUE, title TEXT NOT NULL, created_at TEXT NOT NULL)""",
                """CREATE TABLE turns (
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
                    device_id TEXT NOT NULL, text TEXT NOT NULL, status TEXT NOT NULL
                    CHECK(status IN ('queued','running','waiting_for_device','completed','failed','needs_review')),
                    revision INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL,
                    partial_answer TEXT NOT NULL DEFAULT '', answer TEXT, error TEXT)""",
                """CREATE UNIQUE INDEX one_active_turn ON turns(conversation_id)
                    WHERE status IN ('queued','running','waiting_for_device','needs_review')""",
                """CREATE TABLE messages (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id),
                    turn_id TEXT REFERENCES turns(id), role TEXT NOT NULL
                    CHECK(role IN ('user','assistant','tool')), kind TEXT NOT NULL
                    CHECK(kind IN ('user','assistant','tool','error')), text TEXT NOT NULL,
                    created_at TEXT NOT NULL, legacy_id TEXT,
                    UNIQUE(conversation_id, legacy_id))""",
                "CREATE INDEX message_order ON messages(conversation_id, sequence)",
                """CREATE TABLE imports (
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
                    fingerprint TEXT NOT NULL, imported_count INTEGER NOT NULL)""",
                "PRAGMA user_version = 1",
            ]
            if version == 0:
                for statement in statements:
                    db.execute(statement)
            db.execute("ALTER TABLE turns ADD COLUMN checkpoint TEXT")
            db.execute("""CREATE TABLE devices (id TEXT PRIMARY KEY, key_hash TEXT NOT NULL)""")
            db.execute("""CREATE TABLE device_requests (
                id TEXT PRIMARY KEY, turn_id TEXT NOT NULL REFERENCES turns(id),
                device_id TEXT NOT NULL, name TEXT NOT NULL, arguments TEXT NOT NULL,
                expires_at REAL NOT NULL, result TEXT)""")
            db.execute("CREATE INDEX device_turn ON device_requests(turn_id)")
            db.execute("PRAGMA user_version = 2")

    @staticmethod
    def require_conversation(db, conversation_id):
        if not db.execute("SELECT 1 FROM conversations WHERE id=?", (conversation_id,)).fetchone():
            raise StoreError(404, "not_found", "Conversation not found.")

    def create_conversation(self, conversation_id, title):
        with self.connect(write=True) as db:
            row = db.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
            if row:
                if row["title"] != title:
                    raise StoreError(409, "id_conflict", "Conversation ID already has different input.")
                return dict(row), False
            db.execute("INSERT INTO conversations(id,title,created_at) VALUES(?,?,?)", (conversation_id, title, now()))
            return dict(db.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()), True

    def single_chat(self):
        """Resolve shared history, projecting each earlier message once and retaining originals."""
        with self.connect(write=True) as db:
            db.execute("INSERT OR IGNORE INTO conversations(id,title,created_at) VALUES(?,?,?)",
                       (SINGLE_CHAT_ID, "Entourage", now()))
            self._copy_previous_messages(db)
            return dict(db.execute("SELECT * FROM conversations WHERE id=?", (SINGLE_CHAT_ID,)).fetchone())

    @staticmethod
    def _copy_previous_messages(db):
        """Compatibility projection, inside the shared-chat resolution transaction.

        Keep checking on resolution: older conversation APIs can still receive
        messages after startup. This is not a one-time schema migration.
        """
        db.execute("""INSERT OR IGNORE INTO messages
            (conversation_id,turn_id,role,kind,text,created_at,legacy_id)
            SELECT ?,m.turn_id,m.role,m.kind,m.text,m.created_at,'previous-message-' || m.sequence
            FROM messages m JOIN conversations c ON c.id=m.conversation_id
            WHERE m.conversation_id<>? AND c.title<>'Service verification'
            ORDER BY m.sequence""", (SINGLE_CHAT_ID, SINGLE_CHAT_ID))

    def list_conversations(self, after, limit):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM conversations WHERE sequence>? ORDER BY sequence LIMIT ?", (after, limit + 1)).fetchall()
            return self.page(rows, limit)

    @staticmethod
    def page(rows, limit):
        return {"items": [dict(row) for row in rows[:limit]],
                "next_after": rows[limit - 1]["sequence"] if len(rows) > limit else None}

    def list_messages(self, conversation_id, after, limit):
        if conversation_id == SINGLE_CHAT_ID:
            self.single_chat()
        with self.connect() as db:
            self.require_conversation(db, conversation_id)
            rows = db.execute("SELECT * FROM messages WHERE conversation_id=? AND sequence>? ORDER BY sequence LIMIT ?",
                              (conversation_id, after, limit + 1)).fetchall()
            return self.page(rows, limit)

    def create_turn(self, conversation_id, turn_id, text, device_id):
        with self.connect(write=True) as db:
            self.require_conversation(db, conversation_id)
            row = db.execute("SELECT * FROM turns WHERE id=?", (turn_id,)).fetchone()
            if row:
                if (row["conversation_id"], row["text"], row["device_id"]) != (conversation_id, text, device_id):
                    raise StoreError(409, "id_conflict", "Turn ID already has different input.")
                return dict(row), False
            if db.execute("SELECT 1 FROM turns WHERE conversation_id=? AND status IN ('queued','running','waiting_for_device','needs_review')", (conversation_id,)).fetchone():
                raise StoreError(409, "turn_active", "This conversation already has an unfinished turn.")
            timestamp = now()
            db.execute("INSERT INTO turns(id,conversation_id,device_id,text,status,created_at) VALUES(?,?,?,?,'queued',?)",
                       (turn_id, conversation_id, device_id, text, timestamp))
            db.execute("INSERT INTO messages(conversation_id,turn_id,role,kind,text,created_at) VALUES(?,?,'user','user',?,?)",
                       (conversation_id, turn_id, text, timestamp))
            return dict(db.execute("SELECT * FROM turns WHERE id=?", (turn_id,)).fetchone()), True

    def get_turn(self, turn_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM turns WHERE id=?", (turn_id,)).fetchone()
            if not row:
                raise StoreError(404, "not_found", "Turn not found.")
            return dict(row)

    def import_history(self, conversation_id, import_id, body: HistoryImport, *, append=False):
        fingerprint = hashlib.sha256(json.dumps(body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with self.connect(write=True) as db:
            self.require_conversation(db, conversation_id)
            existing = db.execute("SELECT * FROM imports WHERE id=?", (import_id,)).fetchone()
            if existing:
                if existing["conversation_id"] != conversation_id or existing["fingerprint"] != fingerprint:
                    raise StoreError(409, "id_conflict", "Import ID already has different input.")
                return dict(existing), False
            if not append and db.execute("SELECT 1 FROM messages WHERE conversation_id=?", (conversation_id,)).fetchone():
                raise StoreError(409, "conversation_not_empty", "Import into a new, empty conversation to avoid merging histories.")
            count = 0
            timestamp = now()
            for message in body.messages:
                kind = legacy_kind(message)
                if kind is None:
                    continue
                role = "tool" if kind == "tool" else message.role
                created_at = message.createdAt.astimezone(timezone.utc).isoformat() if message.createdAt else timestamp
                db.execute("INSERT INTO messages(conversation_id,role,kind,text,created_at,legacy_id) VALUES(?,?,?,?,?,?)",
                           (conversation_id, role, kind, message.text, created_at,
                            f"import-{import_id}-{message.id}" if append else message.id))
                count += 1
            db.execute("INSERT INTO imports VALUES(?,?,?,?)", (import_id, conversation_id, fingerprint, count))
            return {"id": import_id, "conversation_id": conversation_id, "imported_count": count}, True
