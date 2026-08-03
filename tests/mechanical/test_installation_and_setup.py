from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_SKILL_NAMES = tuple(
    f"iwe-spec-{name}" for name in ("audit", "map", "specify", "verify", "implement")
)
SETUP_SKILL_NAME = "iwe-spec-setup"
ALL_SKILL_NAMES = (SETUP_SKILL_NAME, *WORKFLOW_SKILL_NAMES)
SHARED = ROOT / "shared"
EXAMPLE = ROOT / "examples/node-express-boilerplate"


def iwe(workspace: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["iwe", *arguments], cwd=workspace, text=True, capture_output=True, check=False
    )


class InstallationIntegrityTests(unittest.TestCase):
    def test_every_skill_has_an_autonomous_copy_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "installed"
            for name in ALL_SKILL_NAMES:
                shutil.copytree(ROOT / "skills" / name, destination / name, symlinks=False)

            setup = destination / SETUP_SKILL_NAME
            self.assertTrue((setup / "SKILL.md").is_file())
            self.assertFalse((setup / "references").exists())
            self.assertFalse((setup / "scripts").exists())
            for relative in ("config.toml", "schemas/specification.yaml"):
                installed_asset = setup / "assets/iwe" / relative
                self.assertFalse(installed_asset.is_symlink())
                self.assertEqual(
                    (SHARED / "assets/iwe" / relative).read_bytes(),
                    installed_asset.read_bytes(),
                )

            for name in WORKFLOW_SKILL_NAMES:
                installed = destination / name
                self.assertTrue((installed / "SKILL.md").is_file())
                for reference in (
                    "specspine-audit.md",
                    "specspine-format.md",
                    "specspine-operations.md",
                    "specspine-semantics.md",
                ):
                    installed_reference = installed / "references" / reference
                    self.assertFalse(installed_reference.is_symlink())
                    self.assertEqual(
                        (SHARED / "references" / reference).read_bytes(),
                        installed_reference.read_bytes(),
                    )
                self.assertFalse((installed / "assets").exists())
                if name in {"iwe-spec-verify", "iwe-spec-implement"}:
                    conformance = installed / "references/specspine-conformance.md"
                    self.assertFalse(conformance.is_symlink())
                    self.assertEqual(
                        (SHARED / "references/specspine-conformance.md").read_bytes(),
                        conformance.read_bytes(),
                    )
                expected_references = {
                    "specspine-audit.md",
                    "specspine-format.md",
                    "specspine-operations.md",
                    "specspine-semantics.md",
                }
                if name in {"iwe-spec-verify", "iwe-spec-implement"}:
                    expected_references.add("specspine-conformance.md")
                self.assertEqual(
                    {path.name for path in (installed / "references").iterdir()},
                    expected_references,
                )
                self.assertFalse((installed / "scripts").exists())

    def test_shared_resources_have_one_physical_source(self) -> None:
        expected_links = [
            *(
                ROOT / "skills" / name / f"references/specspine-{reference}.md"
                for name in WORKFLOW_SKILL_NAMES
                for reference in ("audit", "format", "operations", "semantics")
            ),
            *(
                ROOT / "skills" / name / "references/specspine-conformance.md"
                for name in ("iwe-spec-verify", "iwe-spec-implement")
            ),
            *(
                ROOT / "docs/reference" / f"{reference}.md"
                for reference in ("format", "semantics", "conformance", "operations")
            ),
            ROOT / "skills/iwe-spec-setup/assets/iwe/config.toml",
            ROOT / "skills/iwe-spec-setup/assets/iwe/schemas/specification.yaml",
        ]
        for link in expected_links:
            self.assertTrue(link.is_symlink(), f"expected symlink: {link}")
            self.assertTrue(link.exists(), f"broken symlink: {link}")

    def test_repository_contains_no_broken_symlinks(self) -> None:
        broken = [
            str(path.relative_to(ROOT))
            for path in ROOT.rglob("*")
            if path.is_symlink() and not path.exists()
        ]
        self.assertEqual(broken, [])

    def test_canonical_shared_files_are_not_physically_duplicated(self) -> None:
        canonical = {
            hashlib.sha256(path.read_bytes()).hexdigest(): path
            for path in SHARED.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        duplicates: list[str] = []
        excluded = {".git", "node_modules", "reports", "__pycache__"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.is_symlink() or excluded.intersection(path.parts):
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in canonical and path != canonical[digest]:
                duplicates.append(str(path.relative_to(ROOT)))
        self.assertEqual(duplicates, [])

    def test_implement_is_packaged_without_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / "iwe-spec-implement"
            shutil.copytree(ROOT / "skills/iwe-spec-implement", installed, symlinks=False)
            text = (installed / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("iwe-spec-verify", text)

    def test_audit_uses_native_iwe_without_a_runtime(self) -> None:
        skill = (ROOT / "skills/iwe-spec-audit/SKILL.md").read_text(encoding="utf-8")
        contract = (SHARED / "references/specspine-audit.md").read_text(
            encoding="utf-8"
        )
        compact = " ".join(contract.split())

        self.assertIn("Perform a read-only audit", skill)
        self.assertIn("iwe schema validate", contract)
        self.assertIn("iwe find --filter 'specspine: 5'", contract)
        self.assertIn("frontmatter title equals the first H1", compact)
        self.assertIn("every ID is unique within the owner", compact)
        self.assertIn("coverage.basis", contract)
        self.assertIn("regular existing file inside the workspace", compact)
        self.assertIn("verification: complete", contract)
        self.assertFalse((ROOT / "skills/iwe-spec-audit/scripts").exists())
        self.assertFalse((ROOT / "skills/iwe-spec-audit/assets").exists())

    def test_skills_have_no_specspine_runtime_scripts(self) -> None:
        self.assertFalse((SHARED / "scripts").exists())
        for name in ALL_SKILL_NAMES:
            self.assertFalse((ROOT / "skills" / name / "scripts").exists())
        for name in WORKFLOW_SKILL_NAMES:
            self.assertFalse((ROOT / "skills" / name / "assets").exists())

    def test_setup_skill_is_declarative_and_idempotent_by_contract(self) -> None:
        skill = (ROOT / "skills/iwe-spec-setup/SKILL.md").read_text(encoding="utf-8")
        compact = " ".join(skill.split())
        self.assertIn("iwe init --auto --library <chosen-relative-path>", skill)
        self.assertIn("iwe schema validate", skill)
        self.assertIn("official IWE GitHub README", compact)
        self.assertIn("ask the user which one to use", compact)
        self.assertIn("obtain approval before running it", compact)
        self.assertIn("strict descendant of the resolved IWE library root", compact)
        self.assertIn("This skill contains no scripts", skill)
        self.assertIn("may lag the installed IWE binary", compact)
        self.assertIn("`iwe <command> --help`", skill)
        self.assertIn("Make the operation idempotent", compact)
        self.assertIn("Never replace the generated configuration", compact)
        self.assertTrue(
            (ROOT / "skills/iwe-spec-setup/assets/iwe/config.toml").is_symlink()
        )
        self.assertTrue(
            (
                ROOT
                / "skills/iwe-spec-setup/assets/iwe/schemas/specification.yaml"
            ).is_symlink()
        )

    def test_readme_documents_guided_setup_and_manual_fallback(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("iwe-org/skills --skill iwe-memory-system", readme)
        self.assertIn("$iwe-spec-setup", readme)
        self.assertIn("Which directory inside the workspace", readme)
        self.assertIn("rejects paths outside the IWE library", readme)
        self.assertIn("<details>", readme)
        self.assertIn("Manual workspace setup", readme)
        self.assertIn("iwe init --auto --library docs", readme)
        self.assertIn("[templates.specification]", readme)
        self.assertIn("[schemas.specification]", readme)
        self.assertIn('match = "specs/**"', readme)
        self.assertIn(".iwe/schemas/specification.yaml", readme)

    def test_workflow_skills_delegate_incomplete_setup(self) -> None:
        for name in WORKFLOW_SKILL_NAMES:
            skill_dir = ROOT / "skills" / name
            skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            compact = " ".join(skill.split())
            self.assertIn("installed official `iwe-memory-system` skill", compact)
            self.assertIn("read it before continuing", compact)
            self.assertIn("may lag the installed IWE binary", compact)
            self.assertIn("`iwe <command> --help`", skill)
            self.assertIn("do not retry the known-stale form", compact)
            self.assertIn("ask the operator to run `iwe-spec-setup`", compact)
            self.assertIn("README manual fallback", compact)
            self.assertIn("Do not install or repair setup from this workflow", compact)
            self.assertIn("workspace `.iwe/schemas/specification.yaml`", compact)
            self.assertIn("`iwe schema validate`", skill)
            self.assertIn("specspine-audit.md", skill)
            self.assertIn("specspine-operations.md", skill)
            self.assertNotIn("iwe-readiness.sh", skill)
            self.assertFalse((skill_dir / "assets").exists())


@unittest.skipUnless(
    os.environ.get("SPECSPINE_TEST_NPX") == "1" and shutil.which("npx"),
    "set SPECSPINE_TEST_NPX=1 to run the real npx skills smoke test",
)
class NpxInstallationSmokeTests(unittest.TestCase):
    def test_npx_installs_one_autonomous_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "consumer"
            workspace.mkdir()
            environment = os.environ.copy()
            environment["HOME"] = str(Path(temporary) / "home")
            environment["NPM_CONFIG_CACHE"] = str(Path(temporary) / "npm-cache")
            result = subprocess.run(
                [
                    "npx",
                    "--yes",
                    "skills@latest",
                    "add",
                    str(ROOT),
                    "-s",
                    "iwe-spec-map",
                    "-a",
                    "codex",
                    "-y",
                ],
                cwd=workspace,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
                timeout=180,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            installed = workspace / ".agents/skills/iwe-spec-map"
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "references/specspine-format.md").is_file())
            self.assertTrue((installed / "references/specspine-semantics.md").is_file())
            self.assertEqual(
                {path.name for path in (installed / "references").iterdir()},
                {
                    "specspine-audit.md",
                    "specspine-format.md",
                    "specspine-operations.md",
                    "specspine-semantics.md",
                },
            )
            self.assertFalse((installed / "assets").exists())


@unittest.skipUnless(shutil.which("iwe"), "IWE is required")
class SetupConfigurationTests(unittest.TestCase):
    def copy_example(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        workspace = Path(temporary.name) / "project"
        shutil.copytree(EXAMPLE, workspace, ignore=shutil.ignore_patterns("node_modules"))
        return workspace

    def test_docs_library_keeps_ordinary_notes_outside_the_schema(self) -> None:
        workspace = self.copy_example()
        unrelated = workspace / "docs/ordinary-note.md"
        unrelated.write_text("# Not a specification\n", encoding="utf-8")

        validation = iwe(workspace, "schema", "validate")

        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        keys = set(iwe(workspace, "find", "-f", "keys").stdout.splitlines())
        self.assertIn("ordinary-note", keys)
        self.assertIn("specs/authentication", keys)

    def test_iwe_commands_must_run_from_the_resolved_project_root(self) -> None:
        workspace = self.copy_example()
        nested = workspace / "src/nested"
        nested.mkdir(parents=True)

        root_keys = set(iwe(workspace, "find", "-f", "keys").stdout.splitlines())
        nested_keys = set(iwe(nested, "find", "-f", "keys").stdout.splitlines())

        self.assertIn("specs/authentication", root_keys)
        self.assertEqual(nested_keys, set())

    def test_existing_custom_library_path_is_valid(self) -> None:
        workspace = self.copy_example()
        (workspace / "knowledge").mkdir()
        shutil.move(str(workspace / "docs/specs"), workspace / "knowledge/specs")
        config = workspace / ".iwe/config.toml"
        config.write_text(
            config.read_text(encoding="utf-8").replace('path = "docs"', 'path = "knowledge"'),
            encoding="utf-8",
        )

        validation = iwe(workspace, "schema", "validate")

        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        self.assertFalse((workspace / "docs/specs").exists())
        self.assertIn("specs/authentication", iwe(workspace, "find", "-f", "keys").stdout)

    def test_scoped_binding_preserves_unrelated_iwe_notes(self) -> None:
        workspace = self.copy_example()
        library = workspace / "knowledge"
        (library / "specs").mkdir(parents=True)
        (library / "ordinary.md").write_text("# Ordinary note\n", encoding="utf-8")
        for document in (workspace / "docs/specs").glob("*.md"):
            shutil.move(str(document), library / "specs" / document.name)
        shutil.rmtree(workspace / "docs/specs")
        config = workspace / ".iwe/config.toml"
        config.write_text(
            config.read_text(encoding="utf-8")
            .replace('path = "docs"', 'path = "knowledge"'),
            encoding="utf-8",
        )

        validation = iwe(workspace, "schema", "validate")

        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        self.assertTrue((library / "ordinary.md").is_file())
        keys = set(iwe(workspace, "find", "-f", "keys").stdout.splitlines())
        self.assertIn("ordinary", keys)
        self.assertIn("specs/authentication", keys)

    def test_nested_specspine_directory_uses_library_relative_keys(self) -> None:
        workspace = self.copy_example()
        nested = workspace / "docs/architecture/specs"
        nested.mkdir(parents=True)
        for document in (workspace / "docs/specs").glob("*.md"):
            shutil.move(str(document), nested / document.name)
        shutil.rmtree(workspace / "docs/specs")
        config = workspace / ".iwe/config.toml"
        config.write_text(
            config.read_text(encoding="utf-8")
            .replace(
                'key_template = "specs/{{slug}}"',
                'key_template = "architecture/specs/{{slug}}"',
            )
            .replace('match = "specs/**"', 'match = "architecture/specs/**"'),
            encoding="utf-8",
        )

        validation = iwe(workspace, "schema", "validate")

        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        keys = set(iwe(workspace, "find", "-f", "keys").stdout.splitlines())
        self.assertIn("architecture/specs/authentication", keys)


if __name__ == "__main__":
    unittest.main()
