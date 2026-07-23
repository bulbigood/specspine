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
    def test_pilot_runs_both_rankings_against_identical_slices(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            legacy = BENCHMARK.run_manifest(MANIFEST, "legacy", cache)
            faceted = BENCHMARK.run_manifest(
                MANIFEST, "faceted-bm25", cache
            )

        self.assertEqual("backend-service-en-01", legacy["corpus_id"])
        self.assertEqual("backend-service-en-01", faceted["corpus_id"])
        self.assertEqual(6, legacy["summary"]["ranking_slices"])
        self.assertEqual(1, legacy["summary"]["protocol_slices"])
        self.assertEqual(1.0, legacy["summary"]["status_accuracy"])
        self.assertEqual(1.0, faceted["summary"]["status_accuracy"])
        self.assertEqual(
            [
                scenario["id"]
                for scenario in legacy["scenarios"]
            ],
            [
                scenario["id"]
                for scenario in faceted["scenarios"]
            ],
        )

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


if __name__ == "__main__":
    unittest.main()
