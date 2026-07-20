import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
MODULE_PATH = PROJECT_ROOT / "skills" / "specspine-adapter-generator" / "scripts" / "generate_skills.py"
SPEC = importlib.util.spec_from_file_location("specspine_adapter_generator", MODULE_PATH)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


class AdapterGeneratorTests(unittest.TestCase):
    def test_generated_packages_match_canonical_sources(self):
        source_root = PROJECT_ROOT / "skills" / "specspine-adapter-generator" / "assets" / "skill-sources"
        for name in GENERATOR.PACKAGES:
            files = GENERATOR.package_files(source_root, name)
            errors = GENERATOR.check_package(files, PROJECT_ROOT / "skills" / name)
            self.assertEqual([], errors, name)

    def test_shared_rules_have_one_authoring_source(self):
        source_root = PROJECT_ROOT / "skills" / "specspine-adapter-generator" / "assets" / "skill-sources"
        for consumer in ("specspine-map", "specspine-doctor"):
            for filename in GENERATOR.SHARED_REFERENCES:
                self.assertFalse((source_root / consumer / "references" / filename).exists())

    def test_source_entrypoints_are_not_discoverable_as_skills(self):
        source_root = PROJECT_ROOT / "skills" / "specspine-adapter-generator" / "assets" / "skill-sources"
        self.assertEqual([], list(source_root.rglob("SKILL.md")))
        for name in GENERATOR.PACKAGES:
            self.assertTrue((source_root / name / "SKILL.md.src").is_file())

    def test_prompt_budgets_are_enforced(self):
        source_root = PROJECT_ROOT / "skills" / "specspine-adapter-generator" / "assets" / "skill-sources"
        for name in GENERATOR.PACKAGES:
            files = GENERATOR.package_files(source_root, name)
            self.assertEqual([], GENERATOR.check_word_budgets(name, files), name)

    def test_generated_manifests_are_portable(self):
        for name in GENERATOR.PACKAGES:
            manifest = PROJECT_ROOT / "skills" / name / GENERATOR.MANIFEST
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(f"assets/skill-sources/{name}", data["source"])
            self.assertNotIn(str(PROJECT_ROOT), manifest.read_text(encoding="utf-8"))

    def test_generation_detects_output_drift(self):
        source_root = PROJECT_ROOT / "skills" / "specspine-adapter-generator" / "assets" / "skill-sources"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "skills" / "specspine-init"
            source = source_root / "specspine-init"
            files = GENERATOR.package_files(source_root, "specspine-init")
            GENERATOR.write_package(files, source, target)
            self.assertEqual([], GENERATOR.check_package(files, target))
            (target / "SKILL.md").write_text("drift\n", encoding="utf-8")
            self.assertTrue(
                any("drifted SKILL.md" in error for error in GENERATOR.check_package(files, target))
            )

    def test_init_generates_no_project_local_skill_template(self):
        templates = PROJECT_ROOT / "skills" / "specspine-init" / "assets" / "templates"
        self.assertEqual(
            {"agent-bootstrap.md", "project-binding.md"},
            {path.name for path in templates.iterdir() if path.is_file()},
        )


if __name__ == "__main__":
    unittest.main()
