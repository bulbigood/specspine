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
            "evidence_inspected": ["src/identity.py", "src/tokens.py"],
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
                        "reason": (
                            "Token evidence inspected by this producer exposes "
                            "an independently useful child boundary"
                        ),
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

    @staticmethod
    def documentation_depth(
        document="runtime.md",
        unknown="Recovery ownership after a failed transition",
    ):
        return {
            "anchor_document": document,
            "anchor": "Runtime lifecycle / failure transition",
            "known": "The document establishes normal lifecycle ownership",
            "unknown": unknown,
            "completion_evidence": "Failure call paths and recovery state transitions",
            "excludes": ["deployment", "unrelated protocols"],
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

    def test_frontier_child_must_come_from_producer_inspected_evidence(self):
        self.write_candidate()
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        payload = self.payload()
        payload["evidence_inspected"] = ["src/identity.py"]

        error = self.accept(checker, payload, expected=2)

        self.assertIn("only evidence inspected by this producer", error["error"])
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

    def test_existing_spine_requires_documentation_plan_before_assignment(self):
        ledger = self.root / "existing/campaign.json"
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Complete the existing Spine",
            "--spine-state",
            "existing",
        )
        error = self.cli(
            "add",
            str(ledger),
            "runtime",
            "--parent",
            "root",
            "--question",
            "Map runtime",
            "--origin",
            "runtime composition",
            expected=2,
        )

        self.assertIn("seed-from-spine", error["error"])

    def test_seed_from_spine_records_complete_inventory_and_gap_frontier(self):
        ledger = self.root / "existing/campaign.json"
        spine = self.root / "existing/specspine"
        plan = self.root / "existing/plan.json"
        spine.mkdir(parents=True)
        (spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        (spine / "runtime.md").write_text("# Runtime\n", encoding="utf-8")
        plan.write_text(
            json.dumps(
                {
                    "evidence_inspected": ["README.md", "runtime.md"],
                    "directions": [
                        {
                            "id": "runtime-failures",
                            "question": "Are runtime failure boundaries sufficient?",
                            "documents": ["runtime.md"],
                            "signals": [
                                {
                                    "type": "missing_depth",
                                    "detail": "Recovery behavior is absent",
                                }
                            ],
                            "depth": self.documentation_depth(
                                unknown="Are runtime failure boundaries sufficient?"
                            ),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Complete the existing Spine",
            "--spine-state",
            "existing",
        )

        receipt = self.cli(
            "seed-from-spine",
            str(ledger),
            str(spine),
            str(plan),
        )
        stored = json.loads(ledger.read_text())

        self.assertEqual(["runtime-failures"], receipt["directions"])
        self.assertEqual(2, receipt["documents"])
        self.assertEqual(
            "existing_spine",
            stored["branches"]["runtime-failures"]["plan_origin"],
        )
        self.assertEqual(
            {"README.md", "runtime.md"},
            set(stored["documentation_plan"]["documents"]),
        )
        self.assertEqual(64, len(stored["documentation_plan"]["digest"]))
        self.cli(
            "assign",
            str(ledger),
            "runtime-failures",
            "--owner",
            "/root/runtime",
        )

    def test_seed_from_spine_rejects_partial_document_inventory(self):
        ledger = self.root / "partial/campaign.json"
        spine = self.root / "partial/specspine"
        plan = self.root / "partial/plan.json"
        spine.mkdir(parents=True)
        (spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        (spine / "runtime.md").write_text("# Runtime\n", encoding="utf-8")
        plan.write_text(
            json.dumps(
                {
                    "evidence_inspected": ["README.md"],
                    "directions": [
                        {
                            "id": "runtime",
                            "question": "Check runtime",
                            "documents": ["README.md"],
                            "signals": [
                                {
                                    "type": "coverage_gap",
                                    "detail": "Runtime is partial",
                                }
                            ],
                            "depth": self.documentation_depth(
                                "README.md", "Check runtime"
                            ),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Complete the existing Spine",
            "--spine-state",
            "existing",
        )

        error = self.cli(
            "seed-from-spine",
            str(ledger),
            str(spine),
            str(plan),
            expected=2,
        )

        self.assertIn("does not cover the live Spine", error["error"])

    def test_seed_from_spine_rejects_direction_without_depth_witness(self):
        ledger = self.root / "shallow/campaign.json"
        spine = self.root / "shallow/specspine"
        plan = self.root / "shallow/plan.json"
        spine.mkdir(parents=True)
        (spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        plan.write_text(
            json.dumps(
                {
                    "evidence_inspected": ["README.md"],
                    "directions": [
                        {
                            "id": "runtime",
                            "question": "Map runtime more deeply",
                            "documents": ["README.md"],
                            "signals": [
                                {"type": "missing_depth", "detail": "Too broad"}
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Complete the Spine",
            "--spine-state",
            "existing",
        )

        error = self.cli(
            "seed-from-spine", str(ledger), str(spine), str(plan), expected=2
        )

        self.assertIn("documentation depth witness", error["error"])

    def test_seed_from_spine_rejects_depth_anchor_outside_owner_set(self):
        ledger = self.root / "anchor/campaign.json"
        spine = self.root / "anchor/specspine"
        plan = self.root / "anchor/plan.json"
        spine.mkdir(parents=True)
        (spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        (spine / "runtime.md").write_text("# Runtime\n", encoding="utf-8")
        direction = {
            "id": "runtime-failure",
            "question": "Who owns recovery?",
            "documents": ["runtime.md"],
            "signals": [{"type": "missing_depth", "detail": "Recovery is absent"}],
            "depth": self.documentation_depth("README.md"),
        }
        plan.write_text(
            json.dumps(
                {
                    "evidence_inspected": ["README.md", "runtime.md"],
                    "directions": [direction],
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Complete the Spine",
            "--spine-state",
            "existing",
        )

        error = self.cli(
            "seed-from-spine", str(ledger), str(spine), str(plan), expected=2
        )

        self.assertIn("anchor must be one of its owner documents", error["error"])

    def test_seed_from_spine_rejects_question_wider_than_depth_unknown(self):
        ledger = self.root / "wide-question/campaign.json"
        spine = self.root / "wide-question/specspine"
        plan = self.root / "wide-question/plan.json"
        spine.mkdir(parents=True)
        (spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        plan.write_text(
            json.dumps(
                {
                    "evidence_inspected": ["README.md"],
                    "directions": [
                        {
                            "id": "runtime",
                            "question": "Map all runtime behavior",
                            "documents": ["README.md"],
                            "signals": [
                                {"type": "missing_depth", "detail": "Recovery is absent"}
                            ],
                            "depth": self.documentation_depth(
                                "README.md", "Who owns failed-start recovery?"
                            ),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Complete the Spine",
            "--spine-state",
            "existing",
        )

        error = self.cli(
            "seed-from-spine", str(ledger), str(spine), str(plan), expected=2
        )

        self.assertIn("question must equal its narrower depth unknown", error["error"])

    def test_seed_from_spine_allows_evidence_based_empty_plan(self):
        ledger = self.root / "complete/campaign.json"
        spine = self.root / "complete/specspine"
        plan = self.root / "complete/plan.json"
        spine.mkdir(parents=True)
        (spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        plan.write_text(
            json.dumps(
                {
                    "evidence_inspected": ["README.md"],
                    "directions": [],
                    "terminal_reason": (
                        "no documentation-derived direction: all owners pass "
                        "the documentation quality gate"
                    ),
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Complete the existing Spine",
            "--spine-state",
            "existing",
        )

        receipt = self.cli(
            "seed-from-spine", str(ledger), str(spine), str(plan)
        )

        self.assertEqual([], receipt["directions"])
        self.cli(
            "discovery-pass",
            str(ledger),
            "--evidence",
            "composition roots checked for undocumented owners",
        )

    def test_documentation_pass_reopens_frontier_when_questions_remain(self):
        ledger = self.root / "review/campaign.json"
        spine = self.root / "review/specspine"
        plan = self.root / "review/plan.json"
        spine.mkdir(parents=True)
        (spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
        plan.write_text(
            json.dumps(
                {
                    "evidence_inspected": ["README.md"],
                    "directions": [
                        {
                            "id": "runtime-depth",
                            "question": "Does runtime need deeper coverage?",
                            "documents": ["README.md"],
                            "signals": [
                                {
                                    "type": "coverage_gap",
                                    "detail": "Runtime is still partially mapped",
                                }
                            ],
                            "depth": self.documentation_depth(
                                "README.md", "Does runtime need deeper coverage?"
                            ),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
        )

        receipt = self.cli(
            "documentation-pass", str(ledger), str(spine), str(plan)
        )
        summary = self.cli("summary", str(ledger))

        self.assertEqual("gaps_found", receipt["status"])
        self.assertEqual(["runtime-depth"], summary["ready"])
        self.assertFalse(
            summary["terminal_gates"]["documentation_questions_empty"]
        )
        self.assertFalse(summary["terminal_gates"]["problem_list_empty"])
        self.assertIsNone(summary["terminal"])

    def test_integration_pass_reviews_published_relationships_and_organization(self):
        self.write_candidate()
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        payload = self.payload(candidates=True, frontier=False)
        payload["status"] = "publish_and_locally_saturate"
        payload["continuation"] = None
        payload["terminal_reason"] = (
            "no useful node: candidate passes the complete local quality gate"
        )
        payload["relationships"] = ["Identity depends on session storage"]
        self.accept(checker, payload)
        self.cli("close", str(self.ledger), "identity")
        report = self.root / "integration.json"
        report.write_text(
            json.dumps(
                {
                    "evidence_inspected": ["domains/identity.md"],
                    "relationship_review": [],
                    "organization": {
                        "status": "flat_sufficient",
                        "reason": "One document remains navigable",
                    },
                }
            ),
            encoding="utf-8",
        )
        error = self.cli(
            "integration-pass",
            str(self.ledger),
            str(self.spine),
            str(report),
            "--checker",
            str(checker),
            expected=2,
        )
        self.assertIn("disposition every", error["error"])
        value = json.loads(report.read_text())
        value["relationship_review"] = [
            {
                "branch": "identity",
                "disposition": "integrated",
                "reason": "Canonical edge and navigation were checked",
            }
        ]
        report.write_text(json.dumps(value), encoding="utf-8")

        receipt = self.cli(
            "integration-pass",
            str(self.ledger),
            str(self.spine),
            str(report),
            "--checker",
            str(checker),
        )

        self.assertEqual("integrated", receipt["status"])
        self.assertEqual(["identity"], receipt["reviewed_branches"])

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

    def test_used_producer_requires_fresh_handle_for_top_level_domain(self):
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
        self.cli("release", str(self.ledger), "identity")

        error = self.cli(
            "assign",
            str(self.ledger),
            "runtime",
            "--owner",
            "/root/identity",
            expected=2,
        )

        self.assertIn("fresh producer required", error["error"])

    def test_root_added_child_requires_fresh_producer(self):
        self.cli(
            "add",
            str(self.ledger),
            "identity-manual-child",
            "--parent",
            "identity",
            "--question",
            "Map a child found later by the root",
            "--origin",
            "root integration review",
        )
        self.cli("release", str(self.ledger), "identity")

        error = self.cli(
            "assign",
            str(self.ledger),
            "identity-manual-child",
            "--owner",
            "/root/identity",
            expected=2,
        )
        self.assertIn("fresh producer required", error["error"])
        self.cli(
            "assign",
            str(self.ledger),
            "identity-manual-child",
            "--owner",
            "/root/identity_child_fresh",
        )

    def test_producer_can_reuse_only_child_it_reported_in_checkpoint(self):
        self.write_candidate()
        checker = self.checker("import json\nprint(json.dumps([]))\n")
        payload = self.payload(candidates=True, frontier=True)
        payload["status"] = "publish_and_locally_saturate"
        payload["continuation"] = None
        payload["terminal_reason"] = (
            "no useful node: parent is complete and exposed a related child"
        )
        self.accept(checker, payload)

        self.cli(
            "assign",
            str(self.ledger),
            "identity-tokens",
            "--owner",
            "/root/identity",
        )

        stored = json.loads(self.ledger.read_text())
        child = stored["branches"]["identity-tokens"]
        self.assertEqual("/root/identity", child["discovered_by_owner"])
        self.assertEqual("identity", child["discovered_from_branch"])

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
            documentation_plan = root / "documentation-plan.json"
            integration_report = root / "integration-report.json"
            checker = root / "checker.py"
            spine.mkdir()
            staging.mkdir()
            (spine / "README.md").write_text("# Architecture\n", encoding="utf-8")
            checker.write_text("import json\nprint(json.dumps([]))\n", encoding="utf-8")
            documentation_plan.write_text(
                json.dumps(
                    {
                        "evidence_inspected": ["README.md"],
                        "directions": [],
                        "terminal_reason": (
                            "no documentation-derived direction: final Spine "
                            "has no remaining coverage question"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            integration_report.write_text(
                json.dumps(
                    {
                        "evidence_inspected": ["README.md"],
                        "relationship_review": [],
                        "organization": {
                            "status": "flat_sufficient",
                            "reason": "The single index needs no directory",
                        },
                    }
                ),
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
                    "integration-pass",
                    str(ledger),
                    str(spine),
                    str(integration_report),
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
                    "documentation-pass",
                    str(ledger),
                    str(spine),
                    str(documentation_plan),
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
            self.assertTrue(all(receipt["terminal_gates"].values()))
            self.assertEqual(
                {
                    "created": 0,
                    "replaced": 0,
                    "published_paths": 0,
                    "markdown_total": 1,
                },
                receipt["changes"],
            )
            (spine / "README.md").write_text(
                "# Architecture changed after review\n", encoding="utf-8"
            )
            stale = subprocess.run(
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
            self.assertEqual(2, stale.returncode)
            self.assertIn("changed after", stale.stderr)


if __name__ == "__main__":
    unittest.main()
