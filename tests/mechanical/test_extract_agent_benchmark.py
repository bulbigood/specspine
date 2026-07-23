import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "eval" / "benchmark_extract_agents.py"
SPEC = importlib.util.spec_from_file_location("benchmark_extract_agents", SCRIPT)
BENCHMARK = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BENCHMARK)


class ExtractAgentBenchmarkTests(unittest.TestCase):
    def test_three_fixed_arms_use_current_extract_cases(self):
        self.assertEqual(
            ["no-extract", "fallback", "accelerated"],
            [label for label, *_ in BENCHMARK.ARMS],
        )
        command, report = BENCHMARK.report_command(
            Path("/reports"),
            "fallback",
            "fallback",
            "fallback",
            samples=2,
            jobs=3,
            model="model",
            reasoning_effort="medium",
            timestamp="stamp",
        )
        rendered = " ".join(command)
        self.assertIn("--execution-profile fallback", rendered)
        self.assertIn("--retrieval-profile fallback", rendered)
        self.assertNotIn("--ranking", rendered)
        self.assertNotIn("--graph-limit", rendered)
        self.assertEqual(Path("/reports/fallback.json"), report)
        for case in BENCHMARK.CASES:
            self.assertIn(case, command)

    def test_no_extract_arm_does_not_instrument_missing_skill(self):
        command, _ = BENCHMARK.report_command(
            Path("/reports"),
            "no-extract",
            "no-extract",
            "accelerated",
            samples=1,
            jobs=1,
            model="model",
            reasoning_effort="medium",
            timestamp="stamp",
        )
        rendered = " ".join(command)
        self.assertNotIn("--retrieval-telemetry", rendered)

    def test_comparison_contains_agent_cost_and_quality_metrics(self):
        sample = {
            "case_id": "case",
            "passed": True,
            "agent_duration_seconds": 1.0,
            "token_usage": {
                "input_tokens": 8,
                "cached_input_tokens": 3,
                "output_tokens": 2,
            },
            "agent_runs": [{
                "files_read": 2,
                "retrieval_attempt_count": 1,
                "unexpected_retry": False,
                "cost_ledger": {
                    "tool_cycles": 1,
                    "retrieval_output_utf8_bytes": 20,
                    "project_source_file_bytes": 30,
                },
            }],
        }
        reports = {
            label: {
                "cases": {
                    "case": {
                        "handoff_judgments": {
                            "required": ["specspine/owner.md"],
                            "supporting": ["specspine/support.md"],
                            "relevant": [
                                "specspine/owner.md",
                                "specspine/support.md",
                            ],
                        }
                    }
                },
                "samples": [{
                    **json.loads(json.dumps(sample)),
                    "diagnostics": {
                        "response": "specspine/owner.md specspine/support.md"
                    },
                }],
            }
            for label, *_ in BENCHMARK.ARMS
        }
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "comparison.md"
            BENCHMARK.write_comparison(target, reports)
            text = target.read_text(encoding="utf-8")
        self.assertIn("No Extract", text)
        self.assertIn("Extract fallback", text)
        self.assertIn("Accelerated Extract", text)
        self.assertIn("mean_total_tokens", text)
        self.assertIn("mean_uncached_input_tokens", text)
        self.assertIn("quality_pass_rate", text)
        self.assertIn("mean_tool_cycles", text)
        self.assertIn("mean_required_recall", text)
        self.assertIn("mean_handoff_precision", text)
        self.assertIn("unexpected_retry_rate", text)


if __name__ == "__main__":
    unittest.main()
