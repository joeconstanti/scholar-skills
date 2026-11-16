#!/usr/bin/env python3
"""Mechanical citation checks for Markdown research reports."""
from __future__ import annotations
import argparse, json, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

LINK = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)|<(https?://[^>\s]+)>")
NUMBER = re.compile(r"(?<![\w#/.-])\d[\d,.]*\s*(%|percent|x\b|million|billion|k\b)|\b(19|20)\d{2}\b.*\b(rose|fell|grew|increase|decrease)", re.I)
SEARCH_HOSTS = {"google.com/search", "bing.com/search", "duckduckgo.com/", "news.google.com/rss", "x.com/search", "reddit.com/search", "youtube.com/results", "perplexity.ai/search", "chatgpt.com/"}
UA = "scholar-citecheck/1.0"

def norm(url: str) -> str:
    p = urlsplit(url); return f"{p.netloc.lower().removeprefix('www.')}{p.path.rstrip('/')}"

def ledger_urls(paths: list[str]) -> set[str]:
    urls = set()
    for path in paths:
        p = Path(path)
        if not p.exists(): continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            row = json.loads(line)
            for u in [row.get("url"), *row.get("sources", [])]:
                if u: urls.add(norm(u))
    return urls

RETRY = {429, 500, 502, 503, 504}

def probe(url: str, timeout: float, retries: int = 2, backoff: float = 1.0) -> tuple[str, str]:
    """Return (status, detail). Retry transient failures with exponential backoff."""
    result = ("blocked", "HEAD/GET refused")
    for attempt in range(retries + 1):
        result, transient = _probe_once(url, timeout)
        if not transient or attempt == retries: return result
        time.sleep(backoff * 2 ** attempt)
    return result

def _probe_once(url: str, timeout: float) -> tuple[tuple[str, str], bool]:
    for method in ("HEAD", "GET"):
        try:
            with urlopen(Request(url, method=method, headers={"User-Agent": UA}), timeout=timeout) as r:
                final = r.geturl()
                return (("redirect", final) if norm(final) != norm(url) else ("ok", final)), False
        except HTTPError as exc:
            if method == "HEAD" and exc.code in (403, 405, 501): continue
            if exc.code in (401, 403, 429): return ("blocked", str(exc.code)), exc.code == 429
            return ("dead", str(exc.code)), exc.code in RETRY
        except (URLError, TimeoutError, OSError) as exc:
            return ("dead", str(getattr(exc, "reason", exc))), True
    return ("blocked", "HEAD/GET refused"), False

def check(text: str, ledger: set[str] | None, ignore: list[str], online: bool, timeout: float, workers: int = 8) -> list[tuple[str, int, str, str]]:
    findings, cited, skipping, in_code = [], [], False, False
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("```"): in_code = not in_code; continue
        if in_code or line.lstrip().startswith(("<!--", "|---")): continue
        if line.startswith("#"):
            skipping = any(s.lower() in line.lower() for s in ignore)
            continue
        if skipping: continue
        links = [a or b for a, b in LINK.findall(line)]
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            if NUMBER.search(sentence) and not LINK.search(sentence) and "inference" not in sentence.lower():
                findings.append(("error", n, "uncited-number", sentence.strip()[:120]))
        for url in links:
            key = norm(url)
            if any(key.startswith(h) for h in SEARCH_HOSTS): findings.append(("error", n, "bare-search-link", url))
            if ledger is not None and key not in ledger: findings.append(("warning", n, "not-in-ledger", url))
            cited.append((n, url))
    if online and cited:
        unique = list(dict.fromkeys(url for _, url in cited))
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            results = dict(zip(unique, pool.map(lambda u: probe(u, timeout), unique)))
        for n, url in cited:
            status, detail = results[url]
            if status == "dead": findings.append(("error", n, "dead-link", f"{url} ({detail})"))
            elif status == "redirect": findings.append(("warning", n, "redirect", f"{url} -> {detail}"))
            elif status == "blocked": findings.append(("warning", n, "unverifiable", f"{url} ({detail})"))
        findings.sort(key=lambda f: f[1])
    return findings

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report"); ap.add_argument("--ledger", action="append", default=[])
    ap.add_argument("--ignore-section", action="append", default=[]); ap.add_argument("--online", action="store_true")
    ap.add_argument("--timeout", type=float, default=10)
    ap.add_argument("--workers", type=int, default=8, help="parallel link probes with --online")
    args = ap.parse_args()
    try: text = Path(args.report).read_text(encoding="utf-8")
    except OSError as exc: print(f"error: {exc}", file=sys.stderr); return 2
    findings = check(text, ledger_urls(args.ledger) if args.ledger else None, args.ignore_section, args.online, args.timeout, args.workers)
    for sev, n, code, detail in findings: print(f"{args.report}:{n}: {sev}: {code}: {detail}")
    errors = sum(1 for f in findings if f[0] == "error")
    print(f"{errors} errors, {len(findings) - errors} warnings", file=sys.stderr)
    return 1 if errors else 0

if __name__ == "__main__": raise SystemExit(main())
