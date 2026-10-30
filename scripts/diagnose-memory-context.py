"""Compare bounded evidence-context treatments in isolated memory diagnostics.

Uses diagnose-memory.py arguments plus --source-context none|paragraphs and
--overview-index include|omit. Only one treatment may be active per run. All
changes are process-local; the live service and reviewed bundle stay unchanged.
"""

import argparse
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "scripts"))

from entourage_server.knowledge_bundle import KnowledgeBundle
from memory_source_context import article_source_context
from memory_validation import digest


def omit_overview_index(packet):
    packet = deepcopy(packet)
    result = packet[0]["result"]
    if "articles" not in result:
        raise ValueError("Index omission requires selected article evidence, not an inventory-only condition")
    result["inventory"] = []
    result["scope"] = ("Only this reviewed imported bundle; no conversation contents or full archive supplied. "
                       "Selected articles are supplied in full; uninspected index entries are withheld.")
    return packet


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--source-context", choices=("none", "paragraphs"), default="none")
    parser.add_argument("--overview-index", choices=("include", "omit"), default="include")
    args, remaining = parser.parse_known_args()
    if args.source_context == "paragraphs" and args.overview_index == "omit":
        parser.error("Compare one context treatment at a time")
    spec = importlib.util.spec_from_file_location("source_context_diagnosis", ROOT / "scripts/diagnose-memory.py")
    diagnosis = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diagnosis)
    original_freeze, original_read = diagnosis.freeze, KnowledgeBundle.read_article
    original_overview = diagnosis.overview_evidence
    original_evidence = diagnosis.supplied_evidence

    def freeze(*values, **kwargs):
        manifest = original_freeze(*values, **kwargs)
        for path in (Path(__file__), ROOT / "scripts/memory_source_context.py"):
            manifest["files"][str(path.resolve())] = digest(path)
        manifest["source_context_condition"] = args.source_context
        manifest["overview_index_condition"] = args.overview_index
        manifest["context_treatment_scope"] = "Process-local diagnostic only; no production adoption."
        return manifest

    def read(bundle, slug):
        result = original_read(bundle, slug)
        return article_source_context(bundle, result) if args.source_context == "paragraphs" else result

    def overview(*values, **kwargs):
        packet = original_overview(*values, **kwargs)
        return omit_overview_index(packet) if args.overview_index == "omit" else packet

    def evidence(bundle, case, mode, overview=None):
        if args.source_context == "paragraphs" and mode not in {"retrieval", "articles"}:
            raise ValueError("Source paragraph treatment requires retrieval or article diagnostic modes")
        if args.overview_index == "omit" and mode not in {"flat_overview", "thematic_overview"}:
            raise ValueError("Index omission requires flat or thematic overview modes")
        return original_evidence(bundle, case, mode, overview)

    with patch.object(diagnosis, "freeze", freeze), patch.object(diagnosis, "overview_evidence", overview), \
            patch.object(diagnosis, "supplied_evidence", evidence), \
            patch.object(KnowledgeBundle, "read_article", read), \
            patch.object(sys, "argv", [str(ROOT / "scripts/diagnose-memory.py"), *remaining]):
        diagnosis.main()


if __name__ == "__main__":
    main()
