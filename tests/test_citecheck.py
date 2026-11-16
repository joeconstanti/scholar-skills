import importlib.util, unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "skills/scholar-citecheck/scripts/citecheck.py"
SPEC = importlib.util.spec_from_file_location("citecheck", SCRIPT); CC = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(CC)

REPORT = """# R
## Findings
Adoption rose to 41% in 2026 [survey](https://example.org/survey).
Usage grew 3x last quarter.
We think 50% is plausible (inference).
See [results](https://www.google.com/search?q=x).
## Evidence ledger
Ignored 99% line.
```
code 10% here
```
"""

class CitecheckTests(unittest.TestCase):
    def test_findings(self):
        codes = [(n, c) for _, n, c, _ in CC.check(REPORT, {"example.org/survey"}, ["Evidence ledger"], False, 1)]
        self.assertIn((4, "uncited-number"), codes)
        self.assertIn((6, "bare-search-link"), codes)
        self.assertIn((6, "not-in-ledger"), codes)
        self.assertNotIn((3, "uncited-number"), codes)
        self.assertNotIn((3, "not-in-ledger"), codes)
        self.assertFalse([n for n, _ in codes if n in (5, 8, 10)])

    def test_online_probes_each_url_once(self):
        calls, real = [], CC.probe
        CC.probe = lambda url, timeout: (calls.append(url), ("dead", "404"))[1]
        try:
            text = "A [x](https://e.org/a).\nB [y](https://e.org/a).\nC [z](https://e.org/b).\n"
            found = CC.check(text, None, [], True, 1, workers=4)
        finally: CC.probe = real
        self.assertEqual(sorted(calls), ["https://e.org/a", "https://e.org/b"])
        self.assertEqual([n for _, n, c, _ in found if c == "dead-link"], [1, 2, 3])

    def test_probe_retries_transient_failures(self):
        answers, real = [(("dead", "503"), True), (("ok", "u"), False)], CC._probe_once
        CC._probe_once = lambda url, timeout: answers.pop(0)
        try: self.assertEqual(CC.probe("https://e.org", 1, retries=2, backoff=0), ("ok", "u"))
        finally: CC._probe_once = real
        self.assertEqual(answers, [])

    def test_probe_does_not_retry_permanent_failures(self):
        calls, real = [], CC._probe_once
        CC._probe_once = lambda url, timeout: (calls.append(1), (("dead", "404"), False))[1]
        try: self.assertEqual(CC.probe("https://e.org", 1, retries=3, backoff=0), ("dead", "404"))
        finally: CC._probe_once = real
        self.assertEqual(len(calls), 1)

    def test_query_identity(self):
        self.assertNotEqual(CC.norm("https://e.org/?id=1"), CC.norm("https://e.org/?id=2"))
        self.assertEqual(CC.norm("https://e.org/?b=2&a=1#x"), CC.norm("https://e.org/?a=1&b=2"))
        found = CC.check("[x](https://e.org/?id=2)", {CC.norm("https://e.org/?id=1")}, [], False, 1)
        self.assertEqual(found[0][2], "not-in-ledger")

    def test_search_url_boundaries(self):
        self.assertTrue(CC.is_search_url("https://www.google.com/search?q=a"))
        self.assertFalse(CC.is_search_url("https://google.com/searching"))
        self.assertFalse(CC.is_search_url("https://chatgpt.com.example.org/article"))
        self.assertTrue(CC.is_search_url("https://duckduckgo.com/?q=a"))

    def test_ignored_section_includes_children(self):
        text = "## Ignore\n10%\n### Child\n20%\n## Findings\n30%"
        found = CC.check(text, None, ["Ignore"], False, 1)
        self.assertEqual([f[1] for f in found], [6])

    def test_fence_types_and_lengths(self):
        text = "  ~~~~python\n10%\n~~~\n20%\n  ~~~~\n30%\n````\n```\n40%\n````\n50%"
        self.assertEqual([f[1] for f in CC.check(text, None, [], False, 1)], [6, 11])

    def test_json_cli(self):
        import json, subprocess, sys, tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "report.md"
            path.write_text("Usage grew 30%.")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--format", "json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["findings"][0]["code"], "uncited-number")

    def test_invalid_ledger_fails_with_location(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "items.jsonl"
            with self.assertRaises(OSError): CC.ledger_urls([str(path)])
            for content in ['[]', '{"sources": "bad"}', '{bad']:
                path.write_text(content)
                with self.assertRaisesRegex(ValueError, "items.jsonl:1:"):
                    CC.ledger_urls([str(path)])

if __name__ == "__main__": unittest.main()
