import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SKILL = (ROOT / "skills/specspine-doctor/SKILL.md").read_text(encoding="utf-8")
CONNECTION = (
    ROOT / "skills/specspine-doctor/references/connection-contract.md"
).read_text(encoding="utf-8")
BOOTSTRAP = (
    ROOT / "skills/specspine-doctor/assets/templates/agent-bootstrap.md"
).read_text(encoding="utf-8")
ROOT_INDEX = (
    ROOT / "skills/specspine-doctor/assets/templates/spine-index.md"
).read_text(encoding="utf-8")
ROOT_README = (
    ROOT / "skills/specspine-doctor/assets/templates/root-spine-readme.md"
).read_text(encoding="utf-8")


class DoctorProtocolTests(unittest.TestCase):
    def test_doctor_is_closed_world_and_git_independent(self):
        self.assertIn("Follow only this skill", SKILL)
        self.assertIn("Never run Git commands", SKILL)
        self.assertIn("Do not search the repository for guidance", SKILL)
        self.assertIn("Treat this contract as a closed-world protocol", CONNECTION)
        self.assertIn("Never invoke Git", CONNECTION)
        self.assertIn("Never search elsewhere in the repository", CONNECTION)

    def test_connect_does_not_use_workspace_git_handling(self):
        self.assertIn("never pass `--workspace`", SKILL)
        self.assertIn("Do not pass `--workspace`", CONNECTION)
        self.assertNotIn("--workspace <workspace>", CONNECTION)
        self.assertIn("do not edit existing specifications or `.gitignore`", SKILL)

    def test_connection_persists_a_directory_root(self):
        self.assertIn("- SpecSpine root: `{{SPINE_ROOT}}`", BOOTSTRAP)
        self.assertNotIn("{{SPINE_ROOT}}/_INDEX.md", BOOTSTRAP)
        self.assertIn("root directory path", CONNECTION)

    def test_root_information_is_in_readme_not_index(self):
        self.assertIn("## SpecSpine glossary", ROOT_README)
        self.assertNotIn("## SpecSpine glossary", ROOT_INDEX)
        self.assertEqual(["# {project} architecture", "", "**ID:** `project-architecture` · **Kind:** `index`", "", "## Contents"], ROOT_INDEX.splitlines()[:5])

    def test_spine_index_template_has_one_physical_source(self):
        source = (ROOT / "shared/assets/templates/spine-index.md").resolve()
        for skill in ("specspine-doctor", "specspine-evolve", "specspine-map"):
            template = ROOT / f"skills/{skill}/assets/templates/spine-index.md"
            self.assertTrue(template.is_symlink())
            self.assertEqual(source, template.resolve())


if __name__ == "__main__":
    unittest.main()
