---
name: scholar-citecheck
description: Check a Markdown research report's citations mechanically - numeric or factual sentences with no link, links that are not in the evidence ledger, and dead or redirected URLs. Use as a final gate before sharing a scholar-research report or any cited Markdown document; it does not judge whether a source supports a claim (use scholar-verify for that).
---

# Scholar Citecheck

A fast, mechanical gate. It finds citation defects; it does not decide truth.

## Run

```bash
python3 <skill-dir>/scripts/citecheck.py <run>/report.md \
  --ledger <run>/items.jsonl --ledger <run>/claims.jsonl --online
```

- `--ledger` (repeatable): JSONL files whose `url` or `sources` fields count as collected evidence. Omit to skip the ledger check.
- `--online`: request each unique external link once (HEAD, then GET on 405), in parallel (`--workers`, default 8), with a short timeout. Timeouts, 429 and 5xx responses are retried twice with backoff. Omit when offline or when sites block automated requests.
- `--ignore-section "Evidence ledger"` (repeatable): skip generated sections.

Exit 0 means no errors. Exit 1 lists errors and warnings with line numbers.

## Findings and fixes

| Finding | Severity | Fix |
|---|---|---|
| `uncited-number` | error | Add a direct source link in the same sentence, or label the sentence as inference |
| `not-in-ledger` | warning | Add the source to the ledger (`scholar.py add`) or confirm it is a primary source opened during verification |
| `dead-link` | error | Find the moved URL or an archived copy; never keep a dead citation |
| `redirect` | warning | Replace with the final URL if it is the same document |
| `bare-search-link` | error | Cite the underlying page, not a search or results URL |

Fix every error. Explain any warning you keep in the report's caveats. Rerun until it exits zero.
