import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "shared/scripts/check_spine.py"
SPEC = importlib.util.spec_from_file_location("specspine_v3_check", MODULE_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


INDEX = """# Architecture

**ID:** `project-architecture` · **Kind:** `index`

Project architecture.

## Architecture map

- [Payments](payments.md) — owns payments.

"""

PAYMENTS = """# Payments

**ID:** `payments` · **Kind:** `subsystem`
**Aliases:** Checkout

Owns payment attempts and results.

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


class DoctorCheckerV3Tests(unittest.TestCase):
    def spine(self, payment=PAYMENTS, index=INDEX, extra=None, manifest=None):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "README.md").write_text(index, encoding="utf-8")
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
                "specspine": 3,
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

    def test_accepts_strict_v3_spine(self):
        self.assertEqual([], [item for item in CHECKER.check(self.spine()) if item.severity == "error"])

    def test_doctor_index_template_is_valid(self):
        template = (
            Path(__file__).parents[2]
            / "skills/specspine-doctor/assets/templates/spine-index.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "This directory contains the project's long-lived architectural intent",
            template,
        )
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "README.md").write_text(template, encoding="utf-8")
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
```
"""
        root = self.spine(index=INDEX + fenced)
        codes = self.codes(root)
        self.assertNotIn("BROKEN_LINK", codes)
        self.assertNotIn("ID_OUTSIDE_REGION", codes)

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

    def test_validates_divergence_statement_kinds(self):
        root = self.spine(payment=PAYMENTS.replace(
            "[CON-payment-idempotency](payments.md)",
            "[OBS-provider-duplicates](payments.md)",
            1,
        ))
        self.assertIn("DIVERGENCE_INTENDED_KIND", self.codes(root))

    def test_accepts_v3_normative_claims_and_relations(self):
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

    def test_complete_verification_requires_machine_resolvable_support(self):
        root = self.spine()
        manifest = json.loads((root / "specspine.json").read_text())
        manifest["areas"][0]["facets"]["verification"] = "complete"
        (root / "specspine.json").write_text(json.dumps(manifest))

        self.assertIn("MANIFEST_VERIFICATION_UNSUPPORTED", self.codes(root))

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

    def test_unreachable_node_is_error(self):
        other = PAYMENTS.replace("# Payments", "# Other").replace(
            "**ID:** `payments`", "**ID:** `other`"
        )
        root = self.spine(extra={"other.md": other})
        self.assertIn("UNREACHABLE_SPEC", self.codes(root))


if __name__ == "__main__":
    unittest.main()
