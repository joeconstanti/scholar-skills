# Repository improvement review — 16 November 2026

Reviewed the three skill CLIs, tests, workflow and report scripts. Ranked by demonstrated correctness or reliability impact, implementation confidence, and fit with this dependency-light repository. The first ten comprise this delivery, including Claude's two existing PRs. Remaining items are proposals, not implemented features. Earlier PRs 1–12 are outside this request.

## Comparable projects and evidence

- [lychee](https://github.com/lycheeverse/lychee): asynchronous link checking, Markdown extraction, configurable checks and machine-readable reporting. Motivates robust citation mechanics (1–8, 11–14).
- [STORM](https://github.com/stanford-oval/storm): research and cited report generation. Motivates precise evidence identity, traceability, and coverage (3, 8, 10, 15–20).
- [GPT Researcher](https://github.com/assafelovic/gpt-researcher): research collection and reusable report artifacts. Motivates durable ledgers and reproducibility (9, 21–25).

Sources inspected online on the review date. These are architectural inspirations; the specific defects and proposed implementations below come from this repository's code, not claims that those projects implement each exact solution.

## Ranked candidates

| Rank | Improvement | Local reason and acceptance evidence |
|---|---|---|
| 1 | Deduplicate and parallelise online probes | Serial repeated requests; PR #13, stub verifies one request per unique URL and line order. |
| 2 | Retry transient probe failures | Single network failures caused false dead links; PR #14, retry and permanent-failure tests. |
| 3 | Preserve query identity | Different query resources matched the same ledger entry; regression distinguishes IDs and normalises parameter order. |
| 4 | Parse search host and route boundaries | Prefix matching falsely rejected lookalike hosts and article paths; positive and negative URL fixtures. |
| 5 | Honour ignored section hierarchy | Child headings resumed checking inside an excluded section; nested heading regression. |
| 6 | Respect Markdown fence syntax | Tilde and longer fences leaked code examples into claim checks; mixed fence regression. |
| 7 | Add JSON citation output | Automation otherwise parses human diagnostics; subprocess verifies JSON and exit code. |
| 8 | Validate citation input and limits | Missing ledgers silently skipped and malformed rows crashed; file/line diagnostics and nonpositive limit rejection. |
| 9 | Save claims atomically | Direct overwrite risks truncating existing evidence; injected replacement failure preserves old ledger and cleans temporary files. |
| 10 | List and filter claim work | No direct machine-readable outstanding-claim view; CLI filters tested together and ledger verified unchanged. |
| 11 | Reference-style Markdown citations | LINK regex only recognises inline links; add reference definition resolution with fixtures. |
| 12 | Balanced parentheses in link destinations | Regex truncates valid URLs; adopt a Markdown-aware extractor with escaped-parenthesis fixtures. |
| 13 | Host-aware request pacing | Thread pool can concentrate traffic on one host; add per-host limits and deterministic scheduling tests. |
| 14 | Honour Retry-After | Fixed backoff ignores server rate guidance; test delta-seconds and HTTP-date responses. |
| 15 | Validate evidence row schema | Scholar JSONL ingestion needs a documented schema and row-level diagnostics. |
| 16 | Consolidate repeated report observations | Repeated URLs can dominate evidence presentation; retain observation history but group source cards. |
| 17 | Domain diversity summary | Platform totals do not expose dependence on one publisher; report unique registrable source domains. |
| 18 | Contradiction ledger links | Claims can record a verdict but lack explicit conflicting-evidence fields; link both supporting and opposing sources. |
| 19 | Coverage gap export | Query logs exist; derive a machine-readable attempted/completed/empty coverage matrix. |
| 20 | Claim-to-evidence identifiers | URLs alone do not identify the observed excerpt; retain stable evidence IDs and quote locations. |
| 21 | Collector response fixtures | Expand offline adapter fixtures for malformed, empty and throttled responses. |
| 22 | Run manifest versioning | Record script version and schema version for reproducible replay and migration. |
| 23 | Configurable report scripts | refresh_report.py and qa_report.py contain a fixed historical run path; expose run/output arguments. |
| 24 | Cross-platform and current-Python CI | Current matrix covers Linux 3.10/3.12; extend to macOS and newer supported Python after compatibility checks. |
| 25 | Offline run replay | Rebuild reports from captured responses without API credentials; compare stable report content. |

## Validation and limits

Every implementation has an offline regression test and runs through the full unittest suite and GitHub Actions on Python 3.10 and 3.12. Network probes use stubs in regression tests; this does not establish availability of arbitrary public URLs. Atomic saves prevent partial replacement but do not lock concurrent writers. Citation heuristics remain a mechanical gate rather than semantic fact verification. No additional collectors or paid services were added.
