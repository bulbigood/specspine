import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SEARCH_PATH = ROOT / "skills/specspine-extract/scripts/search_spine.py"
SPEC = importlib.util.spec_from_file_location("specspine_v2_extract", SEARCH_PATH)
assert SPEC and SPEC.loader
SEARCH = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SEARCH
SPEC.loader.exec_module(SEARCH)


INDEX = """# Architecture

**ID:** `project-architecture` · **Kind:** `index`

Example project.

## Architecture map

- [Payments](payments.md) — payments owner.

## Coverage

### Mapped

- [Payments](payments.md) — sufficiently mapped.

### Partially mapped

- Reporting — incomplete.

### Unmapped

- Forecasting.
"""

PAYMENTS = """# Payments

**ID:** `payment-processing` · **Kind:** `subsystem`
**Aliases:** Checkout

Owns provider payment retries and results.

## Responsibility

- owns payment state mutation.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-payment-idempotency** — Apply each provider result once.

## Open questions

- **OQ-retry-limit** — What retry bound is accepted?
<!-- specspine:semantic-ids:end -->

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `constrained-by` | [CON-policy-bound](policy.md) | Applies the system retry bound |
"""

POLICY = """# Retry policy

**ID:** `retry-policy` · **Kind:** `policy`

Defines the bounded retry policy.

## Responsibility

- owns retry bounds.

<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-policy-bound** — Retries are bounded.
<!-- specspine:semantic-ids:end -->
"""


class ExtractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.spine = Path(self.temporary.name)
        (self.spine / "README.md").write_text(INDEX, encoding="utf-8")
        (self.spine / "payments.md").write_text(PAYMENTS, encoding="utf-8")
        (self.spine / "policy.md").write_text(POLICY, encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def query(self, **overrides):
        payload = {
            "id": "change", "targets": ["payment-processing"],
            "terms": [["retry"]], "facets": ["failure"], "token_budget": 8000,
        }
        payload.update(overrides)
        return SEARCH.build_closure(self.spine, payload)

    def test_exact_id_owner_and_typed_closure(self):
        result = self.query()
        self.assertEqual("complete", result["closure_status"])
        self.assertEqual("payment-processing", result["primary"]["id"])
        self.assertEqual(["retry-policy"], [item["id"] for item in result["required"]])
        self.assertEqual(["CON-payment-idempotency", "CON-policy-bound"], [
            item["id"] for item in result["constraints"]
        ])

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

Defines the system retry ceiling.

## Responsibility

- owns the system retry ceiling.
"""
        (self.spine / "base.md").write_text(base, encoding="utf-8")
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

    def test_typed_closure_recognizes_hyphenated_facet_phrases(self):
        result = self.query(facets=["failure-boundary", "migration-lifecycle"])
        self.assertEqual(
            ["retry-policy"],
            [item["id"] for item in result["required"]],
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
            {"closure_status": "complete", "sources": source_paths},
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

    def test_includes_system_wide_claims_and_root_divergences(self):
        root_claims = """

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
| [CON-system-audit](README.md) | [OBS-audit-gap](README.md) | Audit history may be incomplete |
"""
        (self.spine / "README.md").write_text(
            INDEX + root_claims,
            encoding="utf-8",
        )
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
        self.assertEqual("no-match", result["closure_status"])

    def test_partial_coverage_cannot_be_complete(self):
        (self.spine / "README.md").write_text(
            INDEX.replace("### Mapped\n\n- [Payments]", "### Mapped\n\n- Other\n\n### Partially mapped\n\n- [Payments]"),
            encoding="utf-8",
        )
        result = self.query()
        self.assertEqual("partial", result["closure_status"])

    def test_truncation_is_explicit(self):
        (self.spine / "payments.md").write_text(
            PAYMENTS.replace(
                "- owns payment state mutation.",
                "- owns payment state mutation. " + ("extended context " * 2000),
            ),
            encoding="utf-8",
        )
        result = self.query(token_budget=128)
        self.assertEqual("truncated", result["closure_status"])
        self.assertTrue(result["omitted"])
        self.assertLessEqual(SEARCH._estimated_tokens(result), 128)

    def test_invalid_query_and_invalid_spine(self):
        self.assertEqual("invalid", SEARCH.build_closure(self.spine, {"unknown": 1})["closure_status"])
        (self.spine / "payments.md").write_text("# Legacy\n", encoding="utf-8")
        self.assertEqual("invalid", self.query()["closure_status"])

    def test_mechanical_error_makes_closure_invalid(self):
        (self.spine / "payments.md").write_text(
            PAYMENTS + "\n[Missing](missing.md)\n",
            encoding="utf-8",
        )
        result = self.query()
        self.assertEqual("invalid", result["closure_status"])
        self.assertEqual("invalid_spine", result["reason"])
        self.assertIn("BROKEN_LINK", [item.get("code") for item in result["omitted"]])

    def test_coverage_uses_full_relative_target_not_basename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "client").mkdir()
            (root / "server").mkdir()
            (root / "README.md").write_text(
                """# Architecture

**ID:** `project-architecture` · **Kind:** `index`

Example project.

## Architecture map

- [Client auth](client/auth.md) — client owner.
- [Server auth](server/auth.md) — server owner.

## Coverage

### Mapped

- [Client auth](client/auth.md) — sufficiently mapped.

### Partially mapped

- None.

### Unmapped

- [Server auth](server/auth.md) — server failure behavior is unknown.
""",
                encoding="utf-8",
            )
            for area in ("client", "server"):
                (root / area / "auth.md").write_text(
                    f"""# {area.title()} auth

**ID:** `{area}-auth` · **Kind:** `component`

Owns {area} authentication.

## Responsibility

- owns {area} authentication.
""",
                    encoding="utf-8",
                )
            result = SEARCH.build_closure(root, {
                "targets": ["server-auth"],
                "terms": [],
                "facets": [],
                "token_budget": 8000,
            })
            self.assertEqual("partial", result["closure_status"])
            self.assertEqual("unmapped", result["coverage"])

    def test_cli_is_deterministic_machine_json(self):
        payload = {"targets": ["payment-processing"], "terms": [], "facets": [], "token_budget": 8000}
        command = [sys.executable, str(SEARCH_PATH), str(self.spine), "--query-json", json.dumps(payload)]
        first = subprocess.run(command, text=True, capture_output=True, check=False)
        second = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual("complete", json.loads(first.stdout)["closure_status"])


if __name__ == "__main__":
    unittest.main()
