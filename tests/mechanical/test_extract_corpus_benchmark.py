import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).parents[2]
MODULE_PATH = PROJECT_ROOT / "tests/retrieval-corpora/benchmark.py"
MANIFEST = (
    PROJECT_ROOT
    / "tests/retrieval-corpora/corpora/backend-service-en-01/manifest.json"
)
SPEC = importlib.util.spec_from_file_location(
    "specspine_extract_corpus_benchmark", MODULE_PATH
)
assert SPEC and SPEC.loader
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


class ExtractCorpusBenchmarkTests(unittest.TestCase):
    def test_production_ranker_runs_manifest_and_reports_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            result = BENCHMARK.run_manifest(MANIFEST, Path(directory))

        self.assertEqual("backend-service-en-01", result["corpus_id"])
        self.assertEqual(13, result["summary"]["ranking_slices"])
        self.assertEqual("normalized", BENCHMARK.SEARCH.RANKING.RANKING_SYSTEM)
        self.assertEqual(1, BENCHMARK.SEARCH.GRAPH_DEPTH)
        self.assertEqual(2, BENCHMARK.SEARCH.GRAPH_LIMIT)
        self.assertEqual(2, result["summary"]["protocol_slices"])
        self.assertEqual(1.0, result["summary"]["status_accuracy"])
        self.assertEqual(1.0, result["summary"]["owner_recall_at_1"])
        self.assertIn("mean_graph_core_precision", result["summary"])
        self.assertIn("returned_hard_negative_rate", result["summary"])
        self.assertIn("micro_direct_support_recall", result["summary"])
        self.assertIn("micro_support_recall", result["summary"])
        self.assertIn(
            "graph_incremental_support_precision",
            result["summary"],
        )
        self.assertIn("mean_end_to_end_seconds", result["summary"])
        self.assertGreater(result["summary"]["mean_end_to_end_seconds"], 0.0)
        batch = next(
            scenario
            for scenario in result["scenarios"]
            if scenario["id"] == "system-wide-eight-slice-audit"
        )
        self.assertEqual(7, batch["unique_direct_documents"])
        self.assertLessEqual(
            batch["unique_graph_only_documents"],
            batch["unique_graph_documents"],
        )

    def test_graph_metrics_measure_incremental_value_without_empty_support(self):
        judged = {
            "id": "slice",
            "evaluation": "ranking",
            "expected_status": "matched",
            "judgments": [
                {"path": "owner.md", "grade": 3},
                {"path": "direct-support.md", "grade": 2},
                {"path": "graph-support.md", "grade": 2},
                {"path": "noise.md", "grade": 0, "hard_negative": True},
            ],
        }
        routed = SimpleNamespace(
            direct_matches=[
                {"path": "owner.md"},
                {"path": "direct-support.md"},
            ],
            graph_neighbors=[
                {"path": "graph-support.md"},
                {"path": "noise.md"},
            ],
            timings={"search_seconds": 0.001},
        )

        result = BENCHMARK.evaluate_slice(judged, routed)

        self.assertEqual(0.5, result["direct_support_recall"])
        self.assertEqual(1.0, result["support_recall"])
        self.assertEqual(1, result["incremental_support_count"])
        self.assertTrue(result["graph_improved"])
        self.assertEqual(1, result["graph_relevant_count"])

        no_support = {
            **judged,
            "judgments": [{"path": "owner.md", "grade": 3}],
        }
        without_support = BENCHMARK.evaluate_slice(no_support, routed)
        self.assertIsNone(without_support["direct_support_recall"])
        self.assertIsNone(without_support["support_recall"])

    def test_ndcg_rewards_owner_first(self):
        grades = {"owner.md": 3, "support.md": 2, "context.md": 1}

        ideal = BENCHMARK.ndcg_at(
            ["owner.md", "support.md", "context.md"], grades, 5
        )
        reversed_order = BENCHMARK.ndcg_at(
            ["context.md", "support.md", "owner.md"], grades, 5
        )

        self.assertEqual(1.0, ideal)
        self.assertLess(reversed_order, ideal)

    def test_aggregate_by_groups_the_single_production_policy(self):
        grouped = BENCHMARK.aggregate_by(
            [{
                "documentation_language": "en",
                "scenarios": [],
            }],
            "documentation_language",
        )

        self.assertEqual(["en"], list(grouped))
        self.assertEqual(1, grouped["en"]["corpora"])

    def test_aggregate_by_tag_reuses_scenarios_without_double_counting_slices(self):
        scenario = {
            "tags": ["multi-slice", "no-match"],
            "index_state": "warm",
            "end_to_end_seconds": 0.01,
            "output_utf8_bytes": 100,
            "unique_direct_documents": 0,
            "unique_graph_documents": 0,
            "unique_graph_only_documents": 0,
            "slices": [],
        }

        grouped = BENCHMARK.aggregate_by_tag([{"scenarios": [scenario]}])

        self.assertEqual({"multi-slice", "no-match"}, set(grouped))
        self.assertEqual(0, grouped["multi-slice"]["ranking_slices"])


if __name__ == "__main__":
    unittest.main()
