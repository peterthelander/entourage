"""Check knowledge reads by creating an isolated live verification conversation."""

import argparse
import json
from pathlib import Path
import secrets
import time
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-articles", type=int)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use a new smoke-check output file")
    root = Path(__file__).resolve().parents[1]
    token = (root / "server/data/access-token.txt").read_text().strip()

    def call(path, body=None):
        request = Request(args.endpoint.rstrip("/") + "/api/v1" + path,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
                          method="PUT" if body is not None else "GET")
        with urlopen(request, timeout=15) as response:
            return json.load(response)

    device, conversation, turn = (str(uuid4()) for _ in range(3))
    call(f"/devices/{device}", {"key": secrets.token_urlsafe(32)})
    call(f"/conversations/{conversation}", {"title": "Service verification"})
    call(f"/conversations/{conversation}/turns/{turn}", {
        "text": "Use the memory inventory to report how many reviewed imported articles and original source records are available. Do not search the public web.",
        "device_id": device})
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        result = call(f"/turns/{turn}")
        if result["status"] in ("failed", "needs_review"):
            raise RuntimeError("Knowledge smoke turn did not complete")
        if result["status"] == "completed":
            page = call(f"/conversations/{conversation}/messages")
            tools = [m for m in page["items"] if m["kind"] == "tool"]
            inventories = [json.loads(m["text"].split("\n", 1)[1]).get("imported_memory")
                           for m in tools if m["text"].startswith("getMemoryInventory\n")]
            inventory = next((item for item in inventories if item and item.get("status") == "ready"), None)
            if inventory is None:
                raise RuntimeError("The running service did not expose the reviewed knowledge inventory")
            if args.expected_articles is not None and inventory["article_count"] != args.expected_articles:
                raise RuntimeError("Unexpected active article count")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"status": "passed", "conversation_id": conversation,
                "article_count": inventory["article_count"], "source_count": inventory["source_count"],
                "snapshot": inventory["snapshot"], "answer": result["answer"],
                "note": "Verification conversation is excluded from shared-chat consolidation"}, indent=2), encoding="utf-8")
            print(f"PASS: running service retrieved {inventory['article_count']} reviewed articles and {inventory['source_count']} sources.")
            return
        time.sleep(1)
    raise TimeoutError("Knowledge smoke check exceeded five minutes")


if __name__ == "__main__":
    main()
