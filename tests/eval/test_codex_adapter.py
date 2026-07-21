import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("adapters") / "codex.py"
SPEC = importlib.util.spec_from_file_location("specspine_codex_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ADAPTER
SPEC.loader.exec_module(ADAPTER)


class CodexAdapterTests(unittest.TestCase):
    def test_traces_explicit_file_reads(self):
        candidates = ["src/users/model.js", "src/billing/private.js"]
        self.assertEqual(
            {"src/users/model.js"},
            ADAPTER.traced_files("sed -n '1,80p' src/users/model.js", candidates),
        )

    def test_treats_repo_wide_content_search_as_reading_all_candidates(self):
        candidates = ["src/users/model.js", "src/billing/private.js"]
        self.assertEqual(set(candidates), ADAPTER.traced_files("rg TODO .", candidates))

    def test_does_not_treat_file_listing_as_content_read(self):
        candidates = ["src/users/model.js", "src/billing/private.js"]
        self.assertEqual(set(), ADAPTER.traced_files("find . -type f", candidates))


if __name__ == "__main__":
    unittest.main()
