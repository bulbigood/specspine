import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "skills" / "specspine-doctor" / "scripts" / "check_spine.py"
SPEC = importlib.util.spec_from_file_location("specspine_doctor_check", MODULE_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class DoctorCheckerTests(unittest.TestCase):
    def test_companion_rules_are_interchangeable(self):
        project_root = Path(__file__).parents[2]
        for name in ("spec-format.md", "spec-semantics.md", "context-handoff.md"):
            grow = project_root / "skills" / "specspine-grow" / "references" / name
            mapping = project_root / "skills" / "specspine-map" / "references" / name
            self.assertEqual(grow.read_text(encoding="utf-8"), mapping.read_text(encoding="utf-8"), name)

    def test_checker_id_grammar_matches_canonical_format(self):
        format_path = Path(__file__).parents[2] / "skills" / "specspine-grow" / "references" / "spec-format.md"
        text = format_path.read_text(encoding="utf-8")
        match = re.search(r"Use this identifier grammar:\n\n```text\n([^\n]+)\n```", text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), CHECKER.ID_RE.pattern)

    def test_accepts_valid_graph_and_semantic_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Architecture\n\n[Jobs](jobs.md)\n", encoding="utf-8")
            (root / "jobs.md").write_text(
                "# Jobs\n\nOwns jobs.\n\n## Constraints\n\n- **CON-retry-limit** — Retries are bounded.\n",
                encoding="utf-8",
            )
            self.assertEqual([], CHECKER.check(root))

    def test_reports_broken_link_unreachable_file_and_invalid_id_section(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Architecture\n\n[Missing](missing.md)\n", encoding="utf-8")
            (root / "orphan.md").write_text(
                "# Orphan\n\n## Decisions\n\n- **OBS-current-shape** — Current shape.\n",
                encoding="utf-8",
            )
            codes = {finding.code for finding in CHECKER.check(root)}
            self.assertTrue({"BROKEN_LINK", "UNREACHABLE_SPEC", "ID_SECTION"} <= codes)

    def test_reports_unresolved_semantic_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Architecture\n\n[Jobs](jobs.md)\n", encoding="utf-8")
            (root / "jobs.md").write_text(
                "# Jobs\n\nPreserve [CON-missing](owner.md).\n", encoding="utf-8"
            )
            (root / "owner.md").write_text("# Owner\n", encoding="utf-8")
            codes = {finding.code for finding in CHECKER.check(root)}
            self.assertIn("UNRESOLVED_ID", codes)


if __name__ == "__main__":
    unittest.main()
