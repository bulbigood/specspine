import importlib.util
import datetime
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("compare_extract_metrics.py")
SPEC = importlib.util.spec_from_file_location("specspine_extract_metrics", MODULE_PATH)
assert SPEC and SPEC.loader
METRICS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = METRICS
SPEC.loader.exec_module(METRICS)


def report(mode, samples, fingerprint="fixture-1"):
    return {
        "agent_command": f"python3 adapter.py --model model-1 --accelerator-mode {mode}",
        "cases": {"extract": {"fingerprint": fingerprint}},
        "jobs": 8,
        "samples": samples,
        "samples_requested": len(samples),
        "schema_version": 2,
        "fingerprints": {
            "agent_command_files": {"adapter.py": "adapter-1"},
            "runner": "runner-1",
        },
        "runtime": {"python": "3.12", "platform": "test"},
        "run": {"run_id": f"run-{mode}", "cache_profile": ["isolated-cold"]},
    }


def sample(number, mode, duration, tokens, passed, environment_valid=True):
    retrieval_mode = "sqlite-fts5" if mode == "enabled" else "fallback"
    return {
        "agent_duration_seconds": duration,
        "agent_runs": [
            {
                "accelerator_mode": mode,
                "retrieval_mode": retrieval_mode,
                "duration_seconds": duration,
                "environment_invalid": not environment_valid,
                "files_read": number + 2,
                "model": "model-1",
                "reasoning_effort": "medium",
                "cache_profile": "isolated-cold",
                "runtime": {"codex_cli": "codex-test"},
                "event_metrics": {
                    "agent_message_count": number + 1,
                    "command_count": number + 3,
                    "command_output_chars": tokens,
                    "command_metrics": [],
                },
                "cost_ledger": {
                    "prompt_utf8_bytes": 100,
                    "declared_skill_context_utf8_bytes": 200,
                    "retrieval_output_utf8_bytes": 30 if mode == "enabled" else 10,
                    "project_source_file_bytes": tokens,
                    "command_output_utf8_bytes": tokens,
                    "final_response_utf8_bytes": 20,
                    "tool_cycles": number + 3,
                },
                "retrieval_usefulness": {
                    "returned_direct": 2 if mode == "enabled" else 0,
                    "returned_graph": 1 if mode == "enabled" else 0,
                    "read_returned_direct": 1 if mode == "enabled" else 0,
                    "read_returned_graph": 1 if mode == "enabled" else 0,
                    "read_outside_results": 0 if mode == "enabled" else 2,
                    "unread_returned_direct": 1 if mode == "enabled" else 0,
                    "unread_returned_graph": 0,
                    "read_outside_result_paths": [],
                },
                "retrieval_attempts": [
                    {
                        "attempt_number": 1,
                        "mode": retrieval_mode,
                        "exit_code": 2 if retrieval_mode == "fallback" else 0,
                        "failure_kind": None,
                        "reason_code": "cache_unusable" if retrieval_mode == "fallback" else None,
                        "candidates": [],
                    }
                ],
                "token_usage": {"total_tokens": tokens},
            }
        ],
        "case_id": "extract",
        "environment_valid": environment_valid,
        "passed": passed,
        "sample_number": number,
        "token_usage": {
            "cached_input_tokens": 10,
            "input_tokens": tokens - 10,
            "output_tokens": 10,
            "total_tokens": tokens,
        },
    }


