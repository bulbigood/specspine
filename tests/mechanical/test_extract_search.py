import concurrent.futures
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
SEARCH_PATH = PROJECT_ROOT / "skills/specspine-extract/scripts/search_spine.py"
DIAGNOSTIC_PATH = (
    PROJECT_ROOT / "tools/specspine-extract/search_spine_diagnostics.py"
)
SPEC = importlib.util.spec_from_file_location("specspine_extract_search", SEARCH_PATH)
assert SPEC and SPEC.loader
SEARCH = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SEARCH
SPEC.loader.exec_module(SEARCH)


class ExtractSearchTests(unittest.TestCase):
    def test_skill_keeps_the_success_path_monolithic(self):
        skill_root = Path(__file__).parents[2] / "skills" / "specspine-extract"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        self.assertFalse((skill_root / "references").exists())
        self.assertIn("invoke the bundled script exactly once", skill)
        self.assertIn("Do not reread", skill)
        self.assertIn("prepend the repository-relative", skill)
        self.assertIn("README.md` before searching only when", skill)

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
        (self.spine / "README.md").write_text("# Index\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def slices(self, payload):
        return SEARCH.RANKING.parse_query_slices(
            json.dumps(payload, ensure_ascii=False)
        )

    def search(self, payload, **options):
        previous = os.environ.get("SPECSPINE_CACHE_DIR")
        os.environ["SPECSPINE_CACHE_DIR"] = str(self.cache)
        try:
            return SEARCH.execute_searches(
                self.spine,
                self.slices(payload),
                **options,
            )
        finally:
            if previous is None:
                os.environ.pop("SPECSPINE_CACHE_DIR", None)
            else:
                os.environ["SPECSPINE_CACHE_DIR"] = previous

    def run_cli(self, payload):
        environment = os.environ.copy()
        environment["SPECSPINE_CACHE_DIR"] = str(self.cache)
        return subprocess.run(
            [
                sys.executable,
                str(SEARCH_PATH),
                str(self.spine),
                "--queries-json",
                json.dumps(payload, ensure_ascii=False),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=10,
        )

    def test_cli_exposes_one_search_policy_and_effective_configuration(self):
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns alpha beta.\n", encoding="utf-8"
        )

        result = self.run_cli([
            {"id": "owner", "must": [["alpha"], ["beta"]]}
        ])

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            '<<<SPECSPINE_RESULT {"version":2,"mode":"sqlite-fts5",'
            '"ranking":"normalized","graph_depth":1,"graph_limit":2,',
            result.stdout,
        )
        help_result = subprocess.run(
            [sys.executable, str(SEARCH_PATH), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotIn("--ranking", help_result.stdout)
        self.assertNotIn("--graph-limit", help_result.stdout)
        self.assertNotIn("--graph-depth", help_result.stdout)

    def test_must_groups_require_joint_coverage_and_accept_synonyms(self):
        (self.spine / "owner.md").write_text(
            "# Owner\n\nExternal provider retries timed-out operations.\n",
            encoding="utf-8",
        )
        (self.spine / "partial.md").write_text(
            "# Partial\n\nExternal provider retries operations.\n",
            encoding="utf-8",
        )

        outcome = self.search([{
            "id": "retry",
            "must": [
                ["retry", "retries"],
                ["provider"],
                ["timeout", "timed-out"],
            ],
        }], graph_depth=0)

        routed = outcome.slices[0].outcome
        self.assertEqual(["owner.md"], [item["path"] for item in routed.direct_matches])

    def test_slices_are_ranked_independently_in_one_call(self):
        (self.spine / "orders.md").write_text(
            "# Orders\n\nOwns order cancellation.\n", encoding="utf-8"
        )
        (self.spine / "callbacks.md").write_text(
            "# Callbacks\n\nOwns webhook suspension.\n", encoding="utf-8"
        )

        outcome = self.search([
            {"id": "orders", "must": [["order"], ["cancellation"]]},
            {"id": "callbacks", "must": [["webhook"], ["suspension"]]},
        ], graph_depth=0)

        self.assertEqual(["orders", "callbacks"], [
            item.identifier for item in outcome.slices
        ])
        self.assertEqual("orders.md", outcome.slices[0].outcome.direct_matches[0]["path"])
        self.assertEqual(
            "callbacks.md", outcome.slices[1].outcome.direct_matches[0]["path"]
        )

    def test_maximum_batch_keeps_eight_slices_independent_and_deduplicated(self):
        payload = []
        for index in range(SEARCH.RANKING.MAX_SLICES):
            (self.spine / f"owner-{index}.md").write_text(
                f"# Owner {index}\n\nOwns facet{index} invariant{index}.\n",
                encoding="utf-8",
            )
            payload.append({
                "id": f"slice-{index}",
                "must": [[f"facet{index}"], [f"invariant{index}"]],
            })

        outcome = self.search(payload, graph_depth=0)
        output = SEARCH.render_batch_output(self.spine, outcome)

        self.assertEqual(SEARCH.RANKING.MAX_SLICES, len(outcome.slices))
        self.assertEqual(
            [f"owner-{index}.md" for index in range(SEARCH.RANKING.MAX_SLICES)],
            [
                item.outcome.direct_matches[0]["path"]
                for item in outcome.slices
            ],
        )
        self.assertEqual(
            SEARCH.RANKING.MAX_SLICES,
            output.count("<<<SPECSPINE_SLICE "),
        )
        for index in range(SEARCH.RANKING.MAX_SLICES):
            self.assertEqual(
                1,
                output.count(f'DOCUMENT {{"path":"owner-{index}.md"'),
            )

    def test_near_duplicate_decoys_cannot_replace_joint_facet_owner(self):
        (self.spine / "owner.md").write_text(
            "# Retry policy\n\n"
            "Carrier retry uses exponential backoff with bounded jitter.\n",
            encoding="utf-8",
        )
        decoys = {
            "carrier.md": "Carrier retry uses exponential backoff.",
            "jobs.md": "Background retry uses bounded jitter.",
            "limits.md": "Carrier limits use bounded jitter.",
        }
        for name, content in decoys.items():
            (self.spine / name).write_text(
                f"# Decoy\n\n{content}\n",
                encoding="utf-8",
            )

        outcome = self.search([{
            "id": "policy",
            "must": [["carrier"], ["exponential backoff"], ["jitter"]],
        }], graph_depth=0)

        paths = [
            item["path"]
            for item in outcome.slices[0].outcome.direct_matches
        ]
        self.assertEqual(["owner.md"], paths)

    def test_normalization_handles_diverse_writing_systems(self):
        documents = {
            "english.md": "# English\n\nRetries timed-out provider requests.\n",
            "russian.md": "# Русский\n\nПодтверждённая покупка открывает билет.\n",
            "chinese.md": "# 中文\n\n回填任务必须隔离线上消费组并保存检查点。\n",
            "japanese.md": "# 日本語\n\n再試行処理は結果の重複を防止する。\n",
            "korean.md": "# 한국어\n\n재시도작업은중복결과를방지한다.\n",
            "thai.md": "# ภาษาไทย\n\nการลองใหม่ต้องป้องกันผลลัพธ์ซ้ำ.\n",
        }
        for name, content in documents.items():
            (self.spine / name).write_text(content, encoding="utf-8")

        outcome = self.search([
            {"id": "en", "must": [["request"], ["timed"], ["provider"]]},
            {"id": "ru", "must": [["подтверждение"], ["покупки"], ["билет"]]},
            {"id": "zh", "must": [["回填"], ["隔离线上"], ["检查点"]]},
            {"id": "ja", "must": [["試行処理"], ["重複"], ["防止"]]},
            {"id": "ko", "must": [["시도작업"], ["중복결과"], ["방지"]]},
            {"id": "th", "must": [["ลองใหม่"], ["ป้องกัน"], ["ผลลัพธ์ซ้ำ"]]},
        ], graph_depth=0)

        self.assertEqual(
            [
                "english.md",
                "russian.md",
                "chinese.md",
                "japanese.md",
                "korean.md",
                "thai.md",
            ],
            [item.outcome.direct_matches[0]["path"] for item in outcome.slices],
        )

    def test_normalization_handles_diacritics_hyphens_and_mixed_scripts(self):
        (self.spine / "unicode.md").write_text(
            "# Résumé pipeline\n\n"
            "The café worker retries timed-out 请求 and preserves 检查点.\n",
            encoding="utf-8",
        )

        outcome = self.search([{
            "id": "unicode",
            "must": [
                ["resume"],
                ["cafe"],
                ["timed out", "timed-out"],
                ["请求"],
                ["检查点"],
            ],
        }], graph_depth=0)

        self.assertEqual(
            "unicode.md",
            outcome.slices[0].outcome.direct_matches[0]["path"],
        )

    def test_should_groups_rerank_without_filtering(self):
        (self.spine / "preferred.md").write_text(
            "# Preferred\n\nPlugin compatibility with stable diagnostics.\n",
            encoding="utf-8",
        )
        (self.spine / "other.md").write_text(
            "# Other\n\nPlugin compatibility.\n", encoding="utf-8"
        )

        baseline = self.search([{
            "id": "plugin",
            "must": [["plugin"], ["compatibility"]],
        }], graph_depth=0)
        outcome = self.search([{
            "id": "plugin",
            "must": [["plugin"], ["compatibility"]],
            "should": [["stable"], ["diagnostics"]],
        }], graph_depth=0)

        self.assertEqual(
            "other.md", baseline.slices[0].outcome.direct_matches[0]["path"]
        )
        paths = [item["path"] for item in outcome.slices[0].outcome.direct_matches]
        self.assertEqual("preferred.md", paths[0])

    def test_exact_semantic_id_is_a_direct_channel(self):
        (self.spine / "owner.md").write_text(
            "# Owner\n\n"
            "<!-- specspine:semantic-ids:begin -->\n"
            "## Constraints\n\n"
            "- **CON-owner-rule** — Preserve owner behavior.\n"
            "<!-- specspine:semantic-ids:end -->\n",
            encoding="utf-8",
        )

        outcome = self.search([
            {"id": "rule", "must": [["CON-owner-rule"]]}
        ], graph_depth=0)

        match = outcome.slices[0].outcome.direct_matches[0]
        self.assertEqual("owner.md", match["path"])
        self.assertIn("semantic_id", match["signals"]["exact_match_origins"])

    def test_graph_is_one_hop_ranked_and_capped_at_two_per_slice(self):
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns alpha beta. "
            "Uses [Worker](worker.md), [Policy](policy.md), and [Noise](noise.md).\n",
            encoding="utf-8",
        )
        (self.spine / "worker.md").write_text(
            "# Alpha worker\n\nProvides alpha mechanics.\n", encoding="utf-8"
        )
        (self.spine / "policy.md").write_text(
            "# Beta policy\n\nDefines beta policy.\n", encoding="utf-8"
        )
        (self.spine / "noise.md").write_text(
            "# Noise\n\nUnrelated material.\n", encoding="utf-8"
        )

        outcome = self.search([
            {"id": "owner", "must": [["alpha"], ["beta"]]}
        ])

        routed = outcome.slices[0].outcome
        self.assertEqual("owner.md", routed.direct_matches[0]["path"])
        self.assertLessEqual(len(routed.graph_neighbors), 2)
        self.assertTrue(all(
            transition["depth"] == 1
            for item in routed.graph_neighbors
            for transition in item["transitions"]
        ))

    def test_output_contains_full_documents_and_deduplicates_shared_hits(self):
        (self.spine / "shared.md").write_text(
            "# Shared\n\nOwns alpha beta gamma.\n", encoding="utf-8"
        )
        outcome = self.search([
            {"id": "one", "must": [["alpha"], ["beta"]]},
            {"id": "two", "must": [["beta"], ["gamma"]]},
        ], graph_depth=0)

        output = SEARCH.render_batch_output(self.spine, outcome)

        self.assertEqual(2, output.count('"path":"shared.md","origin":"direct"'))
        self.assertEqual(1, output.count('DOCUMENT {"path":"shared.md"'))
        self.assertEqual(1, output.count("# Shared"))

    def test_partial_no_match_keeps_other_hits_and_includes_root_once(self):
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns alpha beta.\n", encoding="utf-8"
        )
        outcome = self.search([
            {"id": "found", "must": [["alpha"], ["beta"]]},
            {"id": "missing", "must": [["absentterm"], ["unknownterm"]]},
        ], graph_depth=0)

        output = SEARCH.render_batch_output(self.spine, outcome)

        self.assertIn('"id":"found","status":"matched"', output)
        self.assertIn('"id":"missing","status":"no_match"', output)
        self.assertIn('"path":"README.md","origin":"root_fallback"', output)
        self.assertIn('DOCUMENT {"path":"owner.md"', output)
        self.assertEqual(1, output.count('DOCUMENT {"path":"README.md"'))
        self.assertIn("# Index", output)

    def test_all_no_match_returns_root_document_successfully(self):
        result = self.run_cli([
            {"id": "missing", "must": [["absentterm"], ["unknownterm"]]}
        ])

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('"status":"no_match"', result.stdout)
        self.assertIn('"root_fallback":"README.md"', result.stdout)
        self.assertIn('DOCUMENT {"path":"README.md"', result.stdout)
        self.assertIn("# Index", result.stdout)

    def test_technical_fallback_still_returns_root_document(self):
        environment = os.environ.copy()
        environment["SPECSPINE_CACHE_DIR"] = "/dev/null"
        result = subprocess.run(
            [
                sys.executable,
                str(SEARCH_PATH),
                str(self.spine),
                "--queries-json",
                json.dumps([
                    {"id": "owner", "must": [["alpha"], ["beta"]]}
                ]),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=10,
        )

        self.assertEqual(SEARCH.FALLBACK_EXIT, result.returncode)
        self.assertIn('"mode":"fallback"', result.stdout)
        self.assertIn('"root_fallback":"README.md"', result.stdout)
        self.assertIn('DOCUMENT {"path":"README.md"', result.stdout)

    def test_output_budget_omits_whole_documents_without_cutting_protocol(self):
        (self.spine / "large.md").write_text(
            "# Large\n\nOwns alpha beta.\n\n" + ("payload " * 2000),
            encoding="utf-8",
        )
        outcome = self.search([
            {"id": "large", "must": [["alpha"], ["beta"]]}
        ], graph_depth=0)

        output = SEARCH.render_batch_output(
            self.spine, outcome, max_output_bytes=4096
        )

        self.assertIn('"truncated":true', output)
        self.assertIn("SPECSPINE_DOCUMENT_OMITTED", output)
        self.assertNotIn("payload payload", output)
        self.assertTrue(output.endswith("<<<SPECSPINE_END_RESULT>>>\n"))

    def test_budgeted_mixed_batch_preserves_all_slices_and_root_fallback(self):
        (self.spine / "large.md").write_text(
            "# Large\n\nOwns alpha beta.\n\n" + ("payload " * 2000),
            encoding="utf-8",
        )
        outcome = self.search([
            {"id": "found", "must": [["alpha"], ["beta"]]},
            {"id": "missing", "must": [["absentterm"], ["unknownterm"]]},
        ], graph_depth=0)

        output = SEARCH.render_batch_output(
            self.spine, outcome, max_output_bytes=4096
        )

        self.assertIn('"id":"found","status":"matched"', output)
        self.assertIn('"id":"missing","status":"no_match"', output)
        self.assertIn('"truncated":true', output)
        self.assertIn("SPECSPINE_DOCUMENT_OMITTED", output)
        self.assertIn('DOCUMENT {"path":"README.md"', output)
        self.assertEqual(1, output.count("# Index"))
        self.assertTrue(output.endswith("<<<SPECSPINE_END_RESULT>>>\n"))

    def test_cold_warm_and_incremental_paths_report_complete_timings(self):
        path = self.spine / "owner.md"
        path.write_text("# Owner\n\nOwns alpha beta.\n", encoding="utf-8")
        payload = [{"id": "owner", "must": [["alpha"], ["beta"]]}]

        cold = self.search(payload, graph_depth=0)
        warm = self.search(payload, graph_depth=0)
        path.write_text(
            "# Owner\n\nOwns alpha beta with refreshed policy.\n",
            encoding="utf-8",
        )
        refreshed = self.search(payload, graph_depth=0)

        self.assertEqual("cold_build", cold.index_state)
        self.assertEqual("warm", warm.index_state)
        self.assertEqual("incremental_refresh", refreshed.index_state)
        self.assertGreaterEqual(refreshed.refreshed, 1)
        for outcome in (cold, warm, refreshed):
            self.assertEqual(
                {
                    "discovery_seconds",
                    "lock_wait_seconds",
                    "build_seconds",
                    "refresh_seconds",
                    "search_seconds",
                    "total_seconds",
                },
                set(outcome.timings),
            )
            self.assertGreaterEqual(
                outcome.timings["total_seconds"],
                outcome.timings["search_seconds"],
            )

    def test_incremental_refresh_removes_stale_normalized_tokens(self):
        path = self.spine / "owner.md"
        path.write_text("# Owner\n\nOwns alpha morphologytarget.\n", encoding="utf-8")
        first = self.search([
            {"id": "first", "must": [["alpha"], ["morphologytarget"]]}
        ], graph_depth=0)
        self.assertTrue(first.slices[0].outcome.direct_matches)

        path.write_text("# Owner\n\nOwns replacement content.\n", encoding="utf-8")
        second = self.search([
            {"id": "second", "must": [["alpha"], ["morphologytarget"]]}
        ], graph_depth=0)

        self.assertFalse(second.slices[0].outcome.direct_matches)
        self.assertGreaterEqual(second.refreshed, 1)

    def test_parallel_cold_searches_share_a_valid_index(self):
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns concurrent alpha beta.\n", encoding="utf-8"
        )
        payload = [{"id": "owner", "must": [["alpha"], ["beta"]]}]

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            outcomes = list(executor.map(lambda _: self.search(payload), range(8)))

        self.assertTrue(all(
            outcome.mode == "sqlite-fts5"
            and outcome.slices[0].outcome.direct_matches[0]["path"] == "owner.md"
            for outcome in outcomes
        ))

    def test_diagnostics_preserves_output_and_writes_sidecar(self):
        (self.spine / "owner.md").write_text(
            "# Owner\n\nOwns alpha beta.\n", encoding="utf-8"
        )
        sidecar = self.base / "telemetry.jsonl"
        environment = os.environ.copy()
        environment["SPECSPINE_CACHE_DIR"] = str(self.cache)
        environment["SPECSPINE_RETRIEVAL_TELEMETRY_FILE"] = str(sidecar)
        result = subprocess.run(
            [
                sys.executable,
                str(DIAGNOSTIC_PATH),
                "--telemetry",
                "full",
                str(self.spine),
                "--queries-json",
                json.dumps([{"id": "owner", "must": [["alpha"], ["beta"]]}]),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=10,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("SPECSPINE_RESULT", result.stdout)
        telemetry = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual("normalized", telemetry["ranking_system"])
        self.assertEqual(1, telemetry["slice_count"])


if __name__ == "__main__":
    unittest.main()
