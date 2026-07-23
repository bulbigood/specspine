import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
GENERATOR_ROOT = PROJECT_ROOT / "tools" / "specspine-adapter-generator"
MODULE_PATH = GENERATOR_ROOT / "scripts" / "generate_resources.py"
SPEC = importlib.util.spec_from_file_location("specspine_adapter_generator", MODULE_PATH)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


class AdapterGeneratorTests(unittest.TestCase):
    def test_publishable_skills_are_canonical_packages(self):
        skills_root = PROJECT_ROOT / "skills"
        for name in GENERATOR.PACKAGES:
            self.assertTrue((skills_root / name / "SKILL.md").is_file(), name)
            self.assertNotEqual({}, GENERATOR.package_files(skills_root, name), name)

    def test_references_have_canonical_shared_sources_and_skill_symlinks(self):
        skills_root = PROJECT_ROOT / "skills"
        files = GENERATOR.shared_files(PROJECT_ROOT, "specspine-grow")
        self.assertEqual(
            PROJECT_ROOT / "shared/references/spec-format.md",
            files["references/spec-format.md"],
        )
        for consumer in GENERATOR.SKILL_REFERENCES:
            self.assertEqual(
                [],
                GENERATOR.check_shared_links(
                    GENERATOR.shared_files(PROJECT_ROOT, consumer),
                    skills_root / consumer,
                ),
                consumer,
            )

    def test_every_skill_reference_is_a_symlink(self):
        for root in (PROJECT_ROOT / "skills").glob("specspine-*/references"):
            for path in root.iterdir():
                self.assertTrue(path.is_symlink(), str(path))

    def test_prompt_budgets_are_enforced_on_canonical_skills(self):
        skills_root = PROJECT_ROOT / "skills"
        for name in GENERATOR.PACKAGES:
            files = GENERATOR.package_files(skills_root, name)
            self.assertEqual([], GENERATOR.check_word_budgets(name, files), name)

    def test_canonical_skills_do_not_claim_to_be_generated(self):
        legacy_manifest = ".generated-by-specspine-adapter-generator.json"
        for name in GENERATOR.PACKAGES:
            self.assertFalse((PROJECT_ROOT / "skills" / name / legacy_manifest).exists())

    def test_cli_synchronizes_only_shared_skill_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            shutil.copytree(PROJECT_ROOT / "skills", repo_root / "skills", symlinks=True)
            shutil.copytree(PROJECT_ROOT / "shared", repo_root / "shared")
            owner = repo_root / "shared/references/spec-format.md"
            consumer = repo_root / "skills/specspine-map/references/spec-format.md"
            connect = repo_root / "skills/specspine-connect/SKILL.md"
            owner_before = owner.read_bytes()
            connect_before = connect.read_bytes()
            consumer.unlink()
            consumer.write_text("drift\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--repo-root",
                    str(repo_root),
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("drift\n", consumer.read_text(encoding="utf-8"))

            subprocess.run(
                [sys.executable, str(MODULE_PATH), "--repo-root", str(repo_root)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(owner_before, owner.read_bytes())
            self.assertTrue(consumer.is_symlink())
            self.assertEqual(owner_before, consumer.read_bytes())
            self.assertEqual(connect_before, connect.read_bytes())
            self.assertFalse((repo_root / "tools").exists())

    def test_focused_generation_repairs_only_selected_skill_links(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            shutil.copytree(PROJECT_ROOT / "skills", repo_root / "skills", symlinks=True)
            shutil.copytree(PROJECT_ROOT / "shared", repo_root / "shared")
            owner = repo_root / "shared/references/spec-format.md"
            expected = owner.read_bytes()
            selected = repo_root / "skills/specspine-map/references/spec-format.md"
            untouched = repo_root / "skills/specspine-doctor/references/spec-format.md"
            selected.unlink()
            selected.write_text("drift\n", encoding="utf-8")
            untouched.unlink()
            untouched.write_text("untouched\n", encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--repo-root",
                    str(repo_root),
                    "--skill",
                    "specspine-map",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(selected.is_symlink())
            self.assertEqual(expected, selected.read_bytes())
            self.assertFalse(untouched.is_symlink())
            self.assertEqual("untouched\n", untouched.read_text(encoding="utf-8"))

    def test_connect_has_only_framework_neutral_bootstrap_template(self):
        templates = PROJECT_ROOT / "skills" / "specspine-connect" / "assets" / "templates"
        self.assertEqual(
            {"agent-bootstrap.md"},
            {path.name for path in templates.iterdir() if path.is_file()},
        )

    def test_connect_bootstrap_persists_documentation_language(self):
        source = PROJECT_ROOT / "skills" / "specspine-connect"
        bootstrap = (source / "assets/templates/agent-bootstrap.md").read_text(encoding="utf-8")
        self.assertIn("{{DOCUMENTATION_LANGUAGE}}", bootstrap)
        self.assertIn("{{RETRIEVAL_ACCELERATOR}}", bootstrap)

    def test_generator_has_no_runtime_skill_or_skill_copies(self):
        self.assertFalse((GENERATOR_ROOT / "SKILL.md").exists())
        self.assertTrue((GENERATOR_ROOT / "MAINTAINER.md").is_file())
        self.assertFalse((GENERATOR_ROOT / "assets" / "skill-sources").exists())
        self.assertEqual([], list((PROJECT_ROOT / "tools").glob("**/SKILL.md")))

    def test_each_runtime_skill_keeps_local_resources(self):
        link_re = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
        for name in GENERATOR.PACKAGES:
            root = PROJECT_ROOT / "skills" / name
            text = (root / "SKILL.md").read_text(encoding="utf-8")
            for raw_target in link_re.findall(text):
                target = raw_target.split("#", 1)[0]
                if target and "://" not in target:
                    self.assertTrue((root / target).is_file(), f"{name}: missing {target}")
            self.assertNotIn("../specspine-", text)


if __name__ == "__main__":
    unittest.main()
