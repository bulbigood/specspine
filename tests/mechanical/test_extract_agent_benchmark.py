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

GRAFANA_SCRIPT = Path(__file__).parents[1] / "eval" / "benchmark_extract_grafana.py"
GRAFANA_SPEC = importlib.util.spec_from_file_location(
    "benchmark_extract_grafana", GRAFANA_SCRIPT
)
GRAFANA_BENCHMARK = importlib.util.module_from_spec(GRAFANA_SPEC)
assert GRAFANA_SPEC.loader is not None
GRAFANA_SPEC.loader.exec_module(GRAFANA_BENCHMARK)


class ExtractAgentBenchmarkTests(unittest.TestCase):
    def test_grafana_case_uses_large_external_fixture_and_fixed_arms(self):
        fixture = Path("/fixtures/grafana")
        case = GRAFANA_BENCHMARK.grafana_case(fixture, "extract")
        self.assertEqual(str(fixture), case["initial_tree"])
        self.assertEqual("expensive", case["category"])
        self.assertIn(
            "specspine/resource-dualwrite-lifecycle.md",
            case["handoff_judgments"]["required"],
        )
        self.assertIn(
            "specspine/resource-provisioning-reconciliation.md",
            case["handoff_judgments"]["hard_negatives"],
        )
        self.assertEqual(
            ["no-extract", "accelerated"],
            [label for label, *_ in GRAFANA_BENCHMARK.ARMS],
        )

    def test_grafana_fixture_copies_only_bootstrap_and_spine(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "grafana"
            (source / "specspine").mkdir(parents=True)
            (source / "AGENTS.md").write_text("bootstrap", encoding="utf-8")
            (source / "specspine" / "README.md").write_text("index", encoding="utf-8")
            (source / "ignored.go").write_text("ignored", encoding="utf-8")
            target = GRAFANA_BENCHMARK.materialize_fixture(source, root / "fixture")
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue((target / "specspine" / "README.md").is_file())
            self.assertFalse((target / "ignored.go").exists())

    def test_grafana_no_extract_adapter_does_not_enable_retrieval_telemetry(self):
        command = GRAFANA_BENCHMARK.adapter_command(
            "accelerated",
            "model",
            "medium",
            instrument_retrieval=False,
        )
        self.assertNotIn("--retrieval-telemetry", command)

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
                "retrieval_phase_metrics": {
                    "pre_retrieval_seconds": 0.5,
                    "production_retrieval_seconds": 0.1,
                    "post_retrieval_seconds": 0.4,
                    "post_retrieval_file_reads": 0,
                    "post_retrieval_returned_file_reads": 0,
                    "post_retrieval_unreturned_file_reads": 0,
                    "post_retrieval_returned_file_paths": [
                        "specspine/owner.md"
                    ],
                    "post_retrieval_unreturned_file_paths": [
                        "specspine/extra.md"
                    ],
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
        self.assertIn("mean_production_retrieval_seconds", text)
        self.assertIn("mean_post_retrieval_file_reads", text)
        self.assertIn("mean_post_retrieval_returned_file_reads", text)
        self.assertIn("mean_post_retrieval_unreturned_file_reads", text)
        self.assertIn("`specspine/owner.md` (1)", text)
        self.assertIn("`specspine/extra.md` (1)", text)


if __name__ == "__main__":
    unittest.main()
