import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "eval" / "benchmark_map_modes.py"
SPEC = importlib.util.spec_from_file_location("benchmark_map_modes", SCRIPT)
BENCHMARK = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BENCHMARK)


class MapModeBenchmarkTests(unittest.TestCase):
    def test_arms_share_the_exact_fixture(self):
        BENCHMARK.validate_equal_fixtures()
        self.assertEqual(["map", "map-large"], [label for label, _ in BENCHMARK.ARMS])

    def test_commands_use_one_case_and_serial_execution(self):
        command, report = BENCHMARK.report_command(
            Path("/reports"), "map", "map-direct-comparison-small",
            samples=2, model="model", reasoning_effort="medium", timestamp="stamp",
        )
        rendered = " ".join(command)
        self.assertIn("--case map-direct-comparison-small", rendered)
        self.assertIn("--samples 2", rendered)
        self.assertIn("--jobs 1", rendered)
        self.assertEqual(Path("/reports/map.json"), report)

    def test_comparison_contains_quality_cost_and_parallelism(self):
        sample = {
            "passed": True,
            "agent_duration_seconds": 4.0,
            "case_duration_seconds": 4.2,
            "token_usage": {
                "input_tokens": 100,
                "cached_input_tokens": 60,
                "cache_write_input_tokens": 4,
                "output_tokens": 10,
                "reasoning_output_tokens": 3,
            },
            "agent_runs": [{
                "files_read": 6,
                "spawned_agent_count": 3,
                "cost_ledger": {"tool_cycles": 5},
            }],
        }
        reports = {
            label: {"samples": [json.loads(json.dumps(sample))]}
            for label, _ in BENCHMARK.ARMS
        }
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "comparison.md"
            BENCHMARK.write_comparison(target, reports)
            text = target.read_text(encoding="utf-8")
        for value in (
            "pass_rate", "quality_pass_rate", "mean_case_wall_time_seconds",
            "mean_agent_tree_wall_time_seconds", "mean_agent_tree_total_tokens",
            "mean_agent_tree_input_tokens", "mean_agent_tree_cached_input_tokens",
            "mean_agent_tree_cache_write_input_tokens",
            "mean_agent_tree_uncached_input_tokens",
            "mean_agent_tree_output_tokens", "mean_agent_tree_reasoning_tokens",
            "mean_files_read", "mean_tool_cycles", "mean_spawned_agents",
        ):
            self.assertIn(value, text)
        self.assertIn("orchestrator plus every nested producer", text)
        self.assertIn("per-thread token usage", text)


if __name__ == "__main__":
    unittest.main()
