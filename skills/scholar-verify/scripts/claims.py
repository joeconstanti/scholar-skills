#!/usr/bin/env python3
"""Claims ledger for scholar-verify: add claims, record verdicts, summarise."""
from __future__ import annotations
import argparse, json, sys, os, tempfile
from datetime import datetime, timezone
from pathlib import Path

KINDS = {"number", "date", "attribution", "causal", "product", "legal", "scientific", "other"}
VERDICTS = {"supported", "partly", "unsupported", "contradicted", "outdated"}
BLOCKING = {None, "unsupported", "contradicted"}

def now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def validate_claim(claim: dict) -> None:
    if not isinstance(claim, dict): raise ValueError("expected a claim object")
    for field in ("id", "claim"):
        if not isinstance(claim.get(field), str) or not claim[field].strip():
            raise ValueError(f"{field} must be a nonempty string")
    if claim.get("kind") not in KINDS: raise ValueError("invalid claim kind")
    verdict = claim.get("verdict")
    if "verdict" in claim and verdict not in VERDICTS: raise ValueError("invalid claim verdict")
    sources = claim.get("sources", [])
    if not isinstance(sources, list) or any(not isinstance(u, str) or not u.strip() for u in sources):
        raise ValueError("sources must be a list of nonempty strings")
    if verdict == "supported" and not sources: raise ValueError("supported needs at least one source")
    note = claim.get("note", "")
    if not isinstance(note, str): raise ValueError("note must be a string")
    if verdict in {"partly", "contradicted"} and not note.strip():
        raise ValueError(f"{verdict} needs a note with the correct version")

def load(path: Path, *, allow_missing: bool = False) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        if allow_missing: return []
        raise
    claims, seen = [], set()
    for number, line in enumerate(text.split("\n"), 1):
        if not line.strip(): continue
        try:
            claim = json.loads(line)
            validate_claim(claim)
            if claim["id"] in seen: raise ValueError(f"duplicate claim id: {claim['id']}")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{path}:{number}: {exc}") from exc
        claims.append(claim); seen.add(claim["id"])
    return claims

def save(path: Path, claims: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            for claim in claims:
                stream.write(json.dumps(claim, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def cmd_add(args):
    path = Path(args.path); claims = load(path, allow_missing=True)
    if args.kind not in KINDS: raise ValueError(f"kind must be one of {sorted(KINDS)}")
    if any(c["id"] == args.id for c in claims): raise ValueError(f"claim id exists: {args.id}")
    claims.append({"id": args.id, "claim": args.claim, "kind": args.kind, "location": args.location or "", "added_at": now_iso()})
    validate_claim(claims[-1])
    save(path, claims); print(args.id); return 0

def cmd_verdict(args):
    path = Path(args.path); claims = load(path)
    if args.verdict not in VERDICTS: raise ValueError(f"verdict must be one of {sorted(VERDICTS)}")
    if args.verdict == "supported" and not args.source: raise ValueError("supported needs at least one --source")
    if args.verdict in {"partly", "contradicted"} and not args.note: raise ValueError(f"{args.verdict} needs a --note with the correct version")
    match = [c for c in claims if c["id"] == args.id]
    if not match: raise ValueError(f"unknown claim id: {args.id}")
    match[0].update({"verdict": args.verdict, "sources": args.source or [], "note": args.note or "", "checked_at": now_iso()})
    validate_claim(match[0])
    save(path, claims); print(f"{args.id}: {args.verdict}"); return 0

def cmd_list(args):
    claims = load(Path(args.path))
    for claim in claims:
        verdict = claim.get("verdict", "unchecked")
        if args.verdict and verdict != args.verdict: continue
        if args.kind and claim.get("kind") != args.kind: continue
        print(json.dumps(claim, ensure_ascii=False, sort_keys=True))
    return 0

def cmd_summary(args):
    claims = load(Path(args.path)); counts = {}
    for c in claims: counts[c.get("verdict", "unchecked")] = counts.get(c.get("verdict", "unchecked"), 0) + 1
    lines = ["# Verification", "", f"_Generated {now_iso()} · {len(claims)} claims · " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + "_", "",
             "| ID | Verdict | Claim | Location | Sources | Note |", "|---|---|---|---|---|---|"]
    esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    for c in claims:
        sources = " ".join(f"[{i}]({u})" for i, u in enumerate(c.get("sources", []), 1)) or "—"
        lines.append(f"| {c['id']} | {c.get('verdict', '**unchecked**')} | {esc(c['claim'])} | {esc(c.get('location', ''))} | {sources} | {esc(c.get('note', ''))} |")
    blocking = [c["id"] for c in claims if c.get("verdict") in BLOCKING]
    lines += ["", f"Blocking: {', '.join(blocking)}" if blocking else "No blocking claims."]
    print("\n".join(lines)); return 1 if blocking else 0

def parser():
    root = argparse.ArgumentParser(description=__doc__); sub = root.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add"); add.add_argument("path"); add.add_argument("--id", required=True); add.add_argument("--claim", required=True)
    add.add_argument("--kind", default="other"); add.add_argument("--location"); add.set_defaults(func=cmd_add)
    v = sub.add_parser("verdict"); v.add_argument("path"); v.add_argument("--id", required=True); v.add_argument("--verdict", required=True)
    v.add_argument("--source", action="append"); v.add_argument("--note"); v.set_defaults(func=cmd_verdict)
    listing = sub.add_parser("list", help="print claims as JSONL, optionally filtered")
    listing.add_argument("path")
    listing.add_argument("--verdict", choices=["unchecked", *sorted(VERDICTS)])
    listing.add_argument("--kind", choices=sorted(KINDS))
    listing.set_defaults(func=cmd_list)
    s = sub.add_parser("summary"); s.add_argument("path"); s.set_defaults(func=cmd_summary); return root

def main():
    try:
        args = parser().parse_args(); return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc: print(f"error: {exc}", file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
