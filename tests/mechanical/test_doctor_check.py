import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "shared/scripts/check_spine.py"
SPEC = importlib.util.spec_from_file_location("specspine_v2_check", MODULE_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


INDEX = """# Architecture

**ID:** `project-architecture` · **Kind:** `index`

Project architecture.

## Architecture map

- [Payments](payments.md) — owns payments.

## Coverage

### Mapped

- [Payments](payments.md) — sufficiently mapped.

### Partially mapped

- Reporting — failure behavior is unknown.

### Unmapped

- Forecasting.
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


class DoctorCheckerV2Tests(unittest.TestCase):
    def spine(self, payment=PAYMENTS, index=INDEX, extra=None):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "README.md").write_text(index, encoding="utf-8")
        (root / "payments.md").write_text(payment, encoding="utf-8")
        for name, content in (extra or {}).items():
            (root / name).write_text(content, encoding="utf-8")
        self.addCleanup(temporary.cleanup)
        return root

    def codes(self, root):
        return {item.code for item in CHECKER.check(root)}

    def test_accepts_complete_v2_spine(self):
        self.assertEqual([], [item for item in CHECKER.check(self.spine()) if item.severity == "error"])

    def test_doctor_index_template_is_valid_v2(self):
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
        self.assertEqual(
            [],
            [item for item in CHECKER.check(root) if item.severity == "error"],
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

    def test_requires_all_coverage_groups(self):
        root = self.spine(index=INDEX.replace("### Unmapped", "### Unknown"))
        self.assertIn("MISSING_COVERAGE_STATUS", self.codes(root))

    def test_validates_divergence_statement_kinds(self):
        root = self.spine(payment=PAYMENTS.replace(
            "[CON-payment-idempotency](payments.md)",
            "[OBS-provider-duplicates](payments.md)",
            1,
        ))
        self.assertIn("DIVERGENCE_INTENDED_KIND", self.codes(root))

    def test_unreachable_node_is_error(self):
        other = PAYMENTS.replace("# Payments", "# Other").replace(
            "**ID:** `payments`", "**ID:** `other`"
        )
        root = self.spine(extra={"other.md": other})
        self.assertIn("UNREACHABLE_SPEC", self.codes(root))


if __name__ == "__main__":
    unittest.main()
