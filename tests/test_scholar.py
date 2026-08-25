import importlib.util, json, subprocess, sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[1]; SCRIPT = ROOT / "skills/scholar-research/scripts/scholar.py"
SPEC = importlib.util.spec_from_file_location("scholar", SCRIPT); SCHOLAR = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(SCHOLAR)

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
            self.assertIn("[A post](https://example.com/post)", (run / "report.md").read_text())

if __name__ == "__main__": unittest.main()
