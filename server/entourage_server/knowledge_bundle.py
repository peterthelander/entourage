"""Read-only bounded bundle retrieval shared by previews and the Python service."""

import hashlib
import json
import re
from pathlib import Path

from .knowledge_contracts import validate_plan, validate_records


class KnowledgeBundle:
    def __init__(self, bundle):
        root = Path(bundle).resolve(strict=True)
        contents = []
        for name in ("records.jsonl", "plan.json"):
            path = root / name
            if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
                raise ValueError("Bundle inputs must be ordinary files inside the bundle")
            with path.open("rb") as source:
                raw = source.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError("Bundle exceeds preview input limit")
            contents.append(raw)
        records = [json.loads(line) for line in contents[0].decode("utf-8").splitlines() if line.strip()]
        self.records = validate_records(records)
        plan = json.loads(contents[1])
        self.articles = {a["slug"]: a for a in validate_plan(plan, self.records)}
        self.snapshot = hashlib.sha256(b"".join(hashlib.sha256(c).digest() for c in contents)).hexdigest()

    def envelope(self, **data):
        return {"status": "unpublished_candidate", "semantic_review": "not_verified_by_preview",
                "snapshot": self.snapshot, **data}

    @staticmethod
    def keywords(values):
        if (not isinstance(values, list) or not 1 <= len(values) <= 6
                or any(not isinstance(v, str) or not v.strip() or len(v) > 80 for v in values)):
            raise ValueError("Supply 1 to 6 nonempty literal keywords, each at most 80 characters")
        return [v.casefold() for v in values]

    def search(self, keywords, *, scope="articles", limit=5):
        terms = self.keywords(keywords)
        if type(limit) is not int or not 1 <= limit <= 5 or scope not in ("articles", "sources"):
            raise ValueError("Invalid search scope or limit")
        matches = []
        if scope == "articles":
            for slug, article in sorted(self.articles.items()):
                text = "\n".join([article["title"], article["description"],
                                  *(c["text"] for c in article["claims"])])
                if all(term in text.casefold() for term in terms):
                    ids = sorted({e["record_id"] for c in article["claims"] for e in c["evidence"]})
                    matches.append({"slug": slug, "title": article["title"], "description": article["description"],
                                    "source_ids": ids, "source_timestamps": {i: self.records[i]["observed_at"] for i in ids}})
        else:
            for identity, record in sorted(self.records.items()):
                if all(term in (record["title"] + "\n" + record["text"]).casefold() for term in terms):
                    first = next((record["text"].casefold().find(t) for t in terms if t in record["text"].casefold()), 0)
                    start = max(0, first - 100)
                    matches.append({"record_id": identity, "title": record["title"], "observed_at": record["observed_at"],
                                    "excerpt": record["text"][start:start + 500], "excerpt_offset": start})
        return self.envelope(scope=scope, total_matches=len(matches), results=matches[:limit], truncated=len(matches) > limit)

    def read_article(self, slug):
        if slug not in self.articles:
            raise ValueError("Unknown article slug")
        article = self.articles[slug]
        ids = sorted({e["record_id"] for c in article["claims"] for e in c["evidence"]})
        result = self.envelope(article=article, source_timestamps={i: self.records[i]["observed_at"] for i in ids})
        if len(json.dumps(result).encode()) > 64000:
            raise ValueError("Article exceeds preview response limit; read its sources separately")
        return result

    def related_search(self, keywords, *, scope="articles", limit=5):
        """Rank possible leads when literal phrases miss; never label them exact matches."""
        terms = self.keywords(keywords)
        if scope not in ("articles", "sources") or type(limit) is not int or not 1 <= limit <= 5:
            raise ValueError("Invalid search scope or limit")
        tokens = list(dict.fromkeys(token for term in terms for token in re.findall(r"\w+", term)))[:48]
        ranked = []
        for identity, item in sorted((self.articles if scope == "articles" else self.records).items()):
            if scope == "articles":
                text = "\n".join([item["title"], item["description"], *(c["text"] for c in item["claims"]), *item["unknowns"]])
                ids = sorted({e["record_id"] for c in item["claims"] for e in c["evidence"]})
                result = {"slug": identity, "title": item["title"], "description": item["description"],
                          "source_ids": ids, "source_timestamps": {i: self.records[i]["observed_at"] for i in ids}}
            else:
                text = item["title"] + "\n" + item["text"]
                result = {"record_id": identity, "title": item["title"], "observed_at": item["observed_at"],
                          "excerpt": item["text"][:500], "excerpt_offset": 0}
            words = set(re.findall(r"\w+", text.casefold()))
            matched = [token for token in tokens if token in words]
            if matched:
                result.update(matched_tokens=matched, missing_tokens=[t for t in tokens if t not in matched])
                ranked.append((len(matched), identity, result))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        return self.envelope(scope=scope, match_mode="ranked_partial", total_matches=len(ranked),
                             results=[r[2] for r in ranked[:limit]], truncated=len(ranked) > limit,
                             retrieval_guidance="Possible leads ranked by literal word overlap, not semantic or complete matches. Read evidence before answering; missing query terms are not established.")

    def read_source(self, identity, *, offset=0, limit=1200, snapshot=None):
        if (snapshot is not None and snapshot != self.snapshot) or (offset and snapshot != self.snapshot):
            raise ValueError("Source continuation requires the matching snapshot")
        if identity not in self.records or type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 6000:
            raise ValueError("Invalid source ID, offset or limit")
        record = self.records[identity]
        if offset > len(record["text"]):
            raise ValueError("Source offset exceeds text length")
        end = min(offset + limit, len(record["text"]))
        return self.envelope(record_id=identity, title=record["title"], observed_at=record["observed_at"],
                             event_date=record.get("event_date"), source=record["source"],
                             text=record["text"][offset:end], offset=offset,
                             next_offset=end if end < len(record["text"]) else None,
                             total_characters=len(record["text"]), evidence_status="source_statement_not_independently_verified")
