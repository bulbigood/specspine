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

    def test_schema_accepts_exhaustive_external_boundary_coverage(self) -> None:
        path = self.workspace / "docs/specs/authentication.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "external-boundary: open", "external-boundary: exhaustive"
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
        self.assertIn("identity-management.md", architecture)
        self.assertIn("identity-management.md", authentication)


if __name__ == "__main__":
    unittest.main()
