# Public API collection

Use `scripts/collect_public_apis.py` when a run needs broader, reproducible discovery beyond the configured MCPs. These endpoints are read-only and available without paid access; always preserve the direct URL and treat discovery indexes as leads until the underlying source is inspected.

| Source | Endpoint | Best use | Interpretation |
|---|---|---|---|
| Hacker News Algolia | `hn.algolia.com/api/v1/search_by_date` | Founder/developer problem language and new tools | Community signal, not buyer prevalence |
| GitHub Search | `api.github.com/search/issues` | Implementation gaps, requested features, recurring failure modes | Technical demand proxy, not commercial intent |
| GDELT DOC 2.0 | `api.gdeltproject.org/api/v2/doc/doc` | International news discovery outside one search index | Open the publisher before citing facts |
| Google News RSS | `news.google.com/rss/search` | Current publisher discovery and query comparison | Syndication can inflate counts |
| GOV.UK Search | `gov.uk/api/search.json` | UK policy, official studies, guidance and statistics | Prefer the underlying publication and methodology |

`GITHUB_TOKEN` is optional but increases GitHub rate limits. Never put tokens in the report or ledger. Record endpoint errors and continue across independent sources rather than silently shrinking scope.

Example:

```bash
python3 <skill-dir>/scripts/collect_public_apis.py <run>/items.jsonl --preview \
  --source all --days 90 --max-results 20 \
  --query "business automation" --query "agentic AI integration"
```

Review the preview for semantic relevance before rerunning without `--preview`. Broad generic terms can create false matches in government and code indexes; use quoted phrases, repository or domain qualifiers, sector names, and concrete workflow language. Do not add a result merely because the endpoint matched it.

For buyer-demand work, build separate query families for workflow pain, purchase intent, implementation barriers, governance, agency operations, and sector-specific processes. Do not combine their counts into a market-size claim.
