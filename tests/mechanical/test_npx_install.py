import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[2]
SKILLS = (
    "specspine-extract",
    "specspine-evolve",
    "specspine-map",
    "specspine-doctor",
    "specspine-verify",
)
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


@unittest.skipUnless(os.environ.get("SPECSPINE_RUN_NPX") == "1", "set SPECSPINE_RUN_NPX=1 for npx integration tests")
class NpxStandaloneInstallTests(unittest.TestCase):
    def test_each_skill_installs_alone_and_is_idempotent(self):
        for name in SKILLS:
            with self.subTest(skill=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                command = [
                    "npx", "--yes", "skills", "add", str(PROJECT_ROOT),
                    "--skill", name, "--agent", "codex", "--copy", "--yes",
                ]
                for _ in range(2):
                    completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
                    self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
                installed_root = root / ".agents" / "skills"
                installed = installed_root / name
                self.assertTrue((installed / "SKILL.md").is_file())
                self.assertTrue((installed / ".gitignore").is_file())
                self.assertTrue((installed / "references/spec-glossary.md").is_file())
                self.assertTrue((installed / "references/vocabulary.json").is_file())
                self.assertEqual({name}, {path.name for path in installed_root.iterdir() if path.is_dir()})
                text = (installed / "SKILL.md").read_text(encoding="utf-8")
                for raw_target in LINK_RE.findall(text):
                    target = raw_target.split("#", 1)[0]
                    if target and "://" not in target:
                        self.assertTrue((installed / target).is_file(), f"{name}: missing {target}")
                if name == "specspine-map":
                    self.assertTrue((installed / "scripts/campaign.py").is_file())
                    self.assertTrue(
                        (installed / "scripts/discovery_finalize.py").is_file()
                    )
                    self.assertTrue((installed / "scripts/finalize_run.py").is_file())
                    self.assertTrue(
                        (installed / "scripts/producer_finalize.py").is_file()
                    )
                    for removed in (
                        "frontier.py",
                        "checkpoint.py",
                        "publish_candidates.py",
                    ):
                        self.assertFalse((installed / "scripts" / removed).exists())


if __name__ == "__main__":
    unittest.main()
