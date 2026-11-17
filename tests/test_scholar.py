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

    def test_canonical_url_handles_ports_shares_and_short_links(self):
        c = SCHOLAR.canonical_url
        self.assertEqual(c("https://example.com:443/a?si=abc"), "https://example.com/a")
        self.assertEqual(c("https://x.com/u/status/1?s=20&t=xyz"), "https://x.com/u/status/1")
        self.assertEqual(c("https://youtu.be/abc123?si=zz"), "https://youtube.com/watch?v=abc123")
        self.assertEqual(c("http://example.com:8080/a?s=keep"), "http://example.com:8080/a?s=keep")

    def test_invalid_metrics_do_not_append_or_score(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "items.jsonl"
            path.write_text("")
            for metric in ("likes=nan", "likes=inf", "likes=-1", "likes=1e999", "=3"):
                result = subprocess.run([sys.executable, str(SCRIPT), "add", str(path),
                                         "--platform", "test", "--url", "https://e.org", "--title", "T",
                                         "--metrics", metric], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, metric)
                self.assertEqual(path.read_bytes(), b"")
                self.assertNotIn("Traceback", result.stderr)
        for metrics in ({"likes": float("nan")}, {"likes": float("inf")}, {"likes": -1},
                        {"likes": "3"}, {"likes": True}, [], {"": 3}, {"likes": 10 ** 400},
                        {"shares": 1e308}):
            with self.subTest(metrics=metrics), self.assertRaises(ValueError):
                SCHOLAR.score({"metrics": metrics})
        self.assertEqual(SCHOLAR.parse_metrics(["custom=2.5", "likes=0"]), {"custom": 2.5, "likes": 0})
        self.assertEqual(SCHOLAR.score({"metrics": {"likes": 0}}), 0)

    def test_report_rejects_invalid_imported_metrics_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "run.json").write_text('{"topic": "Test"}')
            (run / "items.jsonl").write_text(json.dumps({"url": "https://e.org", "metrics": {"likes": -1}}))
            result = subprocess.run([sys.executable, str(SCRIPT), "report", str(run)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("finite and nonnegative", result.stderr)
            self.assertFalse((run / "report.md").exists())

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

    def test_report_preserves_authored_content_unless_forced(self):
        with tempfile.TemporaryDirectory() as temp:
            def cli(*args):
                return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
            self.assertEqual(cli("init", "--topic", "Draft", "--output", temp).returncode, 0)
            run = Path(temp) / "draft"
            self.assertEqual(cli("report", str(run)).returncode, 0)
            report = run / "report.md"
            report.write_text("Authored analysis with sources.\n")
            before = report.read_bytes()
            refused = cli("report", str(run))
            self.assertEqual(refused.returncode, 2)
            self.assertIn("--force", refused.stderr)
            self.assertEqual(report.read_bytes(), before)
            self.assertEqual(cli("report", str(run), "--force").returncode, 0)
            self.assertIn("# Research: Draft", report.read_text())

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

class CollectorTests(unittest.TestCase):
    def test_gdelt_compact_time_is_iso(self):
        self.assertEqual(COLLECTOR.gdelt_time("20260825T090000Z"), "2026-08-25T09:00:00+00:00".replace("+00:00", "Z"))

    def test_arxiv_parses_atom_and_filters_old(self):
        from unittest import mock
        recent = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        feed = f"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/1</id><title>New</title><published>{recent}</published><summary>S</summary><author><name>A</name></author></entry>
        <entry><id>http://arxiv.org/abs/2</id><title>Old</title><published>2001-01-01T00:00:00Z</published></entry></feed>""".encode()
        with mock.patch.object(COLLECTOR, "get", lambda url: feed):
            items = COLLECTOR.collect_arxiv("q", 10, 30)
        self.assertEqual([i["url"] for i in items], ["https://arxiv.org/abs/1"])

    def test_get_retries_on_429(self):
        from unittest import mock
        from urllib.error import HTTPError
        calls = []
        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b"ok"
        def fake(req, timeout):
            calls.append(1)
            if len(calls) == 1: raise HTTPError(req.full_url, 429, "slow", {"Retry-After": "0"}, None)
            return Resp()
        with mock.patch.object(COLLECTOR, "urlopen", fake), mock.patch.object(COLLECTOR.time, "sleep"):
            self.assertEqual(COLLECTOR.get("https://example.com"), b"ok")
        self.assertEqual(len(calls), 2)

if __name__ == "__main__": unittest.main()
