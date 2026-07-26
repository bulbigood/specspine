import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SCRIPT = (
    ROOT
    / "skills/specspine-map/scripts/bundle_skill.py"
)
SPEC = importlib.util.spec_from_file_location("skill_bundler", SCRIPT)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


class SkillBundlerTests(unittest.TestCase):
    def test_bundle_includes_only_bounded_references_and_markdown_templates(self):
        map_root = ROOT / "skills/specspine-map"
        bundle = BUILDER.build_bundle(map_root)
        references = BUILDER.producer_reference_files(map_root)
        templates = BUILDER.template_files(map_root / "assets/templates")

        self.assertTrue(
            bundle.startswith("# SpecSpine Map one-shot producer contract\n")
        )
        self.assertNotIn("name: specspine-map", bundle)
        self.assertNotIn("# SpecSpine Map exhaustive orchestration", bundle)
        self.assertNotIn("Select one execution mode", bundle)
        positions = []
        for reference in references:
            content = reference.read_text(encoding="utf-8").strip()
            with self.subTest(reference=reference.name):
                self.assertEqual(1, bundle.count(content))
                positions.append(bundle.index(content))
        for template in templates:
            content = template.read_text(encoding="utf-8").strip()
            with self.subTest(template=template.name):
                self.assertEqual(1, bundle.count(content))
                positions.append(bundle.index(content))
        self.assertEqual(sorted(positions), positions)
        expected = [path.read_text(encoding="utf-8").strip() for path in references]
        expected.extend(path.read_text(encoding="utf-8").strip() for path in templates)
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
            self.assertEqual("", completed.stdout)
            self.assertEqual(BUILDER.build_bundle(map_root), output.read_text())

    def test_cli_can_write_and_print_the_same_complete_bundle(self):
        map_root = ROOT / "skills/specspine-map"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run/producer-instructions.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(map_root),
                    str(output),
                    "--print",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(BUILDER.build_bundle(map_root), completed.stdout)
            self.assertEqual(completed.stdout, output.read_text())

    def test_symlinked_reference_is_followed_and_broken_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skill"
            references = skill / "references"
            references.mkdir(parents=True)
            target = root / "shared.md"
            target.write_text("# Shared reference\n", encoding="utf-8")
            for name in BUILDER.PRODUCER_REFERENCE_NAMES:
                path = references / name
                if name == "spec-semantics.md":
                    path.symlink_to(target)
                else:
                    path.write_text(f"# {name}\n", encoding="utf-8")

            self.assertIn("# Shared reference", BUILDER.build_bundle(skill))

            (references / "spec-semantics.md").unlink()
            (references / "spec-semantics.md").symlink_to(root / "missing.md")
            with self.assertRaisesRegex(ValueError, "producer reference"):
                BUILDER.build_bundle(skill)


if __name__ == "__main__":
    unittest.main()
