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
            "source_coverage": [
                {
                    "area": "src/identity.py",
                    "classification": "summarized",
                    "reason": "Owned by the identity specification",
                }
            ],
            "quality_gate": {
                name: {"status": "pass", "reason": f"{name} is sufficient"}
                for name in (
                    "ownership_coverage",
                    "orientation",
                    "information_gain",
                    "change_utility",
                    "non_duplication",
                )
            },
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

    def test_candidate_can_publish_and_locally_saturate_atomically(self):
        self.write_candidate()
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        payload = self.payload(frontier=False)
        payload["status"] = "publish_and_locally_saturate"
        payload["continuation"] = None
        payload["terminal_reason"] = (
            "no useful node: candidate passes the complete local quality gate"
        )

        receipt = self.accept(checker, payload)

        self.assertEqual("locally_saturated", receipt["branch_state"])
        self.assertTrue((self.spine / "domains/identity.md").is_file())

    def test_terminal_quality_gap_is_rejected(self):
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        payload = self.payload(candidates=False, frontier=False)
        payload["quality_gate"]["change_utility"] = {
            "status": "gap",
            "reason": "Failure behavior remains unknown",
        }

        error = self.accept(checker, payload, expected=2)

        self.assertIn("quality gaps", error["error"])

    def test_child_cannot_require_its_parent(self):
        self.write_candidate()
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        payload = self.payload()
        payload["coverage_frontier"][0]["prerequisite"] = "identity"

        error = self.accept(checker, payload, expected=2)

        self.assertIn("dependency cycle", error["error"])
        self.assertNotIn(
            "identity-tokens",
            json.loads(self.ledger.read_text())["branches"],
        )

    def test_repair_prerequisite_removes_legacy_cycle(self):
        ledger = json.loads(self.ledger.read_text())
        ledger["branches"]["identity-tokens"] = {
            "id": "identity-tokens",
            "parent": "identity",
            "question": "Map identity tokens",
            "state": "queued",
            "owner": None,
            "terminal_reason": None,
            "published": [],
            "origin": "src/tokens.py",
            "namespace": None,
            "prerequisite": "identity",
        }
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        audit = self.cli("audit", str(self.ledger), expected=1)
        self.assertEqual("dependency_cycle", audit[0]["code"])
        receipt = self.cli(
            "repair-prerequisite",
            str(self.ledger),
            "identity-tokens",
            "--clear",
            "--reason",
            "producer created a parent prerequisite cycle",
        )

        self.assertEqual([], receipt["cycles_after"])
        self.assertEqual(
            None,
            json.loads(self.ledger.read_text())["branches"]["identity-tokens"][
                "prerequisite"
            ],
        )

    def test_recover_preserves_frontier_and_campaign_identity(self):
        destination = self.root / "recovered/campaign.json"
        source = json.loads(self.ledger.read_text())

        receipt = self.cli(
            "recover",
            str(self.ledger),
            str(destination),
            "--reason",
            "move durable state after a tool defect",
        )
        recovered = json.loads(destination.read_text())

        self.assertEqual(source["campaign_id"], receipt["campaign_id"])
        self.assertEqual(set(source["branches"]), set(recovered["branches"]))
        self.assertEqual("queued", recovered["branches"]["identity"]["state"])
        self.assertTrue(recovered["recovery_history"])

    def test_documented_seeding_stops_after_assignment(self):
        error = self.cli(
            "documented",
            str(self.ledger),
            "runtime",
            "--parent",
            "root",
            "--question",
            "Runtime",
            "--origin",
            "specspine/runtime.md",
            "--document",
            "runtime.md",
            expected=2,
        )
        self.assertIn("before assignment", error["error"])

    def test_coverage_report_exposes_unresolved_frontier(self):
        report = self.cli("coverage-report", str(self.ledger))

        self.assertEqual("partially_mapped", report["coverage_claim"])
        self.assertEqual([], report["ready"])
        self.assertEqual("identity", report["unresolved"][0]["id"])

    def test_resume_releases_stale_owners(self):
        receipt = self.cli("resume", str(self.ledger))
        self.assertEqual(["identity"], receipt["released"])
        summary = self.cli("summary", str(self.ledger))
        self.assertEqual(["identity"], summary["ready"])

    def test_producer_cannot_switch_top_level_domains(self):
        self.cli(
            "add",
            str(self.ledger),
            "runtime",
            "--parent",
            "root",
            "--question",
            "Map runtime",
            "--origin",
            "runtime composition",
        )

        error = self.cli(
            "assign",
            str(self.ledger),
            "runtime",
            "--owner",
            "/root/identity",
            expected=2,
        )

        self.assertIn("affinity violation", error["error"])

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

    def test_finalize_receipt_is_bound_to_campaign_identity_and_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = root / "campaign.json"
            spine = root / "specspine"
            staging = root / "staging"
            checkpoint = root / "root.json"
            checker = root / "checker.py"
            spine.mkdir()
            staging.mkdir()
            (spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
            checker.write_text("import json\nprint(json.dumps([]))\n", encoding="utf-8")
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
            checkpoint.write_text(
                json.dumps(
                    {
                        "status": "locally_saturated",
                        "evidence_inspected": ["README.md"],
                        "candidates": [],
                        "mapped_responsibilities": ["Repository architecture"],
                        "relationships": [],
                        "source_coverage": [
                            {
                                "area": "repository",
                                "classification": "summarized",
                                "reason": "No independent production branch remains",
                            }
                        ],
                        "quality_gate": {
                            name: {
                                "status": "pass",
                                "reason": f"{name} passes",
                            }
                            for name in (
                                "ownership_coverage",
                                "orientation",
                                "information_gain",
                                "change_utility",
                                "non_duplication",
                            )
                        },
                        "continuation": None,
                        "coverage_frontier": [],
                        "unresolved": [],
                        "terminal_reason": (
                            "no useful node: repeat scope discovery found no branch"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(CAMPAIGN),
                    "accept",
                    str(ledger),
                    "root",
                    str(checkpoint),
                    str(staging),
                    str(spine),
                    "--checker",
                    str(checker),
                ],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(CAMPAIGN),
                    "discovery-pass",
                    str(ledger),
                    "--evidence",
                    "composition roots and public interfaces checked",
                ],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(CAMPAIGN),
                    "close",
                    str(ledger),
                    "root",
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
                    "--checker",
                    str(checker),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual("finalized", receipt["status"])
            self.assertTrue(receipt["campaign_id"])
            self.assertEqual(64, len(receipt["ledger_digest"]))
            self.assertEqual(
                {
                    "created": 0,
                    "replaced": 0,
                    "published_paths": 0,
                    "markdown_total": 1,
                },
                receipt["changes"],
            )


if __name__ == "__main__":
    unittest.main()
