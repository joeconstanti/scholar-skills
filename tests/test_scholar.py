import importlib.util, json, subprocess, sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[1]; SCRIPT = ROOT / "skills/scholar-research/scripts/scholar.py"
SPEC = importlib.util.spec_from_file_location("scholar", SCRIPT); SCHOLAR = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(SCHOLAR)
COLLECTOR_SCRIPT = ROOT / "skills/scholar-research/scripts/collect_public_apis.py"
COLLECTOR_SPEC = importlib.util.spec_from_file_location("collect_public_apis", COLLECTOR_SCRIPT)
COLLECTOR = importlib.util.module_from_spec(COLLECTOR_SPEC); COLLECTOR_SPEC.loader.exec_module(COLLECTOR)

class ScholarTests(unittest.TestCase):
    def test_canonical_url_removes_tracking_and_fragment(self):
        self.assertEqual(SCHOLAR.canonical_url("HTTPS://Example.com/post/?utm_source=x&id=2#reply"), "https://example.com/post?id=2")

    def test_score_rewards_engagement_and_recency(self):
        observed = datetime(2026, 8, 25, tzinfo=timezone.utc); base = {"published_at": "2026-08-24T00:00:00Z", "metrics": {"likes": 10}}
        self.assertGreater(SCHOLAR.score({**base, "metrics": {"likes": 100}}, observed), SCHOLAR.score(base, observed))
        self.assertGreater(SCHOLAR.score(base, observed), SCHOLAR.score({**base, "published_at": "2026-07-01T00:00:00Z"}, observed))

    def test_end_to_end_and_deduplication(self):
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run([sys.executable, str(SCRIPT), "init", "--topic", "Agent Trends", "--output", temp], check=True, capture_output=True, text=True)
            run = Path(temp) / "agent-trends"
            add = [sys.executable, str(SCRIPT), "add", str(run / "items.jsonl"), "--platform", "reddit", "--url", "https://example.com/post?utm_source=test", "--title", "A post", "--published-at", "2026-08-25T00:00:00Z", "--observed-at", "2026-08-25T01:00:00Z", "--metrics", "likes=20", "comments=3"]
            subprocess.run(add, check=True, capture_output=True, text=True); duplicate = subprocess.run(add, check=True, capture_output=True, text=True)
            self.assertIn("duplicate skipped", duplicate.stderr); records = (run / "items.jsonl").read_text().splitlines(); self.assertEqual(len(records), 1)
            self.assertEqual(json.loads(records[0])["url"], "https://example.com/post")
            subprocess.run([sys.executable, str(SCRIPT), "report", str(run)], check=True, capture_output=True, text=True)
            report = (run / "report.md").read_text(); self.assertIn("[A post](https://example.com/post)", report); self.assertIn("### reddit (1 items)", report); self.assertIn("Rank within reddit: 1/1", report)

    def test_public_api_record_normalizes_text_and_time(self):
        item = COLLECTOR.record("test api", "https://example.com/a", "<b>A title</b>", "agent ops",
                                published_at="Tue, 25 Aug 2026 09:00:00 GMT", text="<p>Useful  evidence</p>")
        self.assertEqual(item["title"], "A title")
        self.assertEqual(item["text"], "Useful evidence")
        self.assertEqual(item["published_at"], "2026-08-25T09:00:00Z")

    def test_public_api_append_deduplicates_platform_and_url(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "items.jsonl"
            item = COLLECTOR.record("test api", "https://example.com/a", "A", "q")
            self.assertEqual(COLLECTOR.append_unique(path, [item, item]), (1, 1))
            self.assertEqual(len(path.read_text().splitlines()), 1)

class ScopeTests(unittest.TestCase):
    def test_init_records_scope_and_report_shows_it(self):
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run([sys.executable, str(SCRIPT), "init", "--topic", "Scope", "--output", temp, "--geography", "UK", "--platforms", "reddit, youtube"], check=True, capture_output=True)
            run = Path(temp) / "scope"; config = json.loads((run / "run.json").read_text())
            self.assertEqual(config["platforms"], ["reddit", "youtube"]); self.assertEqual(config["geography"], "UK")
            subprocess.run([sys.executable, str(SCRIPT), "report", str(run)], check=True, capture_output=True)
            self.assertIn("- Geography: UK", (run / "report.md").read_text())

class QueryLogTests(unittest.TestCase):
    def test_empty_query_is_logged_in_report(self):
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run([sys.executable, str(SCRIPT), "init", "--topic", "Q", "--output", temp], check=True, capture_output=True)
            run = Path(temp) / "q"
            subprocess.run([sys.executable, str(SCRIPT), "log-query", str(run), "--platform", "Reddit", "--query", "agent ops", "--results", "0"], check=True, capture_output=True)
            subprocess.run([sys.executable, str(SCRIPT), "report", str(run)], check=True, capture_output=True)
            self.assertIn("reddit · `agent ops` → 0 results", (run / "report.md").read_text())

if __name__ == "__main__": unittest.main()
