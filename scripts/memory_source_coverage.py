"""Experimental article/source coverage disclosure without adding source prose."""

from copy import deepcopy
import json


def article_source_coverage(bundle, result):
    result = deepcopy(result)
    quotes = {}
    for claim in result["article"]["claims"]:
        for evidence in claim["evidence"]:
            quotes.setdefault(evidence["record_id"], set()).add(evidence["quote"])
    result["source_coverage"] = {
        "scope": "Article claims and selected quotations, not exhaustive source contents. "
                 "A detail absent from this article may still appear in unread original text. "
                 "For requested details or qualifications missing here, read the relevant original "
                 "with readKnowledgeSource using its record_id and this snapshot before claiming "
                 "the source does not specify them.",
        "sources": [{"record_id": identity, "observed_at": bundle.records[identity]["observed_at"],
                     "total_characters": len(bundle.records[identity]["text"]),
                     "full_source_text_provided": bundle.records[identity]["text"] in excerpts}
                    for identity, excerpts in sorted(quotes.items())],
    }
    if len(json.dumps(result).encode()) > 64000:
        raise ValueError("Article with source coverage exceeds response limit")
    return result
