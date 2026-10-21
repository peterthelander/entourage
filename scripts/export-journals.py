"""Export the existing shared chat into local daily Markdown journals."""

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from entourage_server.journals import export_journals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path(os.environ.get(
        "ENTOURAGE_DATABASE_PATH", ROOT / "server/data/entourage.sqlite3")))
    parser.add_argument("--output", type=Path, default=ROOT / "server/data/vault/journals")
    parser.add_argument("--timezone", default=os.environ.get("ENTOURAGE_JOURNAL_TIMEZONE", "UTC"),
                        help="IANA timezone, e.g. America/New_York (default: UTC)")
    args = parser.parse_args()
    try:
        result = export_journals(args.database, args.output, args.timezone)
    except Exception as error:
        parser.exit(1, f"Journal export failed ({type(error).__name__}). Check database, timezone and output permissions.\n")
    print(f"Exported {result['messages']} messages across {result['days']} days; {result['changed']} files updated.")


if __name__ == "__main__":
    main()
