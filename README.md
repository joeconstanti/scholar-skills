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

## Install

Copy or symlink the skill into your agent's skills directory, or install the repository with a compatible skills installer:

```bash
npx skills add . --skill=scholar-research
```

The core pipeline uses only Python 3.10+. Optional collection tools such as [Scrapling](https://github.com/D4Vinci/Scrapling), [Crawl4AI](https://github.com/unclecode/crawl4ai), and [Scrapy](https://github.com/scrapy/scrapy) can be added when ordinary HTTP or browser tools are insufficient. Respect platform terms, robots directives, access controls, privacy, and rate limits; the skill never treats bypassing safeguards as a research requirement.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 /path/to/skill-creator/scripts/quick_validate.py skills/scholar-research
```
