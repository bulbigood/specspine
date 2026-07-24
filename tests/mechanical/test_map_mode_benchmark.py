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
    def test_default_model_routing_uses_terra_orchestrator_and_luna_subagents(self):
        self.assertEqual("gpt-5.6-terra", BENCHMARK.DEFAULT_ORCHESTRATOR_MODEL)
        self.assertEqual(
            "medium", BENCHMARK.DEFAULT_ORCHESTRATOR_REASONING_EFFORT
        )
        self.assertEqual("gpt-5.6-luna", BENCHMARK.DEFAULT_SUBAGENT_MODEL)
        self.assertEqual("medium", BENCHMARK.DEFAULT_SUBAGENT_REASONING_EFFORT)

    def test_arms_share_the_exact_fixture(self):
        BENCHMARK.validate_equal_fixtures()
        self.assertEqual(["map", "map-large"], [label for label, _ in BENCHMARK.ARMS])

    def test_commands_use_one_case_and_serial_execution(self):
        command, report = BENCHMARK.report_command(
            Path("/reports"), "map", "map-direct-comparison-small",
            samples=2, model="model", reasoning_effort="medium",
            subagent_model="worker-model",
            subagent_reasoning_effort="medium", timestamp="stamp",
        )
        rendered = " ".join(command)
        self.assertIn("--case map-direct-comparison-small", rendered)
        self.assertIn("--samples 2", rendered)
        self.assertIn("--jobs 1", rendered)
        self.assertIn("--model model --reasoning-effort medium", rendered)
        self.assertIn(
            "--subagent-model worker-model "
            "--subagent-reasoning-effort medium",
            rendered,
        )
        self.assertEqual(Path("/reports/map.json"), report)

    def test_both_arms_use_the_same_top_level_model(self):
        rendered = []
        for label, case_id in BENCHMARK.ARMS:
            command, _ = BENCHMARK.report_command(
                Path("/reports"),
                label,
                case_id,
                samples=1,
                model="gpt-5.6-terra",
                reasoning_effort="medium",
                subagent_model="gpt-5.6-luna",
                subagent_reasoning_effort="medium",
                timestamp="stamp",
            )
            rendered.append(" ".join(command))

        self.assertTrue(all("--model gpt-5.6-terra" in item for item in rendered))
        self.assertTrue(all("--reasoning-effort medium" in item for item in rendered))
        self.assertTrue(all("--subagent-model gpt-5.6-luna" in item for item in rendered))

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
                "model": "gpt-5.6-terra",
                "reasoning_effort": "medium",
                "subagent_model": "gpt-5.6-luna",
                "subagent_reasoning_effort": "medium",
                "cost_ledger": {"tool_cycles": 5},
                "agent_telemetry": {
                    "producers": [
                        {
                            "observed_duration_seconds": 2.5,
                            "prompt_utf8_bytes": 12000,
                        }
                    ]
                },
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
            "top_level_model", "top_level_reasoning_effort",
            "subagent_model", "subagent_reasoning_effort",
            "pass_rate", "mechanical_quality_pass_rate", "mean_case_wall_time_seconds",
            "mean_agent_tree_wall_time_seconds", "mean_agent_tree_total_tokens",
            "mean_agent_tree_input_tokens", "mean_agent_tree_cached_input_tokens",
            "mean_agent_tree_cache_write_input_tokens",
            "mean_agent_tree_uncached_input_tokens",
            "mean_agent_tree_output_tokens", "mean_agent_tree_reasoning_tokens",
            "mean_document_words", "mean_total_document_words",
            "mean_files_read", "mean_tool_cycles", "mean_spawned_agents",
            "mean_observed_producer_wall_time_seconds",
            "producer_duration_coverage_rate",
            "mean_producer_prompt_utf8_bytes",
            "documentation_quality_architectural_fidelity",
            "documentation_quality_evidence_and_epistemic_discipline",
            "documentation_quality_responsibility_and_boundary_clarity",
            "documentation_quality_coverage_of_material_concerns",
            "documentation_quality_coherence_navigation_and_relationships",
            "documentation_quality_signal_to_noise_and_usefulness",
            "documentation_quality_overall",
            "documentation_quality_preference_rate",
        ):
            self.assertIn(value, text)
        self.assertIn("orchestrator plus every nested producer", text)
        self.assertIn("per-producer token counters", text)
        self.assertIn("terminal lifecycle notification", text)
        self.assertIn("do not penalize length by itself", text)

    def test_quality_rubric_uses_holistic_scores_and_does_not_reward_brevity(self):
        prompt = BENCHMARK.quality_prompt(
            {"src/a.py": "behavior"},
            {"specspine/a.md": "long useful architecture"},
            {"specspine/a.md": "short"},
        )
        self.assertIn("ordinary engineering judgment", prompt)
        self.assertIn("Do not penalize length by itself", prompt)
        self.assertIn("Do not reward brevity by itself", prompt)
        for dimension in BENCHMARK.QUALITY_DIMENSIONS:
            self.assertIn(dimension, prompt)

    def test_quality_judgment_parser_rejects_incomplete_scores(self):
        scores = {
            dimension: 8 for dimension in BENCHMARK.QUALITY_DIMENSIONS
        }
        scores["overall"] = 9
        parsed = BENCHMARK.parse_quality_judgment(
            json.dumps(
                {
                    "A": scores,
                    "B": {**scores, "overall": 7},
                    "preferred": "A",
                    "rationale": "A is clearer and better grounded.",
                }
            )
        )
        self.assertEqual("A", parsed["preferred"])
        with self.assertRaises(ValueError):
            BENCHMARK.parse_quality_judgment(
                json.dumps(
                    {
                        "A": {"overall": 9},
                        "B": scores,
                        "preferred": "A",
                        "rationale": "Incomplete.",
                    }
                )
            )


if __name__ == "__main__":
    unittest.main()
