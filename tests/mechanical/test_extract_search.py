import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).parents[2]
MODULE_PATH = PROJECT_ROOT / "skills/specspine-extract/scripts/search_spine.py"
SPEC = importlib.util.spec_from_file_location("specspine_extract_search", MODULE_PATH)
assert SPEC and SPEC.loader
SEARCH = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SEARCH
SPEC.loader.exec_module(SEARCH)


class ExtractSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            SEARCH.probe_fts5()
        except SEARCH.AcceleratorUnavailable as error:
            raise unittest.SkipTest(str(error)) from error

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.spine = self.base / "specspine"
        self.cache = self.base / "cache"
        self.spine.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def run_search(self, query, *arguments):
        environment = os.environ.copy()
        environment["SPECSPINE_CACHE_DIR"] = str(self.cache)
        result = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                str(self.spine),
                f"--query={query}",
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
        )
        return result, json.loads(result.stdout)

    def test_cli_builds_refreshes_and_removes_without_writing_inside_spine(self):
        (self.spine / "README.md").write_text(
            "# Architecture\n\n[Identity](identity.md)\n", encoding="utf-8"
        )
        identity = self.spine / "identity.md"
        identity.write_text(
            "# Identity\n\nOwns authentication tokens.\n", encoding="utf-8"
        )

        result, payload = self.run_search("authentication token")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("identity.md", payload["candidates"][0]["path"])
        self.assertEqual(2, payload["documents"])
        self.assertEqual([], list(self.spine.rglob("*.sqlite*")))
        self.assertNotEqual([], list(self.cache.rglob("*.sqlite")))

        identity.write_text(
            "# Identity\n\nOwns authenticated sessions.\n", encoding="utf-8"
        )
        result, payload = self.run_search("authenticated session")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, payload["refreshed"])
        self.assertEqual("identity.md", payload["candidates"][0]["path"])

        identity.unlink()
        result, payload = self.run_search("architecture")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, payload["refreshed"])
        self.assertEqual(1, payload["documents"])

    def test_semantic_id_search_traverses_normalized_nested_links(self):
        payments = self.spine / "domains/payments"
        resilience = self.spine / "platform/resilience"
        payments.mkdir(parents=True)
        resilience.mkdir(parents=True)
        (self.spine / "README.md").write_text(
            "# Architecture\n\n[Payments](domains/payments/processing.md)\n",
            encoding="utf-8",
        )
        (payments / "processing.md").write_text(
            "# Payment processing\n\n"
            "Preserve [CON-retry-limit](../../platform/resilience/retry-policy.md).\n",
            encoding="utf-8",
        )
        (resilience / "retry-policy.md").write_text(
            "# Retry policy\n\n## Constraints\n\n"
            "- **CON-retry-limit** — Retries use fiveattemptceiling.\n",
            encoding="utf-8",
        )

        result, payload = self.run_search(
            "CON-retry-limit", "--limit", "3", "--graph-depth", "0"
        )
        self.assertEqual(0, result.returncode, result.stderr)
        by_path = {item["path"]: item for item in payload["candidates"]}
        owner = "platform/resilience/retry-policy.md"
        consumer = "domains/payments/processing.md"
        self.assertEqual(120.0, by_path[owner]["score"])

        result, payload = self.run_search(
            "fiveattemptceiling", "--limit", "3", "--graph-depth", "0"
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn(consumer, {item["path"] for item in payload["candidates"]})

        result, payload = self.run_search(
            "fiveattemptceiling", "--limit", "3", "--graph-depth", "1"
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(consumer, {item["path"] for item in payload["candidates"]})

    def test_fts_limit_counts_unique_documents_not_matching_sections(self):
        connection = SEARCH.sqlite3.connect(":memory:")
        connection.row_factory = SEARCH.sqlite3.Row
        connection.executescript(SEARCH.SCHEMA)
        try:
            for path in ("large.md", "small.md"):
                connection.execute(
                    "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (path, path, "", "hash", 1, 1, 1),
                )
            for ordinal in range(60):
                connection.execute(
                    "INSERT INTO sections_fts(path, title, summary, heading, body) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("large.md", "large.md", "", f"Section {ordinal}", "needle"),
                )
            connection.execute(
                "INSERT INTO sections_fts(path, title, summary, heading, body) "
                "VALUES (?, ?, ?, ?, ?)",
                ("small.md", "small.md", "", "Only section", "needle"),
            )

            candidates = SEARCH.search(connection, "needle", 2, 0)
            self.assertEqual(
                ["large.md", "small.md"],
                [candidate["path"] for candidate in candidates],
            )
        finally:
            connection.close()

    def test_concurrent_cache_user_gets_fallback_instead_of_rebuild(self):
        (self.spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        with patch.dict(os.environ, {"SPECSPINE_CACHE_DIR": str(self.cache)}):
            lock = SEARCH.acquire_cache_lock(SEARCH.cache_path(self.spine.resolve()))
        try:
            result, payload = self.run_search("architecture")
        finally:
            lock.rollback()
            lock.close()

        self.assertEqual(SEARCH.FALLBACK_EXIT, result.returncode)
        self.assertEqual("fallback", payload["mode"])

    def test_corrupt_index_is_rebuilt_under_cache_lock(self):
        (self.spine / "README.md").write_text(
            "# Architecture\n\nOwns routing.\n", encoding="utf-8"
        )
        result, payload = self.run_search("routing")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, payload["documents"])

        index = next(
            path
            for path in self.cache.rglob("index-v*.sqlite")
            if ".lock." not in path.name
        )
        index.write_bytes(b"not a sqlite database")

        result, payload = self.run_search("routing")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("sqlite-fts5", payload["mode"])
        self.assertEqual(1, payload["documents"])

    def test_query_without_searchable_terms_requests_fallback(self):
        (self.spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        result, payload = self.run_search("---")
        self.assertEqual(SEARCH.FALLBACK_EXIT, result.returncode)
        self.assertEqual("fallback", payload["mode"])


if __name__ == "__main__":
    unittest.main()
