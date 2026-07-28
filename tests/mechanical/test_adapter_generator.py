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

    def test_shared_resources_have_canonical_sources_and_skill_symlinks(self):
        skills_root = PROJECT_ROOT / "skills"
        files = GENERATOR.shared_files(PROJECT_ROOT, "specspine-grow")
        self.assertEqual(
            PROJECT_ROOT / "shared/references/spec-format.md",
            files["references/spec-format.md"],
        )
        self.assertEqual(
            PROJECT_ROOT / "shared/scripts/check_spine.py",
            files["scripts/check_spine.py"],
        )
        consumers = set(GENERATOR.SKILL_REFERENCES) | set(GENERATOR.SKILL_SCRIPTS)
        for consumer in consumers:
            self.assertEqual(
                [],
                GENERATOR.check_shared_links(
                    GENERATOR.shared_files(PROJECT_ROOT, consumer),
                    skills_root / consumer,
                ),
                consumer,
            )

    def test_shared_resources_have_multiple_consumers_and_no_skill_duplicates(self):
        self.assertEqual([], GENERATOR.check_resource_ownership(PROJECT_ROOT))

        self.assertTrue(
            (
                PROJECT_ROOT
                / "skills/specspine-grow/references/grow-examples.md"
            ).is_file()
        )
        self.assertFalse(
            (
                PROJECT_ROOT
                / "skills/specspine-grow/references/grow-examples.md"
            ).is_symlink()
        )
        for name in ("connection-contract.md", "review-method.md"):
            private = PROJECT_ROOT / "skills/specspine-doctor/references" / name
            self.assertTrue(private.is_file())
            self.assertFalse(private.is_symlink())

    def test_grow_requires_the_whole_spine_mechanical_gate_after_writes(self):
        skill = (
            PROJECT_ROOT / "skills/specspine-grow/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("scripts/check_spine.py <spine-root>", skill)
        self.assertIn("after every write batch", skill)
        self.assertIn("whole resolved", skill)
        self.assertIn("never claim the Grow operation", skill)

    def test_grow_checker_rejects_nested_unreachable_specification(self):
        index = (
            PROJECT_ROOT
            / "skills/specspine-doctor/assets/templates/spine-index.md"
        ).read_text(encoding="utf-8")
        orphan = """# Orphan

**ID:** `orphan` · **Kind:** `component`

Owns an unreachable architectural responsibility.

## Responsibility

- Owns the orphan responsibility.
"""
        with tempfile.TemporaryDirectory() as directory:
            spine = Path(directory) / "specspine"
            nested = spine / "area"
            nested.mkdir(parents=True)
            (spine / "README.md").write_text(index, encoding="utf-8")
            (nested / "orphan.md").write_text(orphan, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        PROJECT_ROOT
                        / "skills/specspine-grow/scripts/check_spine.py"
                    ),
                    str(spine),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("UNREACHABLE_SPEC area/orphan.md", result.stdout)

    def test_shared_references_are_symlinks_and_private_references_are_local(self):
        shared = {
            PROJECT_ROOT / "skills" / skill / relative
            for skill in GENERATOR.SKILL_REFERENCES
            for relative in GENERATOR.shared_files(PROJECT_ROOT, skill)
        }
        for root in (PROJECT_ROOT / "skills").glob("specspine-*/references"):
            for path in root.iterdir():
                if path in shared:
                    self.assertTrue(path.is_symlink(), str(path))
                else:
                    self.assertTrue(path.is_file(), str(path))
                    self.assertFalse(path.is_symlink(), str(path))

        private_references = (
            PROJECT_ROOT / "skills/specspine-map/references/bounded-mode.md",
            PROJECT_ROOT / "skills/specspine-map/references/mapping-method.md",
            PROJECT_ROOT / "skills/specspine-map/references/orchestration.md",
        )
        for private in private_references:
            self.assertTrue(private.is_file())
            self.assertFalse(private.is_symlink())

    def test_prompt_budgets_are_enforced_on_canonical_skills(self):
        skills_root = PROJECT_ROOT / "skills"
        for name in GENERATOR.PACKAGES:
            files = GENERATOR.package_files(skills_root, name)
            self.assertEqual([], GENERATOR.check_word_budgets(name, files), name)

    def test_generator_does_not_manage_private_mapping_protocols(self):
        self.assertNotIn(
            "mapping-method.md",
            GENERATOR.SKILL_REFERENCES["specspine-map"],
        )
        self.assertNotIn(
            "orchestration.md",
            GENERATOR.SKILL_REFERENCES["specspine-map"],
        )

    def test_cli_synchronizes_only_shared_skill_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            shutil.copytree(PROJECT_ROOT / "skills", repo_root / "skills", symlinks=True)
            shutil.copytree(PROJECT_ROOT / "shared", repo_root / "shared")
            owner = repo_root / "shared/references/spec-format.md"
            consumer = repo_root / "skills/specspine-map/references/spec-format.md"
            doctor = repo_root / "skills/specspine-doctor/SKILL.md"
            owner_before = owner.read_bytes()
            doctor_before = doctor.read_bytes()
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
            self.assertEqual(doctor_before, doctor.read_bytes())
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

    def test_doctor_has_only_connection_templates(self):
        templates = PROJECT_ROOT / "skills/specspine-doctor/assets/templates"
        self.assertEqual(
            {"agent-bootstrap.md", "spine-index.md", "specspine.json"},
            {path.name for path in templates.iterdir() if path.is_file()},
        )

    def test_doctor_bootstrap_persists_documentation_language(self):
        source = PROJECT_ROOT / "skills/specspine-doctor"
        bootstrap = (source / "assets/templates/agent-bootstrap.md").read_text(encoding="utf-8")
        self.assertIn("{{DOCUMENTATION_LANGUAGE}}", bootstrap)

    def test_doctor_contract_requires_confirmed_first_setup(self):
        source = PROJECT_ROOT / "skills/specspine-doctor"
        skill = (source / "SKILL.md").read_text(encoding="utf-8")
        contract = (source / "references/connection-contract.md").read_text(
            encoding="utf-8"
        )
        instructions = skill + "\n" + contract
        index = (source / "assets/templates/spine-index.md").read_text(encoding="utf-8")
        for value in ("`specspine`", "`English`", "`AGENTS.md`"):
            self.assertIn(value, instructions)
        self.assertIn("<spine-root>/README.md", instructions)
        self.assertLess(
            instructions.index("Ask for `<spine-root>`"),
            instructions.index("Detect its dominant natural language"),
        )
        self.assertIn("immediate entries", instructions)
        self.assertIn("untrusted project content", instructions)
        self.assertIn("specspine.json", instructions)
        self.assertIn("exact label accepted by the operator", instructions)
        self.assertIn("Do not translate its headings", instructions)
        self.assertIn("natural-language headings", instructions)
        self.assertIn("accepted documentation language", instructions)
        self.assertIn("MUST NOT include a", instructions)
        self.assertIn("tutorial, framework purpose", instructions)
        self.assertIn(
            "the index answers what architecture this project has",
            instructions,
        )
        self.assertIn("# Project architecture", index)
        self.assertIn(
            "This directory contains the project's long-lived architectural intent",
            index,
        )
        self.assertIn(
            "architecture-relevant repository observations",
            index,
        )
        self.assertNotIn("SpecSpine is", index)
        self.assertNotIn("specspine-extract", index)

    def test_doctor_explains_modes_before_requesting_a_selection(self):
        source = PROJECT_ROOT / "skills/specspine-doctor"
        skill = (source / "SKILL.md").read_text(encoding="utf-8")
        self.assertFalse((source / "references/operation-modes.md").exists())
        self.assertIn("briefly explain", skill)
        self.assertIn("read/write boundaries", skill)
        public_modes = re.findall(r"^- `([^`]+)` —", skill, re.MULTILINE)
        self.assertEqual(
            ["connect", "disconnect", "check", "repair"],
            public_modes,
        )
        for mode in ("`connect` —", "`disconnect` —", "`check` —", "`repair` —"):
            with self.subTest(mode=mode):
                self.assertIn(mode, skill)
        self.assertIn("read-only review", skill)
        self.assertIn("approved bounded corrections", skill)
    def test_doctor_reviews_flat_layout_as_navigation_not_hierarchy(self):
        source = PROJECT_ROOT / "skills/specspine-doctor"
        skill = (source / "SKILL.md").read_text(encoding="utf-8")
        method = (source / "references/review-method.md").read_text(
            encoding="utf-8"
        )
        instructions = skill + "\n" + method
        self.assertIn("directory decomposition independently", instructions)
        self.assertIn("not a defect or a fixed threshold", instructions)
        self.assertIn("navigation aids, not ownership", instructions)
        self.assertIn("Do not require every specification", instructions)
        self.assertIn("review every specification's placement", instructions)
        self.assertIn("do not infer either from the path", instructions)
        self.assertIn("cross-cutting or intentionally root-level", instructions)
        self.assertIn("do not claim directory-placement", instructions)
        self.assertIn("exact moves and every affected", instructions)
        self.assertIn("Preserve document IDs, canonical ownership", instructions)
        self.assertIn("several destinations are plausible", instructions)

    def test_doctor_connection_contract_covers_selected_root_edge_states(self):
        contract = (
            PROJECT_ROOT
            / "skills/specspine-doctor/references/connection-contract.md"
        ).read_text(encoding="utf-8")
        for state in (
            "Path absent",
            "Empty directory",
            "Complete v3 root pair present",
            "Exactly one root file present",
            "Empty or mixed-language `README.md`",
            "Nonempty directory without root files",
            "Root is a file or unreadable directory",
            "`README.md` is not a readable regular text file",
            "unrelated project/package README",
            "Nested `README.md` only",
            "Case-variant index",
            "Selected root is the project root",
            "Symlink escapes the project",
        ):
            with self.subTest(state=state):
                self.assertIn(state, contract)
        self.assertIn("Do not recursively inspect", contract)
        self.assertIn("changed since inspection", contract)
        self.assertIn("Never overwrite a concurrently created root", contract)
        for state in (
            "File absent",
            "No managed region",
            "Exactly one balanced, non-nested region",
            "Multiple, nested, reversed, or unpaired markers",
        ):
            with self.subTest(state=state):
                self.assertIn(state, contract)
        self.assertIn("Connect means idempotently ensure", contract)
        self.assertIn("Preserve every recognized existing setting", contract)
        self.assertIn("requested state is already satisfied", contract)
        self.assertIn("Disconnect requires an exact selected instruction file", contract)
        self.assertIn("do not delete an otherwise empty instruction file", contract)
        self.assertIn("disconnect reports already disconnected and creates nothing", contract)
        self.assertIn("entire standalone line outside fenced code", contract)

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
