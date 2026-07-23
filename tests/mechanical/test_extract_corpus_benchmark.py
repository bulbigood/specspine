import importlib.util
import tempfile
import unittest
from pathlib import Path


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
        self.assertEqual(6, result["summary"]["ranking_slices"])
        self.assertEqual("normalized", BENCHMARK.SEARCH.RANKING.RANKING_SYSTEM)
        self.assertEqual(1, BENCHMARK.SEARCH.GRAPH_DEPTH)
        self.assertEqual(2, BENCHMARK.SEARCH.GRAPH_LIMIT)
        self.assertEqual(1, result["summary"]["protocol_slices"])
        self.assertEqual(1.0, result["summary"]["status_accuracy"])
        self.assertEqual(1.0, result["summary"]["owner_recall_at_1"])
        self.assertIn("mean_graph_core_precision", result["summary"])
        self.assertIn("returned_hard_negative_rate", result["summary"])

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


if __name__ == "__main__":
    unittest.main()
