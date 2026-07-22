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
from types import SimpleNamespace
from unittest.mock import Mock, patch


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
        self.assertEqual("identity.md", payload["direct_matches"][0]["path"])
        self.assertEqual(2, payload["documents"])
        self.assertEqual("cold_build", payload["index_state"])
        self.assertEqual(2, payload["schema_version"])
        self.assertIn("fts", payload["direct_matches"][0]["origins"])
        self.assertGreaterEqual(payload["timings"]["total_seconds"], 0)
        self.assertTrue(payload["runtime"]["fts5"])
        self.assertEqual([], list(self.spine.rglob("*.sqlite*")))
        self.assertNotEqual([], list(self.cache.rglob("*.sqlite")))

        identity.write_text(
            "# Identity\n\nOwns authenticated sessions.\n", encoding="utf-8"
        )
        result, payload = self.run_search("authenticated session")
        self.assertEqual("incremental_refresh", payload["index_state"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, payload["refreshed"])
        self.assertEqual("identity.md", payload["direct_matches"][0]["path"])

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
        by_path = {item["path"]: item for item in payload["direct_matches"]}
        owner = "platform/resilience/retry-policy.md"
        consumer = "domains/payments/processing.md"
        self.assertEqual(owner, payload["direct_matches"][0]["path"])
        self.assertIn("semantic_id", by_path[owner]["origins"])

        result, payload = self.run_search(
            "fiveattemptceiling", "--limit", "3", "--graph-depth", "0"
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn(consumer, {item["path"] for item in payload["direct_matches"]})

        result, payload = self.run_search(
            "fiveattemptceiling", "--limit", "3", "--graph-depth", "1"
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(consumer, {item["path"] for item in payload["graph_neighbors"]})

    def test_graph_corroboration_outranks_single_term_matches(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n[Boundary](boundary.md)\n",
            encoding="utf-8",
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns alphacontract betapolicy gammalimit. "
            "Uses [Boundary](boundary.md).\n",
            encoding="utf-8",
        )
        (self.spine / "boundary.md").write_text(
            "# Boundary\n\nProvides alphacontract execution for [Owner](owner.md).\n",
            encoding="utf-8",
        )
        for index, token in enumerate(("betapolicy", "gammalimit", "noisecontext")):
            (self.spine / f"decoy-{index}.md").write_text(
                f"# Decoy {index}\n\nUnrelated {token} material.\n",
                encoding="utf-8",
            )

        result, payload = self.run_search(
            "alphacontract betapolicy gammalimit noisecontext"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            ["owner.md", "boundary.md"],
            [candidate["path"] for candidate in payload["direct_matches"][:2]],
        )
        boundary = payload["direct_matches"][1]
        self.assertEqual(
            {"fts", "graph_outgoing", "graph_incoming"},
            set(boundary["origins"]),
        )

    def test_candidate_payload_omits_cached_document_content(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Target](target.md)\n", encoding="utf-8"
        )
        (self.spine / "target.md").write_text(
            "# Target\n\nOwns payloadsentinel routing.\n", encoding="utf-8"
        )

        result, payload = self.run_search("payloadsentinel")

        self.assertEqual(0, result.returncode, result.stderr)
        candidate = payload["direct_matches"][0]
        self.assertNotIn("summary", candidate)
        self.assertNotIn("reasons", candidate)

    def test_direct_matches_and_graph_neighbors_have_independent_contracts(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns directsentinel. Uses [Worker](worker.md).\n",
            encoding="utf-8",
        )
        (self.spine / "worker.md").write_text(
            "# Worker\n\nProvides execution mechanics.\n", encoding="utf-8"
        )

        result, payload = self.run_search(
            "directsentinel", "--limit", "1", "--graph-limit", "1"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["owner.md"], [item["path"] for item in payload["direct_matches"]])
        self.assertEqual(["worker.md"], [item["path"] for item in payload["graph_neighbors"]])
        neighbor = payload["graph_neighbors"][0]
        self.assertEqual("owner.md", neighbor["source_path"])
        self.assertEqual("outgoing", neighbor["direction"])
        self.assertEqual(1, neighbor["depth"])

    def test_inline_code_identifiers_are_searchable_without_creating_links(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nUses `RetryEnvelopeV2` and `[not-a-link](missing.md)`.\n",
            encoding="utf-8",
        )

        result, payload = self.run_search("RetryEnvelopeV2")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("owner.md", payload["direct_matches"][0]["path"])
        self.assertNotIn(
            "missing.md", {item["path"] for item in payload["graph_neighbors"]}
        )

    def test_stable_read_retries_a_file_changed_during_read(self):
        first = SimpleNamespace(st_size=3, st_mtime_ns=1, st_ctime_ns=1)
        second = SimpleNamespace(st_size=4, st_mtime_ns=2, st_ctime_ns=2)
        source = Mock()
        source.read_bytes.side_effect = [b"old", b"new!"]
        source.stat.side_effect = [second, second]

        raw, observed = SEARCH.stable_read(source, first)

        self.assertEqual(b"new!", raw)
        self.assertIs(second, observed)

    def test_stable_read_falls_back_when_source_keeps_changing(self):
        first = SimpleNamespace(st_size=1, st_mtime_ns=1, st_ctime_ns=1)
        second = SimpleNamespace(st_size=2, st_mtime_ns=2, st_ctime_ns=2)
        third = SimpleNamespace(st_size=3, st_mtime_ns=3, st_ctime_ns=3)
        source = Mock()
        source.read_bytes.side_effect = [b"a", b"bb"]
        source.stat.side_effect = [second, third]

        with self.assertRaises(SEARCH.AcceleratorUnavailable) as raised:
            SEARCH.stable_read(source, first)

        self.assertEqual("source_changed_during_index", raised.exception.reason_code)

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

            direct, graph = SEARCH.search(connection, "needle", 2, 0, 2)
            self.assertEqual(
                ["large.md", "small.md"],
                [candidate["path"] for candidate in direct],
            )
            self.assertEqual([], graph)
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
        self.assertEqual("target.md", payload["direct_matches"][0]["path"])
        self.assertEqual(1, len(payload["direct_matches"]))

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
        self.assertIn("timeout.md", {item["path"] for item in payload["direct_matches"]})

    def test_cold_cache_waits_for_current_builder(self):
        (self.spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        with patch.dict(os.environ, {"SPECSPINE_CACHE_DIR": str(self.cache)}):
            lock, _ = SEARCH.acquire_cache_lock(SEARCH.cache_path(self.spine.resolve()))
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
            lock, _ = SEARCH.acquire_cache_lock(SEARCH.cache_path(self.spine.resolve()))
        try:
            result, payload = self.run_search("routing")
        finally:
            lock.rollback()
            lock.close()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("sqlite-fts5", payload["mode"])
        self.assertEqual("warm", payload["index_state"])

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
        workers = 8
        barrier = threading.Barrier(workers)

        def search():
            barrier.wait()
            return self.run_search("parallel retrieval", "--graph-depth", "0")

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(lambda _: search(), range(workers)))

        for result, payload in results:
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("sqlite-fts5", payload["mode"])
            self.assertEqual("target.md", payload["direct_matches"][0]["path"])
        states = {payload["index_state"] for _, payload in results}
        self.assertIn("cold_build", states)
        self.assertLessEqual(states, {"cold_build", "waited_for_builder", "warm"})

    def test_parallel_warm_searches_do_not_fallback(self):
        (self.spine / "README.md").write_text(
            "# Architecture\n\nOwns warm parallel retrieval.\n", encoding="utf-8"
        )
        result, _ = self.run_search("parallel retrieval")
        self.assertEqual(0, result.returncode, result.stderr)
        workers = 8
        barrier = threading.Barrier(workers)

        def search():
            barrier.wait()
            return self.run_search("parallel retrieval", "--graph-depth", "0")

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(lambda _: search(), range(workers)))

        for result, payload in results:
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("sqlite-fts5", payload["mode"])
            self.assertEqual("warm", payload["index_state"])

    def test_parallel_incremental_refreshes_remain_available(self):
        target = self.spine / "target.md"
        (self.spine / "README.md").write_text(
            "# Architecture\n\n[Target](target.md)\n", encoding="utf-8"
        )
        target.write_text("# Target\n\nOwns oldsentinel.\n", encoding="utf-8")
        result, _ = self.run_search("oldsentinel")
        self.assertEqual(0, result.returncode, result.stderr)
        target.write_text("# Target\n\nOwns newsentinel.\n", encoding="utf-8")
        workers = 8
        barrier = threading.Barrier(workers)

        def search():
            barrier.wait()
            return self.run_search("newsentinel", "--graph-depth", "0")

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(lambda _: search(), range(workers)))

        for result, payload in results:
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("target.md", payload["direct_matches"][0]["path"])
        result, payload = self.run_search("newsentinel", "--graph-depth", "0")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(0, payload["refreshed"])

    def test_rebuild_and_parallel_readers_remain_available(self):
        (self.spine / "README.md").write_text(
            "# Architecture\n\nOwns rebuildsentinel.\n", encoding="utf-8"
        )
        result, _ = self.run_search("rebuildsentinel")
        self.assertEqual(0, result.returncode, result.stderr)
        workers = 8
        barrier = threading.Barrier(workers)

        def search(index):
            barrier.wait()
            arguments = ("--rebuild",) if index == 0 else ()
            return self.run_search("rebuildsentinel", *arguments)

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(search, range(workers)))

        for result, payload in results:
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("sqlite-fts5", payload["mode"])

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
        self.assertEqual("rebuild", payload["index_state"])
        self.assertEqual(1, payload["documents"])

    def test_query_without_searchable_terms_requests_fallback(self):
        (self.spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        result, payload = self.run_search("---")
        self.assertEqual(SEARCH.FALLBACK_EXIT, result.returncode)
        self.assertEqual("fallback", payload["mode"])
        self.assertEqual("invalid_query", payload["reason_code"])

    def test_unavailable_cache_path_requests_fallback(self):
        (self.spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        self.cache.touch()

        result, payload = self.run_search("architecture")

        self.assertEqual(SEARCH.FALLBACK_EXIT, result.returncode)
        self.assertEqual("fallback", payload["mode"])
        self.assertEqual("cache_unusable", payload["reason_code"])


if __name__ == "__main__":
    unittest.main()
