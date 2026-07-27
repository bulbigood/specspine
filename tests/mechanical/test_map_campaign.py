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
        self.repository = self.root / "repository"
        self.spine = self.repository / "specspine"
        self.spine.mkdir(parents=True)
        (self.spine / "README.md").write_text(
            "# Architecture\n\n"
            "- **OBS-architecture-root** — broad system owner.\n"
            "- Candidate evidence: `src/identity`.\n"
            "- Build evidence: `pyproject.toml`.\n",
            encoding="utf-8",
        )
        (self.repository / "src/identity").mkdir(parents=True)
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = True\n",
            encoding="utf-8",
        )
        (self.repository / "tests").mkdir()
        (self.repository / "tests/session_test.py").write_text(
            "def test_session(): pass\n",
            encoding="utf-8",
        )
        (self.repository / "pyproject.toml").write_text(
            "[project]\nname='fixture'\n",
            encoding="utf-8",
        )
        self.run = self.root / "run"
        self.ledger = self.run / "campaign.json"
        self.staging = self.run / "staging"
        self.staging.mkdir(parents=True)
        self.checkpoint = self.run / "checkpoint.json"
        self.checker = self.root / "checker.py"
        self.checker.write_text(
            "import json\nprint(json.dumps([]))\n",
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(self.ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, *arguments, expected=0, script=CAMPAIGN):
        result = subprocess.run(
            [sys.executable, str(script), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return json.loads(result.stdout or result.stderr)

    def ledger_value(self):
        return json.loads(self.ledger.read_text(encoding="utf-8"))

    def source_pass(self, *, expected=0):
        return self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            expected=expected,
        )

    def task_for_unit(self, unit):
        ledger = self.ledger_value()
        task_id = ledger["source_pass"]["inventory"][unit]["task"]
        return task_id, ledger["tasks"][task_id]

    def assign(self, task_id, owner="/root/producer-1"):
        return self.cli(
            "assign",
            str(self.ledger),
            task_id,
            "--owner",
            owner,
        )

    def checkpoint_payload(
        self,
        *,
        outcome,
        evidence,
        directions=None,
        owner_document="README.md",
        owner_claim_ids=None,
    ):
        payload = {
            "outcome": outcome,
            "evidence": evidence,
            "summary": "The bounded unit and its responsibility were inspected",
            "directions": directions or [],
        }
        if outcome == "covered":
            payload["owner"] = (
                {
                    "document": owner_document,
                    "claims": owner_claim_ids or ["OBS-architecture-root"],
                }
            )
        elif outcome == "retry":
            payload["need"] = ["src/identity/recovery.py"]
        elif outcome in {"blocked", "supporting"}:
            payload["reason"] = "External evidence is unavailable"
        return payload

    def accept(self, task_id, payload, *, owner="/root/producer-1", expected=0):
        self.checkpoint.write_text(json.dumps(payload), encoding="utf-8")
        return self.cli(
            "accept",
            str(self.ledger),
            task_id,
            str(self.checkpoint),
            str(self.staging),
            str(self.spine),
            "--owner",
            owner,
            "--checker",
            str(self.checker),
            expected=expected,
        )

    def covered(self, task_id, evidence, *, owner="/root/producer-1"):
        self.assign(task_id, owner)
        return self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="covered",
                evidence=[evidence],
            ),
            owner=owner,
        )

    def integration_report(self, *, todo=None, omit_suggestions=False):
        ledger = self.ledger_value()
        settled = [
            task
            for task in ledger["tasks"].values()
            if task["state"] in {"published", "review"}
        ]
        reviews = [
            {
                "task": task["id"],
                "disposition": (
                    "confirmed_supporting"
                    if task.get("checkpoint_outcome") == "supporting"
                    else "already_canonical"
                    if task["state"] == "review"
                    else "integrated"
                ),
                "reason": "Root integration confirmed the producer result",
            }
            for task in settled
        ]
        suggestion_reviews = []
        if not omit_suggestions:
            for task in settled:
                for suggestion in task["producer_suggestions"]:
                    suggestion_reviews.append(
                        {
                            "task": task["id"],
                            "suggestion": suggestion["id"],
                            "disposition": "queued",
                            "todo": suggestion["id"],
                            "reason": "The integrated result leaves this direction open",
                        }
                    )
        raw_todo = todo or []
        return {
            "evidence_inspected": sorted(
                path.relative_to(self.spine).as_posix()
                for path in self.spine.rglob("*.md")
            ),
            "task_reviews": reviews,
            "suggestion_reviews": suggestion_reviews,
            "todo": raw_todo,
            "organization": {
                "status": "flat_sufficient",
                "reason": "The fixture remains directly navigable",
            },
            "terminal_reason": (
                None
                if raw_todo
                else "no integration-derived ToDo: all settled results were reviewed"
            ),
        }

    def integrate(self, report=None, *, expected=0):
        path = self.run / "integration.json"
        path.write_text(
            json.dumps(report or self.integration_report()),
            encoding="utf-8",
        )
        return self.cli(
            "integration-pass",
            str(self.ledger),
            str(self.spine),
            str(path),
            "--checker",
            str(self.checker),
            expected=expected,
        )

    def verify_all_source_units(self):
        self.source_pass()
        ledger = self.ledger_value()
        queued = [
            (area, value["task"])
            for area, value in ledger["source_pass"]["inventory"].items()
            if value["classification"] == "queued"
        ]
        for index, (area, task_id) in enumerate(queued):
            samples = ledger["source_pass"]["inventory"][area]["samples"]
            owner = f"/root/producer-{index}"
            self.assign(task_id, owner)
            self.accept(
                task_id,
                self.checkpoint_payload(outcome="covered", evidence=samples),
                owner=owner,
            )
        self.integrate()

    def test_init_uses_schema_five_and_private_ledger(self):
        ledger = self.ledger_value()
        self.assertEqual(5, ledger["schema_version"])
        self.assertEqual({}, ledger["tasks"])
        self.assertEqual(0o600, self.ledger.stat().st_mode & 0o777)

    def test_inventory_groups_root_manifests_and_excludes_spine(self):
        first = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        second = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        self.assertEqual(first["digest"], second["digest"])
        areas = {value["area"] for value in first["areas"]}
        self.assertEqual(
            {"repository-root/manifests", "src/identity", "tests/@test-only"},
            areas,
        )

    def test_source_pass_mechanically_queues_every_production_unit(self):
        receipt = self.source_pass()
        self.assertEqual(3, receipt["areas"])
        self.assertEqual(2, receipt["verification_todo"])
        ledger = self.ledger_value()
        self.assertEqual(
            "test-only",
            ledger["source_pass"]["inventory"]["tests/@test-only"]["classification"],
        )
        for area in ("src/identity", "repository-root/manifests"):
            row = ledger["source_pass"]["inventory"][area]
            self.assertEqual("queued", row["classification"])
            self.assertEqual("todo", ledger["tasks"][row["task"]]["state"])

    def test_inventory_splits_oversized_units_mechanically(self):
        large = self.repository / "packages/big/src"
        large.mkdir(parents=True)
        for index in range(401):
            (large / f"file_{index:03d}.ts").write_text(
                f"export const value{index} = {index};\n",
                encoding="utf-8",
            )
        inventory = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        units = [
            value
            for value in inventory["areas"]
            if value["area"].startswith("packages/big")
        ]
        self.assertEqual(401, sum(value["files"] for value in units))
        self.assertTrue(all(value["files"] <= 80 for value in units))
        self.assertEqual(401, len({path for value in units for path in value["members"]}))

    def test_inventory_splits_large_units_by_directory_before_chunks(self):
        for directory in ("alpha", "beta"):
            root = self.repository / "packages/big" / directory
            root.mkdir(parents=True)
            for index in range(70):
                (root / f"file_{index:03d}.ts").write_text(
                    f"export const value{index} = {index};\n",
                    encoding="utf-8",
                )
        inventory = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        units = [
            value
            for value in inventory["areas"]
            if value["classification"] == "queued"
            and value["area"].startswith("packages/big/")
        ]
        self.assertEqual(2, len(units))
        self.assertTrue(
            all(
                len({Path(path).parts[2] for path in value["members"]}) == 1
                for value in units
            )
        )

    def test_nested_tests_fixtures_and_generated_files_are_not_queued(self):
        root = self.repository / "src/identity"
        (root / "testdata").mkdir()
        (root / "generated").mkdir()
        (root / "testdata/case.json").write_text("{}", encoding="utf-8")
        (root / "generated/client.ts").write_text("export {}", encoding="utf-8")
        (root / "session_test.go").write_text("package identity", encoding="utf-8")
        self.source_pass()
        inventory = self.ledger_value()["source_pass"]["inventory"]
        terminal_members = {
            path
            for value in inventory.values()
            if value["classification"] != "queued"
            for path in value["members"]
        }
        self.assertIn("src/identity/testdata/case.json", terminal_members)
        self.assertIn("src/identity/generated/client.ts", terminal_members)
        self.assertIn("src/identity/session_test.go", terminal_members)
        production = inventory["src/identity"]
        self.assertEqual(["src/identity/session.py"], production["members"])

    def test_candidate_owner_search_uses_every_member_not_only_samples(self):
        root = self.repository / "src/identity"
        for index in range(25):
            (root / f"module_{index:02d}.py").write_text(
                f"VALUE = {index}\n",
                encoding="utf-8",
            )
        (self.spine / "late-owner.md").write_text(
            "# Late owner\n\n"
            "- **OBS-late-owner** — `src/identity/module_24.py`.\n",
            encoding="utf-8",
        )
        self.source_pass()
        _, task = self.task_for_unit("src/identity")
        self.assertIn("late-owner.md", task["documents"])
        self.assertTrue(task["evidence_strata"])
        self.assertEqual(
            task["evidence"],
            [value["sample"] for value in task["evidence_strata"]],
        )

    def test_candidate_owner_packet_is_bounded(self):
        for index in range(20):
            (self.spine / f"candidate-{index:02d}.md").write_text(
                f"# Candidate {index}\n\n"
                "- **OBS-candidate** — `src/identity`.\n",
                encoding="utf-8",
            )
        self.source_pass()
        _, task = self.task_for_unit("src/identity")
        self.assertEqual(12, len(task["documents"]))

    def test_local_editor_directories_are_repository_support(self):
        editor = self.repository / ".vscode"
        editor.mkdir()
        (editor / "settings.json").write_text("{}", encoding="utf-8")
        self.source_pass()
        row = self.ledger_value()["source_pass"]["inventory"][
            ".vscode/@repository-support"
        ]
        self.assertEqual("repository-support", row["classification"])
        self.assertIsNone(row["task"])

    def test_broad_existing_owner_cannot_eliminate_verification_todo(self):
        self.source_pass()
        task_id, task = self.task_for_unit("src/identity")
        self.assertIn("README.md", task["documents"])
        self.assertEqual("todo", task["state"])
        self.assertIn(task_id, self.cli("ready", str(self.ledger))["ready"])

    def test_existing_spine_requires_documentation_seed(self):
        ledger = self.run / "existing.json"
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
            "--spine-state",
            "existing",
        )
        error = self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            expected=2,
        )
        self.assertIn("seed-from-spine", error["error"])

    def test_documentation_seed_is_mechanical_and_needs_no_ai_plan(self):
        ledger = self.run / "existing-seeded.json"
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
            "--spine-state",
            "existing",
        )
        receipt = self.cli(
            "seed-from-spine",
            str(ledger),
            str(self.spine),
        )
        self.assertEqual(1, receipt["documents"])
        self.assertEqual([], receipt["added_todo"])
        self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
        )

    def test_source_pass_is_immutable(self):
        self.source_pass()
        error = self.source_pass(expected=2)
        self.assertIn("immutable", error["error"])

    def test_one_producer_can_run_only_one_task(self):
        self.source_pass()
        first, _ = self.task_for_unit("src/identity")
        second, _ = self.task_for_unit("repository-root/manifests")
        self.assign(first)
        self.cli("release", str(self.ledger), first)
        error = self.cli(
            "assign",
            str(self.ledger),
            second,
            "--owner",
            "/root/producer-1",
            expected=2,
        )
        self.assertIn("one producer may run only one task", error["error"])

    def test_covered_by_owner_requires_existing_semantic_claim(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        error = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="covered",
                evidence=["src/identity/session.py"],
                owner_claim_ids=["OBS-does-not-exist"],
            ),
            expected=2,
        )
        self.assertIn("claim IDs do not exist", error["error"])

    def test_checkpoint_requires_concrete_evidence_from_task_unit(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        error = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="covered",
                evidence=["pyproject.toml"],
            ),
            expected=2,
        )
        self.assertIn("every task unit", error["error"])

    def test_covered_by_owner_waits_for_root_integration(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        receipt = self.covered(task_id, "src/identity/session.py")
        self.assertEqual("review", receipt["task_state"])
        summary = self.cli("summary", str(self.ledger))
        self.assertFalse(summary["terminal_gates"]["publications_integrated"])

    def test_covered_requires_evidence_from_every_mechanical_stratum(self):
        root = self.repository / "src/identity"
        for index in range(40):
            (root / f"module_{index:02d}.py").write_text(
                f"VALUE = {index}\n",
                encoding="utf-8",
            )
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        error = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="covered",
                evidence=["src/identity/session.py"],
            ),
            expected=2,
        )
        self.assertIn("every evidence stratum", error["error"])

    def test_producer_can_classify_unit_as_supporting(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="supporting",
                evidence=["src/identity/session.py"],
            ),
        )
        self.assertEqual("review", receipt["task_state"])
        self.integrate()
        task = self.ledger_value()["tasks"][task_id]
        self.assertEqual("complete", task["state"])
        self.assertEqual("supporting", task["checkpoint_outcome"])

    def test_root_can_retry_weak_supporting_receipt(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="supporting",
                evidence=["src/identity/session.py"],
            ),
        )
        report = self.integration_report()
        report["task_reviews"][0]["disposition"] = "retry"
        self.integrate(report)
        self.assertEqual("todo", self.ledger_value()["tasks"][task_id]["state"])

    def test_draft_publication_records_suggestions_but_not_todo(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n- **OBS-identity-owner** — owner.\n",
            encoding="utf-8",
        )
        direction = "Who owns failed refresh recovery?"
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
                directions=[direction],
            ),
        )
        self.assertEqual("published", receipt["task_state"])
        self.assertEqual(1, len(receipt["suggestions_pending_review"]))
        self.assertNotIn(receipt["suggestions_pending_review"][0], self.ledger_value()["tasks"])

    def test_needs_more_evidence_returns_task_for_fresh_producer(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="retry",
                evidence=["src/identity/session.py"],
            ),
        )
        self.assertEqual("todo", receipt["task_state"])
        self.assertIn(
            "src/identity/recovery.py",
            self.ledger_value()["tasks"][task_id]["evidence"],
        )

    def test_live_checker_failure_rolls_back_publication(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        source = self.staging / "identity.md"
        source.write_text("# Identity\n", encoding="utf-8")
        self.checker.write_text(
            "import json, sys\n"
            "findings = [] if '--candidates' in sys.argv else "
            "[{'severity':'error','code':'BROKEN'}]\n"
            "print(json.dumps(findings))\n"
            "raise SystemExit(1 if findings else 0)\n",
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
            expected=2,
        )
        self.assertTrue(source.exists())
        self.assertFalse((self.spine / "identity.md").exists())
        self.assertEqual("assigned", self.ledger_value()["tasks"][task_id]["state"])

    def test_candidate_checker_receives_live_root_and_staging_path(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n",
            encoding="utf-8",
        )
        self.checker.write_text(
            "import json, pathlib, sys\n"
            "if '--candidates' in sys.argv:\n"
            "    index = sys.argv.index('--candidates')\n"
            "    valid = pathlib.Path(sys.argv[1]).is_dir() and "
            "pathlib.Path(sys.argv[index + 1]).is_dir()\n"
            "else:\n"
            "    valid = pathlib.Path(sys.argv[1]).is_dir()\n"
            "print(json.dumps([] if valid else [{'code':'BAD_ARGS'}]))\n"
            "raise SystemExit(0 if valid else 1)\n",
            encoding="utf-8",
        )
        receipt = self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        self.assertEqual("published", receipt["task_state"])

    def test_root_cannot_discard_source_publication_as_not_architectural(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n",
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        report = self.integration_report()
        report["task_reviews"][0]["disposition"] = "not_architectural"
        error = self.integrate(report, expected=2)
        self.assertIn("invalid integration disposition", error["error"])

    def test_root_cannot_mark_deleted_source_publication_integrated(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n",
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        (self.spine / "identity.md").unlink()
        report = self.integration_report()
        error = self.integrate(report, expected=2)
        self.assertIn("cannot discard producer publications", error["error"])

    def test_integration_adds_document_derived_todo(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        new_todo = {
            "id": "session-recovery",
            "question": "Who owns failed refresh recovery?",
            "reason": "Integration exposes unresolved recovery",
            "evidence": ["src/identity/session.py"],
            "documents": ["README.md"],
            "excludes": [],
            "anchor": {
                "document": "README.md",
                "location": "Architecture",
                "known": "Normal ownership is covered",
            },
        }
        report = self.integration_report(todo=[new_todo])
        self.integrate(report)
        self.assertEqual(
            "todo",
            self.ledger_value()["tasks"]["session-recovery"]["state"],
        )

    def test_integration_must_review_every_covered_task(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        report = self.integration_report()
        report["task_reviews"] = []
        error = self.integrate(report, expected=2)
        self.assertIn("every settled producer task", error["error"])

    def test_inventory_verified_requires_every_unit_and_empty_integration(self):
        self.verify_all_source_units()
        summary = self.cli("summary", str(self.ledger))
        self.assertEqual("inventory_verified", summary["terminal"])
        self.assertTrue(all(summary["terminal_gates"].values()))
        next_action = self.cli("next-action", str(self.ledger))
        self.assertTrue(next_action["may_finish"])
        self.assertEqual("finalize", next_action["action"])
        coverage = self.cli("coverage-report", str(self.ledger))
        self.assertEqual("inventory_verified", coverage["coverage_claim"])

    def test_next_action_for_active_campaign_forbids_finishing(self):
        self.source_pass()
        next_action = self.cli("next-action", str(self.ledger))
        self.assertFalse(next_action["may_finish"])
        self.assertEqual("dispatch", next_action["action"])
        self.assertGreater(next_action["counts"]["todo"], 0)

    def test_repository_content_change_invalidates_inventory(self):
        self.verify_all_source_units()
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = False\nRECOVERY = True\n",
            encoding="utf-8",
        )
        summary = self.cli("summary", str(self.ledger))
        self.assertFalse(summary["terminal_gates"]["source_inventory_current"])
        self.assertIsNone(summary["terminal"])

    def test_live_spine_change_invalidates_integration(self):
        self.verify_all_source_units()
        (self.spine / "README.md").write_text(
            "# Architecture\n\nChanged after integration.\n",
            encoding="utf-8",
        )
        summary = self.cli("summary", str(self.ledger))
        self.assertFalse(summary["terminal_gates"]["integration_current"])
        self.assertIsNone(summary["terminal"])

    def test_finalize_requires_inventory_verified(self):
        self.verify_all_source_units()
        receipt = self.cli(
            str(self.ledger),
            str(self.spine),
            "--checker",
            str(self.checker),
            script=FINALIZE,
        )
        self.assertEqual("finalized", receipt["status"])
        self.assertEqual("inventory_verified", receipt["terminal"])


if __name__ == "__main__":
    unittest.main()
