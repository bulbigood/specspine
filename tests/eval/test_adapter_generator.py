import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
GENERATOR_ROOT = PROJECT_ROOT / "tools" / "specspine-adapter-generator"
MODULE_PATH = GENERATOR_ROOT / "scripts" / "generate_skills.py"
SPEC = importlib.util.spec_from_file_location("specspine_adapter_generator", MODULE_PATH)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


class AdapterGeneratorTests(unittest.TestCase):
    def test_generated_packages_match_canonical_sources(self):
        source_root = GENERATOR_ROOT / "assets" / "skill-sources"
        for name in GENERATOR.PACKAGES:
            files = GENERATOR.package_files(source_root, name)
            errors = GENERATOR.check_package(files, PROJECT_ROOT / "skills" / name)
            self.assertEqual([], errors, name)

    def test_shared_rules_have_one_authoring_source(self):
        source_root = GENERATOR_ROOT / "assets" / "skill-sources"
        for consumer in ("specspine-map", "specspine-doctor"):
            for filename in GENERATOR.SHARED_REFERENCES:
                self.assertFalse((source_root / consumer / "references" / filename).exists())

    def test_source_entrypoints_are_not_discoverable_as_skills(self):
        source_root = GENERATOR_ROOT / "assets" / "skill-sources"
        self.assertEqual([], list(source_root.rglob("SKILL.md")))
        for name in GENERATOR.PACKAGES:
            self.assertTrue((source_root / name / "SKILL.md.src").is_file())

    def test_prompt_budgets_are_enforced(self):
        source_root = GENERATOR_ROOT / "assets" / "skill-sources"
        for name in GENERATOR.PACKAGES:
            files = GENERATOR.package_files(source_root, name)
            self.assertEqual([], GENERATOR.check_word_budgets(name, files), name)

    def test_generated_manifests_are_portable(self):
        for name in GENERATOR.PACKAGES:
            manifest = PROJECT_ROOT / "skills" / name / GENERATOR.MANIFEST
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(GENERATOR.CONTRACT_VERSION, data["contract_version"])
            self.assertEqual(f"assets/skill-sources/{name}", data["source"])
            self.assertNotIn(str(PROJECT_ROOT), manifest.read_text(encoding="utf-8"))

    def test_generation_detects_output_drift(self):
        source_root = GENERATOR_ROOT / "assets" / "skill-sources"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "skills" / "specspine-connect"
            source = source_root / "specspine-connect"
            files = GENERATOR.package_files(source_root, "specspine-connect")
            GENERATOR.write_package(files, source, target)
            self.assertEqual([], GENERATOR.check_package(files, target))
            (target / "SKILL.md").write_text("drift\n", encoding="utf-8")
            self.assertTrue(
                any("drifted SKILL.md" in error for error in GENERATOR.check_package(files, target))
            )

    def test_connect_generates_no_project_local_skill_template(self):
        templates = PROJECT_ROOT / "skills" / "specspine-connect" / "assets" / "templates"
        self.assertEqual(
            {"agent-bootstrap.md", "project-binding.md"},
            {path.name for path in templates.iterdir() if path.is_file()},
        )

    def test_connect_bootstrap_requires_documentation_language(self):
        source = (
            GENERATOR_ROOT
            / "assets"
            / "skill-sources"
            / "specspine-connect"
        )
        skill = (source / "SKILL.md.src").read_text(encoding="utf-8")
        bootstrap = (source / "assets/templates/agent-bootstrap.md").read_text(encoding="utf-8")
        self.assertIn("ask the user", skill)
        self.assertIn("{{DOCUMENTATION_LANGUAGE}}", bootstrap)

    def test_generator_is_not_discoverable_as_a_runtime_skill(self):
        self.assertFalse((GENERATOR_ROOT / "SKILL.md").exists())
        self.assertTrue((GENERATOR_ROOT / "MAINTAINER.md").is_file())
        self.assertEqual(
            [],
            list((PROJECT_ROOT / "tools").glob("**/SKILL.md")),
        )

    def test_each_runtime_skill_is_standalone(self):
        link_re = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
        versions = set()
        for name in GENERATOR.PACKAGES:
            root = PROJECT_ROOT / "skills" / name
            manifest = json.loads((root / GENERATOR.MANIFEST).read_text(encoding="utf-8"))
            versions.add(manifest["contract_version"])
            text = (root / "SKILL.md").read_text(encoding="utf-8")
            for raw_target in link_re.findall(text):
                target = raw_target.split("#", 1)[0]
                if target and "://" not in target:
                    self.assertTrue((root / target).is_file(), f"{name}: missing {target}")
            self.assertNotIn("../specspine-", text)
        self.assertEqual({GENERATOR.CONTRACT_VERSION}, versions)


if __name__ == "__main__":
    unittest.main()
