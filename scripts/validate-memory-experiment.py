"""Freeze source-first memory inputs, prepare reviews, or check review completeness."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from memory_validation import freeze, review_template, summarize_review, write_new
import importlib.util


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("freeze")
    for name in ("bundle", "fixture", "expected", "output"):
        command.add_argument("--" + name, type=Path, required=True)
    command.add_argument("--providers", nargs="+", choices=("local", "gemini"), default=["local"])
    command.add_argument("--repeats", type=int, choices=(1, 2, 3), default=2)
    command.add_argument("--gemini-model", default="gemini-4-argon")
    for name in ("review-template", "summarize"):
        command = sub.add_parser(name)
        for field in ("report", "expected", "output"):
            command.add_argument("--" + field, type=Path, required=True)
        command.add_argument("--manifest", type=Path)
        if name == "summarize":
            command.add_argument("--review", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze":
        spec = importlib.util.spec_from_file_location("knowledge_evaluation", ROOT / "scripts/evaluate-knowledge.py")
        evaluation = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evaluation)
        evaluation.evaluation.load_cases(args.fixture)
        value = freeze(ROOT, args.bundle, args.fixture, args.expected, evaluation.evaluation.live_settings(),
                       providers=args.providers, repeats=args.repeats, gemini_model=args.gemini_model)
    elif args.command == "review-template":
        value = review_template(args.report, args.expected, manifest_path=args.manifest)
    else:
        value = summarize_review(args.report, args.expected, args.review, manifest_path=args.manifest)
    write_new(args.output, value)
    print(args.output)


if __name__ == "__main__":
    main()
