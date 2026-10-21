"""Save the Gemini lookup credential locally without echoing it or making API calls."""

from getpass import getpass
from pathlib import Path


def main():
    key = getpass("Gemini API key (hidden): ").strip()
    if not key or any(c.isspace() for c in key):
        raise SystemExit("No key saved: enter a nonempty key without whitespace.")
    path = Path(__file__).resolve().parents[1] / "server" / "data" / "gemini-api-key.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key + "\n", encoding="utf-8")
    path.chmod(0o600)
    print("Gemini key saved in ignored server/data/gemini-api-key.txt. Restart the Python service to enable web lookup.")


if __name__ == "__main__":
    main()
