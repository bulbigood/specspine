import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
CAMPAIGN = ROOT / "skills/specspine-map/scripts/campaign.py"
FINALIZE = ROOT / "skills/specspine-map/scripts/finalize_run.py"


class MapCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.ledger = self.root / "run/campaign.json"
        self.spine = self.root / "specspine"
        self.staging = self.root / "run/staging/identity"
        self.checkpoint = self.root / "run/identity.json"
        self.spine.mkdir(parents=True)
        self.staging.mkdir(parents=True)
        self.cli(
            "init",
            str(self.ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
        )
        self.cli(
            "add",
            str(self.ledger),
            "identity",
            "--parent",
            "root",
            "--question",
            "Map identity",
            "--origin",
            "identity registry",
        )
        self.cli(
            "assign",
            str(self.ledger),
            "identity",
            "--owner",
            "/root/identity",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, *arguments, expected=0):
        result = subprocess.run(
            [sys.executable, str(CAMPAIGN), *arguments],
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

    def payload(self, *, candidates=True, frontier=True):
        return {
            "status": "continuing" if candidates else "locally_saturated",
            "evidence_inspected": ["src/identity.py"],
            "candidates": (
                [{"path": "domains/identity.md", "operation": "create"}]
                if candidates
                else []
            ),
            "mapped_responsibilities": ["Identity boundary"],
            "relationships": [],
            "source_coverage": [],
            "continuation": "Inspect tokens" if candidates else None,
            "coverage_frontier": (
                [
                    {
                        "id": "identity-tokens",
                        "question": "Map identity tokens",
                        "evidence": ["src/tokens.py"],
                        "namespace": "domains",
                        "prerequisite": None,
                        "classification": "fork_candidate",
                        "document": None,
                        "reason": None,
                    }
                ]
                if frontier
                else []
            ),
            "unresolved": [],
            "terminal_reason": (
                None if candidates else "no useful node: identity evidence exhausted"
            ),
        }

    def write_candidate(self, content="# Identity\n"):
        path = self.staging / "domains/identity.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def accept(self, checker, payload=None, expected=0):
        self.checkpoint.write_text(
            json.dumps(payload or self.payload()), encoding="utf-8"
        )
        return self.cli(
            "accept",
            str(self.ledger),
            "identity",
            str(self.checkpoint),
            str(self.staging),
            str(self.spine),
            "--checker",
            str(checker),
            expected=expected,
        )

    def test_init_is_private_atomic_and_add_is_idempotent(self):
        self.assertEqual(0o600, self.ledger.stat().st_mode & 0o777)
        self.assertFalse(list(self.ledger.parent.glob("*.tmp")))
        first = self.cli(
            "add",
            str(self.ledger),
            "runtime",
            "--parent",
            "root",
            "--question",
            "Map runtime",
            "--origin",
            "composition root",
        )
        result = self.cli(
            "add",
            str(self.ledger),
            "runtime",
            "--parent",
            "root",
            "--question",
            "Map runtime",
            "--origin",
            "composition root",
        )
        self.assertEqual(first["revision"], result["revision"])

    def test_accept_commits_file_frontier_and_ledger_together(self):
        source = self.write_candidate()
        checker = self.checker("import json\nprint(json.dumps([]))\n")

        receipt = self.accept(checker)

        self.assertEqual("accepted", receipt["status"])
        self.assertEqual(["domains/identity.md"], receipt["published"])
        self.assertEqual(["identity-tokens"], receipt["added_branches"])
        self.assertFalse(source.exists())
        self.assertTrue((self.spine / "domains/identity.md").is_file())
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(
            ["domains/identity.md"], ledger["branches"]["identity"]["published"]
        )
        self.assertEqual("queued", ledger["branches"]["identity-tokens"]["state"])

    def test_error_level_unreachable_is_deferred(self):
        self.write_candidate()
        checker = self.checker(
            "import json, sys\n"
            "findings = [] if '--candidates' in sys.argv else "
            "[{'severity':'error','code':'UNREACHABLE_SPEC'}]\n"
            "print(json.dumps(findings))\n"
            "raise SystemExit(1 if findings else 0)\n"
        )

        receipt = self.accept(checker)

        self.assertEqual("accepted", receipt["status"])
        self.assertTrue((self.spine / "domains/identity.md").is_file())

    def test_non_navigation_failure_rolls_back_everything(self):
        source = self.write_candidate()
        checker = self.checker(
            "import json, sys\n"
            "findings = [] if '--candidates' in sys.argv else "
            "[{'severity':'error','code':'BROKEN'}]\n"
            "print(json.dumps(findings))\n"
            "raise SystemExit(1 if findings else 0)\n"
        )
        before = json.loads(self.ledger.read_text())

        error = self.accept(checker, expected=2)

        self.assertIn("BROKEN", error["error"])
        self.assertTrue(source.is_file())
        self.assertFalse((self.spine / "domains/identity.md").exists())
        self.assertEqual(before, json.loads(self.ledger.read_text()))

    def test_candidate_validation_failure_imports_no_children(self):
        self.write_candidate()
        checker = self.checker(
            "import json\n"
            "print(json.dumps([{'severity':'error','code':'BAD_CANDIDATE'}]))\n"
        )

        self.accept(checker, expected=2)

        ledger = json.loads(self.ledger.read_text())
        self.assertNotIn("identity-tokens", ledger["branches"])
        self.assertEqual([], ledger["branches"]["identity"]["published"])

    def test_digest_binds_checkpoint_and_file_bytes(self):
        self.write_candidate("version one")
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        first = self.accept(checker, self.payload(frontier=False))

        self.cli("release", str(self.ledger), "identity")
        self.cli("assign", str(self.ledger), "identity", "--owner", "/root/identity-2")
        replacement = self.payload(frontier=False)
        replacement["candidates"][0]["operation"] = "replace"
        self.write_candidate("version two")
        second = self.accept(checker, replacement)

        self.assertNotEqual(first["digest"], second["digest"])

    def test_terminal_accept_and_bottom_up_close(self):
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        receipt = self.accept(checker, self.payload(candidates=False, frontier=False))
        self.assertEqual("locally_saturated", receipt["branch_state"])
        self.cli("close", str(self.ledger), "identity")
        self.assertEqual(
            "complete",
            json.loads(self.ledger.read_text())["branches"]["identity"]["state"],
        )

    def test_resume_releases_stale_owners(self):
        receipt = self.cli("resume", str(self.ledger))
        self.assertEqual(["identity"], receipt["released"])
        summary = self.cli("summary", str(self.ledger))
        self.assertEqual(["identity"], summary["ready"])

    def test_path_traversal_and_live_staging_are_rejected(self):
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        payload = self.payload(frontier=False)
        payload["candidates"][0]["path"] = "../outside.md"
        self.write_candidate()
        self.accept(checker, payload, expected=2)

        self.checkpoint.write_text(json.dumps(self.payload(frontier=False)))
        result = self.cli(
            "accept",
            str(self.ledger),
            "identity",
            str(self.checkpoint),
            str(self.spine),
            str(self.spine),
            "--checker",
            str(checker),
            expected=2,
        )
        self.assertIn("disjoint", result["error"])


class MapFinalizeTests(unittest.TestCase):
    def test_finalize_requires_clean_complete_campaign(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = root / "campaign.json"
            spine = root / "specspine"
            staging = root / "staging"
            spine.mkdir()
            staging.mkdir()
            (spine / "README.md").write_text(
                "# Architecture\n\n**ID:** `architecture` · **Kind:** `index`\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(CAMPAIGN),
                    "init",
                    str(ledger),
                    "--scope",
                    "repository",
                    "--root-question",
                    "Map repository",
                ],
                check=True,
                capture_output=True,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(FINALIZE),
                    str(ledger),
                    str(spine),
                    "--staging-root",
                    str(staging),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, result.returncode)


if __name__ == "__main__":
    unittest.main()
