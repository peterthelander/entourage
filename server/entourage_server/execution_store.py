"""Durable worker checkpoints and device request acknowledgements."""

import hashlib
import hmac
import json
import time
from uuid import uuid4

from .storage import Store, StoreError, now


class ExecutionStore(Store):
    def recover(self):
        # No automatic replay of potentially ambiguous work after restart.
        with self.connect(write=True) as db:
            db.execute("""UPDATE turns SET status='needs_review', revision=revision+1,
                error='Service stopped during this turn. Dismiss the interruption before starting another request.'
                WHERE status IN ('running','waiting_for_device')""")

    def claim(self):
        with self.connect(write=True) as db:
            row = db.execute("SELECT * FROM turns WHERE status='queued' ORDER BY created_at,id LIMIT 1").fetchone()
            if not row:
                return None
            db.execute("UPDATE turns SET status='running',revision=revision+1 WHERE id=?", (row["id"],))
            return dict(row)

    def context_history(self, conversation_id):
        with self.connect() as db:
            rows = db.execute("""SELECT m.role,m.text,m.created_at FROM messages m LEFT JOIN turns t ON t.id=m.turn_id
                WHERE m.conversation_id=? AND m.kind IN ('user','assistant')
                AND (m.turn_id IS NULL OR t.status='completed') ORDER BY m.sequence DESC LIMIT 128""",
                (conversation_id,)).fetchall()
            return [dict(row) for row in reversed(rows)]

    def progress(self, turn_id, partial):
        with self.connect(write=True) as db:
            db.execute("UPDATE turns SET partial_answer=?,revision=revision+1 WHERE id=?", (partial, turn_id))

    def checkpoint(self, turn_id, messages, calls_used):
        """Retain tool-loop state for inspection, not automatic restart replay.

        Recovery still marks interrupted turns needs_review. Turns without tools
        do not have a checkpoint; this is not a complete inference request log.
        """
        with self.connect(write=True) as db:
            self._write_checkpoint(db, turn_id, messages, calls_used)

    @staticmethod
    def _write_checkpoint(db, turn_id, messages, calls_used):
        db.execute("UPDATE turns SET checkpoint=?,revision=revision+1 WHERE id=?",
                   (json.dumps({"messages": messages, "calls_used": calls_used}), turn_id))

    def tool_result(self, turn, name, content, messages, calls_used):
        with self.connect(write=True) as db:
            db.execute("INSERT INTO messages(conversation_id,turn_id,role,kind,text,created_at) VALUES(?,?,'tool','tool',?,?)",
                       (turn["conversation_id"], turn["id"], f"{name}\n{content}", now()))
            self._write_checkpoint(db, turn["id"], messages, calls_used)

    def finish(self, turn, answer=None, error=None, status=None):
        status = status or ("failed" if error else "completed")
        with self.connect(write=True) as db:
            changed = db.execute("UPDATE turns SET status=?,answer=?,error=?,revision=revision+1 WHERE id=? AND status IN ('running','waiting_for_device')",
                       (status, answer, error, turn["id"]))
            if answer is not None and changed.rowcount:
                db.execute("INSERT INTO messages(conversation_id,turn_id,role,kind,text,created_at) VALUES(?,?,'assistant','assistant',?,?)",
                           (turn["conversation_id"], turn["id"], answer, now()))

    def cancel(self, turn_id):
        with self.connect(write=True) as db:
            row = db.execute("SELECT status,error FROM turns WHERE id=?", (turn_id,)).fetchone()
            if not row:
                raise StoreError(404, "not_found", "Turn not found.")
            if row["status"] == "completed":
                raise StoreError(409, "already_completed", "This request already completed.")
            if row["status"] == "failed":
                return
            db.execute("UPDATE turns SET status='failed',error='Stopped by user.',revision=revision+1 WHERE id=?", (turn_id,))

    def register_device(self, device_id, key):
        digest = hashlib.sha256(key.encode()).hexdigest()
        with self.connect(write=True) as db:
            row = db.execute("SELECT key_hash FROM devices WHERE id=?", (device_id,)).fetchone()
            if row and not hmac.compare_digest(row[0], digest):
                raise StoreError(409, "device_conflict", "Device ID already registered with another credential.")
            db.execute("INSERT OR IGNORE INTO devices VALUES(?,?)", (device_id, digest))

    def has_device(self, device_id):
        with self.connect() as db:
            return db.execute("SELECT 1 FROM devices WHERE id=?", (device_id,)).fetchone() is not None

    def request_device(self, turn, name, arguments, timeout):
        request_id = str(uuid4())
        with self.connect(write=True) as db:
            db.execute("INSERT INTO device_requests VALUES(?,?,?,?,?,?,NULL)",
                       (request_id, turn["id"], turn["device_id"], name, json.dumps(arguments), time.time() + timeout))
            db.execute("UPDATE turns SET status='waiting_for_device',revision=revision+1 WHERE id=?", (turn["id"],))
        return request_id

    def device_request(self, request_id):
        with self.connect() as db:
            return dict(db.execute("SELECT * FROM device_requests WHERE id=?", (request_id,)).fetchone())

    def resume(self, turn_id):
        with self.connect(write=True) as db:
            db.execute("UPDATE turns SET status='running',revision=revision+1 WHERE id=?", (turn_id,))

    def submit_device(self, turn_id, request_id, device_id, key, content):
        with self.connect(write=True) as db:
            device = db.execute("SELECT key_hash FROM devices WHERE id=?", (device_id,)).fetchone()
            if not device or not hmac.compare_digest(device[0], hashlib.sha256(key.encode()).hexdigest()):
                raise StoreError(403, "device_forbidden", "Device credential does not match.")
            row = db.execute("SELECT * FROM device_requests WHERE id=? AND turn_id=?", (request_id, turn_id)).fetchone()
            if not row or row["device_id"] != device_id:
                raise StoreError(404, "not_found", "Device request not found.")
            if row["result"] is not None:
                if row["result"] != content:
                    raise StoreError(409, "id_conflict", "Device request already has another result.")
                return
            turn = db.execute("SELECT status FROM turns WHERE id=?", (turn_id,)).fetchone()
            if time.time() >= row["expires_at"] or turn[0] != "waiting_for_device":
                raise StoreError(409, "device_expired", "Device request is no longer active.")
            db.execute("UPDATE device_requests SET result=? WHERE id=?", (content, request_id))

    def get_turn(self, turn_id):
        result = super().get_turn(turn_id)
        result.pop("checkpoint", None)
        with self.connect() as db:
            rows = db.execute("SELECT id,device_id,name,arguments,expires_at,result FROM device_requests WHERE turn_id=? ORDER BY rowid", (turn_id,)).fetchall()
        result["device_requests"] = [{**dict(row), "arguments": json.loads(row["arguments"])} for row in rows]
        return result

    def active_turn(self, conversation_id):
        with self.connect() as db:
            self.require_conversation(db, conversation_id)
            row = db.execute("SELECT id FROM turns WHERE conversation_id=? AND status IN ('queued','running','waiting_for_device','needs_review')",
                             (conversation_id,)).fetchone()
        return self.get_turn(row[0]) if row else None

    def latest_turn(self, conversation_id):
        with self.connect() as db:
            self.require_conversation(db, conversation_id)
            row = db.execute("""SELECT id FROM turns WHERE conversation_id=? OR id IN
                (SELECT turn_id FROM messages WHERE conversation_id=? AND turn_id IS NOT NULL)
                ORDER BY rowid DESC LIMIT 1""", (conversation_id, conversation_id)).fetchone()
        return self.get_turn(row[0]) if row else None
