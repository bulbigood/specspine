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


class ExtractV2Tests(unittest.TestCase):
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

    def test_retrieves_by_alias_and_responsibility(self):
        result = self.query(targets=[], terms=[["Checkout"], ["state mutation"]])
        self.assertEqual("payment-processing", result["primary"]["id"])

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
        result = self.query(token_budget=128)
        self.assertEqual("truncated", result["closure_status"])
        self.assertTrue(result["omitted"])

    def test_invalid_query_and_invalid_spine(self):
        self.assertEqual("invalid", SEARCH.build_closure(self.spine, {"unknown": 1})["closure_status"])
        (self.spine / "payments.md").write_text("# Legacy\n", encoding="utf-8")
        self.assertEqual("invalid", self.query()["closure_status"])

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
