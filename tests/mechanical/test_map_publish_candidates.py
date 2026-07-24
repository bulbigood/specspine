import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
FRONTIER = ROOT / "skills/specspine-map/scripts/frontier.py"
PUBLISHER = ROOT / "skills/specspine-map/scripts/publish_candidates.py"


class MapPublishCandidatesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.ledger = self.root / "run/frontier.json"
        self.spine = self.root / "specspine"
        self.staging = self.root / "run/staging-identity"
        self.spine.mkdir(parents=True)
        self.staging.mkdir(parents=True)
        self.frontier(
            "init",
            str(self.ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
        )
        self.frontier(
            "add",
            str(self.ledger),
            "identity",
            "--parent",
            "root",
            "--question",
            "Map identity",
            "--origin",
            "router registry",
        )
        self.frontier(
            "assign",
            str(self.ledger),
            "identity",
            "--owner",
            "producer-1",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def frontier(self, *arguments, expected=0):
        result = subprocess.run(
            [sys.executable, str(FRONTIER), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout or result.stderr)

    def checker(self, body):
        path = self.root / f"checker-{len(list(self.root.glob('checker-*')))}.py"
        path.write_text(body, encoding="utf-8")
        return path

    def candidate(self, relative="architecture/identity.md", content="# Identity\n"):
        path = self.staging / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def publish(self, checker, *extra):
        return subprocess.run(
            [
                sys.executable,
                str(PUBLISHER),
                str(self.ledger),
                "identity",
                str(self.spine),
                str(self.staging),
                "--path",
                "architecture/identity.md",
                "--checker",
                str(checker),
                *extra,
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_success_moves_exact_candidate_and_records_compact_receipt(self):
        source = self.candidate()
        checker = self.checker("import json\nprint(json.dumps([]))\n")

        result = self.publish(checker)

        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual("published", receipt["status"])
        self.assertEqual(["architecture/identity.md"], receipt["paths"])
        self.assertNotIn("branches", receipt)
        self.assertFalse(source.exists())
        self.assertTrue((self.spine / "architecture/identity.md").is_file())
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        identity = ledger["branches"]["identity"]
        self.assertEqual(["architecture/identity.md"], identity["published"])
        self.assertEqual(["architecture/identity.md"], identity["reservations"])

    def test_checker_finding_blocks_live_move(self):
        source = self.candidate()
        checker = self.checker(
            "import json\n"
            "print(json.dumps([{'severity': 'note', 'code': 'TEST'}]))\n"
        )

        result = self.publish(checker)

        self.assertEqual(2, result.returncode)
        payload = json.loads(result.stderr)
        self.assertEqual("TEST", payload["findings"][0]["code"])
        self.assertTrue(source.is_file())
        self.assertFalse((self.spine / "architecture/identity.md").exists())
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual([], ledger["branches"]["identity"]["published"])

    def test_late_checker_failure_rolls_move_back(self):
        source = self.candidate()
        checker = self.checker(
            "import json, sys\n"
            "findings = [] if '--candidates' in sys.argv else "
            "[{'severity': 'error', 'code': 'LATE'}]\n"
            "print(json.dumps(findings))\n"
        )

        result = self.publish(checker)

        self.assertEqual(2, result.returncode)
        self.assertTrue(source.is_file())
        self.assertFalse((self.spine / "architecture/identity.md").exists())
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual([], ledger["branches"]["identity"]["published"])

    def test_late_unreachable_warning_is_deferred_to_normalization(self):
        source = self.candidate()
        checker = self.checker(
            "import json, sys\n"
            "findings = [] if '--candidates' in sys.argv else "
            "[{'severity': 'warning', 'code': 'UNREACHABLE_SPEC'}]\n"
            "print(json.dumps(findings))\n"
        )

        result = self.publish(checker)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(source.exists())
        self.assertTrue((self.spine / "architecture/identity.md").is_file())

    def test_late_non_navigation_warning_rolls_move_back(self):
        source = self.candidate()
        checker = self.checker(
            "import json, sys\n"
            "findings = [] if '--candidates' in sys.argv else "
            "[{'severity': 'warning', 'code': 'OTHER_WARNING'}]\n"
            "print(json.dumps(findings))\n"
        )

        result = self.publish(checker)

        self.assertEqual(2, result.returncode)
        self.assertTrue(source.is_file())
        self.assertFalse((self.spine / "architecture/identity.md").exists())

    def test_late_failure_restores_replaced_live_file(self):
        source = self.candidate(content="new candidate")
        destination = self.spine / "architecture/identity.md"
        destination.parent.mkdir(parents=True)
        destination.write_text("original live file", encoding="utf-8")
        checker = self.checker(
            "import json, sys\n"
            "findings = [] if '--candidates' in sys.argv else "
            "[{'severity': 'error', 'code': 'LATE'}]\n"
            "print(json.dumps(findings))\n"
        )

        result = self.publish(
            checker,
            "--replace-existing",
            "architecture/identity.md",
        )

        self.assertEqual(2, result.returncode)
        self.assertEqual("new candidate", source.read_text(encoding="utf-8"))
        self.assertEqual("original live file", destination.read_text(encoding="utf-8"))

    def test_misplaced_candidate_is_rejected_without_relocation(self):
        misplaced = self.candidate("identity.md")
        checker = self.checker("import json\nprint(json.dumps([]))\n")

        result = self.publish(checker)

        self.assertEqual(2, result.returncode)
        payload = json.loads(result.stderr)
        self.assertIn("staging paths differ", payload["error"])
        self.assertTrue(misplaced.is_file())
        self.assertFalse((self.spine / "architecture/identity.md").exists())

    def test_nonactive_branch_cannot_move_live_files(self):
        source = self.candidate()
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        self.frontier(
            "state",
            str(self.ledger),
            "identity",
            "locally_saturated",
            "--terminal-reason",
            "no useful node: evidence exhausted",
        )

        result = self.publish(checker)

        self.assertEqual(2, result.returncode)
        self.assertTrue(source.is_file())
        self.assertFalse((self.spine / "architecture/identity.md").exists())

    def test_live_spine_cannot_be_used_as_staging(self):
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        candidate = self.spine / "architecture/identity.md"
        candidate.parent.mkdir(parents=True)
        candidate.write_text("live", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(PUBLISHER),
                str(self.ledger),
                "identity",
                str(self.spine),
                str(self.spine),
                "--path",
                "architecture/identity.md",
                "--checker",
                str(checker),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(2, result.returncode)
        self.assertEqual("live", candidate.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
