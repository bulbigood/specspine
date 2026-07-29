import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SEARCH_PATH = ROOT / "skills/specspine-extract/scripts/search_spine.py"
SPEC = importlib.util.spec_from_file_location("specspine_v3_extract", SEARCH_PATH)
assert SPEC and SPEC.loader
SEARCH = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SEARCH
SPEC.loader.exec_module(SEARCH)
INDEXER_PATH = ROOT / "shared/scripts/rebuild_indexes.py"
INDEXER_SPEC = importlib.util.spec_from_file_location(
    "specspine_v3_indexer", INDEXER_PATH
)
assert INDEXER_SPEC and INDEXER_SPEC.loader
INDEXER = importlib.util.module_from_spec(INDEXER_SPEC)
sys.modules[INDEXER_SPEC.name] = INDEXER
INDEXER_SPEC.loader.exec_module(INDEXER)


INDEX = """# Architecture

**ID:** `project-architecture` · **Kind:** `index`

Example project.

## Architecture map

- [Payments](payments.md) — payments owner.
- [specspine.json](specspine.json)

"""

PAYMENTS = """# Payments

**ID:** `payment-processing` · **Kind:** `subsystem`
**Aliases:** Checkout

**Summary:** Owns provider payment retries and results.

## Responsibility

- owns payment state mutation.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-payment-idempotency** — Apply each provider result once.

## Open questions

- **OQ-retry-limit** — What retry bound is accepted?

## Observed

- **OBS-provider-retries** — The current provider client retries failures.

## Inferred

- **INF-provider-backoff** — Retry delays appear to use bounded backoff.
<!-- specspine:semantic-ids:end -->

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `constrained-by` | [CON-policy-bound](policy.md) | Applies the system retry bound |
"""

POLICY = """# Retry policy

**ID:** `retry-policy` · **Kind:** `policy`

**Summary:** Defines the bounded retry policy.

## Responsibility

- owns retry bounds.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-policy-bound** — Retries are bounded.

## Verification

- **VER-policy-bound** — A retry sequence stops at its configured bound.
<!-- specspine:semantic-ids:end -->
"""


class ExtractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.spine = Path(self.temporary.name)
        (self.spine / "_INDEX.md").write_text(INDEX, encoding="utf-8")
        (self.spine / "payments.md").write_text(PAYMENTS, encoding="utf-8")
        (self.spine / "policy.md").write_text(POLICY, encoding="utf-8")
        self.write_manifest()

    def tearDown(self):
        self.temporary.cleanup()

    def query(self, **overrides):
        INDEXER.rebuild(self.spine)
        payload = {
            "id": "change", "targets": ["payment-processing"],
            "terms": [["retry"]], "facets": ["failure"], "token_budget": 8000,
        }
        payload.update(overrides)
        return SEARCH.build_closure(self.spine, payload)

    def write_manifest(self, payment_status="partial", assets=None):
        facets = [
            "architecture", "behavior", "interfaces", "data", "failure",
            "quality", "verification",
        ]
        payload = {
            "specspine": 3,
            "project": "test",
            "implementation_freedom": "contract-equivalent",
            "areas": [
                {
                    "owner": "payment-processing",
                    "facets": {
                        facet: (
                            payment_status
                            if facet in {
                                "architecture", "behavior", "failure",
                                "verification",
                            }
                            else "not-applicable"
                        )
                        for facet in facets
                    },
                    "blockers": [],
                },
                {
                    "owner": "retry-policy",
                    "facets": {
                        facet: (
                            "complete"
                            if facet in {"architecture", "behavior", "verification"}
                            else "not-applicable"
                        )
                        for facet in facets
                    },
                    "blockers": [],
                },
            ],
            "assets": assets or [],
        }
        (self.spine / "specspine.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def test_exact_id_owner_and_typed_closure(self):
        result = self.query()
        self.assertEqual("incomplete", result["status"]["code"])
        self.assertEqual("payment-processing", result["primary"]["id"])
        self.assertEqual(["retry-policy"], [item["id"] for item in result["required"]])
        self.assertEqual(["CON-payment-idempotency", "CON-policy-bound"], [
            item["id"] for item in result["constraints"]
        ])
        self.assertEqual("partial", result["status"]["facets"]["architecture"])
        self.assertEqual(
            "contract-equivalent",
            result["status"]["implementation_freedom"],
        )
        self.assertEqual(["failure"], result["status"]["requested_facets"])
        self.assertEqual(
            ["failure"],
            result["status"]["incomplete_requested_facets"],
        )

    def test_returns_observations_and_inferences_as_separate_orientation(self):
        result = self.query()

        self.assertEqual(
            ["OBS-provider-retries"],
            [item["id"] for item in result["observations"]],
        )
        self.assertEqual(
            ["INF-provider-backoff"],
            [item["id"] for item in result["inferences"]],
        )

    def test_returns_v3_normative_claims_and_computed_status(self):
        self.write_manifest(payment_status="complete")
        (self.spine / "payments.md").write_text(
            PAYMENTS.replace(
                "## Constraints",
                """## Requirements

- **REQ-payment-result** — Payment MUST expose a terminal result.

## Guarantees

- **GUA-payment-idempotency** — Duplicate results MUST be harmless.

## Invariants

- **INV-payment-identity** — Payment identity MUST remain stable.

## Quality constraints

- **QLT-payment-latency** — Result SHOULD be visible within one second.

## Verification

- **VER-payment-duplicate** — Replaying a result leaves one transition.

## Constraints""",
            ),
            encoding="utf-8",
        )
        result = self.query()
        self.assertEqual("ready", result["status"]["code"])
        self.assertEqual(["REQ-payment-result"], [
            item["id"] for item in result["requirements"]
        ])
        self.assertEqual(["GUA-payment-idempotency"], [
            item["id"] for item in result["guarantees"]
        ])
        self.assertEqual(["INV-payment-identity"], [
            item["id"] for item in result["invariants"]
        ])
        self.assertEqual(["QLT-payment-latency"], [
            item["id"] for item in result["quality_constraints"]
        ])
        self.assertEqual(["VER-payment-duplicate", "VER-policy-bound"], [
            item["id"] for item in result["verification"]
        ])

    def test_returns_owned_machine_readable_contract_assets(self):
        contracts = self.spine / "contracts"
        contracts.mkdir()
        (contracts / "payments.openapi.yaml").write_text(
            "openapi: 3.1.0\n", encoding="utf-8"
        )
        (self.spine / "payments.md").write_text(
            PAYMENTS
            + "\n## Interfaces\n\n"
            + "[Payment API](contracts/payments.openapi.yaml) is normative.\n",
            encoding="utf-8",
        )
        self.write_manifest(assets=[{
            "path": "contracts/payments.openapi.yaml",
            "owner": "payment-processing",
            "role": "interface-contract",
            "format": "openapi-3.1",
            "normative": True,
            "verifies": [],
        }])
        result = self.query()
        self.assertEqual(
            ["contracts/payments.openapi.yaml"],
            [item["path"] for item in result["assets"]],
        )

    def test_manifest_blocker_controls_status(self):
        manifest = json.loads((self.spine / "specspine.json").read_text())
        manifest["areas"][0]["blockers"] = ["OQ-retry-limit"]
        (self.spine / "specspine.json").write_text(json.dumps(manifest))

        result = self.query()

        self.assertEqual("blocked", result["status"]["code"])
        self.assertEqual(["OQ-retry-limit"], result["status"]["blockers"])

    def test_spine_relative_query_path_selects_spine_document(self):
        result = self.query(
            targets=[],
            paths=["payments.md"],
            terms=[],
            facets=[],
        )
        self.assertEqual("payment-processing", result["primary"]["id"])

    def test_typed_closure_follows_required_relationships_to_depth_two(self):
        base = """# Base policy

**ID:** `base-policy` · **Kind:** `policy`

**Summary:** Defines the system retry ceiling.

## Responsibility

- owns the system retry ceiling.
"""
        (self.spine / "base.md").write_text(base, encoding="utf-8")
        manifest = json.loads((self.spine / "specspine.json").read_text())
        manifest["areas"].append({
            "owner": "base-policy",
            "facets": {
                facet: (
                    "complete"
                    if facet in {"architecture", "behavior"}
                    else "partial"
                    if facet == "verification"
                    else "not-applicable"
                )
                for facet in SEARCH.CHECKER.FACET_NAMES
            },
            "blockers": [],
        })
        (self.spine / "specspine.json").write_text(json.dumps(manifest))
        (self.spine / "policy.md").write_text(
            POLICY + """

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `constrained-by` | [Base policy](base.md) | Applies the system ceiling |
""",
            encoding="utf-8",
        )
        result = self.query()
        self.assertEqual(
            ["base-policy", "retry-policy"],
            [item["id"] for item in result["required"]],
        )

    def test_typed_closure_recognizes_known_facets_inside_task_phrases(self):
        result = self.query(facets=["availability failure", "migration lifecycle"])
        self.assertEqual(
            ["retry-policy"],
            [item["id"] for item in result["required"]],
        )
        self.assertEqual(
            ["behavior", "data", "failure"],
            result["status"]["requested_facets"],
        )

    def test_typed_closure_recognizes_hyphenated_facet_phrases(self):
        result = self.query(facets=["failure-boundary", "migration-lifecycle"])
        self.assertEqual(
            ["retry-policy"],
            [item["id"] for item in result["required"]],
        )

    def test_requested_not_applicable_facet_is_not_silently_complete(self):
        result = self.query(facets=["data-mutation"])

        self.assertEqual(["data"], result["status"]["requested_facets"])
        self.assertEqual(
            ["data"],
            result["status"]["incomplete_requested_facets"],
        )

    def test_closure_returns_complete_files_with_named_separators(self):
        result = self.query()
        concatenated = result["concatenated_files"]
        self.assertTrue(
            concatenated.startswith(
                "The following content is the complete, concatenated content"
            )
        )
        self.assertEqual(
            result["sources"],
            result["concatenated_source_paths"],
        )
        self.assertEqual([], result["concatenated_files_omitted_paths"])
        self.assertNotIn("concatenated_files_truncated", result)
        for relative in result["concatenated_source_paths"]:
            self.assertIn(
                f'<<<SPECSPINE_FILE path="{relative}">>>',
                concatenated,
            )
            self.assertIn(
                (self.spine / relative).read_text(encoding="utf-8").rstrip("\n"),
                concatenated,
            )

    def test_concatenation_names_only_files_omitted_by_budget(self):
        (self.spine / "small.md").write_text("# Small\n", encoding="utf-8")
        (self.spine / "large.md").write_text(
            "# Large\n\n" + ("large context " * 2000),
            encoding="utf-8",
        )
        source_paths = ["small.md", "large.md"]
        result = SEARCH._attach_concatenated_files(
            self.spine.resolve(),
            {"status": {"code": "ready"}, "sources": source_paths},
            source_paths,
            256,
        )

        self.assertEqual(["small.md"], result["concatenated_source_paths"])
        self.assertEqual(
            ["large.md"],
            result["concatenated_files_omitted_paths"],
        )
        self.assertIn('path="small.md"', result["concatenated_files"])
        self.assertNotIn('path="large.md"', result["concatenated_files"])
        self.assertNotIn("concatenated_files_truncated", result)
        self.assertLessEqual(SEARCH._estimated_tokens(result), 256)

    def test_includes_system_wide_claims_and_divergences_from_related_owner(self):
        system_claims = """# System policy

**ID:** `system-policy` · **Kind:** `system`

**Summary:** Defines system-wide audit policy.

## Responsibility

- owns system-wide audit requirements.

<!-- specspine:evidence-baseline source=commit-abc123; inspected=2026-07-25 -->
<!-- specspine:semantic-ids:begin -->
## System-wide constraints

- **CON-system-audit** — Payment mutations are audited.

## Observed

- **OBS-audit-gap** — Some payment mutations lack audit evidence.
<!-- specspine:semantic-ids:end -->

## Known divergences

| Intended | Observed | Consequence |
|---|---|---|
| [CON-system-audit](system.md) | [OBS-audit-gap](system.md) | Audit history may be incomplete |
"""
        (self.spine / "system.md").write_text(system_claims, encoding="utf-8")
        (self.spine / "payments.md").write_text(
            PAYMENTS.replace(
                "| `constrained-by` | [CON-policy-bound](policy.md) | Applies the system retry bound |",
                "| `constrained-by` | [CON-policy-bound](policy.md) | Applies the system retry bound |\n"
                "| `constrained-by` | [CON-system-audit](system.md) | Applies the system audit policy |",
            ),
            encoding="utf-8",
        )
        manifest = json.loads((self.spine / "specspine.json").read_text())
        manifest["areas"].append({
            "owner": "system-policy",
            "facets": {
                name: (
                    "partial"
                    if name in {"architecture", "behavior", "failure", "verification"}
                    else "not-applicable"
                )
                for name in SEARCH.CHECKER.FACET_NAMES
            },
            "blockers": [],
        })
        (self.spine / "specspine.json").write_text(json.dumps(manifest))
        result = self.query()
        self.assertIn(
            "CON-system-audit",
            [item["id"] for item in result["constraints"]],
        )
        self.assertEqual(
            ["CON-system-audit"],
            [item["intended"] for item in result["known_divergences"]],
        )

    def test_retrieves_by_alias_and_responsibility(self):
        result = self.query(targets=[], terms=[["Checkout"], ["state mutation"]])
        self.assertEqual("payment-processing", result["primary"]["id"])

    def test_query_group_uses_strongest_synonym_match(self):
        score = SEARCH._query_group_score(
            ["state mutation", "Checkout"],
            {
                "title": "payments",
                "alias": "checkout",
                "summary": "",
                "responsibility": "state mutation",
                "body": "",
            },
        )
        self.assertEqual(110.0, score)

    def test_query_group_normalizes_diacritics_and_symmetric_word_forms(self):
        cases = (
            ("cafe", "café"),
            ("café", "cafe\u0301"),
            ("ежик", "ёжик"),
            ("конфликтов", "конфликт"),
            ("retries", "retry"),
            ("покуп", "покупка"),
        )
        for query, document in cases:
            with self.subTest(query=query, document=document):
                self.assertEqual(
                    120.0,
                    SEARCH._query_group_score(
                        [query],
                        {
                            "title": document,
                            "alias": "",
                            "summary": "",
                            "responsibility": "",
                            "body": "",
                        },
                    ),
                )

    def test_query_group_rejects_infixes_and_one_character_cjk_fragments(self):
        searchable = {
            "title": "catalog 水位线",
            "alias": "",
            "summary": "",
            "responsibility": "",
            "body": "",
        }
        self.assertEqual(0.0, SEARCH._query_group_score(["log"], searchable))
        self.assertEqual(0.0, SEARCH._query_group_score(["位"], searchable))
        self.assertEqual(120.0, SEARCH._query_group_score(["水位线"], searchable))

    def test_multilingual_corpus_prefers_owner_over_title_and_body_decoys(self):
        spine = (
            ROOT
            / "tests/retrieval-corpora/corpora/mobile-app-ru-01/project/specspine"
        )
        cases = (
            (
                [
                    ["ссылка", "URI", "redirect"],
                    ["билет", "билета"],
                    ["разбор", "разборщик", "нормализует"],
                    ["внешний", "внешняя"],
                    ["маршрут", "навигация"],
                ],
                "deep-links.md",
            ),
            (
                [
                    ["регистрация", "зарегистрировать"],
                    ["устройство", "установки"],
                    ["push-токен", "токен доставки"],
                    ["подтверждение", "подтверждения"],
                    ["идемпотентный", "идемпотентен"],
                ],
                "push-notifications.md",
            ),
        )
        for terms, expected in cases:
            with self.subTest(expected=expected):
                result = SEARCH.build_closure(
                    spine,
                    {
                        "targets": [],
                        "semantic_ids": [],
                        "paths": [],
                        "terms": terms,
                        "facets": [],
                        "token_budget": 8000,
                    },
                )
                self.assertEqual(expected, result["primary"]["path"])

    def test_skill_forbids_generated_cross_language_synonyms(self):
        instructions = (
            ROOT / "skills/specspine-extract/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "Do not generate translated or cross-language synonyms",
            instructions,
        )

    def test_task_context_covers_query_with_source_excerpts(self):
        result = self.query()
        context = result["task_context"]
        self.assertTrue(context["complete"])
        self.assertFalse(context["uncovered_query_groups"])
        self.assertFalse(context["suggested_paths"])
        payment = next(
            item
            for item in context["documents"]
            if item["id"] == "payment-processing"
        )
        self.assertEqual("primary", payment["role"])
        self.assertIn("payment state mutation", payment["responsibility"])
        self.assertTrue(payment["excerpts"])

    def test_no_match_is_explicit(self):
        result = self.query(targets=[], terms=[["absent"]])
        self.assertEqual("no-match", result["status"]["code"])

    def test_incomplete_facets_cannot_be_ready(self):
        result = self.query()
        self.assertEqual("incomplete", result["status"]["code"])

    def test_truncation_is_explicit(self):
        (self.spine / "payments.md").write_text(
            PAYMENTS.replace(
                "- owns payment state mutation.",
                "- owns payment state mutation. " + ("extended context " * 2000),
            ),
            encoding="utf-8",
        )
        result = self.query(token_budget=128)
        self.assertEqual("truncated", result["status"]["code"])
        self.assertEqual("incomplete", result["status"]["area_code"])
        self.assertEqual(
            "contract-equivalent",
            result["status"]["implementation_freedom"],
        )
        self.assertEqual(["failure"], result["status"]["requested_facets"])
        self.assertTrue(result["omitted"])
        self.assertLessEqual(SEARCH._estimated_tokens(result), 128)

    def test_invalid_query_and_invalid_spine(self):
        self.assertEqual("invalid", SEARCH.build_closure(self.spine, {"unknown": 1})["status"]["code"])
        (self.spine / "payments.md").write_text("# Invalid\n", encoding="utf-8")
        self.assertEqual("invalid", self.query()["status"]["code"])

    def test_mechanical_error_makes_closure_invalid(self):
        (self.spine / "payments.md").write_text(
            PAYMENTS + "\n[Missing](missing.md)\n",
            encoding="utf-8",
        )
        result = self.query()
        self.assertEqual("invalid", result["status"]["code"])
        self.assertEqual("invalid_spine", result["status"]["reason"])
        self.assertIn("BROKEN_LINK", [item.get("code") for item in result["omitted"]])

    def test_manifest_status_uses_document_id_not_basename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "client").mkdir()
            (root / "server").mkdir()
            (root / "_INDEX.md").write_text(
                """# Architecture

**ID:** `project-architecture` · **Kind:** `index`

Example project.

## Architecture map

- [Client auth](client/auth.md) — client owner.
- [Server auth](server/auth.md) — server owner.

""",
                encoding="utf-8",
            )
            for area in ("client", "server"):
                (root / area / "auth.md").write_text(
                    f"""# {area.title()} auth

**ID:** `{area}-auth` · **Kind:** `component`

**Summary:** Owns {area} authentication.

## Responsibility

- owns {area} authentication.
""",
                    encoding="utf-8",
                )
            facets = {
                name: (
                    "not-applicable"
                    if name in {"interfaces", "data", "quality"}
                    else "missing"
                )
                for name in SEARCH.CHECKER.FACET_NAMES
            }
            (root / "specspine.json").write_text(json.dumps({
                "specspine": 3,
                "project": "test",
                "implementation_freedom": "contract-equivalent",
                "areas": [
                    {
                        "owner": "client-auth",
                        "facets": {**facets, "architecture": "complete"},
                        "blockers": [],
                    },
                    {
                        "owner": "server-auth",
                        "facets": {**facets, "architecture": "missing"},
                        "blockers": [],
                    },
                ],
                "assets": [],
            }), encoding="utf-8")
            INDEXER.rebuild(root)
            result = SEARCH.build_closure(root, {
                "targets": ["server-auth"],
                "terms": [],
                "facets": [],
                "token_budget": 8000,
            })
            self.assertEqual("incomplete", result["status"]["code"])
            self.assertEqual("missing", result["status"]["facets"]["architecture"])

    def test_cli_is_deterministic_machine_json(self):
        INDEXER.rebuild(self.spine)
        payload = {"targets": ["payment-processing"], "terms": [], "facets": [], "token_budget": 8000}
        command = [sys.executable, str(SEARCH_PATH), str(self.spine), "--query-json", json.dumps(payload)]
        first = subprocess.run(command, text=True, capture_output=True, check=False)
        second = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual("incomplete", json.loads(first.stdout)["status"]["code"])


if __name__ == "__main__":
    unittest.main()
