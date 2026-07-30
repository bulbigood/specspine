import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "shared/scripts/bootstrap_spine.py"


class BootstrapSpineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.spine = self.root / "specspine"
        self.index = self.root / "index.md"
        self.index.write_text(
            "# Project architecture\n\n"
            "**ID:** `project-architecture` · **Kind:** `index`\n\n"
            "## Architecture map\n\nNothing is documented yet.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, *extra, expected=0):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(self.spine),
                "--project",
                "fixture",
                *extra,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr)
        return json.loads(result.stdout if expected == 0 else result.stderr)

    def test_workspace_initialization_adds_gitignore_rule_idempotently(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        ignore = self.root / ".gitignore"
        ignore.write_text("dist/", encoding="utf-8")
        first = self.cli(
            "--index-file",
            str(self.index),
            "--workspace",
            str(self.root),
        )
        second = self.cli("--workspace", str(self.root))
        self.assertEqual("updated", first["workspace_gitignore"])
        self.assertEqual("already_present", second["workspace_gitignore"])
        self.assertEqual("dist/\n.specspine\n", ignore.read_text(encoding="utf-8"))

    def test_workspace_initialization_creates_gitignore(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        result = self.cli(
            "--index-file",
            str(self.index),
            "--workspace",
            str(self.root),
        )
        self.assertEqual("created", result["workspace_gitignore"])
        self.assertEqual(
            ".specspine\n",
            (self.root / ".gitignore").read_text(encoding="utf-8"),
        )

    def test_workspace_initialization_skips_gitignore_without_repository(self):
        result = self.cli(
            "--index-file",
            str(self.index),
            "--workspace",
            str(self.root),
        )
        self.assertEqual("not_git_repository", result["workspace_gitignore"])
        self.assertFalse((self.root / ".gitignore").exists())

    def test_workspace_initialization_does_not_write_from_repository_subdirectory(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        nested = self.root / "nested"
        nested.mkdir()
        result = self.cli(
            "--index-file",
            str(self.index),
            "--workspace",
            str(nested),
        )
        self.assertEqual("not_git_repository", result["workspace_gitignore"])
        self.assertFalse((nested / ".gitignore").exists())

    def test_creates_pair_and_is_idempotent(self):
        first = self.cli("--index-file", str(self.index))
        second = self.cli()
        self.assertEqual(["_INDEX.md", "specspine.json", "README.md"], first["created"])
        self.assertEqual("already_ready", second["status"])

    def test_renders_project_placeholder(self):
        self.index.write_text(
            "# {project} architecture\n\n"
            "**ID:** `project-architecture` · **Kind:** `index`\n",
            encoding="utf-8",
        )
        self.cli("--index-file", str(self.index))
        self.assertIn(
            "# fixture architecture",
            (self.spine / "_INDEX.md").read_text(encoding="utf-8"),
        )

    def test_completes_partial_root_without_overwriting_index(self):
        self.spine.mkdir()
        existing = "# Existing\n"
        (self.spine / "_INDEX.md").write_text(existing, encoding="utf-8")
        result = self.cli()
        self.assertEqual(["specspine.json", "README.md"], result["created"])
        self.assertEqual(existing, (self.spine / "_INDEX.md").read_text())

    def test_requires_rendered_index_when_index_is_missing(self):
        error = self.cli(expected=2)
        self.assertIn("--index-file is required", error["error"])

    def test_exact_mode_rejects_existing_different_index(self):
        self.spine.mkdir()
        (self.spine / "_INDEX.md").write_text("# Different\n", encoding="utf-8")
        error = self.cli(
            "--index-file",
            str(self.index),
            "--require-exact",
            expected=2,
        )
        self.assertIn("differs from rendered bootstrap", error["error"])


if __name__ == "__main__":
    unittest.main()
