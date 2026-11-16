#!/usr/bin/env python3
"""Collect public demand signals into a scholar-research JSONL ledger.

The collectors are deliberately read-only, dependency-free, and conservative.
They use documented public endpoints and preserve the query and source URL so
the resulting records remain auditable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

USER_AGENT = "scholar-research/1.0 (+local evidence collection)"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean(value: str | None, limit: int = 800) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()[:limit]


def get(url: str, headers: dict[str, str] | None = None) -> bytes:
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json, application/xml, text/xml;q=0.9, */*;q=0.8"}
    request_headers.update(headers or {})
    with urlopen(Request(url, headers=request_headers), timeout=30) as response:
        return response.read()


def get_json(url: str, headers: dict[str, str] | None = None):
    return json.loads(get(url, headers).decode("utf-8"))


def record(platform: str, url: str, title: str, query: str, *, published_at=None,
           text=None, metrics=None, author=None, notes=None) -> dict:
    item = {
        "platform": platform,
        "url": url,
        "title": clean(title, 300),
        "observed_at": now_iso(),
        "metrics": metrics or {},
        "query": query,
    }
    optional = {
        "published_at": iso(published_at), "text": clean(text),
        "author": clean(author, 200), "notes": clean(notes),
    }
    item.update({key: value for key, value in optional.items() if value})
    return item


def collect_hn(query: str, limit: int, days: int) -> list[dict]:
    after = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    params = urlencode({"query": query, "tags": "(story,ask_hn,show_hn)",
                        "numericFilters": f"created_at_i>{after}", "hitsPerPage": min(limit, 100)})
    data = get_json(f"https://hn.algolia.com/api/v1/search_by_date?{params}")
    result = []
    for hit in data.get("hits", [])[:limit]:
        title = hit.get("title") or hit.get("story_title")
        if not title:
            continue
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        result.append(record("hacker news api", url, title, query,
                             published_at=hit.get("created_at"), author=hit.get("author"),
                             text=hit.get("story_text"),
                             metrics={"points": hit.get("points") or 0,
                                      "comments": hit.get("num_comments") or 0},
                             notes="Public HN Algolia demand/discussion signal; not representative polling."))
    return result


def collect_github(query: str, limit: int, days: int) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    search = f"{query} in:title,body created:>={since}"
    params = urlencode({"q": search, "sort": "comments", "order": "desc", "per_page": min(limit, 100)})
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    data = get_json(f"https://api.github.com/search/issues?{params}", headers)
    return [record("github search api", item["html_url"], item["title"], query,
                   published_at=item.get("created_at"), author=item.get("user", {}).get("login"),
                   text=item.get("body"), metrics={"comments": item.get("comments") or 0},
                   notes="Public issue or discussion; useful as implementation-friction evidence, not market size.")
            for item in data.get("items", [])[:limit] if item.get("html_url")]


def collect_gdelt(query: str, limit: int, days: int) -> list[dict]:
    start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y%m%d%H%M%S")
    params = urlencode({"query": query, "mode": "artlist", "format": "json",
                        "maxrecords": min(limit, 250), "startdatetime": start,
                        "sort": "hybridrel"})
    data = get_json(f"https://api.gdeltproject.org/api/v2/doc/doc?{params}")
    return [record("gdelt doc api", item["url"], item.get("title") or item["url"], query,
                   published_at=item.get("seendate"), text=item.get("socialimage"),
                   notes=f"GDELT news-discovery record from {item.get('domain', 'unknown domain')}; inspect the underlying article before factual use.")
            for item in data.get("articles", [])[:limit] if item.get("url")]


def collect_google_news(query: str, limit: int, days: int) -> list[dict]:
    rss_query = f"{query} when:{days}d"
    url = "https://news.google.com/rss/search?" + urlencode({"q": rss_query, "hl": "en-GB", "gl": "GB", "ceid": "GB:en"})
    root = ET.fromstring(get(url))
    result = []
    for item in root.findall("./channel/item")[:limit]:
        source = item.find("source")
        result.append(record("google news rss", item.findtext("link") or "", item.findtext("title") or "Untitled", query,
                             published_at=item.findtext("pubDate"), author=source.text if source is not None else None,
                             notes="Google News RSS discovery record; open the underlying publisher before factual use."))
    return [item for item in result if item["url"]]


def collect_govuk(query: str, limit: int, days: int) -> list[dict]:
    params = urlencode({"q": query, "count": min(limit, 100), "order": "-public_timestamp"})
    data = get_json(f"https://www.gov.uk/api/search.json?{params}")
    result = []
    for item in data.get("results", [])[:limit]:
        path = item.get("link")
        if not path:
            continue
        result.append(record("gov.uk search api", "https://www.gov.uk" + path, item.get("title") or path, query,
                             published_at=item.get("public_timestamp"), text=item.get("description"),
                             notes="Official GOV.UK Search API result."))
    return result


COLLECTORS = {
    "hn": collect_hn,
    "github": collect_github,
    "gdelt": collect_gdelt,
    "google-news": collect_google_news,
    "govuk": collect_govuk,
}


def append_unique(path: Path, items: list[dict]) -> tuple[int, int]:
    existing = []
    if path.exists():
        existing = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    seen = {(item.get("platform"), item.get("url")) for item in existing}
    added = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for item in items:
            identity = (item["platform"], item["url"])
            if identity in seen:
                continue
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
            seen.add(identity)
            added += 1
    return added, len(items) - added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Destination items.jsonl")
    parser.add_argument("--source", action="append", choices=[*COLLECTORS, "all"], default=[])
    parser.add_argument("--query", action="append", required=True)
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--pause", type=float, default=0.4)
    parser.add_argument("--preview", action="store_true", help="Print collected records without changing the ledger")
    args = parser.parse_args()
    sources = list(COLLECTORS) if not args.source or "all" in args.source else args.source
    collected = []
    errors = []
    for source in sources:
        for query in args.query:
            try:
                collected.extend(COLLECTORS[source](query, args.max_results, args.days))
            except Exception as exc:  # Continue across independent public surfaces.
                errors.append(f"{source} / {query}: {exc}")
            time.sleep(max(0, args.pause))
    if args.preview:
        print(json.dumps({"collected": collected, "errors": errors}, ensure_ascii=False, indent=2))
        return 1 if errors and not collected else 0
    added, skipped = append_unique(args.path, collected)
    print(json.dumps({"added": added, "duplicates": skipped, "collected": len(collected), "errors": errors}, indent=2))
    return 1 if errors and not collected else 0


if __name__ == "__main__":
    raise SystemExit(main())
