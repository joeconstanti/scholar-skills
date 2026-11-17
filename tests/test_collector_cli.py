"""Collector orchestration tests use offline adapters; no public requests."""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).parents[1] / "skills/scholar-research/scripts/collect_public_apis.py"
SPEC = importlib.util.spec_from_file_location("collector_cli", SCRIPT)
COLLECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECTOR)


class CollectorCliTests(unittest.TestCase):
    def invoke(self, path, *options):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT), str(path), "--source", "hn", "--query", "test", *options]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            try:
                code = COLLECTOR.main()
            except SystemExit as exc:
                code = exc.code
        return code, output.getvalue(), errors.getvalue()

    def test_invalid_options_stop_before_requests_and_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "items.jsonl"
            invalid = [("--max-results", "0"), ("--max-results", "-2"),
                       ("--days", "0"), ("--days", "-1"),
                       ("--pause", "nan"), ("--pause", "inf"), ("--pause", "-0.1"),
                       ("--query", " ")]
            with patch.object(COLLECTOR, "get") as get, patch.object(COLLECTOR, "append_unique") as append:
                for options in invalid:
                    with self.subTest(options=options):
                        code, output, errors = self.invoke(path, *options)
                        self.assertEqual(code, 2)
                        self.assertEqual(output, "")
                        self.assertIn("error:", errors)
                        self.assertNotIn("Traceback", errors)
                get.assert_not_called()
                append.assert_not_called()
                self.assertFalse(path.exists())

    def test_valid_defaults_and_zero_pause(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "items.jsonl"
            adapter = Mock(return_value=[])
            with patch.dict(COLLECTOR.COLLECTORS, {"hn": adapter}), patch.object(COLLECTOR.time, "sleep") as sleep:
                self.assertEqual(self.invoke(path)[0], 0)
                adapter.assert_called_with("test", 20, 90)
                sleep.assert_called_with(0.4)
                self.assertEqual(self.invoke(path, "--pause", "0", "--max-results", "1", "--days", "1")[0], 0)
                adapter.assert_called_with("test", 1, 1)
                sleep.assert_called_with(0)
            self.assertEqual(path.read_text(), "")


if __name__ == "__main__":
    unittest.main()
