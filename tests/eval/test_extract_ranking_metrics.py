import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("compare_extract_rankings.py")
SPEC = importlib.util.spec_from_file_location("specspine_extract_ranking_metrics", MODULE_PATH)
assert SPEC and SPEC.loader
METRICS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = METRICS
SPEC.loader.exec_module(METRICS)


def sample(ranking, response, *, calls=1, passed=True):
    attempts = [
        {
            "ranking_system": ranking,
            "slices": [
                {"id": "owner", "status": "matched"},
                {"id": "support", "status": "no_match"},
            ],
        }
    ] * calls
    return {
        "case_id": "extract-v2-case",
        "sample_number": 1,
        "environment_valid": True,
        "passed": passed,
        "diagnostics": {"response": response},
        "token_usage": {"total_tokens": 123},
        "agent_runs": [
            {
                "ranking_system": ranking,
                "retrieval_attempts": attempts,
                "cost_ledger": {
                    "final_response_utf8_bytes": len(response.encode()),
                    "retrieval_output_utf8_bytes": 456,
                    "project_source_file_bytes": 789,
                    "tool_cycles": 3,
                },
                "files_read": 2,
            }
        ],
    }


def report(ranking, response, *, calls=1):
    return {
        "schema_version": 2,
        "agent_command": f"python3 adapter.py --model sentinel --ranking {ranking}",
        "runtime": {"python": "3.12", "platform": "test"},
        "fingerprints": {
            "runner": "runner",
            "agent_command_files": {"adapter.py": "adapter"},
        },
        "cases": {
            "extract-v2-case": {
                "fingerprint": "case",
                "handoff_judgments": {
                    "required": ["specspine/owner.md"],
                    "supporting": ["specspine/support.md"],
                    "relevant": [
                        "specspine/owner.md",
                        "specspine/support.md",
                        "specspine/optional.md",
                    ],
                    "hard_negatives": ["specspine/decoy.md"],
                },
            }
        },
        "samples": [sample(ranking, response, calls=calls)],
    }


class ExtractRankingMetricsTests(unittest.TestCase):
    def test_counts_handoff_quality_and_repeat_searches(self):
        current = report(
            "faceted-normalized",
            "Owner [doc](specspine/owner.md), support `specspine/support.md`, "
            "and wrong specspine/decoy.md.",
            calls=2,
        )

        values = METRICS.sample_metrics(current, current["samples"][0])

        self.assertEqual(1.0, values["required_recall"])
        self.assertEqual(1.0, values["core_recall"])
        self.assertEqual(2 / 3, values["relevant_precision"])
        self.assertEqual(1.0, values["extra_documents"])
        self.assertEqual(1.0, values["hard_negatives"])
        self.assertEqual(2.0, values["retrieval_calls"])
        self.assertEqual(1.0, values["repeat_searches"])
        self.assertEqual(4.0, values["query_slices"])
        self.assertEqual(2.0, values["no_match_slices"])
        self.assertEqual(3.0, values["tool_cycles"])
        self.assertEqual(2.0, values["files_read"])

    def test_readme_is_neutral_for_precision(self):
        current = report(
            "legacy",
            "specspine/README.md specspine/owner.md",
        )

        values = METRICS.sample_metrics(current, current["samples"][0])

        self.assertEqual(1.0, values["relevant_precision"])
        self.assertEqual(0.0, values["extra_documents"])

    def test_reports_may_differ_only_by_ranking_argument(self):
        legacy = report("legacy", "specspine/owner.md")
        normalized = report("faceted-normalized", "specspine/owner.md")

        arms = METRICS.validate_reports([legacy, normalized])

        self.assertEqual({"legacy", "faceted-normalized"}, set(arms))

    def test_rejects_different_case_fingerprints(self):
        legacy = report("legacy", "specspine/owner.md")
        normalized = report("faceted-normalized", "specspine/owner.md")
        normalized["cases"]["extract-v2-case"]["fingerprint"] = "different"

        with self.assertRaises(METRICS.ComparisonError):
            METRICS.validate_reports([legacy, normalized])

    def test_render_contains_requested_agent_level_metrics(self):
        legacy = report("legacy", "specspine/owner.md")
        normalized = report(
            "faceted-normalized",
            "specspine/owner.md specspine/support.md",
        )

        rendered = METRICS.render([legacy, normalized])

        self.assertIn("Owner + supporting recall", rendered)
        self.assertIn("Unnecessary documents", rendered)
        self.assertIn("Repeat searches", rendered)
        self.assertIn("Final handoff bytes", rendered)


if __name__ == "__main__":
    unittest.main()
