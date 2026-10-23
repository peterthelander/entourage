"""Activate one explicitly reviewed immutable bundle in the Python service's knowledge store."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from entourage_server.knowledge import publish_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--knowledge-root", type=Path, required=True)
    parser.add_argument("--bundle-id")
    args = parser.parse_args()
    print(json.dumps(publish_bundle(args.bundle, args.review, args.knowledge_root, bundle_id=args.bundle_id), indent=2))


if __name__ == "__main__":
    main()
