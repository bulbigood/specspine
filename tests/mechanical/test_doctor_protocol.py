import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
SKILL = (ROOT / "skills/specspine-doctor/SKILL.md").read_text(encoding="utf-8")
CONNECTION = (
    ROOT / "skills/specspine-doctor/references/connection-contract.md"
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


if __name__ == "__main__":
    unittest.main()
