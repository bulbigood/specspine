import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SCRIPT = (
    ROOT
    / "skills/specspine-map-large/scripts/bundle_skill.py"
)
SPEC = importlib.util.spec_from_file_location("skill_bundler", SCRIPT)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


class SkillBundlerTests(unittest.TestCase):
    def test_bundle_strips_frontmatter_and_includes_every_map_reference(self):
        map_root = ROOT / "skills/specspine-map"
        bundle = BUILDER.build_bundle(map_root)
        references = BUILDER.reference_files(map_root / "references")

        self.assertTrue(bundle.startswith("# SpecSpine Map\n"))
        self.assertNotIn("name: specspine-map", bundle)
        positions = []
        for reference in references:
            content = reference.read_text(encoding="utf-8").strip()
            with self.subTest(reference=reference.name):
                self.assertEqual(1, bundle.count(content))
                positions.append(bundle.index(content))
        self.assertEqual(sorted(positions), positions)
        expected = [BUILDER.strip_frontmatter(
            (map_root / "SKILL.md").read_text(encoding="utf-8")
        ).strip()]
        expected.extend(path.read_text(encoding="utf-8").strip() for path in references)
        self.assertEqual(BUILDER.SECTION_SEPARATOR.join(expected) + "\n", bundle)

    def test_cli_writes_the_deterministic_bundle(self):
        map_root = ROOT / "skills/specspine-map"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run/producer-instructions.md"
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(map_root), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(BUILDER.build_bundle(map_root), output.read_text())

    def test_unclosed_frontmatter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unclosed YAML frontmatter"):
            BUILDER.strip_frontmatter("---\nname: broken\n")

    def test_symlinked_reference_is_followed_and_broken_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skill"
            references = skill / "references"
            references.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: sample\ndescription: sample\n---\n# Sample\n",
                encoding="utf-8",
            )
            target = root / "shared.md"
            target.write_text("# Shared reference\n", encoding="utf-8")
            (references / "shared.md").symlink_to(target)

            self.assertIn("# Shared reference", BUILDER.build_bundle(skill))

            (references / "broken.md").symlink_to(root / "missing.md")
            with self.assertRaisesRegex(ValueError, "not a readable regular file"):
                BUILDER.build_bundle(skill)


if __name__ == "__main__":
    unittest.main()
