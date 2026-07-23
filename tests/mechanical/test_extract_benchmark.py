import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("benchmark_extract_search.py")
SPEC = importlib.util.spec_from_file_location("specspine_extract_benchmark", MODULE_PATH)
assert SPEC and SPEC.loader
BENCHMARK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BENCHMARK
SPEC.loader.exec_module(BENCHMARK)


class ExtractBenchmarkTests(unittest.TestCase):
    def test_generated_project_uses_canonical_agent_bootstrap(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            BENCHMARK.write_agent_bootstrap(project)
            content = (project / "AGENTS.md").read_text(encoding="utf-8")

        self.assertEqual(1, content.count("<!-- specspine:begin -->"))
        self.assertEqual(1, content.count("<!-- specspine:end -->"))
        self.assertIn("specspine/README.md", content)
        self.assertNotIn("{{", content)

    def test_small_scale_reports_ranking_and_cost_metrics(self):
        result = BENCHMARK.run_scale(40, 3)

        self.assertEqual(40, result["documents"])
        self.assertEqual("cold_build", result["cold"]["index_state"])
        self.assertEqual(1.0, result["workloads"]["hybrid"]["recall_at_1"])
        self.assertEqual(1.0, result["workloads"]["ambiguous"]["recall_at_1"])
        self.assertLessEqual(
            result["workloads"]["ambiguous"]["mean_direct_results"], 3
        )
        self.assertEqual(1.0, result["workloads"]["semantic-id"]["recall_at_1"])
        self.assertGreater(result["workloads"]["hybrid"]["mean_output_utf8_bytes"], 0)

    def test_faceted_scale_uses_same_workload_contract(self):
        result = BENCHMARK.run_scale(40, 3, "faceted-bm25")

        self.assertEqual("faceted-bm25", result["ranking_system"])
        self.assertEqual(1.0, result["workloads"]["hybrid"]["recall_at_1"])
        self.assertEqual(1.0, result["workloads"]["ambiguous"]["recall_at_1"])
        self.assertEqual(1.0, result["workloads"]["semantic-id"]["recall_at_1"])
        self.assertLessEqual(
            result["workloads"]["ambiguous"]["mean_direct_results"], 1
        )


if __name__ == "__main__":
    unittest.main()
