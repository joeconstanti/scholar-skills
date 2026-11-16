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

    def test_failed_replace_preserves_ledger(self):
        import importlib.util
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location("claims", SCRIPT)
        claims = importlib.util.module_from_spec(spec); spec.loader.exec_module(claims)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "claims.jsonl"
            claims.save(path, [{"id": "old"}])
            with patch.object(claims.os, "replace", side_effect=OSError("disk failure")):
                with self.assertRaises(OSError): claims.save(path, [{"id": "new"}])
            self.assertEqual(claims.load(path), [{"id": "old"}])
            self.assertEqual(list(Path(temp).iterdir()), [path])
            claims.save(path, [{"id": "new"}])
            self.assertEqual(claims.load(path), [{"id": "new"}])

if __name__ == "__main__": unittest.main()
