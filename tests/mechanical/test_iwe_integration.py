from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/node-express-boilerplate"
CANONICAL = ROOT / "shared/assets/iwe"


def iwe(workspace: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["iwe", *arguments],
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
    )


@unittest.skipUnless(shutil.which("iwe"), "IWE is required")
class IweIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name) / "project"
        shutil.copytree(
            EXAMPLE,
            self.workspace,
            ignore=shutil.ignore_patterns("node_modules"),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_example_uses_canonical_assets(self) -> None:
        self.assertEqual(
            (CANONICAL / "config.toml").read_text(encoding="utf-8"),
            (EXAMPLE / ".iwe/config.toml").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            (CANONICAL / "schemas/specification.yaml").read_text(encoding="utf-8"),
            (EXAMPLE / ".iwe/schemas/specification.yaml").read_text(encoding="utf-8"),
        )
        config = (CANONICAL / "config.toml").read_text()
        self.assertIn('path = "docs"', config)
        self.assertIn('key_template = "specs/{{slug}}"', config)
        self.assertIn('match = "specs/**"', config)

    def test_schema_and_iwe_relationships(self) -> None:
        validation = iwe(self.workspace, "schema", "validate", "-f", "json")
        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        self.assertEqual(json.loads(validation.stdout or "[]"), [])

        tree = iwe(self.workspace, "tree", "-f", "json")
        self.assertEqual(tree.returncode, 0, tree.stderr)
        roots = json.loads(tree.stdout)
        architecture = next(item for item in roots if item["key"] == "specs/architecture")
        self.assertEqual(
            {child["key"] for child in architecture["children"]},
            {"specs/authentication", "specs/user-management"},
        )

        included = iwe(
            self.workspace, "find", "--included-by", "specs/architecture", "-f", "keys"
        )
        self.assertEqual(
            set(included.stdout.splitlines()),
            {"specs/authentication", "specs/user-management"},
        )

        references = iwe(
            self.workspace, "find", "--references", "specs/user-management", "-f", "keys"
        )
        self.assertEqual(references.stdout.splitlines(), ["specs/authentication"])

    def test_schema_rejects_wrong_statement_prefix(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "REQ-valid-credentials", "OBS-valid-credentials"
            ),
            encoding="utf-8",
        )
        validation = iwe(self.workspace, "schema", "validate", "-f", "json")
        self.assertNotEqual(validation.returncode, 0)
        reports = json.loads(validation.stdout)
        self.assertEqual(reports[0]["key"], "specs/authentication")

    def test_schema_requires_explicit_external_boundary_coverage(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "coverage:\n  external-boundary: open\n", ""
            ),
            encoding="utf-8",
        )
        validation = iwe(self.workspace, "schema", "validate", "-f", "json")
        self.assertNotEqual(validation.returncode, 0)
        reports = json.loads(validation.stdout)
        self.assertEqual(reports[0]["key"], "specs/authentication")

    def test_schema_rejects_exhaustive_coverage_without_basis(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "external-boundary: open", "external-boundary: exhaustive"
            ),
            encoding="utf-8",
        )
        validation = iwe(self.workspace, "schema", "validate", "-f", "json")

        self.assertNotEqual(validation.returncode, 0)
        reports = json.loads(validation.stdout)
        self.assertEqual(reports[0]["key"], "specs/authentication")

    def test_schema_accepts_exhaustive_coverage_with_basis(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            .replace(
                "  external-boundary: open",
                "  external-boundary: exhaustive\n  basis: CON-complete-boundary",
            )
            + "\n## Constraints\n\n"
            "- CON-complete-boundary — The enumerated external boundary is complete.\n",
            encoding="utf-8",
        )
        validation = iwe(self.workspace, "schema", "validate", "-f", "json")

        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        self.assertEqual(json.loads(validation.stdout or "[]"), [])

    def test_schema_rejects_basis_for_open_coverage(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "  external-boundary: open",
                "  external-boundary: open\n  basis: CON-unused-boundary",
            ),
            encoding="utf-8",
        )

        validation = iwe(self.workspace, "schema", "validate", "-f", "json")

        self.assertNotEqual(validation.returncode, 0)
        reports = json.loads(validation.stdout)
        self.assertEqual(reports[0]["key"], "specs/authentication")

    def test_schema_rejects_not_applicable_required_facet(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "  behavior: complete", "  behavior: not-applicable"
            ),
            encoding="utf-8",
        )

        validation = iwe(self.workspace, "schema", "validate", "-f", "json")

        self.assertNotEqual(validation.returncode, 0)
        reports = json.loads(validation.stdout)
        self.assertEqual(reports[0]["key"], "specs/authentication")

    def test_schema_enforces_required_facets_for_every_kind_family(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        original = path.read_text(encoding="utf-8")
        cases = (
            ("system", "behavior", "complete"),
            ("interface", "interfaces", "complete"),
            ("data", "data", "partial"),
            ("policy", "behavior", "complete"),
            ("deployment", "quality", "partial"),
            ("concept", "architecture", "complete"),
        )

        for kind, facet, current in cases:
            with self.subTest(kind=kind, facet=facet):
                path.write_text(
                    original.replace("kind: capability", f"kind: {kind}").replace(
                        f"  {facet}: {current}", f"  {facet}: not-applicable"
                    ),
                    encoding="utf-8",
                )
                validation = iwe(self.workspace, "schema", "validate", "-f", "json")
                self.assertNotEqual(validation.returncode, 0)
                reports = json.loads(validation.stdout)
                self.assertEqual(reports[0]["key"], "specs/authentication")

    def test_schema_rejects_unsafe_asset_path(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "implementation_freedom: contract-equivalent",
                "implementation_freedom: contract-equivalent\n"
                "assets:\n"
                "  - path: ../../outside.yaml\n"
                "    role: interface-contract\n"
                "    format: openapi-3.1\n"
                "    normative: true",
            ),
            encoding="utf-8",
        )

        validation = iwe(self.workspace, "schema", "validate", "-f", "json")

        self.assertNotEqual(validation.returncode, 0)
        reports = json.loads(validation.stdout)
        self.assertEqual(reports[0]["key"], "specs/authentication")

    def test_schema_requires_verification_asset_targets(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "implementation_freedom: contract-equivalent",
                "implementation_freedom: contract-equivalent\n"
                "assets:\n"
                "  - path: src/docs/components.yml\n"
                "    role: verification\n"
                "    format: yaml\n"
                "    normative: true",
            ),
            encoding="utf-8",
        )

        validation = iwe(self.workspace, "schema", "validate", "-f", "json")

        self.assertNotEqual(validation.returncode, 0)
        reports = json.loads(validation.stdout)
        self.assertEqual(reports[0]["key"], "specs/authentication")

    def test_iwe_projection_exposes_semantic_audit_input(self) -> None:
        projected = iwe(
            self.workspace,
            "find",
            "-k",
            "specs/authentication",
            "--add-fields",
            "kind=kind,facets=facets,coverage=coverage,blockers=blockers,"
            "implementation_freedom=implementation_freedom,assets=assets,body=$content",
            "-f",
            "json",
        )

        self.assertEqual(projected.returncode, 0, projected.stderr)
        owner = json.loads(projected.stdout)[0]
        self.assertEqual(owner["kind"], "capability")
        self.assertEqual(owner["coverage"]["external-boundary"], "open")
        self.assertIn("REQ-valid-credentials", owner["body"])

    def test_schema_leaves_cross_statement_checks_to_semantic_audit(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            .replace("title: Authentication", "title: Identity access")
            .replace("blockers: []", "blockers: [OQ-missing-policy]")
            .replace(
                "implementation_freedom: contract-equivalent",
                "implementation_freedom: contract-equivalent\n"
                "assets:\n"
                "  - path: contracts/missing-auth.openapi.yaml\n"
                "    role: interface-contract\n"
                "    format: openapi-3.1\n"
                "    normative: true",
            )
            .replace("REQ-invalid-credentials", "REQ-valid-credentials")
            .replace(
                "\n## Verification\n\n"
                "- VER-login — Black-box login tests cover success and invalid credentials.\n",
                "",
            ),
            encoding="utf-8",
        )

        validation = iwe(self.workspace, "schema", "validate", "-f", "json")

        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        self.assertEqual(json.loads(validation.stdout or "[]"), [])

    def test_template_creates_a_strictly_valid_specification(self) -> None:
        created = iwe(
            self.workspace,
            "create",
            "--template",
            "specification",
            "--var",
            "title=Rate limits",
            "--var",
            "body=Own request admission limits.",
            "--strict",
        )
        self.assertEqual(created.returncode, 0, created.stderr + created.stdout)
        self.assertTrue((self.workspace / "docs/specs/rate-limits.md").is_file())
        validation = iwe(self.workspace, "schema", "validate", "-f", "json")
        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        self.assertEqual(json.loads(validation.stdout or "[]"), [])

    def test_iwe_rename_updates_inclusion_and_reference_links(self) -> None:
        renamed = iwe(
            self.workspace,
            "rename",
            "specs/user-management",
            "specs/identity-management",
            "-f",
            "keys",
        )
        self.assertEqual(renamed.returncode, 0, renamed.stderr)
        self.assertTrue((self.workspace / "docs/specs/identity-management.md").is_file())
        self.assertFalse((self.workspace / "docs/specs/user-management.md").exists())
        architecture = (self.workspace / "docs/specs/architecture.md").read_text()
        authentication = (self.workspace / "docs/specs/authentication.md").read_text()
        self.assertIn("(identity-management)", architecture)
        self.assertIn("(identity-management)", authentication)
        self.assertNotIn("user-management", architecture)
        self.assertNotIn("user-management", authentication)


if __name__ == "__main__":
    unittest.main()
