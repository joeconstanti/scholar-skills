"""Exit status and retained evidence for independent offline API adapters."""
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
SPEC = importlib.util.spec_from_file_location("collector_outcomes", SCRIPT)
COLLECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECTOR)


class CollectorOutcomeTests(unittest.TestCase):
    def collect(self, path, adapters, preview):
        output = io.StringIO()
        args = [str(SCRIPT), str(path), "--query", "topic", "--pause", "0"]
        if preview: args.append("--preview")
        with patch.object(sys, "argv", args), patch.object(COLLECTOR, "COLLECTORS", adapters), patch.object(COLLECTOR.time, "sleep"), contextlib.redirect_stdout(output):
            code = COLLECTOR.main()
        return code, json.loads(output.getvalue())

    def test_partial_failure_keeps_success_and_fails_in_both_modes(self):
        item = COLLECTOR.record("test", "https://example.org/evidence", "Evidence", "topic")
        for preview in (True, False):
            with self.subTest(preview=preview), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "items.jsonl"
                failed = Mock(side_effect=OSError("source unavailable"))
                succeeded = Mock(return_value=[item])
                code, output = self.collect(path, {"failed": failed, "succeeded": succeeded}, preview)
                self.assertEqual(code, 1)
                self.assertEqual(len(output["errors"]), 1)
                self.assertIn("failed / topic", output["errors"][0])
                succeeded.assert_called_once_with("topic", 20, 90)
                if preview:
                    self.assertEqual(output["collected"], [item])
                    self.assertFalse(path.exists())
                else:
                    self.assertEqual(output["added"], 1)
                    self.assertEqual(json.loads(path.read_text()), item)

    def test_total_failure_preserves_existing_evidence(self):
        for preview in (True, False):
            with self.subTest(preview=preview), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "items.jsonl"
                path.write_text('{"platform":"old","url":"https://example.org/old"}\n')
                before = path.read_bytes()
                adapters = {"first": Mock(side_effect=ValueError("bad response")),
                            "second": Mock(side_effect=OSError("offline"))}
                code, output = self.collect(path, adapters, preview)
                self.assertEqual(code, 1)
                self.assertEqual(len(output["errors"]), 2)
                for adapter in adapters.values(): adapter.assert_called_once()
                self.assertEqual(path.read_bytes(), before)

    def test_success_including_empty_results_exits_zero(self):
        item = COLLECTOR.record("test", "https://example.org/a", "A", "topic")
        for preview in (True, False):
            for items in ([], [item]):
                with self.subTest(preview=preview, items=items), tempfile.TemporaryDirectory() as temp:
                    path = Path(temp) / "items.jsonl"
                    code, output = self.collect(path, {"source": Mock(return_value=items)}, preview)
                    self.assertEqual(code, 0)
                    self.assertEqual(output["errors"], [])
                    if not preview: self.assertEqual(output["added"], len(items))


if __name__ == "__main__":
    unittest.main()
