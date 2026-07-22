import importlib.util
import sys
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
        "schema_version": 1,
    }


def sample(number, mode, duration, tokens, passed, environment_valid=True):
    return {
        "agent_duration_seconds": duration,
        "agent_runs": [
            {
                "accelerator_mode": mode,
                "duration_seconds": duration,
                "environment_invalid": not environment_valid,
                "files_read": number + 2,
                "model": "model-1",
                "reasoning_effort": "medium",
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
    def test_failed_behavioral_samples_remain_in_pairs(self):
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

        self.assertEqual(([10.0, 30.0], [5.0, 15.0]), METRICS.paired_metric(left, right, "agent_duration_seconds"))
        self.assertEqual(([100.0, 300.0], [50.0, 150.0]), METRICS.paired_metric(left, right, "total_tokens"))

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

        self.assertEqual(([], []), METRICS.paired_metric(left, right, "total_tokens"))

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


if __name__ == "__main__":
    unittest.main()
