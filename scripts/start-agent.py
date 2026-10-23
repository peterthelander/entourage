"""Start the single-owner agent with a persistent local credential (Windows/Mac)."""

import argparse
import os
from pathlib import Path
import secrets
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--origin", action="append", default=[], help="Additional exact browser origin allowed to use the API")
    args = parser.parse_args()
    # Machine-local inference selection survives restarts; explicit environment wins.
    inference_file = ROOT / "server" / "data" / "inference.json"
    if inference_file.exists():
        inference = json.loads(inference_file.read_text(encoding="utf-8"))
        allowed = {"ENTOURAGE_INFERENCE_PROVIDER", "ENTOURAGE_LLAMA_CPP_UPSTREAM",
                   "ENTOURAGE_OLLAMA_UPSTREAM", "ENTOURAGE_MODEL", "ENTOURAGE_CONTEXT_TOKENS",
                   "ENTOURAGE_MAX_OUTPUT_TOKENS", "ENTOURAGE_CONTEXT_SESSION_GAP_MINUTES", "ENTOURAGE_KNOWLEDGE_ENABLED"}
        if not isinstance(inference, dict) or set(inference) - allowed:
            raise ValueError("Invalid keys in local inference.json.")
        for name, value in inference.items():
            os.environ.setdefault(name, str(value))
    os.environ.setdefault("ENTOURAGE_EXECUTION_ENABLED", "1")
    token_file = ROOT / "server" / "data" / "access-token.txt"
    if not os.environ.get("ENTOURAGE_API_TOKEN"):
        token_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                file.write(secrets.token_urlsafe(32))
        os.environ["ENTOURAGE_API_TOKEN"] = token_file.read_text(encoding="utf-8").strip()
        print("Local diagnostic credential is available; browser access connects automatically.", flush=True)
    from entourage_server.config import Settings
    from entourage_server.app import create_app
    from dataclasses import replace
    import uvicorn

    settings = Settings.from_environment()
    login, origins = settings.tailscale_login, list(args.origin)
    try:
        result = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=10, check=True)
        status = json.loads(result.stdout)
        owner = status.get("User", {}).get(str(status["Self"]["UserID"]), {})
        login = login or owner.get("LoginName", "")
        dns = status["Self"].get("DNSName", "").rstrip(".")
        if dns:
            origins.append("https://" + dns)
    except (OSError, subprocess.SubprocessError, KeyError, ValueError):
        print("Tailscale identity unavailable; localhost access remains automatic.", flush=True)
    settings = replace(settings, trust_local=True, tailscale_login=login,
                       allowed_origins=tuple(dict.fromkeys((*settings.allowed_origins, *origins))))
    # Preserve the actual socket peer for identity-header trust checks.
    uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port, access_log=False, proxy_headers=False)


if __name__ == "__main__":
    main()
