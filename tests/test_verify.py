import subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "skills/scholar-verify/scripts/claims.py"
def run(*args): return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

class ClaimsTests(unittest.TestCase):
    def test_flow_blocks_until_all_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / "claims.jsonl")
            self.assertEqual(run("add", path, "--id", "C1", "--claim", "41% adopt", "--kind", "number").returncode, 0)
            self.assertEqual(run("add", path, "--id", "C1", "--claim", "dup").returncode, 2)
            self.assertEqual(run("summary", path).returncode, 1)
            self.assertEqual(run("verdict", path, "--id", "C1", "--verdict", "supported").returncode, 2)
            self.assertEqual(run("verdict", path, "--id", "C1", "--verdict", "partly").returncode, 2)
            self.assertEqual(run("verdict", path, "--id", "C1", "--verdict", "supported", "--source", "https://e.org/s").returncode, 0)
            out = run("summary", path); self.assertEqual(out.returncode, 0); self.assertIn("[1](https://e.org/s)", out.stdout)

    def test_cli_round_trips_unicode_separators_in_claims(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / "claims.jsonl")
            claim = "one\u0085two\u2028three\u2029four"
            self.assertEqual(run("add", path, "--id", "C1", "--claim", claim).returncode, 0)
            listed = run("list", path)
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(json.loads(listed.stdout)["claim"], claim)

    def test_failed_replace_preserves_ledger(self):
        import importlib.util
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location("claims", SCRIPT)
        claims = importlib.util.module_from_spec(spec); spec.loader.exec_module(claims)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "claims.jsonl"
            claims.save(path, [{"id": "old", "claim": "old claim", "kind": "other"}])
            with patch.object(claims.os, "replace", side_effect=OSError("disk failure")):
                with self.assertRaises(OSError): claims.save(path, [{"id": "new", "claim": "new claim", "kind": "other"}])
            self.assertEqual(claims.load(path), [{"id": "old", "claim": "old claim", "kind": "other"}])
            self.assertEqual(list(Path(temp).iterdir()), [path])
            claims.save(path, [{"id": "new", "claim": "new claim", "kind": "other"}])
            self.assertEqual(claims.load(path), [{"id": "new", "claim": "new claim", "kind": "other"}])

    def test_missing_and_invalid_ledgers_fail_closed(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "claims.jsonl"
            for command in ("summary", "list"):
                result = run(command, str(path))
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("No blocking claims", result.stdout)
            self.assertFalse(path.exists())
            valid = {"id": "C1", "claim": "claim", "kind": "other"}
            invalid = [None, [], {"id": "C1"}, {**valid, "verdict": "typo"},
                       {**valid, "verdict": None}, {**valid, "verdict": "supported"},
                       {**valid, "sources": "url"}, {**valid, "sources": [2]},
                       {**valid, "verdict": "partly", "note": " "},
                       {**valid, "kind": []}]
            for row in invalid:
                path.write_text("\n" + json.dumps(row) + "\n")
                before = path.read_bytes()
                for args in [("summary",), ("list",), ("add", "--id", "C2", "--claim", "new")]:
                    result = run(args[0], str(path), *args[1:])
                    self.assertEqual(result.returncode, 2, row)
                    self.assertIn("claims.jsonl:2:", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual(path.read_bytes(), before)
            path.write_text(json.dumps(valid) + "\n" + json.dumps(valid) + "\n")
            self.assertIn("duplicate claim id", run("summary", str(path)).stderr)
            path.write_text("")
            self.assertEqual(run("summary", str(path)).returncode, 0)

    def test_blank_claim_and_verdict_evidence_are_not_saved(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "claims.jsonl"
            self.assertEqual(run("add", str(path), "--id", " ", "--claim", "text").returncode, 2)
            self.assertFalse(path.exists())
            self.assertEqual(run("add", str(path), "--id", "C1", "--claim", "text").returncode, 0)
            before = path.read_bytes()
            result = run("verdict", str(path), "--id", "C1", "--verdict", "supported", "--source", " ")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(path.read_bytes(), before)

    def test_list_filters_claims_without_mutating(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "claims.jsonl"
            run("add", str(path), "--id", "C1", "--claim", "one", "--kind", "number")
            run("add", str(path), "--id", "C2", "--claim", "two", "--kind", "date")
            run("verdict", str(path), "--id", "C2", "--verdict", "supported", "--source", "https://e.org")
            before = path.read_bytes()
            result = run("list", str(path), "--verdict", "unchecked", "--kind", "number")
            self.assertEqual(result.returncode, 0)
            self.assertEqual([json.loads(line)["id"] for line in result.stdout.splitlines()], ["C1"])
            self.assertEqual(run("list", str(path), "--kind", "legal").stdout, "")
            self.assertEqual(path.read_bytes(), before)

if __name__ == "__main__": unittest.main()
