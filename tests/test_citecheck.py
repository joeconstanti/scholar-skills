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

if __name__ == "__main__": unittest.main()