class ExtractMetricsTests(unittest.TestCase):
    def test_bootstrap_effect_is_deterministic_for_separated_samples(self):
        first = METRICS.bootstrap_median_effect(
            [100, 100, 100], [50, 50, 50], "sentinel"
        )
        second = METRICS.bootstrap_median_effect(
            [100, 100, 100], [50, 50, 50], "sentinel"
        )

        self.assertEqual(first, second)
        self.assertEqual((-0.5, -0.5), first)

    def test_independent_metrics_include_failed_behavioral_samples(self):
        fallback = report(
            "fallback",
            [
                sample(1, "fallback", 10, 100, True),
                sample(2, "fallback", 30, 300, False),
            ],
        )
        accelerated = report(
            "enabled",
            [
                sample(1, "enabled", 5, 50, True),
                sample(2, "enabled", 15, 150, False),
            ],
        )

        left, right = METRICS.validate_comparable(fallback, accelerated)

        self.assertEqual(
            [10.0, 30.0],
            METRICS.metric_values(left.values(), "agent_duration_seconds"),
        )
        self.assertEqual(
            [50.0, 150.0], METRICS.metric_values(right.values(), "total_tokens")
        )

    def test_environment_invalid_pair_is_excluded(self):
        fallback = report(
            "fallback",
            [sample(1, "fallback", 10, 100, False, environment_valid=False)],
        )
        accelerated = report(
            "enabled",
            [sample(1, "enabled", 5, 50, True)],
        )

        left, right = METRICS.validate_comparable(fallback, accelerated)

        valid_left = METRICS.cohort(
            left, lambda item: bool(item.get("environment_valid"))
        )
        valid_right = METRICS.cohort(
            right, lambda item: bool(item.get("environment_valid"))
        )
        self.assertEqual([], METRICS.metric_values(valid_left, "total_tokens"))
        self.assertEqual(
            [50.0], METRICS.metric_values(valid_right, "total_tokens")
        )

    def test_total_tokens_are_derived_when_counter_is_absent(self):
        value = METRICS.metric_value(
            sample(1, "enabled", 5, 50, True), "total_tokens"
        )
        without_total = sample(1, "enabled", 5, 50, True)
        del without_total["token_usage"]["total_tokens"]

        self.assertEqual(value, METRICS.metric_value(without_total, "total_tokens"))

    def test_cost_metrics_are_read_from_deterministic_ledger(self):
        value = METRICS.metric_value(
            sample(1, "enabled", 5, 50, True), "retrieval_output_utf8_bytes"
        )

        self.assertEqual(30.0, value)

    def test_agent_message_events_are_read_from_event_metrics(self):
        result = sample(2, "enabled", 5, 50, True)

        self.assertEqual(3.0, METRICS.metric_value(result, "agent_message_count"))

    def test_retrieval_usefulness_aggregates_agent_runs(self):
        result = sample(1, "enabled", 5, 50, True)
        second = dict(result["agent_runs"][0])
        second["retrieval_usefulness"] = {
            "returned_direct": 1,
            "returned_graph": 0,
            "read_returned_direct": 1,
            "read_returned_graph": 0,
            "read_outside_results": 1,
            "unread_returned_direct": 0,
            "unread_returned_graph": 0,
            "read_outside_result_paths": ["specspine/extra.md"],
        }
        result["agent_runs"].append(second)

        usefulness = METRICS.aggregate_usefulness(result)

        self.assertEqual(3, usefulness["returned_direct"])
        self.assertEqual(1, usefulness["read_outside_results"])
        self.assertEqual(["specspine/extra.md"], usefulness["read_outside_result_paths"])

    def test_rejects_different_case_fingerprints(self):
        fallback = report("fallback", [sample(1, "fallback", 10, 100, True)])
        accelerated = report(
            "enabled",
            [sample(1, "enabled", 5, 50, True)],
            fingerprint="fixture-2",
        )

        with self.assertRaises(METRICS.ComparisonError):
            METRICS.validate_comparable(fallback, accelerated)

    def test_rejects_different_adapter_fingerprints(self):
        fallback = report("fallback", [sample(1, "fallback", 10, 100, True)])
        accelerated = report("enabled", [sample(1, "enabled", 5, 50, True)])
        accelerated["fingerprints"]["agent_command_files"]["adapter.py"] = "adapter-2"

        with self.assertRaises(METRICS.ComparisonError):
            METRICS.validate_comparable(fallback, accelerated)

    def test_observed_concurrency_uses_sample_intervals(self):
        samples = [
            {"started_at": "2026-07-22T10:00:00+00:00", "finished_at": "2026-07-22T10:00:03+00:00"},
            {"started_at": "2026-07-22T10:00:01+00:00", "finished_at": "2026-07-22T10:00:02+00:00"},
            {"started_at": "2026-07-22T10:00:03+00:00", "finished_at": "2026-07-22T10:00:04+00:00"},
        ]

        self.assertEqual(2, METRICS.observed_concurrency(samples))

    def test_observed_concurrency_prefers_agent_intervals(self):
        samples = [
            {
                "started_at": "2026-07-22T10:00:00+00:00",
                "finished_at": "2026-07-22T10:01:00+00:00",
                "agent_runs": [
                    {
                        "started_at": "2026-07-22T10:00:01+00:00",
                        "finished_at": "2026-07-22T10:00:02+00:00",
                    }
                ],
            },
            {
                "started_at": "2026-07-22T10:00:00+00:00",
                "finished_at": "2026-07-22T10:01:00+00:00",
                "agent_runs": [
                    {
                        "started_at": "2026-07-22T10:00:03+00:00",
                        "finished_at": "2026-07-22T10:00:04+00:00",
                    }
                ],
            },
        ]

        self.assertEqual(1, METRICS.observed_concurrency(samples))

    def test_single_expected_attempt_accepts_compact_fallback(self):
        fallback = sample(1, "fallback", 10, 100, True)
        accelerated = sample(1, "enabled", 10, 100, True)

        self.assertTrue(METRICS.single_expected_attempt(fallback, "fallback"))
        self.assertTrue(METRICS.single_expected_attempt(accelerated, "sqlite-fts5"))
        fallback["agent_runs"][0]["retrieval_attempts"][0]["reason_code"] = None
        self.assertTrue(METRICS.single_expected_attempt(fallback, "fallback"))
        fallback["agent_runs"][0]["retrieval_attempts"][0]["exit_code"] = 0
        self.assertFalse(METRICS.single_expected_attempt(fallback, "fallback"))

    def test_markdown_writer_creates_requested_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "nested" / "metrics.md"

            written = METRICS.write_markdown(target, "sentinel")

            self.assertEqual(target, written)
            self.assertEqual("sentinel\n", target.read_text(encoding="utf-8"))

    def test_markdown_writer_never_overwrites_an_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "metrics.md"
            target.write_text("old\n", encoding="utf-8")

            written = METRICS.write_markdown(target, "new")

            self.assertEqual("old\n", target.read_text(encoding="utf-8"))
            self.assertNotEqual(target, written)
            self.assertEqual("new\n", written.read_text(encoding="utf-8"))

    def test_default_report_names_are_timestamped(self):
        instant = datetime.datetime(2026, 7, 22, 10, 11, 12, 123456, tzinfo=datetime.timezone.utc)

        result = METRICS.default_output_path(instant)

        self.assertEqual(
            METRICS.DEFAULT_OUTPUT_DIRECTORY / "extract-metrics-20260722T101112.123456Z.md",
            result,
        )

    def test_report_directories_are_resolved_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)

            result = METRICS.report_directories(
                (source / "fallback.json", source / "accelerated.json")
            )

            self.assertEqual((source.resolve(),), result)

    def test_markdown_contains_source_report_directories(self):
        fallback = report("fallback", [sample(1, "fallback", 10, 100, True)])
        accelerated = report("enabled", [sample(1, "enabled", 5, 50, True)])
        sources = (Path("/sentinel/source-a"), Path("/sentinel/source-b"))

        rendered = METRICS.render_comparison(fallback, accelerated, sources)

        self.assertTrue(all(str(source) in rendered for source in sources))

    def test_markdown_reports_observed_retrieval_and_failed_checks(self):
        fallback_sample = sample(1, "fallback", 10, 100, False)
        fallback_sample["failed_checks"] = [{"type": "sentinel-check"}]
        fallback = report("fallback", [fallback_sample])
        accelerated = report("enabled", [sample(1, "enabled", 5, 50, True)])

        rendered = METRICS.render_comparison(fallback, accelerated)

        self.assertIn("sqlite-fts5", rendered)
        self.assertIn("sentinel-check", rendered)

    def test_three_way_report_compares_cold_and_prewarmed_profiles(self):
        fallback = report("fallback", [sample(1, "fallback", 10, 100, True)])
        cold = report("enabled", [sample(1, "enabled", 8, 80, True)])
        cold["samples"][0]["agent_runs"][0]["retrieval_attempts"][0]["query"] = "cold query"
        warm_sample = sample(1, "enabled", 6, 60, True)
        warm_sample["agent_runs"][0]["retrieval_attempts"][0]["query"] = "warm query"
        warm_sample["agent_runs"][0]["cache_profile"] = "prewarmed"
        warm = report("enabled", [warm_sample])
        warm["agent_command"] += " --cache-profile prewarmed"
        warm["run"]["cache_profile"] = ["prewarmed"]

        rendered = METRICS.render_three_way(fallback, cold, warm)

        self.assertIn("Cold accelerator vs fallback", rendered)
        self.assertIn("Prewarmed accelerator vs fallback", rendered)
        self.assertIn("Cold vs prewarmed accelerator", rendered)
        self.assertIn("prewarmed", rendered)
        self.assertIn("cold query", rendered)
        self.assertIn("warm query", rendered)
        self.assertIn("does not isolate cache-state effects", rendered)

    def test_report_aggregates_direct_and_graph_candidates(self):
        fallback = report("fallback", [sample(1, "fallback", 10, 100, True)])
        accelerated_sample = sample(1, "enabled", 5, 50, True)
        attempt = accelerated_sample["agent_runs"][0]["retrieval_attempts"][0]
        attempt["direct_count"] = 1
        attempt["graph_count"] = 1
        attempt["direct_matches"] = [{"path": "owner.md", "score": 10, "origins": ["fts"]}]
        attempt["graph_neighbors"] = [
            {
                "path": "worker.md",
                "score": 2,
                "transitions": [
                    {
                        "source_path": "owner.md",
                        "direction": "outgoing",
                        "depth": 1,
                    }
                ],
            }
        ]
        accelerated = report("enabled", [accelerated_sample])

        rendered = METRICS.render_comparison(fallback, accelerated)

        self.assertNotIn("D:owner.md", rendered)
        self.assertNotIn("G:worker.md", rendered)
        self.assertIn("Deterministic cost ledger", rendered)
        self.assertIn("Retrieval usefulness", rendered)


if __name__ == "__main__":
    unittest.main()
