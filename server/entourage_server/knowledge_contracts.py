"""Shared source-record and article contracts; service owns live memory semantics."""

from datetime import date, datetime
import re

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_records(records):
    require(isinstance(records, list), "records must be a list")
    by_id = {}
    for record in records:
        require(isinstance(record, dict), "record must be an object")
        require(type(record.get("version")) is int and record["version"] == 1, "unsupported source record version")
        identity = record.get("id")
        require(isinstance(identity, str) and SLUG.fullmatch(identity), "invalid record ID")
        require(identity not in by_id, f"duplicate record ID: {identity}")
        for field in ("kind", "title", "text", "observed_at"):
            require(nonempty(record.get(field)), f"{identity}: missing {field}")
        observed = datetime.fromisoformat(record["observed_at"])
        require(observed.utcoffset() is not None, "observed_at must include UTC offset")
        if record.get("event_date") is not None:
            date.fromisoformat(record["event_date"])
        source = record.get("source")
        require(isinstance(source, dict), "source must be an object")
        require(nonempty(source.get("uri")) and nonempty(source.get("locator")), "missing source locator")
        require(isinstance(source.get("sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", source["sha256"]), "invalid source SHA256")
        labels = record.get("labels", [])
        require(isinstance(labels, list) and all(nonempty(x) for x in labels), "invalid labels")
        require("Category Promotions" not in labels, "input must already exclude Promotions")
        by_id[identity] = record
    return by_id


def validate_plan(plan, records):
    require(isinstance(plan, dict) and type(plan.get("version")) is int and plan["version"] == 1, "unsupported plan version")
    articles = plan.get("articles")
    require(isinstance(articles, list), "articles must be a list")
    slugs = set()
    for article in articles:
        require(isinstance(article, dict), "article must be an object")
        slug = article.get("slug")
        require(isinstance(slug, str) and SLUG.fullmatch(slug), "invalid article slug")
        require(slug not in slugs, "duplicate article slug")
        slugs.add(slug)
        require(article.get("type") in ("concept", "instance"), "invalid article type")
        if "activity_period" in article:
            period = article["activity_period"]
            require(article["type"] == "instance" and isinstance(period, dict)
                    and set(period) == {"start_date", "end_date"}, "invalid activity period")
            for value in period.values():
                require(isinstance(value, str) and date.fromisoformat(value).isoformat() == value, "invalid activity date")
            require(period["start_date"] <= period["end_date"], "reversed activity period")
        if "series_slug" in article:
            require(article["type"] == "instance" and isinstance(article["series_slug"], str)
                    and SLUG.fullmatch(article["series_slug"]), "invalid series reference")
        for field in ("title", "description"):
            require(nonempty(article.get(field)) and "\n" not in article[field] and "\r" not in article[field], f"invalid {field}")
        require(isinstance(article.get("claims"), list), "claims must be a list")
        for claim in article["claims"]:
            require(isinstance(claim, dict) and claim.get("type") in ("source_statement", "inference", "suggestion"), "invalid claim type")
            require(nonempty(claim.get("text")), "missing claim text")
            require(isinstance(claim.get("evidence"), list) and claim["evidence"], "claims need evidence")
            for evidence in claim["evidence"]:
                require(isinstance(evidence, dict), "invalid evidence")
                identity = evidence.get("record_id")
                require(isinstance(identity, str) and identity in records, "unknown evidence record")
                require(nonempty(evidence.get("quote")) and evidence["quote"] in records[identity]["text"], "evidence quote not present in source text")
        for field in ("unknowns", "links"):
            require(isinstance(article.get(field), list) and all(nonempty(x) for x in article[field]), f"invalid {field}")
    for article in articles:
        require(all(link in slugs for link in article["links"]), "unknown article link")
        if "series_slug" in article:
            require(any(a["slug"] == article["series_slug"] and a["type"] == "concept" for a in articles),
                    "series reference must name a concept article")
    return articles
