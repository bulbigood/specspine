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
V2_MODULE_PATH = PROJECT_ROOT / "skills/specspine-extract/scripts/search_spine_v2.py"
DIAGNOSTIC_PATH = PROJECT_ROOT / "tools/specspine-extract/search_spine_diagnostics.py"
SPEC = importlib.util.spec_from_file_location("specspine_extract_search", MODULE_PATH)
assert SPEC and SPEC.loader
SEARCH = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SEARCH
SPEC.loader.exec_module(SEARCH)
V2_SPEC = importlib.util.spec_from_file_location("specspine_extract_search_v2", V2_MODULE_PATH)
assert V2_SPEC and V2_SPEC.loader
V2_SEARCH = importlib.util.module_from_spec(V2_SPEC)
sys.modules[V2_SPEC.name] = V2_SEARCH
V2_SPEC.loader.exec_module(V2_SEARCH)


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
        query_arguments = (
            [f"--query={query}"] if query.startswith("-") else ["--query", query]
        )
        result = subprocess.run(
            [
                sys.executable,
                str(DIAGNOSTIC_PATH),
                "--telemetry",
                "full",
                str(self.spine),
                *query_arguments,
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
        )
        return result, json.loads(result.stdout)

    def run_default_search(self, query, *arguments):
        environment = os.environ.copy()
        environment["SPECSPINE_CACHE_DIR"] = str(self.cache)
        query_arguments = (
            [f"--query={query}"] if query.startswith("-") else ["--query", query]
        )
        result = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                str(self.spine),
                *query_arguments,
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
        )
        return result, json.loads(result.stdout)

    def run_batch(self, slices, ranking="faceted-bm25", *arguments):
        environment = os.environ.copy()
        environment["SPECSPINE_CACHE_DIR"] = str(self.cache)
        result = subprocess.run(
            [
                sys.executable,
                str(V2_MODULE_PATH),
                str(self.spine),
                "--queries-json",
                json.dumps(slices),
                "--ranking",
                ranking,
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
        )
        return result, result.stdout

    def run_diagnostic_batch(self, slices, ranking="faceted-bm25", *arguments):
        environment = os.environ.copy()
        environment["SPECSPINE_CACHE_DIR"] = str(self.cache)
        environment["SPECSPINE_PRODUCTION_SEARCH"] = str(V2_MODULE_PATH)
        sidecar = self.base / "batch-retrieval.jsonl"
        sidecar.unlink(missing_ok=True)
        environment["SPECSPINE_RETRIEVAL_TELEMETRY_FILE"] = str(sidecar)
        result = subprocess.run(
            [
                sys.executable,
                str(DIAGNOSTIC_PATH),
                "--telemetry",
                "full",
                str(self.spine),
                "--queries-json",
                json.dumps(slices),
                "--ranking",
                ranking,
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
        )
        telemetry = json.loads(sidecar.read_text(encoding="utf-8"))
        return result, telemetry

    def test_default_payload_omits_diagnostics(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns compactpayloadsentinel. Uses [Worker](worker.md).\n",
            encoding="utf-8",
        )
        (self.spine / "worker.md").write_text(
            "# Worker\n\nProvides mechanics.\n", encoding="utf-8"
        )

        result, payload = self.run_default_search(
            "compactpayloadsentinel", "--limit", "1", "--graph-limit", "1"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            {"schema_version", "mode", "direct_matches", "graph_neighbors"},
            set(payload),
        )
        self.assertEqual([{"path": "owner.md"}], payload["direct_matches"])
        self.assertEqual("worker.md", payload["graph_neighbors"][0]["path"])
        self.assertEqual(
            {"root_path", "source_path", "direction", "depth"},
            set(payload["graph_neighbors"][0]["transitions"][0]),
        )

    def test_default_result_caps_bound_direct_and_graph_routing(self):
        links = []
        for index in range(12):
            owner = f"owner-{index}.md"
            neighbor = f"neighbor-{index}.md"
            links.append(f"[Owner {index}]({owner})")
            (self.spine / owner).write_text(
                f"# Owner {index}\n\nOwns sharedsignal secondsignal. "
                f"Uses [Neighbor]({neighbor}).\n",
                encoding="utf-8",
            )
            (self.spine / neighbor).write_text(
                f"# Neighbor {index}\n\nProvides auxiliary boundary {index}.\n",
                encoding="utf-8",
            )
        (self.spine / "README.md").write_text(
            "# Root\n\n" + "\n".join(links) + "\n",
            encoding="utf-8",
        )

        result, payload = self.run_default_search("sharedsignal secondsignal")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(10, len(payload["direct_matches"]))
        self.assertEqual(2, len(payload["graph_neighbors"]))

    def test_minimal_observer_preserves_production_stdout_and_writes_sidecar(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns telemetrysentinel.\n", encoding="utf-8"
        )
        environment = os.environ.copy()
        environment["SPECSPINE_CACHE_DIR"] = str(self.cache)
        production = subprocess.run(
            [sys.executable, str(MODULE_PATH), str(self.spine), "--query=telemetrysentinel"],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
        )
        sidecar = self.base / "retrieval.jsonl"
        environment["SPECSPINE_RETRIEVAL_TELEMETRY_FILE"] = str(sidecar)
        environment["SPECSPINE_RETRIEVAL_TELEMETRY_LEVEL"] = "minimal"
        observed = subprocess.run(
            [
                sys.executable,
                str(DIAGNOSTIC_PATH),
                str(self.spine),
                "--query=telemetrysentinel",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
        )

        self.assertEqual(0, production.returncode, production.stderr)
        self.assertEqual(0, observed.returncode, observed.stderr)
        self.assertEqual(production.stdout, observed.stdout)
        telemetry = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual("minimal", telemetry["telemetry_level"])
        self.assertEqual("warm", telemetry["index_state"])
        self.assertEqual(len(observed.stdout.encode()), telemetry["production_output_utf8_bytes"])
        self.assertNotIn("direct_matches", telemetry)

    def test_default_fallback_payload_omits_diagnostics(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        self.cache.write_text("unavailable", encoding="utf-8")

        result, payload = self.run_default_search("anything")

        self.assertEqual(2, result.returncode)
        self.assertEqual({"schema_version": 2, "mode": "fallback"}, payload)

    def test_cli_accepts_unquoted_multiword_query(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns multiword query routing.\n", encoding="utf-8"
        )

        result, payload = self.run_default_search("multiword", "query", "routing")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([{"path": "owner.md"}], payload["direct_matches"])

    def test_faceted_ranking_requires_every_group_and_accepts_synonyms(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Retry owner\n\nOwns provider failures, timed-out attempts, and retries.\n",
            encoding="utf-8",
        )
        (self.spine / "provider-only.md").write_text(
            "# Provider\n\nOwns provider integration.\n", encoding="utf-8"
        )
        (self.spine / "timeout-only.md").write_text(
            "# Timeout\n\nDescribes timed-out requests.\n", encoding="utf-8"
        )
        slices = [{
            "id": "retry-owner",
            "must": [
                ["provider"],
                ["timeout", "timed-out"],
                ["retry", "retries"],
            ],
        }]

        result, output = self.run_batch(
            slices, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            '<<<SPECSPINE_RESULT {"version":2,"mode":"sqlite-fts5",'
            '"ranking":"faceted-bm25","truncated":false}>>>',
            output,
        )
        self.assertIn(
            '<<<SPECSPINE_SLICE {"id":"retry-owner","status":"matched",'
            '"match_tier":"strict","joint_df":1}>>>',
            output,
        )
        self.assertIn(
            '<<<SPECSPINE_HIT {"path":"owner.md","origin":"direct",',
            output,
        )
        self.assertIn('"matched_must_terms":["provider","timed-out","retry"]', output)
        self.assertIn('<<<SPECSPINE_DOCUMENT {"path":"owner.md",', output)
        self.assertIn("# Retry owner", output)
        self.assertNotIn("provider-only.md", output)
        self.assertNotIn("timeout-only.md", output)

    def test_normalized_facets_match_english_inflection(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "incident.md").write_text(
            "# Incident\n\nOperators pause callbacks during an incident.\n",
            encoding="utf-8",
        )
        slices = [{
            "id": "callback-pause",
            "must": [["incident"], ["pause"], ["callback"]],
        }]

        strict_result, strict = self.run_diagnostic_batch(
            slices, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )
        result, payload = self.run_diagnostic_batch(
            slices, "faceted-normalized", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(2, strict_result.returncode, strict_result.stderr)
        self.assertEqual([], strict["slices"][0]["direct_matches"])
        self.assertEqual(0, result.returncode, result.stderr)
        routed = payload["slices"][0]
        self.assertEqual("normalized", routed["selection"]["match_tier"])
        self.assertEqual(["incident.md"], [
            item["path"] for item in routed["direct_matches"]
        ])
        self.assertIn(
            "morphology",
            routed["direct_matches"][0]["signals"]["match_origins"],
        )

    def test_normalized_facets_match_russian_word_forms(self):
        (self.spine / "README.md").write_text("# Корень\n", encoding="utf-8")
        (self.spine / "incident.md").write_text(
            "# Инцидент\n\nВыключатель останавливает создание рассылки.\n",
            encoding="utf-8",
        )
        slices = [{
            "id": "pause",
            "must": [["инцидент"], ["остановить"], ["рассылка"]],
        }]

        result, payload = self.run_diagnostic_batch(
            slices, "faceted-normalized", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        routed = payload["slices"][0]
        self.assertEqual(["incident.md"], [
            item["path"] for item in routed["direct_matches"]
        ])
        self.assertEqual("normalized", routed["selection"]["match_tier"])

    def test_normalized_facets_match_cjk_substrings(self):
        (self.spine / "README.md").write_text("# 根\n", encoding="utf-8")
        (self.spine / "event-time.md").write_text(
            "# 事件时间与水位线\n\n迟到事件写入 late-event 隔离流。\n",
            encoding="utf-8",
        )
        slices = [{
            "id": "late-events",
            "must": [["水位线"], ["迟到事件"], ["隔离流"]],
        }]

        result, payload = self.run_diagnostic_batch(
            slices, "faceted-normalized", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        routed = payload["slices"][0]
        self.assertEqual(["event-time.md"], [
            item["path"] for item in routed["direct_matches"]
        ])
        self.assertIn(
            "cjk_substring",
            routed["direct_matches"][0]["signals"]["match_origins"],
        )

    def test_normalized_facets_preserve_structured_no_match(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "migration.md").write_text(
            "# Migration\n\nMigration workers use a local process lock.\n",
            encoding="utf-8",
        )
        slices = [{
            "id": "remote",
            "must": [
                ["Kubernetes"],
                ["migration workers"],
                ["availability zones"],
            ],
        }]

        result, output = self.run_batch(
            slices, "faceted-normalized", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn(
            '<<<SPECSPINE_SLICE {"id":"remote","status":"no_match",'
            '"match_tier":"strict","joint_df":0}>>>',
            output,
        )
        self.assertNotIn("SPECSPINE_HIT", output)

    def test_normalized_morphology_does_not_blur_identifiers(self):
        self.assertFalse(
            V2_SEARCH.RANKING.morphological_token_match(
                "invariant0",
                "invariant1",
            )
        )
        self.assertTrue(
            V2_SEARCH.RANKING.morphological_token_match(
                "callback",
                "callbacks",
            )
        )

    def test_same_facets_support_legacy_and_faceted_ab_comparison(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns alphafacet betafacet gammafacet.\n", encoding="utf-8"
        )
        decoy_terms = (
            "alphafacet betafacet",
            "betafacet gammafacet",
            "alphafacet gammafacet",
        )
        for index, terms in enumerate(decoy_terms):
            (self.spine / f"decoy-{index}.md").write_text(
                f"# Decoy {index}\n\nMentions only {terms}.\n", encoding="utf-8"
            )
        slices = [{
            "id": "owner",
            "must": [["alphafacet"], ["betafacet"], ["gammafacet"]],
        }]

        legacy_result, legacy = self.run_diagnostic_batch(
            slices, "legacy", "--graph-depth=0", "--graph-limit=0"
        )
        faceted_result, faceted = self.run_diagnostic_batch(
            slices, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(0, legacy_result.returncode, legacy_result.stderr)
        self.assertEqual(0, faceted_result.returncode, faceted_result.stderr)
        self.assertGreater(len(legacy["slices"][0]["direct_matches"]), 1)
        self.assertEqual(
            ["owner.md"],
            [item["path"] for item in faceted["slices"][0]["direct_matches"]],
        )

    def test_batch_slices_are_ranked_independently_after_one_index_build(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "alpha.md").write_text(
            "# Alpha owner\n\nOwns alphaone alphatwo.\n", encoding="utf-8"
        )
        (self.spine / "beta.md").write_text(
            "# Beta owner\n\nOwns betaone betatwo.\n", encoding="utf-8"
        )
        slices = [
            {"id": "alpha", "must": [["alphaone"], ["alphatwo"]]},
            {"id": "beta", "must": [["betaone"], ["betatwo"]]},
        ]

        result, payload = self.run_diagnostic_batch(
            slices, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("<<<SPECSPINE_RESULT ", result.stdout)
        self.assertNotEqual("{", result.stdout.lstrip()[:1])
        self.assertEqual("cold_build", payload["index_state"])
        self.assertEqual(2, payload["slice_count"])
        self.assertEqual(
            ["alpha.md", "beta.md"],
            [item["direct_matches"][0]["path"] for item in payload["slices"]],
        )
        raw_result, output = self.run_batch(
            slices, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )
        self.assertEqual(0, raw_result.returncode, raw_result.stderr)
        self.assertEqual(2, output.count("<<<SPECSPINE_SLICE "))
        self.assertIn("# Alpha owner", output)
        self.assertIn("# Beta owner", output)

    def test_normalized_batch_precomputes_documents_once(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns callbacks and retries.\n", encoding="utf-8"
        )
        slices = V2_SEARCH.RANKING.parse_query_slices(json.dumps([
            {"id": "callbacks", "must": [["callback"]]},
            {"id": "retries", "must": [["retry"]]},
        ]))

        with patch.dict(
            os.environ,
            {"SPECSPINE_CACHE_DIR": str(self.cache)},
        ), patch.object(
            V2_SEARCH.RANKING,
            "load_normalized_documents",
            wraps=V2_SEARCH.RANKING.load_normalized_documents,
        ) as load:
            outcome = V2_SEARCH.execute_searches(
                self.spine,
                slices,
                graph_depth=0,
                graph_limit=0,
                ranking_system="faceted-normalized",
            )

        self.assertEqual(0, outcome.exit_code)
        self.assertEqual(1, load.call_count)

    def test_should_groups_boost_without_filtering_candidates(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "preferred.md").write_text(
            "# Preferred\n\nOwns mustalpha mustbeta preferredsignal.\n",
            encoding="utf-8",
        )
        (self.spine / "other.md").write_text(
            "# Other\n\nOwns mustalpha mustbeta.\n", encoding="utf-8"
        )
        slices = [{
            "id": "owner",
            "must": [["mustalpha"], ["mustbeta"]],
            "should": [["preferredsignal"]],
        }]

        result, payload = self.run_diagnostic_batch(
            slices, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        matches = payload["slices"][0]["direct_matches"]
        self.assertEqual("preferred.md", matches[0]["path"])
        self.assertIn("other.md", {item["path"] for item in matches})
        self.assertEqual(1, matches[0]["signals"]["matched_should_groups"])

    def test_faceted_scoring_does_not_truncate_before_should_reranking(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        for index in range(60):
            (self.spine / f"decoy-{index:02d}.md").write_text(
                f"# Decoy {index}\n\nOwns poolalpha poolbeta.\n",
                encoding="utf-8",
            )
        (self.spine / "z-preferred.md").write_text(
            "# Preferred\n\nOwns poolalpha poolbeta rarepreference.\n",
            encoding="utf-8",
        )
        slices = [{
            "id": "owner",
            "must": [["poolalpha"], ["poolbeta"]],
            "should": [["rarepreference"]],
        }]

        result, payload = self.run_diagnostic_batch(
            slices,
            "faceted-bm25",
            "--limit=1",
            "--graph-depth=0",
            "--graph-limit=0",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        routed = payload["slices"][0]
        self.assertEqual("z-preferred.md", routed["direct_matches"][0]["path"])
        self.assertEqual(61, routed["selection"]["direct_considered"])
        self.assertEqual(3, routed["selection"]["term_queries"])

    def test_exact_path_title_and_semantic_id_are_faceted_channels(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "owner.md").write_text(
            "# Exact Owner\n\n## Constraints\n\n"
            "- **CON-owner-exact** — Canonical ownership.\n",
            encoding="utf-8",
        )
        slices = [
            {"id": "path", "must": [["owner.md"]]},
            {"id": "title", "must": [["Exact Owner"]]},
            {"id": "semantic", "must": [["CON-owner-exact"]]},
        ]

        result, payload = self.run_diagnostic_batch(
            slices, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        expected_origins = ("exact_path", "exact_title", "semantic_id")
        for routed, expected_origin in zip(payload["slices"], expected_origins):
            self.assertEqual("owner.md", routed["direct_matches"][0]["path"])
            self.assertIn(
                expected_origin,
                routed["direct_matches"][0]["signals"]["exact_match_origins"],
            )

    def test_output_deduplicates_document_content_across_slices(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "owner.md").write_text(
            "# Shared owner\n\nOwns sharedalpha sharedbeta.\n", encoding="utf-8"
        )
        slices = [
            {"id": "alpha", "must": [["sharedalpha"]]},
            {"id": "beta", "must": [["sharedbeta"]]},
        ]

        result, output = self.run_batch(
            slices, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(2, output.count('<<<SPECSPINE_HIT {"path":"owner.md"'))
        self.assertEqual(
            1, output.count('<<<SPECSPINE_DOCUMENT {"path":"owner.md",')
        )
        self.assertEqual(1, output.count("# Shared owner"))

    def test_partial_batch_marks_each_slice_status(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns presentneedle.\n", encoding="utf-8"
        )

        result, output = self.run_batch(
            [
                {"id": "found", "must": [["presentneedle"]]},
                {"id": "missing", "must": [["absentneedle"]]},
            ],
            "faceted-bm25",
            "--graph-depth=0",
            "--graph-limit=0",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            '<<<SPECSPINE_SLICE {"id":"found","status":"matched",'
            '"match_tier":"strict","joint_df":1}>>>',
            output,
        )
        self.assertIn(
            '<<<SPECSPINE_SLICE {"id":"missing","status":"no_match",'
            '"match_tier":"strict","joint_df":0}>>>',
            output,
        )

    def test_legacy_batch_keeps_valid_absent_terms_as_no_match(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns presentneedle.\n", encoding="utf-8"
        )

        result, output = self.run_batch(
            [
                {"id": "found", "must": [["presentneedle"]]},
                {
                    "id": "missing",
                    "must": [["warehouse"], ["barcode"], ["cycle count"]],
                },
            ],
            "legacy",
            "--graph-depth=0",
            "--graph-limit=0",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            '<<<SPECSPINE_SLICE {"id":"found","status":"matched"}>>>',
            output,
        )
        self.assertIn(
            '<<<SPECSPINE_SLICE {"id":"missing","status":"no_match"}>>>',
            output,
        )
        self.assertNotIn('"mode":"fallback"', output)

    def test_output_budget_omits_whole_documents_without_cutting_protocol(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "large.md").write_text(
            "# Large\n\nbudgetneedle\n\n" + ("large-content " * 1000),
            encoding="utf-8",
        )

        result, output = self.run_batch(
            [{"id": "large", "must": [["budgetneedle"]]}],
            "faceted-bm25",
            "--graph-depth=0",
            "--graph-limit=0",
            "--max-output-bytes=4096",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertLessEqual(len(output.encode("utf-8")), 4096)
        self.assertIn('"truncated":true', output)
        self.assertIn("SPECSPINE_DOCUMENT_OMITTED", output)
        self.assertNotIn("large-content", output)
        self.assertTrue(output.endswith("<<<SPECSPINE_END_RESULT>>>\n"))

    def test_invalid_structured_query_returns_marked_fallback(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")

        result, payload = self.run_batch(
            [{"id": "invalid", "must": []}], "faceted-bm25"
        )

        self.assertEqual(2, result.returncode)
        self.assertEqual(
            '<<<SPECSPINE_RESULT {"version":2,"mode":"fallback",'
            '"ranking":"faceted-bm25","reason":"invalid_query",'
            '"truncated":false}>>>\n'
            "<<<SPECSPINE_END_RESULT>>>\n",
            payload,
        )

    def test_faceted_document_index_refreshes_incrementally(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        owner = self.spine / "owner.md"
        owner.write_text(
            "# Owner\n\nOwns refreshalpha refreshbeta.\n", encoding="utf-8"
        )
        old_slice = [{
            "id": "owner",
            "must": [["refreshalpha"], ["refreshbeta"]],
        }]
        new_slice = [{
            "id": "owner",
            "must": [["refreshalpha"], ["refreshgamma"]],
        }]

        first, first_payload = self.run_diagnostic_batch(
            old_slice, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )
        owner.write_text(
            "# Owner\n\nOwns refreshalpha refreshgamma.\n", encoding="utf-8"
        )
        second, second_payload = self.run_diagnostic_batch(
            new_slice, "faceted-bm25", "--graph-depth=0", "--graph-limit=0"
        )

        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual("owner.md", first_payload["slices"][0]["direct_matches"][0]["path"])
        self.assertEqual("incremental_refresh", second_payload["index_state"])
        self.assertEqual("owner.md", second_payload["slices"][0]["direct_matches"][0]["path"])

    def test_faceted_ranking_preserves_graph_routing(self):
        (self.spine / "README.md").write_text("# Root\n", encoding="utf-8")
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns graphalpha graphbeta. Uses [Worker](worker.md).\n",
            encoding="utf-8",
        )
        (self.spine / "worker.md").write_text(
            "# Worker\n\nProvides execution mechanics.\n", encoding="utf-8"
        )
        slices = [{
            "id": "owner",
            "must": [["graphalpha"], ["graphbeta"]],
        }]

        result, payload = self.run_diagnostic_batch(
            slices, "faceted-bm25", "--graph-depth=1", "--graph-limit=1"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        routed = payload["slices"][0]
        self.assertEqual(
            ["owner.md"], [item["path"] for item in routed["direct_matches"]]
        )
        self.assertEqual("worker.md", routed["graph_neighbors"][0]["path"])
        self.assertEqual(
            "owner.md",
            routed["graph_neighbors"][0]["transitions"][0]["source_path"],
        )
        raw_result, output = self.run_batch(
            slices, "faceted-bm25", "--graph-depth=1", "--graph-limit=1"
        )
        self.assertEqual(0, raw_result.returncode, raw_result.stderr)
        self.assertIn(
            '<<<SPECSPINE_HIT {"path":"worker.md","origin":"graph"}>>>',
            output,
        )
        self.assertIn('<<<SPECSPINE_DOCUMENT {"path":"worker.md",', output)
        self.assertIn("# Worker", output)

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
        self.assertEqual(1, payload["selection"]["direct_returned"])
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
        transition = next(
            item for item in payload["graph_neighbors"] if item["path"] == consumer
        )["transitions"][0]
        self.assertEqual("CON-retry-limit", transition["semantic_id"])

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

    def test_final_direct_results_drop_single_term_tail(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n[Weak](weak.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns alphacontract betapolicy.\n", encoding="utf-8"
        )
        for index in range(2):
            (self.spine / f"weak-{index}.md").write_text(
                f"# Weak {index}\n\nMentions gammalimit.\n", encoding="utf-8"
            )

        result, payload = self.run_search(
            "alphacontract betapolicy gammalimit", "--graph-depth", "0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["owner.md"], [item["path"] for item in payload["direct_matches"]])
        self.assertEqual(0, payload["selection"]["direct_weak_returned"])

    def test_graph_prunes_only_when_one_neighbor_is_more_relevant(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns ownerterm timeout provider handling. "
            "Links [Navigation](navigation.md) and [Provider](provider-webhooks.md).\n",
            encoding="utf-8",
        )
        (self.spine / "navigation.md").write_text(
            "# Navigation\n\nGeneral boundary.\n", encoding="utf-8"
        )
        (self.spine / "provider-webhooks.md").write_text(
            "# Webhooks\n\nProvider boundary.\n", encoding="utf-8"
        )
        for index in range(3):
            (self.spine / f"common-{index}.md").write_text(
                f"# Common {index}\n\nProvider reference.\n", encoding="utf-8"
            )

        result, payload = self.run_search("ownerterm timeout provider")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["owner.md"], [item["path"] for item in payload["direct_matches"]])
        self.assertEqual(
            ["provider-webhooks.md"],
            [item["path"] for item in payload["graph_neighbors"]],
        )

    def test_graph_preserves_tied_neighbors(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns ownerterm timeout. Links [A](a.md) and [B](b.md).\n",
            encoding="utf-8",
        )
        for path in ("a.md", "b.md"):
            (self.spine / path).write_text("# Neighbor\n\nGeneral boundary.\n", encoding="utf-8")

        result, payload = self.run_search("ownerterm timeout")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            ["a.md", "b.md"],
            [item["path"] for item in payload["graph_neighbors"]],
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
        self.assertEqual(
            {"token_hits", "query_tokens", "rare_token_hits", "fts_rank"},
            set(candidate["signals"]),
        )

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
        self.assertEqual("owner.md", neighbor["transitions"][0]["root_path"])
        self.assertEqual("owner.md", neighbor["transitions"][0]["source_path"])
        self.assertEqual("outgoing", neighbor["transitions"][0]["direction"])
        self.assertEqual(1, neighbor["transitions"][0]["depth"])
        self.assertEqual("Worker", neighbor["transitions"][0]["edge_label"])

    def test_semantic_id_uses_strong_match_without_fts_tail(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n", encoding="utf-8"
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\n## Constraints\n\n"
            "- **CON-addressed-owner** — Owns repeated common material.\n",
            encoding="utf-8",
        )
        for index in range(8):
            (self.spine / f"decoy-{index}.md").write_text(
                f"# Decoy {index}\n\nCON-addressed-owner repeated common material.\n",
                encoding="utf-8",
            )

        result, payload = self.run_search(
            "CON-addressed-owner", "--graph-depth", "0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("strong-match", payload["retrieval_strategy"])
        self.assertIsNone(payload["selection"]["direct_cutoff_score"])
        self.assertEqual(["owner.md"], [item["path"] for item in payload["direct_matches"]])
        self.assertEqual(
            ["CON-ADDRESSED-OWNER"],
            payload["direct_matches"][0]["signals"]["semantic_ids"],
        )

    def test_hybrid_search_adaptively_drops_weak_tail_and_readme(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n",
            encoding="utf-8",
        )
        terms = [f"targetsignal{index}" for index in range(8)]
        (self.spine / "owner.md").write_text(
            f"# Owner\n\nOwns {' '.join(terms)}.\n",
            encoding="utf-8",
        )
        for index, term in enumerate(terms):
            (self.spine / f"decoy-{index}.md").write_text(
                f"# Decoy {index}\n\nGeneric {term} material.\n", encoding="utf-8"
            )

        result, payload = self.run_search(
            " ".join(terms), "--limit", "12", "--graph-depth", "0"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("hybrid-fts", payload["retrieval_strategy"])
        self.assertEqual("owner.md", payload["direct_matches"][0]["path"])
        self.assertNotIn(
            "README.md", {item["path"] for item in payload["direct_matches"]}
        )
        self.assertGreater(
            payload["selection"]["direct_considered"],
            payload["selection"]["direct_returned"],
        )

    def test_broad_query_prefers_multi_term_coverage_over_one_phrase(self):
        (self.spine / "README.md").write_text(
            "# Root\n\n[Owner](owner.md)\n[Phrase](phrase.md)\n",
            encoding="utf-8",
        )
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns ownersignal secondsignal thirdsignal.\n",
            encoding="utf-8",
        )
        (self.spine / "phrase.md").write_text(
            "# Phrase\n\nMentions commonsignal phrasesignal.\n",
            encoding="utf-8",
        )
        for index in range(4):
            (self.spine / f"common-{index}.md").write_text(
                f"# Common {index}\n\nMentions commonsignal.\n",
                encoding="utf-8",
            )

        result, payload = self.run_search(
            "commonsignal phrasesignal ownersignal secondsignal thirdsignal",
            "--graph-depth",
            "0",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("owner.md", payload["direct_matches"][0]["path"])

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

            direct, graph, strategy, selection = SEARCH.search(
                connection, "needle", 2, 0, 2
            )
            self.assertEqual(
                ["large.md", "small.md"],
                [candidate["path"] for candidate in direct],
            )
            self.assertEqual([], graph)
            self.assertEqual("hybrid-fts", strategy)
            self.assertEqual(2, selection["direct_returned"])
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
