import concurrent.futures
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
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

    def test_query_discards_terms_present_in_most_documents(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Target](target.md)\n", encoding="utf-8"
        )
        (self.spine / "target.md").write_text(
            "# Target\n\ncommonterm raretarget\n", encoding="utf-8"
        )
        for index in range(10):
            (self.spine / f"decoy-{index}.md").write_text(
                f"# Decoy {index}\n\ncommonterm\n", encoding="utf-8"
            )

        result, payload = self.run_search("commonterm raretarget", "--graph-depth", "0")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("target.md", payload["candidates"][0]["path"])
        self.assertEqual(1, len(payload["candidates"]))

    def test_query_keeps_informative_terms_when_a_phrase_matches_elsewhere(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Account](account.md)\n[Timeout](timeout.md)\n",
            encoding="utf-8",
        )
        (self.spine / "account.md").write_text(
            "# Account\n\nChange account ownership.\n", encoding="utf-8"
        )
        (self.spine / "timeout.md").write_text(
            "# Timeout\n\nTimeout policy belongs here.\n", encoding="utf-8"
        )

        result, payload = self.run_search(
            "change account investigate timeout", "--graph-depth", "0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("timeout.md", {item["path"] for item in payload["candidates"]})

    def test_cold_cache_waits_for_current_builder(self):
        (self.spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        with patch.dict(os.environ, {"SPECSPINE_CACHE_DIR": str(self.cache)}):
            lock = SEARCH.acquire_cache_lock(SEARCH.cache_path(self.spine.resolve()))
        environment = os.environ.copy()
        environment["SPECSPINE_CACHE_DIR"] = str(self.cache)
        process = subprocess.Popen(
            [
                sys.executable,
                str(MODULE_PATH),
                str(self.spine),
                "--query=architecture",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        try:
            time.sleep(0.2)
            self.assertIsNone(process.poll())
        finally:
            lock.rollback()
            lock.close()
        stdout, stderr = process.communicate(timeout=5)
        payload = json.loads(stdout)

        self.assertEqual(0, process.returncode, stderr)
        self.assertEqual("sqlite-fts5", payload["mode"])

    def test_warm_search_does_not_take_build_lock(self):
        (self.spine / "README.md").write_text(
            "# Architecture\n\nOwns routing.\n", encoding="utf-8"
        )
        result, _ = self.run_search("routing")
        self.assertEqual(0, result.returncode, result.stderr)
        with patch.dict(os.environ, {"SPECSPINE_CACHE_DIR": str(self.cache)}):
            lock = SEARCH.acquire_cache_lock(SEARCH.cache_path(self.spine.resolve()))
        try:
            result, payload = self.run_search("routing")
        finally:
            lock.rollback()
            lock.close()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("sqlite-fts5", payload["mode"])

    def test_parallel_cold_searches_share_the_built_index(self):
        (self.spine / "README.md").write_text(
            "# Architecture\n\n[Target](target.md)\n", encoding="utf-8"
        )
        (self.spine / "target.md").write_text(
            "# Target\n\nOwns parallel retrieval.\n", encoding="utf-8"
        )
        for index in range(200):
            (self.spine / f"decoy-{index}.md").write_text(
                f"# Decoy {index}\n\nUnrelated content.\n", encoding="utf-8"
            )
        workers = 6
        barrier = threading.Barrier(workers)

        def search():
            barrier.wait()
            return self.run_search("parallel retrieval", "--graph-depth", "0")

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(lambda _: search(), range(workers)))

        for result, payload in results:
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("sqlite-fts5", payload["mode"])
            self.assertEqual("target.md", payload["candidates"][0]["path"])

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

    def test_unavailable_cache_path_requests_fallback(self):
        (self.spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        self.cache.touch()

        result, payload = self.run_search("architecture")

        self.assertEqual(SEARCH.FALLBACK_EXIT, result.returncode)
        self.assertEqual("fallback", payload["mode"])


if __name__ == "__main__":
    unittest.main()
