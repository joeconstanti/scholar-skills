# Evolve review — 17 November 2026

Baseline: origin https://github.com/joeconstanti/scholar-skills.git, default `main`, `ddd72f93ee38638bfcf70d06fb7060ee5a816a67`. Clean isolated T3 workspace. No open PRs/issues. Prior campaign #13–22 merged; this campaign does not repeat them. No package manifest or separate architecture document exists: README, three SKILL.md files and reference guides define the standard-library CLI architecture. Applicable global AGENTS.md read; no repository AGENTS.md or CONTEXT.md found. Baseline: 25 local tests pass and latest main Action 43934790561 succeeded. Main branch protection endpoint returns 404.

Rank uses impact, confidence, effort and risk: confirmed data-loss and false-success defects first, then collector correctness, then broader parsing and schema work. D = confirmed code defect or contract mismatch; P = proposed enhancement. Effort S/M/L; risk L/M/H. First five selected; each is independent from the baseline. All require the full unittest/skill-lint suite, diff review and green hosted Python 3.10/3.12 checks before merge. No UI or installed app exists; CLI subprocess and offline fixtures are the acceptance surfaces. No paid service or release is required.

## External sources inspected on 17 November 2026

[S1](https://docs.python.org/3/library/pathlib.html#pathlib.Path.open) Python file modes; [S2](https://docs.python.org/3/library/json.html#infinite-and-nan-number-values) JSON nonfinite values; [S3](https://docs.python.org/3/library/math.html#math.isfinite) finite-number validation; [S4](https://docs.python.org/3/library/argparse.html#type) CLI validation; [S5](https://docs.python.org/3/library/sys.html#sys.exit) exit status; [S6](https://spec.commonmark.org/current/) Markdown links and blocks; [S7](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after) HTTP retry guidance; [S8](https://api.stackexchange.com/docs/throttle) API backoff; [S9](https://docs.python.org/3/library/urllib.parse.html#url-parsing-security) URL validation.

Comparable maintained projects: [lychee](https://github.com/lycheeverse/lychee) checks links and exposes machine output; [STORM](https://github.com/stanford-oval/storm) builds cited reports; [GPT Researcher](https://github.com/assafelovic/gpt-researcher) produces research artifacts. Their public READMEs were inspected; these are purpose and architecture comparisons, not proof that they implement each proposal. Exact behavior below comes from local source inspection. No inaccessible source is used as evidence.

## Ranked backlog and acceptance criteria

| Rank | Type | Problem / affected flow and repository evidence | External basis | Benefit | Effort | Risk | Dependencies | Acceptance / validation |
|---|---|---|---|---|---|---|---|---|
| 1 | D | **Protect authored reports** — scholar.py cmd_report writes report.md unconditionally; SKILL directs repeated generation plus manual synthesis | S1; GPT Researcher | Avoid loss of authored analysis | S | M | None | First creation succeeds; second refuses without byte changes; explicit --force replaces |
| 2 | D | **Reject missing or malformed claims ledgers** — claims.py load returns [] for missing files; summary exits 0; non-object and unknown verdict rows bypass or crash gate | S2; STORM | Make verification fail closed | M | M | None | Missing read paths, malformed rows, duplicate IDs and invalid verdict evidence exit 2 without writes; valid empty file allowed |
| 3 | D | **Reject invalid engagement metrics** — scholar.py parse_metrics accepts nan/inf and empty names; score accepts negative/nonfinite hand-edited metrics | S2,S3 | Keep JSON and ranking meaningful | S | L | None | Reject invalid input before append; valid zeros and custom metrics remain; report rejects corrupt metrics |
| 4 | D | **Validate collection bounds before network access** — collector main accepts zero/negative results/days and nonfinite pause; slicing and sleep then fail or mislead | S3,S4 | Avoid wasted requests and misleading samples | S | L | None | Invalid options exit 2 with no requests/files; valid defaults and zero pause work |
| 5 | D | **Signal partial collection failure** — collector main returns 0 if errors coexist with records in preview and append | S5; STORM | Expose incomplete coverage to automation while retaining good records | S | L | None | Mixed and total failure exit 1; successful empty result exits 0; independent sources continue |
| 6 | D | **Respect Stack Exchange backoff** — collect_stackexchange discards response backoff; repeated queries follow only --pause | S8 | Comply with API throttle | M | M | Per-method scheduler | Mock consecutive queries and assert no early request |
| 7 | D | **Honour full Retry-After** — collector get supports only numeric seconds and caps them; citecheck probe ignores header | S7 | Avoid premature retries | M | M | Bounded deferred retry design | Delta/date header tests including long wait stop |
| 8 | D | **Check reference-style citations** — citecheck LINK recognises inline links and autolinks only | S6; lychee | Avoid false uncited reports and missing link probes | M | M | None | Full/collapsed/shortcut refs with case and whitespace fixtures |
| 9 | D | **Handle balanced link destinations** — citecheck LINK stops at first closing parenthesis | S6; lychee | Probe full article URLs | M | M | Shared link extractor | Nested/escaped parentheses and title fixtures |
| 10 | D | **Exclude inline code from claim checks** — citecheck check excludes fences but scans inline code examples | S6 | Reduce false alarms | M | M | Markdown extraction | Code span delimiters and real prose tests |
| 11 | D | **Exclude multiline HTML comments** — citecheck skips opening comment line only | S6 | Avoid checking hidden draft text | S | M | Markdown extraction | Multiline comments and trailing prose fixtures |
| 12 | D | **Validate evidence ledger row types** — scholar read_items accepts arrays/null and report assumes dict | S2 | Actionable file/line errors | M | M | Schema contract | Malformed imported rows fail before output |
| 13 | D | **Validate evidence timestamps at add** — scholar cmd_add stores invalid dates; score parses later | S4 | Avoid delayed report failure | S | L | None | Invalid observed/published times leave ledger unchanged |
| 14 | D | **Validate direct source URLs** — canonical_url accepts relative/non-HTTP values and strips credentials silently | S9 | Keep traceable source identity | M | M | URL contract | Schemes/ports/IPv6 fixtures and no append on failure |
| 15 | D | **Reject negative coverage counts** — cmd_log_query accepts --results -1 | S4 | Keep coverage totals meaningful | S | L | None | Zero succeeds; negative rejected without append |
| 16 | D | **Apply GOV.UK time window** — collect_govuk accepts days but never uses it | STORM | Keep collection inside stated scope | M | M | Official endpoint filter research | Old/recent dated fixtures and request assertions |
| 17 | D | **Preserve monitoring observations** — append_unique deduplicates platform+URL forever; monitoring.md requires new snapshots | GPT Researcher | Retain longitudinal engagement evidence | M | H | Explicit snapshot identity policy | Repeat run history preserved without same-run duplicates |
| 18 | P | **Per-host probe pacing** — citecheck pool can send all workers to one host | S7; lychee | Reduce server pressure | M | M | Scheduling policy | Mock host concurrency ceiling |
| 19 | P | **Record collector query coverage automatically** — collector output only reports errors/counts; queries.jsonl requires separate manual command | STORM | Audit empty and failed searches | M | M | Run path/status schema | Mock success/empty/error matrix |
| 20 | P | **Freeze report scoring time** — cmd_report score uses a new now per item and current wall clock per replay | GPT Researcher | Reproducible ranking | M | L | Versioned as-of contract | Same input/as-of produces same scores |
| 21 | P | **Group repeated evidence observations** — cmd_report emits each snapshot as independent item | STORM | Reduce repeated-source dominance | M | M | Snapshot policy #17 | Multiple snapshots retain history with one source group |
| 22 | P | **Run schema and tool version** — cmd_init records topic/scope without schema/tool revision | GPT Researcher | Explain replay drift | M | M | Migration policy | Old runs readable; new version fields tested |
| 23 | P | **Export coverage matrix** — queries ledger exists; report emits plain list only | STORM | Expose platform gaps | M | L | #19 optional | JSON counts match successful/empty/failed fixtures |
| 24 | P | **Add cross-platform CI** — workflow tests Linux Python 3.10/3.12 only | S1 | Detect filesystem portability issues | M | L | CI resource budget | macOS temporary-file and CLI checks |
| 25 | P | **Claim evidence excerpt identifiers** — claims sources contain URLs without excerpt anchors or item IDs | STORM | Improve source traceability | L | M | Backward-compatible schema | Round-trip excerpt/location and legacy ledger tests |

## Progress

Research complete. Top five accepted for implementation under the criteria above. Network adapter tests will use offline fixtures: these prove CLI and error behavior, not current availability of arbitrary research sources. Human source support remains outside the mechanical citation gate. No production deployment workflow is present.

### Implementation milestones

- #1 report protection: PR #23 merged; 26 local tests and hosted Python 3.10/3.12 checks passed; main Action 44131322356 succeeded.
- #2 claims input gate: PR #24 merged; 28 local tests and both hosted checks passed; main Action 44131612912 succeeded.
- #3 finite metrics: PR #25 merged; 30 local tests and both hosted checks passed; main Action 44131884332 succeeded.
- #4 collector options: PR #26 merged after 32 local tests and both hosted checks passed. Main workflow tracked in the campaign thread.
- #5 partial collection status: focused offline tests cover mixed failure, total failure, successful empty and nonempty outcomes in preview/append modes. Hosted full-suite checks and merge tracked in the campaign thread.

The coordinator paused new heavy local validation because of shared host load after the already-running 32-test suite. Further validation uses focused local tests and hosted full suites until a slot is available. Historical campaign #13–22 is separate from this campaign. No earlier failed run is being used to excuse a current failure.
