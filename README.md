# Scholar Skills

Local-first skills for deep, reproducible trend research across social and search platforms.

## Included skill

### `scholar-research`

Researches a topic across X, LinkedIn, Facebook, Google Search, Instagram, Reddit, ChatGPT Search, Perplexity, TikTok, and YouTube. It separates discovery signals from verified claims, preserves source evidence, and produces a cited Markdown report.

The skill includes a dependency-free Python pipeline for long-running research:

```bash
python3 skills/scholar-research/scripts/scholar.py init --topic "AI coding agents" --output runs
python3 skills/scholar-research/scripts/scholar.py add runs/ai-coding-agents/items.jsonl \
  --platform reddit --url https://reddit.com/r/example/comments/123/post \
  --title "Example discussion" --author example --published-at 2026-08-25T10:00:00Z \
  --metrics likes=120 comments=42 --text "Discussion summary"
python3 skills/scholar-research/scripts/scholar.py report runs/ai-coding-agents
```

`add` normalizes records and deduplicates them by platform, canonical URL, and observation time. `report` computes transparent, within-platform trend scores and writes `report.md`. Raw records remain JSONL so runs can be resumed, audited, or fed by browser automation and optional crawlers.

For broader no-cost discovery, the skill also includes a preview-first public API collector for Hacker News Algolia, GitHub Search, GDELT DOC 2.0, Google News RSS, and GOV.UK Search:

```bash
python3 skills/scholar-research/scripts/collect_public_apis.py runs/example/items.jsonl --preview \
  --source all --query "agentic AI integration" --days 90
```

Review semantic relevance before rerunning without `--preview`. `GITHUB_TOKEN` is optional and only raises GitHub API rate limits.

## Install

Install the skill directly from GitHub with a compatible skills installer:

```bash
npx skills add joeconstanti/scholar-skills --skill=scholar-research
```

For local development, replace `joeconstanti/scholar-skills` with `.` and run the command from the repository root.

The core pipeline uses only Python 3.10+. Optional collection tools such as [Scrapling](https://github.com/D4Vinci/Scrapling), [Crawl4AI](https://github.com/unclecode/crawl4ai), and [Scrapy](https://github.com/scrapy/scrapy) can be added when ordinary HTTP or browser tools are insufficient. Respect platform terms, robots directives, access controls, privacy, and rate limits; the skill never treats bypassing safeguards as a research requirement.

## Project-local MCP pilot

This repository includes a project-scoped `.mcp.json` for the read-only research pilot:

- Trends MCP for normalized trend signals across multiple public platforms.
- The official X MCP for X search and engagement evidence.

Copy `.env.example` to a local environment file or export the relevant variables before starting the MCP-capable client. Do not commit credentials. No global MCP configuration is modified by this project. TikTok is intentionally excluded because the available MCP required a paid TikNeuron API key.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 /path/to/skill-creator/scripts/quick_validate.py skills/scholar-research
```
