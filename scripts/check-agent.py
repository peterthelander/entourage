"""Live smoke check of the authenticated server-owned calculator loop."""

import argparse
import json
from pathlib import Path
import secrets
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000")
    args = parser.parse_args()
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
        "text": "Use the calculator to compute 12 multiplied by 13, then give a short answer.", "device_id": device,
    })
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        snapshot = call(f"/turns/{turn}")
        if snapshot["status"] in ("failed", "needs_review"):
            raise RuntimeError(snapshot["error"])
        if snapshot["status"] == "completed":
            page = call(f"/conversations/{conversation}/messages")
            tool_rows = [item for item in page["items"] if item["kind"] == "tool"]
            if len(tool_rows) != 1 or not tool_rows[0]["text"].startswith("calculate\n"):
                raise RuntimeError("Expected exactly one recorded calculator call.")
            measured = json.loads(tool_rows[0]["text"].split("\n", 1)[1])
            if measured.get("result") != 156 or "156" not in snapshot["answer"]:
                raise RuntimeError("Calculator result and final answer did not agree.")
            print("PASS: authenticated server turn completed with one calculator call and answer 156.")
            return
        time.sleep(1)
    raise TimeoutError("Agent smoke check exceeded five minutes.")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        raise SystemExit(f"Agent returned HTTP {error.code}.") from None
