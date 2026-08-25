---
name: scholar-research
description: Research trends deeply across social platforms and search engines, preserving source evidence and producing a cited, reproducible report. Use for multi-platform trend discovery, content intelligence, audience research, or long-running topic monitoring; not for private-data collection or engagement automation.
---

# Scholar Research

Turn a research question into an auditable evidence set and an answer-first report.

## Start

Clarify the topic, audience, geography, language, time window, platforms, and desired deliverable from the request. Infer low-risk omissions and record them. Never invent access to a platform: list unavailable or excluded sources in the report.

Create a resumable run:

```bash
python3 <skill-dir>/scripts/scholar.py init --topic "<topic>" --output <workspace>/research-runs
```

Read [references/method.md](references/method.md) before collecting. Read only the platform sections needed from [references/platforms.md](references/platforms.md). For repeat or scheduled monitoring, also read [references/monitoring.md](references/monitoring.md).

## Collection posture

Prefer, in order:

1. Existing user-provided exports, URLs, files, or authenticated browser sessions.
2. Public first-party search, feeds, pages, and documented endpoints.
3. Ordinary HTTP/browser collection with conservative concurrency and caching.
4. Optional local crawlers when scale or JavaScript rendering warrants them.
5. Paid APIs or scraping services only after explaining the access gap and asking for credentials or spend authorization.

Do not bypass authentication, CAPTCHAs, paywalls, access controls, or platform safeguards. Do not collect private profiles or unnecessary personal data. Stop on explicit denial, repeated throttling, or a platform instruction prohibiting the attempted access method; record the gap and continue with other sources.

## Evidence records

Write one JSON object per observed item to `items.jsonl`. Preserve the source URL and observed facts; keep interpretation in `notes` or the final report. Use the helper where practical:

```bash
python3 <skill-dir>/scripts/scholar.py add <run>/items.jsonl \
  --platform <platform> --url <url> --title <title> \
  --published-at <ISO-8601> --observed-at <ISO-8601> \
  --metrics likes=10 comments=2 views=300 --text <summary>
```

Engagement values are platform-specific snapshots, not comparable audience counts. Store query-result pages only as discovery evidence; open the underlying source before using it to support a factual claim.

## Synthesis and stopping

Periodically generate the working report:

```bash
python3 <skill-dir>/scripts/scholar.py report <run>
```

Use trend scores to prioritize reading, never as proof of importance. Synthesize recurring themes, emerging signals, disagreements, audience language, and actionable opportunities. Distinguish observed evidence, cross-source inference, verified claims, and open uncertainty.

Stop when the requested deadline or cap is reached, every in-scope platform is covered or documented as unavailable, and the latest collection round adds no material theme or changes no conclusion. For open-ended requests, default to two collection passes and at least two independent sources for each major conclusion; extend only while new evidence materially changes the answer.

## Deliverable

Update `report.md` with an executive answer, scope and method, strongest trends, platform differences, evidence links, opportunities, caveats, and uncovered gaps. Cite the direct item or authoritative source beside each claim. State exact collection dates and do not describe a trend as current outside the observed window.
