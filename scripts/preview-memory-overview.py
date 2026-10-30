"""Validate and export an experimental overview packet without running inference."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from entourage_server.knowledge import ReviewedKnowledge
from memory_overview import load_overview, overview_evidence
from memory_validation import write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--overview", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("inventory", "flat_overview", "thematic_overview", "selected_overview"),
                        default="thematic_overview")
    parser.add_argument("--detail-article", action="append", default=[])
    args = parser.parse_args()
    bundle = ReviewedKnowledge(args.bundle)
    plan = load_overview(args.overview)
    packet = overview_evidence(bundle, plan, args.mode, args.detail_article)
    write_new(args.output, packet)
    print(json.dumps({"status": "experimental_preview", "snapshot": bundle.snapshot,
                      "mode": args.mode, "utf8_bytes": len(json.dumps(packet, ensure_ascii=False).encode("utf-8")),
                      "note": "No inference, live memory changes or semantic approval."}))


if __name__ == "__main__":
    main()
