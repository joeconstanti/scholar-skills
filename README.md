# scholar-skills

<div align="center">

![Made by Joe](https://img.shields.io/badge/Made%20by-Joe-red?style=for-the-badge)
![Agent Skills](https://img.shields.io/badge/Agent-Skills-orange?style=for-the-badge)
![Local First](https://img.shields.io/badge/Scope-Local%20First-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)

[![Tests](https://github.com/joeconstanti/scholar-skills/actions/workflows/test.yml/badge.svg)](https://github.com/joeconstanti/scholar-skills/actions/workflows/test.yml)

---

**Three skills for deep, reproducible trend research with agents. Collect evidence, check every claim, gate every citation.**

[Skills](#skills) • [Quick Start](#quick-start) • [Agent Support](#agent-support) • [Report Bug](https://github.com/joeconstanti/scholar-skills/issues)

</div>

## Features

<div align="center">

| Feature | What it does |
|---------|--------------|
| **Auditable evidence ledger** | One JSONL record per observed item, with source URL, timestamps and engagement snapshot |
| **Recorded scope** | Decision, audience, geography, window, platforms and exclusions saved in `run.json` |
| **Coverage log** | Every search is logged, including searches with no results |
| **Honest ranking** | Scores rank items only within one platform; the report never mixes them |
| **No-cost public APIs** | Hacker News, GitHub, GDELT, Google News RSS, GOV.UK, arXiv and Stack Exchange |
| **Claim-level fact check** | Atomic claims, primary sources and a verdict for each claim |
| **Citation gate** | Finds uncited numbers, search-page citations, ledger gaps and dead links |
| **Dependency-free** | Python standard library only |

</div>

## Skills

| Skill | Outcome | Side effects |
|-------|---------|--------------|
| `scholar-research` | Multi-platform trend research into an evidence ledger and a cited `report.md` | Writes to `research-runs/<topic>/`; reads public sources only |
| `scholar-verify` | Claim-by-claim fact check with a `claims.jsonl` ledger and `verification.md` | Writes the claims ledger; edits the report only to fix claims |
| `scholar-citecheck` | Mechanical citation check before you share a report | Read-only; `--online` sends HEAD/GET requests to cited links |

Typical flow: **research → verify → citecheck**. Each skill also works alone.

Skills are agent instructions. An agent can find and use the correct skill from a
natural-language request, for example "research what buyers say about n8n agencies"
or "fact-check this report before I send it".

The skills never bypass logins, CAPTCHAs, paywalls or rate limits, and do not
collect private profiles. Unavailable platforms are reported as gaps, not hidden.

## Technologies Used

<div align="center">

![Markdown](https://img.shields.io/badge/Markdown-000000?style=flat-square&logo=markdown&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)

</div>

| Technology | Purpose |
|------------|---------|
| **Markdown + SKILL.md** | Portable, readable workflow instructions |
| **Python 3.10+ standard library** | Evidence pipeline, API collector, claims ledger and citation checker |
| **JSONL** | Append-only, resumable evidence and claims ledgers |
| **Optional MCPs** | Trends MCP and the official X MCP for the research pilot |
| **Optional crawlers** | [Scrapling](https://github.com/D4Vinci/Scrapling), [Crawl4AI](https://github.com/unclecode/crawl4ai), [Scrapy](https://github.com/scrapy/scrapy) for large public collections |

## Project Structure

```text
scholar-skills/
├── skills/
│   ├── scholar-research/
│   │   ├── SKILL.md
│   │   ├── references/          # method, platforms, apis, monitoring
│   │   └── scripts/
│   │       ├── scholar.py       # init / add / log-query / report
│   │       └── collect_public_apis.py
│   ├── scholar-verify/
│   │   ├── SKILL.md
│   │   └── scripts/claims.py    # add / verdict / summary
│   └── scholar-citecheck/
│       ├── SKILL.md
│       └── scripts/citecheck.py
├── tests/                       # Unit tests and skill lint
├── .github/workflows/test.yml   # Python 3.10 and 3.12 matrix
├── .mcp.json                    # Project-local MCP pilot
└── .env.example
```

A research run:

```text
research-runs/<topic>/
├── run.json          # Topic and scope
├── items.jsonl       # Evidence ledger
├── queries.jsonl     # Coverage log
├── claims.jsonl      # Verify ledger
├── report.md
└── verification.md
```

## Local Development

### Quick Start

Install with a compatible skills installer:

```sh
npx skills add joeconstanti/scholar-skills --skill=scholar-research
npx skills add joeconstanti/scholar-skills --skill=scholar-verify
npx skills add joeconstanti/scholar-skills --skill=scholar-citecheck
```

For local development, replace `joeconstanti/scholar-skills` with `.` and run from the repository root.

Run the pipeline directly:

```sh
S=skills/scholar-research/scripts
python3 $S/scholar.py init --topic "AI coding agents" --output runs \
  --geography UK --platforms reddit,youtube
python3 $S/collect_public_apis.py runs/ai-coding-agents/items.jsonl --preview \
  --source all --query "AI coding agents" --days 90
python3 $S/scholar.py add runs/ai-coding-agents/items.jsonl \
  --platform reddit --url https://reddit.com/r/example/comments/123/post \
  --title "Example discussion" --published-at 2026-08-25T10:00:00Z \
  --metrics likes=120 comments=42 --text "Discussion summary"
python3 $S/scholar.py log-query runs/ai-coding-agents --platform reddit \
  --query "AI coding agents" --results 12
python3 $S/scholar.py report runs/ai-coding-agents
```

`report` preserves an existing `report.md`. To replace it with a new scaffold, save any authored analysis and pass `report <run> --force`.

Review `--preview` output for relevance before you run the collector without it.

Verify and check the report:

```sh
python3 skills/scholar-verify/scripts/claims.py add runs/x/claims.jsonl --id C1 --claim "41% of firms adopt" --kind number
python3 skills/scholar-verify/scripts/claims.py verdict runs/x/claims.jsonl --id C1 --verdict supported --source https://example.org/study
python3 skills/scholar-verify/scripts/claims.py summary runs/x/claims.jsonl > runs/x/verification.md
python3 skills/scholar-citecheck/scripts/citecheck.py runs/x/report.md \
  --ledger runs/x/items.jsonl --ledger runs/x/claims.jsonl --online
```

`summary` and `citecheck.py` exit non-zero while blocking problems remain.

### Agent Support

| Agent | Discovery / invocation |
|-------|------------------------|
| **Claude Code** | `.claude/skills/<name>/SKILL.md`; natural language or `/scholar-research` |
| **Codex** | `.agents/skills/<name>/SKILL.md`; `$scholar-research` (see `agents/openai.yaml`) |
| **Other coding agents** | Read the canonical SKILL.md directly |

### Project-local MCP pilot

`.mcp.json` configures two read-only research MCPs:

- Trends MCP for normalized trend signals across public platforms.
- The official X MCP for X search and engagement evidence.

Copy `.env.example` to `.env` or export the variables before you start the client.
Do not commit credentials. `GITHUB_TOKEN` is optional and only raises GitHub rate
limits. TikTok is excluded because the available MCP needs a paid API key.

## Contributing

<div align="center">

![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen?style=for-the-badge)
[![Issues](https://img.shields.io/badge/Issues-Welcome-red?style=for-the-badge)](https://github.com/joeconstanti/scholar-skills/issues)

</div>

| Step | Action |
|------|--------|
| **Branch** | Use a descriptive branch such as `fix/gdelt-dates` |
| **Change** | Keep skills concise, evidence-first and inside platform rules |
| **Validate** | Run `python3 -m unittest discover -s tests -v`; it also lints every skill |
| **PR** | Explain the behavior change and give the actual validation |

See [CI validation notes](docs/ci.md) for focused commands, run triggers, cancellation and evidence limits.

Useful contributions: new no-key public sources, better deduplication and
stronger verification checks. Keep paid services optional.

## Acknowledgments

<div align="center">

![Evidence First](https://img.shields.io/badge/Inspired%20By-Evidence%20First%20Research-purple?style=flat-square)

</div>

- [jwynia/agent-skills fact-check](https://skillselion.com/skills/jwynia/agent-skills/fact-check) and [collaborative-deep-research fact-check](https://skillselion.com/skills/collaborative-deep-research/agent-papers-cli/fact-check): a separate fact-check pass after research.
- [liangdabiao citation-validator](https://claudeskills.info/skills/liangdabiao/claude-code-stock-deep-research-agent/citation-validator/): citation checks as their own step.
- [Made by Joe](https://github.com/madebyjoe/madebyjoe): README structure and presentation reference.

The skill instructions and scripts in this repository are original.

## License

No license file is published yet. Until one is added, all rights are reserved.

---

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/joeconstanti/scholar-skills?style=social)](https://github.com/joeconstanti/scholar-skills/stargazers)

**Made by [Joe](https://madebyjoe.co)**

[GitHub](https://github.com/joeconstanti/scholar-skills) • [Report Bug](https://github.com/joeconstanti/scholar-skills/issues)

</div>
