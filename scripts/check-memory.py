"""Isolated real-Ollama memory smoke check; never writes to personal history."""

import argparse
import asyncio
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from entourage_server.agent import Ollama, Worker
from entourage_server.config import Settings
from entourage_server.execution_store import ExecutionStore
from entourage_server.journals import export_journals
from entourage_server.storage import SINGLE_CHAT_ID


async def check(model, overview=False):
    with TemporaryDirectory() as directory:
        path = Path(directory) / "test.db"
        settings = Settings.from_environment()
        from dataclasses import replace
        settings = replace(settings, database_path=path, model=model or settings.model)
        store = ExecutionStore(path)
        store.initialize()
        store.single_chat()
        with store.connect(write=True) as db:
            for text in ["My lantern project code is Cedar-71.", "Correction: my lantern project code is Birch-92."]:
                db.execute("INSERT INTO messages(conversation_id,role,kind,text,created_at) VALUES(?,'user','user',?,?)",
                           (SINGLE_CHAT_ID, text, "2026-10-16T12:00:00+00:00"))
        export_journals(path, path.parent / "vault/journals", "UTC")
        # Separate verification conversation ensures no seeded facts in recent context.
        store.create_conversation("verification", "Service verification")
        prompt = ("Use getMemoryInventory to report which dates my memories cover, then use readMemories to read the earliest day and summarize its topics. Cite source message IDs."
                  if overview else "Search my memories for lantern. What is my corrected project code? Cite the source message ID.")
        store.create_turn("verification", "test-turn", prompt, "test-device")
        turn = store.claim()
        async with httpx.AsyncClient(timeout=300) as client:
            await asyncio.wait_for(Worker(store, settings, Ollama(settings, client)).execute(turn), timeout=300)
        result = store.get_turn("test-turn")
        rows = store.list_messages("verification", 0, 100)["items"]
        tools = {row["text"].split("\n", 1)[0] for row in rows if row["kind"] == "tool"}
        required = {"getMemoryInventory", "readMemories"} if overview else {"searchMemories"}
        expected = "lantern" if overview else "Birch-92"
        if result["status"] != "completed" or not required <= tools or expected.casefold() not in (result["answer"] or "").casefold():
            raise RuntimeError("Model did not complete grounded memory recall; inspect model tool support.")
        print("PASS: real Ollama completed isolated memory inventory and topic reading." if overview else
              "PASS: real Ollama retrieved isolated journals and answered with the corrected project code.")
        print("Answer:", result["answer"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--overview", action="store_true")
    args = parser.parse_args()
    asyncio.run(check(args.model, args.overview))
