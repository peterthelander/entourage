"""Read-only retrieval over isolated candidate bundles; never opens live agent memory."""

import argparse
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from entourage_server.knowledge_bundle import KnowledgeBundle as MemoryPreview


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    search = commands.add_parser("search")
    search.add_argument("keywords", nargs="+")
    search.add_argument("--scope", choices=("articles", "sources"), default="articles")
    article = commands.add_parser("article")
    article.add_argument("slug")
    source = commands.add_parser("source")
    source.add_argument("id")
    source.add_argument("--offset", type=int, default=0)
    source.add_argument("--limit", type=int, default=1200)
    source.add_argument("--snapshot")
    args = parser.parse_args()
    preview = MemoryPreview(args.bundle)
    if args.command == "search":
        result = preview.search(args.keywords, scope=args.scope)
    elif args.command == "article":
        result = preview.read_article(args.slug)
    else:
        result = preview.read_source(args.id, offset=args.offset, limit=args.limit, snapshot=args.snapshot)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
