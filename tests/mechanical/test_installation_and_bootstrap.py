from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_NAMES = tuple(f"iwe-spec-{name}" for name in ("map", "specify", "verify", "implement"))
SHARED = ROOT / "shared"
PRESET = ROOT / "presets/iwe"
EXAMPLE = ROOT / "examples/node-express-boilerplate"


def iwe(workspace: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["iwe", *arguments], cwd=workspace, text=True, capture_output=True, check=False
    )


class InstallationIntegrityTests(unittest.TestCase):
    def test_every_skill_has_an_autonomous_copy_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "installed"
            for name in SKILL_NAMES:
                shutil.copytree(ROOT / "skills" / name, destination / name, symlinks=False)

            for name in SKILL_NAMES:
                installed = destination / name
                self.assertTrue((installed / "SKILL.md").is_file())
                self.assertFalse((installed / "assets/iwe").is_symlink())
                self.assertFalse((installed / "references/iwe-bootstrap.md").is_symlink())
                self.assertEqual(
                    (SHARED / "references/iwe-bootstrap.md").read_bytes(),
                    (installed / "references/iwe-bootstrap.md").read_bytes(),
                )
                self.assertEqual(
                    (SHARED / "assets/iwe/config.toml").read_bytes(),
                    (installed / "assets/iwe/config.toml").read_bytes(),
                )
                self.assertTrue((installed / "scripts/iwe-readiness.sh").is_file())

    def test_shared_resources_have_one_physical_source(self) -> None:
        expected_links = [
            *(ROOT / "skills" / name / "references/iwe-bootstrap.md" for name in SKILL_NAMES),
            *(ROOT / "skills" / name / "assets/iwe" for name in SKILL_NAMES),
            *(ROOT / "skills" / name / "scripts/iwe-readiness.sh" for name in SKILL_NAMES),
            PRESET / "config.toml",
            PRESET / "specification.md",
            PRESET / "schemas/specification.yaml",
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

    def test_readiness_script_finds_hidden_ancestor_and_descendant_configs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            package = workspace / "packages/service"
            nested = package / "src"
            (package / ".iwe").mkdir(parents=True)
            nested.mkdir(parents=True)
            (package / ".iwe/config.toml").write_text("version = 3\n")
            other = workspace / "packages/other/.iwe"
            other.mkdir(parents=True)
            (other / "config.toml").write_text("version = 3\n")

            script = SHARED / "scripts/iwe-readiness.sh"
            ancestor = subprocess.run(
                [str(script)], cwd=nested, text=True, capture_output=True, check=False
            )
            descendants = subprocess.run(
                [str(script), "--descendants"],
                cwd=workspace,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(ancestor.returncode, 0, ancestor.stderr)
            self.assertIn(str(package / ".iwe/config.toml"), ancestor.stdout)
            self.assertIn(f"bundled_config={SHARED / 'assets/iwe/config.toml'}", ancestor.stdout)
            self.assertIn(
                f"bundled_schema={SHARED / 'assets/iwe/schemas/specification.yaml'}",
                ancestor.stdout,
            )
            self.assertIn("packages/other/.iwe/config.toml", descendants.stdout)
            self.assertIn("packages/service/.iwe/config.toml", descendants.stdout)


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
            self.assertTrue((installed / "references/iwe-bootstrap.md").is_file())
            self.assertTrue((installed / "assets/iwe/config.toml").is_file())


@unittest.skipUnless(shutil.which("iwe"), "IWE is required")
class BootstrapConfigurationTests(unittest.TestCase):
    def copy_example(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        workspace = Path(temporary.name) / "project"
        shutil.copytree(EXAMPLE, workspace, ignore=shutil.ignore_patterns("node_modules"))
        return workspace

    def test_fallback_scopes_iwe_to_docs_specs(self) -> None:
        workspace = self.copy_example()
        unrelated = workspace / "docs/ordinary-note.md"
        unrelated.write_text("# Not a specification\n", encoding="utf-8")

        validation = iwe(workspace, "schema", "validate")

        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        self.assertNotIn("ordinary-note", iwe(workspace, "find", "-f", "keys").stdout)

    def test_existing_custom_library_path_is_valid(self) -> None:
        workspace = self.copy_example()
        (workspace / "knowledge").mkdir()
        for document in (workspace / "docs/specs").glob("*.md"):
            shutil.move(str(document), workspace / "knowledge" / document.name)
        (workspace / "docs/specs").rmdir()
        config = workspace / ".iwe/config.toml"
        config.write_text(
            config.read_text(encoding="utf-8").replace('path = "docs/specs"', 'path = "knowledge"'),
            encoding="utf-8",
        )

        validation = iwe(workspace, "schema", "validate")

        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        self.assertFalse((workspace / "docs/specs").exists())
        self.assertIn("authentication", iwe(workspace, "find", "-f", "keys").stdout)

    def test_scoped_binding_preserves_unrelated_iwe_notes(self) -> None:
        workspace = self.copy_example()
        library = workspace / "knowledge"
        (library / "specspine").mkdir(parents=True)
        (library / "ordinary.md").write_text("# Ordinary note\n", encoding="utf-8")
        for document in (workspace / "docs/specs").glob("*.md"):
            shutil.move(str(document), library / "specspine" / document.name)
        shutil.rmtree(workspace / "docs/specs")
        config = workspace / ".iwe/config.toml"
        config.write_text(
            config.read_text(encoding="utf-8")
            .replace('path = "docs/specs"', 'path = "knowledge"')
            .replace('key_template = "{{slug}}"', 'key_template = "specspine/{{slug}}"')
            .replace('match = "**"', 'match = "specspine/**"'),
            encoding="utf-8",
        )

        validation = iwe(workspace, "schema", "validate")

        self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
        self.assertTrue((library / "ordinary.md").is_file())
        keys = set(iwe(workspace, "find", "-f", "keys").stdout.splitlines())
        self.assertIn("ordinary", keys)
        self.assertIn("specspine/authentication", keys)


if __name__ == "__main__":
    unittest.main()
