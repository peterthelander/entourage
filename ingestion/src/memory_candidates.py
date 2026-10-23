"""Render generic candidate documents using the Python service's shared contracts."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from entourage_server.knowledge_contracts import validate_plan, validate_records
from entourage_server.knowledge_documents import build, render


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = build(args.records, args.plan, args.output)
    print(f"Validated and wrote {len(files)} candidate files to {args.output}")


if __name__ == "__main__":
    main()
