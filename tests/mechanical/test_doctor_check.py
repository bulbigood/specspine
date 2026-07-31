import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "shared/scripts/check_spine.py"
SPEC = importlib.util.spec_from_file_location("specspine_v4_check", MODULE_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


INDEX = """# Architecture

**ID:** `project-architecture` · **Kind:** `index`

## Contents

- [README.md](README.md)
- [Payments](payments.md) — owns payments.
- [specspine.json](specspine.json)

"""

PAYMENTS = """# Payments

**ID:** `payments` · **Kind:** `subsystem`
**Aliases:** Checkout

**Summary:** Owns payment attempts and results.

## Responsibility

- owns payment state.

<!-- specspine:evidence-baseline source=commit-abc123; inspected=2026-07-25 -->
<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-payment-idempotency** — A result is applied once.

## Observed

- **OBS-provider-duplicates** — Provider events are not deduplicated.
  Evidence: `src/payments/provider.ts`.
<!-- specspine:semantic-ids:end -->

## Known divergences

| Intended | Observed | Consequence |
|---|---|---|
| [CON-payment-idempotency](payments.md) | [OBS-provider-duplicates](payments.md) | A transition may apply twice |
"""

GRAPH_RENDERING = """# Graph rendering

**ID:** `graph-rendering` · **Kind:** `component`

**Summary:** Renders prepared series through a reusable graph lifecycle.

## Responsibility

Records the observed graph-rendering boundary.

<!-- specspine:evidence-baseline source=commit-abc123; inspected=2026-07-25 -->
<!-- specspine:semantic-ids:begin -->
## Observed

- **OBS-payment-graph-flow** — Payments provide result series to graph rendering.
  Evidence: `src/payments/provider.ts`.
<!-- specspine:semantic-ids:end -->
"""


class DoctorCheckerV4Tests(unittest.TestCase):
    def spine(self, payment=PAYMENTS, index=INDEX, extra=None, manifest=None):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "README.md").write_text("# SpecSpine\n", encoding="utf-8")
        (root / "_INDEX.md").write_text(index, encoding="utf-8")
        (root / "payments.md").write_text(payment, encoding="utf-8")
        for name, content in (extra or {}).items():
            (root / name).write_text(content, encoding="utf-8")
        if manifest is None:
            owners = ["payments"]
            if extra:
                owners.extend(
                    match.group(1)
                    for content in extra.values()
                    for line in content.splitlines()
                    if (match := CHECKER.IDENTITY_RE.fullmatch(line))
                )
            manifest = {
                "specspine": 4,
                "project": "test",
                "implementation_freedom": "contract-equivalent",
                "areas": [
                    {
                        "owner": owner,
                        "facets": {
                            name: (
                                "complete"
                                if name in {"architecture", "behavior", "failure"}
                                else "partial"
                                if name == "verification"
                                else "not-applicable"
                            )
                            for name in CHECKER.FACET_NAMES
                        },
                        "blockers": [],
                    }
                    for owner in owners
                ],
                "assets": [],
            }
        (root / "specspine.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        self.addCleanup(temporary.cleanup)
        return root

    def codes(self, root):
        return {item.code for item in CHECKER.check(root)}

    def test_accepts_strict_v4_spine(self):
        self.assertEqual([], [item for item in CHECKER.check(self.spine()) if item.severity == "error"])

    def test_accepts_mapping_frontier_and_obs_backed_edge(self):
        index = INDEX.replace(
            "- [Payments](payments.md) — owns payments.",
            "- [Graph rendering](graph.md) — renders result series.\n"
            "- [Payments](payments.md) — owns payments.",
        )
        root = self.spine(extra={"graph.md": GRAPH_RENDERING}, index=index)
        manifest = json.loads((root / "specspine.json").read_text())
        manifest["mapping"] = {
            "frontier": [{
                "id": "graph-tooltip",
                "from_owner": "graph-rendering",
                "title": "Graph tooltip",
                "question": "Which contextual interaction boundary does it own?",
                "reason": "Graph rendering delegates a distinct interaction.",
                "seed_paths": ["src/graph/tooltip.ts"],
            }],
            "observed_edges": [{
                "source_owner": "payments",
                "target_owner": "graph-rendering",
                "observation": "OBS-payment-graph-flow",
            }],
        }
        (root / "specspine.json").write_text(json.dumps(manifest))
        self.assertEqual(
            [],
            [item for item in CHECKER.check(root) if item.severity == "error"],
        )

    def test_rejects_stale_frontier_and_invalid_observed_edge(self):
        root = self.spine()
        manifest = json.loads((root / "specspine.json").read_text())
        manifest["mapping"] = {
            "frontier": [{
                "id": "payments",
                "from_owner": "missing-owner",
                "title": "Duplicate owner",
                "question": "Should this exist?",
                "reason": "Invalid fixture.",
                "seed_paths": ["../outside.ts"],
            }],
            "observed_edges": [{
                "source_owner": "payments",
                "target_owner": "payments",
                "observation": "CON-payment-idempotency",
            }],
        }
        (root / "specspine.json").write_text(json.dumps(manifest))
        codes = self.codes(root)
        self.assertIn("MANIFEST_FRONTIER_ID", codes)
        self.assertIn("MANIFEST_FRONTIER_OWNER", codes)
        self.assertIn("MANIFEST_FRONTIER_PATH", codes)
        self.assertIn("MANIFEST_OBSERVED_EDGE_OWNER", codes)
        self.assertIn("MANIFEST_OBSERVED_EDGE_OBSERVATION", codes)

    def test_default_order_prioritizes_divergence_before_evidence(self):
        order = list(CHECKER.DEFAULT_HEADINGS)
        self.assertLess(order.index("relationships"), order.index("requirements"))
        self.assertLess(order.index("known-divergences"), order.index("observed"))
        self.assertLess(order.index("observed"), order.index("implementation"))

    def test_rejects_html_disclosure_in_canonical_markdown(self):
        payment = PAYMENTS + "\n<details>\n<summary>Evidence</summary>\n</details>\n"
        self.assertIn("SEMANTIC_DISCLOSURE", self.codes(self.spine(payment=payment)))

        fenced = PAYMENTS + "\n```html\n<details></details>\n```\n"
        self.assertNotIn("SEMANTIC_DISCLOSURE", self.codes(self.spine(payment=fenced)))

    def test_candidate_may_create_integration_indexed_directory(self):
        root = self.spine()
        staging_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(staging_temporary.cleanup)
        staging = Path(staging_temporary.name)
        candidate = staging / "shipping" / "shipping.md"
        candidate.parent.mkdir(parents=True)
        candidate.write_text(
            PAYMENTS.replace("Payments", "Shipping")
            .replace("payments", "shipping")
            .replace("payment", "shipping")
            .replace(
                "OBS-provider-duplicates",
                "OBS-shipping-provider-duplicates",
            ),
            encoding="utf-8",
        )
        findings = CHECKER.check_candidates(root, staging)
        self.assertNotIn(
            "DIRECTORY_INDEX_MISSING",
            {item.code for item in findings},
        )
        self.assertEqual([], [item for item in findings if item.severity == "error"])

    def test_accepts_localized_presentation_headings(self):
        manifest = {
            "specspine": 4,
            "project": "test",
            "implementation_freedom": "contract-equivalent",
            "presentation": {
                "profile": 1,
                "language": "ru",
                "headings": {
                    "responsibility": "Ответственность",
                    "constraints": "Ограничения",
                    "observed": "Наблюдаемое",
                    "known-divergences": "Известные расхождения",
                },
            },
            "areas": [{
                "owner": "payments",
                "facets": {
                    name: (
                        "complete"
                        if name in {"architecture", "behavior", "failure"}
                        else "partial"
                        if name == "verification"
                        else "not-applicable"
                    )
                    for name in CHECKER.FACET_NAMES
                },
                "blockers": [],
            }],
            "assets": [],
        }
        localized = (
            PAYMENTS
            .replace("## Responsibility", "## Ответственность")
            .replace("## Constraints", "## Ограничения")
            .replace("## Observed", "## Наблюдаемое")
            .replace("## Known divergences", "## Известные расхождения")
        )
        errors = [
            item
            for item in CHECKER.check(self.spine(localized, manifest=manifest))
            if item.severity == "error"
        ]
        self.assertEqual([], errors)

    def test_rejects_semantically_ambiguous_presentation(self):
        root = self.spine()
        manifest = json.loads((root / "specspine.json").read_text())
        manifest["presentation"] = {
            "profile": 1,
            "language": "en",
            "headings": {
                "responsibility": "Contract",
                "interfaces": "Contract",
            },
        }
        (root / "specspine.json").write_text(json.dumps(manifest))
        self.assertIn("MANIFEST_PRESENTATION", self.codes(root))

    def test_doctor_index_template_is_valid(self):
        template = (
            Path(__file__).parents[2]
            / "skills/specspine-doctor/assets/templates/spine-index.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn("## How to use this Spine", template)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        readme = (
            Path(__file__).parents[2]
            / "skills/specspine-doctor/assets/templates/root-spine-readme.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "This directory contains the project's long-lived architectural intent",
            readme,
        )
        (root / "README.md").write_text(readme, encoding="utf-8")
        (root / "_INDEX.md").write_text(template, encoding="utf-8")
        manifest = (
            Path(__file__).parents[2]
            / "skills/specspine-doctor/assets/templates/specspine.json"
        ).read_text(encoding="utf-8")
        (root / "specspine.json").write_text(manifest, encoding="utf-8")
        self.assertEqual(
            [],
            [item for item in CHECKER.check(root) if item.severity == "error"],
        )

    def test_manifest_schema_matches_checker_vocabulary(self):
        schema = json.loads(
            (
                Path(__file__).parents[2]
                / "shared/references/specspine.schema.json"
            ).read_text(encoding="utf-8")
        )
        definitions = schema["$defs"]
        self.assertEqual(
            CHECKER.MANIFEST_KEYS,
            set(schema["properties"]),
        )
        self.assertEqual(CHECKER.FACET_VALUES, set(definitions["facet"]["enum"]))
        self.assertEqual(
            CHECKER.FACET_NAME_SET,
            set(definitions["facets"]["properties"]),
        )
        self.assertEqual(
            CHECKER.ASSET_ROLES,
            set(definitions["asset"]["properties"]["role"]["enum"]),
        )

    def test_ignores_links_and_semantic_ids_in_fenced_examples(self):
        fenced = """

```markdown
[Missing](missing.md)
- **CON-example-only** — This is not a canonical statement.
- **OBS-example-only** — This is not repository evidence.
```
"""
        root = self.spine(index=INDEX + fenced)
        codes = self.codes(root)
        self.assertNotIn("BROKEN_LINK", codes)
        self.assertNotIn("ID_OUTSIDE_REGION", codes)

        repository_codes = {
            item.code
            for item in CHECKER.check(root, repository_root=root)
        }
        self.assertNotIn("OBS_EVIDENCE_MISSING", repository_codes)

    def test_missing_identity_is_rejected(self):
        root = self.spine(payment="# Payments\n\n## Responsibility\n\n- owns payments.\n")
        self.assertTrue({"MISSING_DOCUMENT_ID", "MISSING_SUMMARY"} <= self.codes(root))

    def test_duplicate_document_ids_are_errors(self):
        other = PAYMENTS.replace("# Payments", "# Other").replace("payments` ·", "payments` ·")
        root = self.spine(extra={"other.md": other}, index=INDEX.replace(
            "- [Payments](payments.md) — owns payments.",
            "- [Payments](payments.md) — owns payments.\n- [Other](other.md) — duplicate fixture.",
        ))
        self.assertIn("DUPLICATE_DOCUMENT_ID", self.codes(root))

    def test_kind_extensions_are_accepted_and_unknown_kind_warns(self):
        root = self.spine(payment=PAYMENTS.replace("`subsystem`", "`x-control-plane`"))
        self.assertNotIn("UNKNOWN_KIND", self.codes(root))
        root = self.spine(payment=PAYMENTS.replace("`subsystem`", "`service`"))
        self.assertIn("UNKNOWN_KIND", self.codes(root))

    def test_validates_typed_target_duplicate_and_cycles(self):
        relationship = """

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `contains` | [Payments](payments.md) | Self composition |
"""
        root = self.spine(payment=PAYMENTS + relationship)
        self.assertIn("RELATIONSHIP_CYCLE", self.codes(root))

    def test_validates_semantic_relationship_target(self):
        relationship = """

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `constrained-by` | [CON-missing](payments.md) | Missing statement |
"""
        root = self.spine(payment=PAYMENTS + relationship)
        self.assertIn("UNKNOWN_RELATION_STATEMENT", self.codes(root))

    def test_requires_manifest(self):
        root = self.spine()
        (root / "specspine.json").unlink()
        self.assertIn("MANIFEST_MISSING", self.codes(root))

    def test_rejects_legacy_coverage_section(self):
        root = self.spine(index=INDEX + "\n## Coverage\n\n- Mapped.\n")
        self.assertIn("COMPLETENESS_IN_MARKDOWN", self.codes(root))

    def test_rejects_legacy_semantic_definition(self):
        root = self.spine(
            payment=PAYMENTS
            + "\n**ID:** `OBS-legacy-payment` · **Status:** `OBS`\n\n"
            + "Legacy observation text.\n"
        )
        self.assertIn("LEGACY_SEMANTIC_DEFINITION", self.codes(root))

    def test_map_mode_validates_observation_evidence_paths(self):
        root = self.spine()
        repository = root / "repository"
        repository.mkdir()

        codes = {
            item.code
            for item in CHECKER.check(root, repository_root=repository)
        }

        self.assertIn("EVIDENCE_PATH_MISSING", codes)

    def test_map_mode_requires_observation_evidence_baseline(self):
        root = self.spine(
            payment=PAYMENTS.replace(
                "<!-- specspine:evidence-baseline "
                "source=commit-abc123; inspected=2026-07-25 -->\n",
                "",
            )
        )

        codes = {
            item.code
            for item in CHECKER.check(root, repository_root=root)
        }

        self.assertIn("EVIDENCE_BASELINE_MISSING", codes)

    def test_map_mode_requires_observation_evidence_clause(self):
        root = self.spine(
            payment=PAYMENTS.replace(
                "  Evidence: `src/payments/provider.ts`.\n",
                "",
            )
        )

        codes = {
            item.code
            for item in CHECKER.check(root, repository_root=root)
        }

        self.assertIn("OBS_EVIDENCE_MISSING", codes)

    def test_rejects_semantic_definition_without_same_line_text(self):
        root = self.spine(
            payment=PAYMENTS.replace(
                "- **OBS-provider-duplicates** — Provider events are not deduplicated.",
                "- **OBS-provider-duplicates** —\n  Provider events are not deduplicated.",
            )
        )

        self.assertIn("MALFORMED_ID_DEFINITION", self.codes(root))

    def test_observation_definition_belongs_only_under_observed(self):
        root = self.spine(
            payment=PAYMENTS.replace(
                "## Observed\n\n"
                "- **OBS-provider-duplicates**",
                "## Responsibility\n\n"
                "- **OBS-provider-duplicates**",
            )
        )

        self.assertIn("ID_SECTION", self.codes(root))

    def test_validates_divergence_statement_kinds(self):
        root = self.spine(payment=PAYMENTS.replace(
            "[CON-payment-idempotency](payments.md)",
            "[OBS-provider-duplicates](payments.md)",
            1,
        ))
        self.assertIn("DIVERGENCE_INTENDED_KIND", self.codes(root))

    def test_accepts_v4_normative_claims_and_relations(self):
        normative = PAYMENTS.replace(
            "## Constraints",
            """## Requirements

- **REQ-payment-result** — A payment MUST expose its terminal result.

## Guarantees

- **GUA-payment-idempotency** — Duplicate results MUST be harmless.

## Invariants

- **INV-payment-identity** — Payment identity MUST remain stable.

## Quality constraints

- **QLT-payment-latency** — A result SHOULD be visible within one second.

## Verification

- **VER-payment-duplicate** — Replaying a result leaves one transition.

## Constraints""",
        )
        self.assertEqual(
            [],
            [
                item
                for item in CHECKER.check(self.spine(payment=normative))
                if item.severity == "error"
            ],
        )

    def test_validates_manifest_facets_and_blockers(self):
        root = self.spine()
        manifest = json.loads((root / "specspine.json").read_text())
        del manifest["areas"][0]["facets"]["failure"]
        (root / "specspine.json").write_text(json.dumps(manifest))
        self.assertIn("MANIFEST_FACETS", self.codes(root))

        root = self.spine()
        manifest = json.loads((root / "specspine.json").read_text())
        manifest["areas"][0]["blockers"] = ["OQ-missing"]
        (root / "specspine.json").write_text(json.dumps(manifest))
        self.assertIn("MANIFEST_BLOCKER", self.codes(root))

    def test_accepts_and_validates_optional_inspection_coverage(self):
        root = self.spine()
        manifest = json.loads((root / "specspine.json").read_text())
        manifest["areas"][0]["inspection"] = {
            "source": "commit-abc1234",
            "inspected": "2026-07-29",
            "mode": "refresh",
            "facets": {
                name: (
                    "checked"
                    if name in {"architecture", "behavior", "interfaces", "data", "failure"}
                    else "not-checked"
                )
                for name in CHECKER.FACET_NAMES
            },
        }
        (root / "specspine.json").write_text(json.dumps(manifest))
        self.assertNotIn("MANIFEST_INSPECTION", self.codes(root))

        manifest["areas"][0]["inspection"]["facets"]["quality"] = "complete"
        (root / "specspine.json").write_text(json.dumps(manifest))
        self.assertIn("MANIFEST_INSPECTION_FACET_VALUE", self.codes(root))

    def test_complete_verification_requires_machine_resolvable_support(self):
        root = self.spine()
        manifest = json.loads((root / "specspine.json").read_text())
        manifest["areas"][0]["facets"]["verification"] = "complete"
        (root / "specspine.json").write_text(json.dumps(manifest))

        self.assertIn("MANIFEST_VERIFICATION_UNSUPPORTED", self.codes(root))

    def test_warns_when_complete_facet_has_no_resolvable_support(self):
        root = self.spine()
        findings = CHECKER.check(root)

        self.assertTrue(any(
            item.code == "MANIFEST_FACET_SUPPORT_UNVERIFIED"
            and "failure" in item.message
            for item in findings
        ))

        (root / "payments.md").write_text(
            PAYMENTS
            + "\n## Failure behavior\n\n"
            + "Provider timeouts preserve the pending payment state.\n",
            encoding="utf-8",
        )
        findings = CHECKER.check(root)
        self.assertFalse(any(
            item.code == "MANIFEST_FACET_SUPPORT_UNVERIFIED"
            and "failure" in item.message
            for item in findings
        ))

    def test_requires_markdown_owner_for_specification_assets(self):
        root = self.spine()
        contracts = root / "contracts"
        contracts.mkdir()
        asset = contracts / "payments.openapi.yaml"
        asset.write_text("openapi: 3.1.0\n", encoding="utf-8")
        self.assertIn("UNREGISTERED_SPEC_ASSET", self.codes(root))
        (root / "payments.md").write_text(
            PAYMENTS
            + "\n## Interfaces\n\n"
            + "[Payment API](contracts/payments.openapi.yaml) is normative.\n",
            encoding="utf-8",
        )
        manifest = json.loads((root / "specspine.json").read_text())
        manifest["assets"].append({
            "path": "contracts/payments.openapi.yaml",
            "owner": "payments",
            "role": "interface-contract",
            "format": "openapi-3.1",
            "normative": True,
            "verifies": [],
        })
        (root / "specspine.json").write_text(json.dumps(manifest))
        self.assertNotIn("UNREGISTERED_SPEC_ASSET", self.codes(root))

    def test_rejects_legacy_execution_contract_asset(self):
        root = self.spine()
        contracts = root / "contracts"
        contracts.mkdir()
        asset = contracts / "reconstruction.json"
        asset.write_text(
            '{"toolchains":[{"name":"go","version":">=1.24"}]}',
            encoding="utf-8",
        )
        (root / "payments.md").write_text(
            PAYMENTS
            + "\n## Configuration contract\n\n"
            + "[Reconstruction environment](contracts/reconstruction.json) "
            + "defines the normative toolchain.\n",
            encoding="utf-8",
        )
        manifest = json.loads((root / "specspine.json").read_text())
        manifest["assets"].append({
            "path": "contracts/reconstruction.json",
            "owner": "payments",
            "role": "execution-contract",
            "format": "specspine-execution-contract-json-v1",
            "normative": True,
            "verifies": [],
        })
        (root / "specspine.json").write_text(json.dumps(manifest))

        self.assertIn("MANIFEST_ASSET_ROLE", self.codes(root))
        self.assertNotIn("UNREGISTERED_SPEC_ASSET", self.codes(root))

    def test_unreachable_node_is_error(self):
        other = PAYMENTS.replace("# Payments", "# Other").replace(
            "**ID:** `payments`", "**ID:** `other`"
        )
        root = self.spine(extra={"other.md": other})
        self.assertIn("UNREACHABLE_SPEC", self.codes(root))


if __name__ == "__main__":
    unittest.main()
