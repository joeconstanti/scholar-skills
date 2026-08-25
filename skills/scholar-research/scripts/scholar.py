#!/usr/bin/env python3
"""Local, dependency-free evidence pipeline for scholar-research."""
from __future__ import annotations
import argparse, json, math, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {"fbclid", "gclid", "igshid", "ref", "source"}
METRIC_WEIGHTS = {"views": .05, "likes": 1, "reactions": 1, "comments": 2, "shares": 3, "reposts": 3}

def now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def slugify(value): return (re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:64] or "research")

def canonical_url(value):
    parts = urlsplit(value.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING_KEYS]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/") or "/", urlencode(query), ""))

def parse_metrics(values):
    result = {}
    for value in values:
        if "=" not in value: raise ValueError(f"metric must be NAME=NUMBER: {value}")
        name, raw = value.split("=", 1); number = float(raw)
        if number < 0: raise ValueError("metrics cannot be negative")
        result[name.strip().lower()] = number
    return result

def parse_time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)

def score(item, observed=None):
    observed = observed or datetime.now(timezone.utc)
    published = item.get("published_at") or item.get("observed_at")
    age = max(0, (observed - parse_time(published)).total_seconds() / 86400) if published else 0
    engagement = sum(METRIC_WEIGHTS.get(k, .25) * float(v) for k, v in item.get("metrics", {}).items())
    return round(math.log1p(engagement) / (1 + age / 7), 4)

def read_items(path):
    if not path.exists(): return []
    items = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try: items.append(json.loads(line))
            except json.JSONDecodeError as exc: raise ValueError(f"invalid JSON on {path}:{line_no}: {exc.msg}") from exc
    return items

def cmd_init(args):
    run = Path(args.output) / slugify(args.topic); run.mkdir(parents=True, exist_ok=True)
    config = run / "run.json"
    if config.exists() and not args.force: raise ValueError(f"run already exists: {run} (use --force to update metadata)")
    config.write_text(json.dumps({"topic": args.topic, "created_at": now_iso(), "status": "collecting"}, indent=2) + "\n", encoding="utf-8")
    (run / "items.jsonl").touch(exist_ok=True); print(run); return 0

def cmd_add(args):
    path = Path(args.path); path.parent.mkdir(parents=True, exist_ok=True); url = canonical_url(args.url)
    items = read_items(path); observed_at = args.observed_at or now_iso(); identity = (args.platform.lower(), url, observed_at)
    if any((i.get("platform"), i.get("url"), i.get("observed_at")) == identity for i in items):
        print("duplicate skipped", file=sys.stderr); return 0
    item = {"platform": args.platform.lower(), "url": url, "title": args.title, "observed_at": observed_at, "metrics": parse_metrics(args.metrics)}
    for name in ("author", "published_at", "query", "text", "notes"):
        if getattr(args, name): item[name] = getattr(args, name)
    with path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    print(url); return 0

def cmd_report(args):
    run = Path(args.run); config = json.loads((run / "run.json").read_text(encoding="utf-8")); items = read_items(run / "items.jsonl")
    ranked = sorted(((score(i), i) for i in items), key=lambda pair: pair[0], reverse=True)
    platforms = sorted({i.get("platform", "unknown") for i in items})
    lines = [f"# Research: {config['topic']}", "", f"_Generated {now_iso()} from {len(items)} evidence items across {len(platforms)} platforms._", "", "## Executive answer", "", "<!-- Replace with evidence-backed synthesis. -->", "", "## Scope and method", "", f"Platforms observed: {', '.join(platforms) if platforms else 'None yet'}.", "", "Trend scores are within-platform reading priorities based on recency and visible engagement; they are not comparable popularity measures.", "", "## Evidence ledger", ""]
    if not ranked: lines.append("No evidence collected yet.")
    for item_score, item in ranked:
        metrics = ", ".join(f"{k}={v:g}" for k, v in item.get("metrics", {}).items()) or "no visible metrics"
        lines += [f"### [{item.get('title') or item['url']}]({item['url']})", "", f"- Platform: {item.get('platform', 'unknown')} · score: {item_score:.4f}", f"- Published: {item.get('published_at', 'unknown')} · observed: {item.get('observed_at', 'unknown')}", f"- Metrics at observation: {metrics}"]
        if item.get("text"): lines.append(f"- Summary: {item['text']}")
        lines.append("")
    lines += ["## Findings", "", "<!-- Cluster evidence into supported trends and counter-signals. -->", "", "## Gaps and caveats", "", "<!-- Record unavailable platforms, sampling limits, and unresolved claims. -->", ""]
    output = run / "report.md"; output.write_text("\n".join(lines), encoding="utf-8"); print(output); return 0

def parser():
    root = argparse.ArgumentParser(description=__doc__); commands = root.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init"); init.add_argument("--topic", required=True); init.add_argument("--output", default="research-runs"); init.add_argument("--force", action="store_true"); init.set_defaults(func=cmd_init)
    add = commands.add_parser("add"); add.add_argument("path"); add.add_argument("--platform", required=True); add.add_argument("--url", required=True); add.add_argument("--title", required=True)
    for name in ("author", "published_at", "observed_at", "query", "text", "notes"): add.add_argument(f"--{name.replace('_', '-')}")
    add.add_argument("--metrics", nargs="*", default=[]); add.set_defaults(func=cmd_add)
    report = commands.add_parser("report"); report.add_argument("run"); report.set_defaults(func=cmd_report); return root

def main():
    try:
        args = parser().parse_args()
        return args.func(args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc: print(f"error: {exc}", file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
