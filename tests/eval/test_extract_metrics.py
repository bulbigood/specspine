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
                "retrieval_attempts": [
                    {
                        "attempt_number": 1,
                        "mode": retrieval_mode,
                        "exit_code": 2 if retrieval_mode == "fallback" else 0,
                        "failure_kind": None,
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


if __name__ == "__main__":
    unittest.main()
