import hashlib
import json
import re
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
            "**ID:** `project-architecture` · **Kind:** `index`\n\n"
            "Architecture fixture.\n\n"
            "## Architecture map\n\n"
            "The fixture has one source boundary.\n\n"
            "<!-- specspine:evidence-baseline "
            "source=fixture; inspected=2026-07-28 -->\n"
            "<!-- specspine:semantic-ids:begin -->\n"
            "## Observed\n\n"
            "- **OBS-architecture-root** — Broad system owner. "
            "Evidence: `src/identity/session.py`, `pyproject.toml`.\n"
            "<!-- specspine:semantic-ids:end -->\n",
            encoding="utf-8",
        )
        (self.spine / "specspine.json").write_text(
            json.dumps(
                {
                    "specspine": 3,
                    "project": "fixture",
                    "implementation_freedom": "contract-equivalent",
                    "areas": [],
                    "assets": [],
                }
            ),
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
        self.integration_index = 0
        self.current_workspace = None

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

    def draft_evidence(self, task_id):
        marker = self.ledger_value()["tasks"][task_id]["evidence_baseline"]
        return f"\n{marker}\n"

    def add_spine_candidate(self, filename, document_id, evidence):
        (self.spine / filename).write_text(
            f"# {document_id}\n\n"
            f"**ID:** `{document_id}` · **Kind:** `concept`\n\n"
            "Candidate owner fixture.\n\n"
            "## Responsibility\n\n"
            "Owns the candidate boundary.\n\n"
            "<!-- specspine:evidence-baseline "
            "source=fixture; inspected=2026-07-28 -->\n"
            "<!-- specspine:semantic-ids:begin -->\n"
            "## Observed\n\n"
            f"- **OBS-{document_id}** — Candidate evidence exists. "
            f"Evidence: `{evidence}`.\n"
            "<!-- specspine:semantic-ids:end -->\n",
            encoding="utf-8",
        )
        with (self.spine / "README.md").open("a", encoding="utf-8") as stream:
            stream.write(f"\n- [{document_id}]({filename}) — candidate.\n")
        manifest_path = self.spine / "specspine.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["areas"].append(
            {
                "owner": document_id,
                "facets": {
                    name: "missing"
                    for name in (
                        "architecture",
                        "behavior",
                        "interfaces",
                        "data",
                        "failure",
                        "quality",
                        "verification",
                    )
                },
                "blockers": [],
            }
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def topic_plan_path(self):
        inventory = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        grouped = {}
        for path in inventory["production_files"]:
            value = Path(path)
            unit = (
                "repository-root/manifests"
                if len(value.parts) == 1
                and value.name
                in {
                    "Makefile",
                    "go.mod",
                    "go.work",
                    "package.json",
                    "pyproject.toml",
                }
                else (
                    "repository-root/runtime"
                    if len(value.parts) == 1
                    else value.parent.as_posix()
                )
            )
            grouped.setdefault(unit, []).append(path)
        topics = []
        used = set()
        for index, (unit, files) in enumerate(sorted(grouped.items()), start=1):
            slug = re.sub(r"[^a-z0-9]+", "-", unit.lower()).strip("-")
            topic_id = slug
            if topic_id in used:
                topic_id = f"{slug}-{index}"
            used.add(topic_id)
            topics.append(
                {
                    "id": topic_id,
                    "title": unit,
                    "responsibility": f"Observed responsibility for {unit}",
                    "reason": f"Fixture semantic plan for {unit}",
                    "files": files,
                }
            )
        plan = self.run / "topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": topics,
                    "covered": [],
                    "supporting": [],
                    "open_leads": [],
                }
            ),
            encoding="utf-8",
        )
        return plan

    def discovery_corpus_path(self):
        corpus = self.run / "discovery-corpus.json"
        if corpus.exists():
            return corpus
        scope = self.run / "scope.json"
        scope.write_text(
            json.dumps(
                {
                    "kind": "repository",
                    "title": "Whole repository",
                    "question": "Map the whole repository",
                    "inclusion_rule": "All repository architecture is in scope.",
                    "exclusion_rule": "Only mechanically excluded support is out of scope.",
                }
            ),
            encoding="utf-8",
        )
        discovery = self.run / "discovery"
        self.cli(
            "discovery-start",
            str(self.repository),
            str(self.spine),
            str(scope),
            str(discovery),
            "--inventory-accelerator",
        )
        results = self.run / "discovery-results"
        for packet_path in sorted(discovery.rglob("lead-*.json")):
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            lead = packet["lead"]
            result_path = results / packet_path.relative_to(discovery)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(
                json.dumps(
                    {
                        "lead_id": lead["id"],
                        "status": "leaf",
                        "reason": "Fixture discovery leaf.",
                        "inspected": {
                            "files": lead["seed_files"],
                            "queries": [],
                        },
                        "topics": [],
                        "supporting": (
                            [
                                {
                                    "reason": "Fixture disposition.",
                                    "files": lead["seed_files"],
                                }
                            ]
                            if lead["seed_files"]
                            else []
                        ),
                        "child_leads": [],
                    }
                ),
                encoding="utf-8",
            )
        self.cli(
            "discovery-collect",
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(corpus),
        )
        return corpus

    def source_pass(self, *, expected=0):
        plan = self.topic_plan_path()
        return self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(plan),
            expected=expected,
        )

    def task_for_unit(self, unit):
        ledger = self.ledger_value()
        topics = [
            topic
            for topic in ledger["source_pass"]["topic_plan"]["topics"]
            if topic["title"] == unit
        ]
        self.assertEqual(1, len(topics), unit)
        task_id = ledger["source_pass"]["topic_tasks"][topics[0]["id"]]
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
        if outcome in {"covered", "answered"}:
            payload["owner"] = (
                {
                    "document": owner_document,
                    "claims": owner_claim_ids or ["OBS-architecture-root"],
                }
            )
        elif outcome == "retry":
            payload["need"] = ["src/identity/recovery.py"]
        elif outcome in {"blocked", "supporting", "unresolved"}:
            payload["reason"] = "External evidence is unavailable"
        return payload

    def accept(self, task_id, payload, *, owner="/root/producer-1", expected=0):
        self.checkpoint.write_text(json.dumps(payload), encoding="utf-8")
        attempt = self.ledger_value()["tasks"][task_id]["attempts"]
        harvest_receipt = self.run / f"harvest-{task_id}-{attempt}.json"
        harvest = subprocess.run(
            [
                sys.executable,
                str(CAMPAIGN),
                "harvest",
                str(self.ledger),
                task_id,
                str(self.checkpoint),
                str(self.staging),
                str(self.spine),
                "--owner",
                owner,
                "--output",
                str(harvest_receipt),
                "--checker",
                str(self.checker),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        harvest_payload = json.loads(harvest.stdout or harvest.stderr)
        if harvest.returncode != 0:
            self.assertEqual(expected, harvest.returncode, harvest.stderr)
            return harvest_payload
        self.assertEqual(0, harvest.returncode, harvest.stderr)
        return self.cli(
            "accept",
            str(self.ledger),
            task_id,
            str(self.checkpoint),
            str(self.staging),
            str(self.spine),
            "--owner",
            owner,
            "--harvest-receipt",
            str(harvest_receipt),
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

    def unresolved_anchored_task(self, task_id="session-recovery"):
        self.source_pass()
        source_task, _ = self.task_for_unit("src/identity")
        self.covered(source_task, "src/identity/session.py")
        todo = {
            "id": task_id,
            "question": "Who owns failed session recovery?",
            "reason": "Recovery ownership remains unspecified",
            "evidence": ["src/identity/session.py"],
            "documents": ["README.md"],
            "excludes": [],
            "anchor": {
                "document": "README.md",
                "location": "Architecture map",
                "known": "Normal session ownership is documented",
            },
        }
        workspace = self.prepare_integration()
        self.integrate(
            self.integration_report(todo=[todo], workspace=workspace),
            workspace=workspace,
        )
        owner = "/root/producer-unresolved"
        self.assign(task_id, owner)
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="unresolved",
                evidence=["src/identity/session.py"],
            ),
            owner=owner,
        )
        return task_id

    def prepare_integration(self):
        self.integration_index += 1
        workspace = self.run / f"integration-workspace-{self.integration_index}"
        self.cli(
            "prepare-integration",
            str(self.ledger),
            str(self.spine),
            str(workspace),
        )
        self.current_workspace = workspace
        return workspace

    def integration_report(self, *, todo=None, omit_suggestions=False, workspace=None):
        workspace = workspace or self.current_workspace or self.prepare_integration()
        raw_todo = todo or []
        for value in raw_todo:
            value.setdefault("basis", "repository-observation")
            anchor = value.get("anchor")
            if anchor is None:
                continue
            anchor.setdefault("question", value["question"])
            document = workspace / anchor["document"]
            body = document.read_text(encoding="utf-8")
            if value["question"] not in body:
                document.write_text(
                    body + f"\n- {value['question']}\n",
                    encoding="utf-8",
                )
        ledger = self.ledger_value()
        before = ledger.get("spine_snapshot")
        if before is None:
            before = (ledger.get("integration_pass") or {}).get("documents")
        if before is None:
            before = (ledger.get("documentation_seed") or {}).get("documents", {})
        after = {
            path.relative_to(workspace).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(workspace.rglob("*.md"))
        }
        manifest = workspace / "specspine.json"
        if manifest.is_file():
            after["specspine.json"] = hashlib.sha256(
                manifest.read_bytes()
            ).hexdigest()
        changed_documents = [
            {
                "path": path,
                "operation": (
                    "created"
                    if path not in before
                    else "deleted"
                    if path not in after
                    else "changed"
                ),
            }
            for path in sorted(before.keys() | after.keys())
            if before.get(path) != after.get(path)
        ]
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
                    else "answered_canonical"
                    if task.get("checkpoint_outcome") == "answered"
                    else "still_open"
                    if task.get("checkpoint_outcome") == "unresolved"
                    else "already_canonical"
                    if task["state"] == "review"
                    else "integrated"
                ),
                "reason": "Root integration confirmed the producer result",
                **(
                    {
                        "anchor_disposition": {
                            "status": (
                                "still-open"
                                if task.get("checkpoint_outcome") == "unresolved"
                                else "resolved"
                            ),
                            "reason": "Root reviewed the originating question",
                        }
                    }
                    if task.get("anchor") is not None
                    else {}
                ),
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
        return {
            "evidence_inspected": sorted(
                path.relative_to(workspace).as_posix()
                for path in workspace.rglob("*.md")
            ),
            "changed_documents": changed_documents,
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

    def integrate(self, report=None, *, workspace=None, expected=0):
        workspace = workspace or self.current_workspace or self.prepare_integration()
        path = self.run / "integration.json"
        path.write_text(
            json.dumps(report or self.integration_report(workspace=workspace)),
            encoding="utf-8",
        )
        result = self.cli(
            "integration-pass",
            str(self.ledger),
            str(self.spine),
            str(workspace),
            str(path),
            "--checker",
            str(self.checker),
            expected=expected,
        )
        self.current_workspace = None
        return result

    def verify_all_source_units(self):
        self.source_pass()
        ledger = self.ledger_value()
        queued = ledger["source_pass"]["todo"]
        for index, task_id in enumerate(queued):
            samples = ledger["tasks"][task_id]["evidence"]
            owner = f"/root/producer-{index}"
            self.assign(task_id, owner)
            self.accept(
                task_id,
                self.checkpoint_payload(outcome="covered", evidence=samples),
                owner=owner,
            )
        self.integrate()

    def test_init_uses_current_schema_and_private_ledger(self):
        ledger = self.ledger_value()
        self.assertEqual(11, ledger["schema_version"])
        contract = ROOT / "skills/specspine-map/references/producer-task.md"
        self.assertEqual(5, ledger["producer_contract_version"])
        self.assertEqual(
            hashlib.sha256(contract.read_bytes()).hexdigest(),
            ledger["producer_contract_digest"],
        )
        self.assertEqual({}, ledger["tasks"])
        self.assertEqual(0o600, self.ledger.stat().st_mode & 0o777)

    def test_inventory_returns_flat_production_files_and_exclusions(self):
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
        self.assertEqual(
            ["pyproject.toml", "src/identity/session.py"],
            first["production_files"],
        )
        self.assertEqual(
            ["tests/session_test.py"],
            first["excluded"]["test-only"],
        )

    def test_source_pass_queues_semantic_topics_over_discovery_scope(self):
        receipt = self.source_pass()
        self.assertEqual("repository", receipt["scope_kind"])
        self.assertEqual(2, receipt["evidence_files"])
        self.assertEqual(2, receipt["topics"])
        self.assertEqual(2, receipt["verification_todo"])
        self.assertEqual(2, receipt["added_todo_count"])
        self.assertNotIn("added_todo", receipt)
        ledger = self.ledger_value()
        self.assertEqual(
            "repository",
            ledger["source_pass"]["scope"]["kind"],
        )
        self.assertTrue(
            all(ledger["tasks"][task_id]["state"] == "todo"
                for task_id in ledger["source_pass"]["todo"])
        )

    def test_ready_and_todo_can_limit_large_frontier_output(self):
        self.source_pass()

        ready = self.cli("ready", str(self.ledger), "--limit", "1")
        todo = self.cli("todo", str(self.ledger), "--limit", "1")

        self.assertEqual(1, ready["returned"])
        self.assertEqual(2, ready["total"])
        self.assertEqual(1, len(ready["ready"]))
        self.assertEqual(1, todo["returned"])
        self.assertEqual(2, todo["total"])
        self.assertEqual(1, len(todo["todo"]))

    def test_ready_prioritizes_system_breadth_before_leaf_detail(self):
        (self.repository / "main.go").write_text("package main\n", encoding="utf-8")
        for relative in (
            "cmd/server/main.go",
            "apps/advisor/app.go",
            "pkg/services/auth/service.go",
            "public/app/features/dashboard/index.ts",
        ):
            path = self.repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("production\n", encoding="utf-8")
        self.source_pass()
        by_unit = {
            unit: self.task_for_unit(unit)[0]
            for unit in (
                "repository-root/runtime",
                "repository-root/manifests",
                "cmd/server",
                "apps/advisor",
                "pkg/services/auth",
            )
        }
        ready = self.cli("ready", str(self.ledger), "--limit", "5")["ready"]
        self.assertEqual(
            [
                by_unit["repository-root/runtime"],
                by_unit["repository-root/manifests"],
                by_unit["cmd/server"],
                by_unit["apps/advisor"],
                by_unit["pkg/services/auth"],
            ],
            ready,
        )

    def test_inventory_keeps_large_production_inventory_flat(self):
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
        files = [
            value
            for value in inventory["production_files"]
            if value.startswith("packages/big/")
        ]
        self.assertEqual(401, len(files))
        self.assertEqual(401, len(set(files)))

    def test_repository_discovery_uses_flat_inventory_as_neutral_accelerator(self):
        for directory in ("alpha", "beta"):
            root = self.repository / "packages/big" / directory
            root.mkdir(parents=True)
            for index in range(70):
                (root / f"file_{index:03d}.ts").write_text(
                    f"export const value{index} = {index};\n",
                    encoding="utf-8",
                )
        scope = self.run / "scope.json"
        scope.write_text(
            json.dumps(
                {
                    "kind": "repository",
                    "title": "Repository",
                    "question": "Map the repository",
                    "inclusion_rule": "All architecture is in scope.",
                    "exclusion_rule": "Mechanical support files are excluded.",
                }
            ),
            encoding="utf-8",
        )
        discovery = self.run / "discovery"
        receipt = self.cli(
            "discovery-start",
            str(self.repository),
            str(self.spine),
            str(scope),
            str(discovery),
            "--inventory-accelerator",
            "--page-size",
            "80",
        )
        packets = [json.loads(Path(path).read_text()) for path in receipt["packets"]]
        inventory = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        paged = [
            path
            for packet in packets
            for path in packet["lead"]["seed_files"]
        ]
        self.assertEqual(inventory["production_files"], paged)
        self.assertTrue(
            all(
                set(packet)
                == {
                    "discovery_contract_version",
                    "repository_root",
                    "spine_root",
                    "scope",
                    "lead",
                    "source_refs",
                }
                for packet in packets
            )
        )

    def test_topic_discovery_starts_without_repository_inventory(self):
        scope = self.run / "scope.json"
        scope.write_text(
            json.dumps(
                {
                    "kind": "topic",
                    "title": "Session lifecycle",
                    "question": "Fully map session lifecycle and related services",
                    "inclusion_rule": "Direct session lifecycle responsibilities.",
                    "exclusion_rule": "Unrelated runtime services.",
                }
            ),
            encoding="utf-8",
        )
        discovery = self.run / "discovery"
        receipt = self.cli(
            "discovery-start",
            str(self.repository),
            str(self.spine),
            str(scope),
            str(discovery),
        )
        self.assertFalse(receipt["inventory_accelerator"])
        self.assertEqual(0, receipt["seed_files"])
        packet = json.loads(Path(receipt["packets"][0]).read_text())
        self.assertEqual("scope-root", packet["lead"]["id"])
        self.assertEqual([], packet["lead"]["seed_files"])

    def test_discovery_collect_requires_every_seed_result(self):
        self.discovery_corpus_path()
        discovery = self.run / "discovery"
        results = self.run / "discovery-results"
        first = sorted(results.rglob("lead-*.json"))[0]
        first.unlink()
        corpus = self.run / "second-corpus.json"
        error = self.cli(
            "discovery-collect",
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(corpus),
            expected=2,
        )
        self.assertIn("missing discovery result", error["error"])

    def test_discovery_collect_rejects_unclosed_child_frontier(self):
        scope = self.run / "scope.json"
        scope.write_text(
            json.dumps(
                {
                    "kind": "topic",
                    "title": "Sessions",
                    "question": "Map sessions",
                    "inclusion_rule": "Session responsibilities.",
                    "exclusion_rule": "Unrelated services.",
                }
            ),
            encoding="utf-8",
        )
        discovery = self.run / "discovery"
        self.cli(
            "discovery-start",
            str(self.repository),
            str(self.spine),
            str(scope),
            str(discovery),
        )
        packet_path = next(discovery.rglob("lead-*.json"))
        results = self.run / "results"
        result_path = results / packet_path.relative_to(discovery)
        result_path.parent.mkdir(parents=True)
        result_path.write_text(
            json.dumps(
                {
                    "lead_id": "scope-root",
                    "status": "expanded",
                    "reason": "A child responsibility was exposed.",
                    "inspected": {
                        "files": ["src/identity/session.py"],
                        "queries": ["session"],
                    },
                    "topics": [
                        {
                            "id": "sessions",
                            "title": "Sessions",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Session evidence.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "supporting": [],
                    "child_leads": [
                        {
                            "id": "session-storage",
                            "title": "Session storage",
                            "question": "Who stores sessions?",
                            "reason": "The lifecycle references durable state.",
                            "seed_files": ["src/identity/session.py"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        error = self.cli(
            "discovery-collect",
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(self.run / "corpus.json"),
            expected=2,
        )
        self.assertIn("frontier is not closed", error["error"])

    def test_topic_discovery_closes_recursive_semantic_frontier(self):
        scope = self.run / "scope.json"
        scope.write_text(
            json.dumps(
                {
                    "kind": "topic",
                    "title": "Sessions",
                    "question": "Fully map sessions and related services",
                    "inclusion_rule": "Direct session lifecycle responsibilities.",
                    "exclusion_rule": "Unrelated services.",
                }
            ),
            encoding="utf-8",
        )
        discovery = self.run / "discovery"
        self.cli(
            "discovery-start",
            str(self.repository),
            str(self.spine),
            str(scope),
            str(discovery),
        )
        root_packet = next(discovery.rglob("lead-*.json"))
        results = self.run / "results"
        root_result = results / root_packet.relative_to(discovery)
        root_result.parent.mkdir(parents=True)
        root_result.write_text(
            json.dumps(
                {
                    "lead_id": "scope-root",
                    "status": "expanded",
                    "reason": "Session persistence needs one deeper pass.",
                    "inspected": {
                        "files": [
                            "pyproject.toml",
                            "src/identity/session.py",
                        ],
                        "queries": ["session"],
                    },
                    "topics": [
                        {
                            "id": "session-lifecycle",
                            "title": "Session lifecycle",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Runtime evidence.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "supporting": [],
                    "child_leads": [
                        {
                            "id": "runtime-manifest",
                            "title": "Session runtime manifest",
                            "question": "How is the session runtime composed?",
                            "reason": "The runtime dependency remains unclassified.",
                            "seed_files": ["pyproject.toml"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        frontier = self.run / "frontier.json"
        frontier.write_text(
            json.dumps(
                {
                    "decisions": [
                        {
                            "disposition": "queue",
                            "sources": ["scope-root/runtime-manifest"],
                            "lead": {
                                "id": "session-runtime-manifest",
                                "title": "Session runtime manifest",
                                "question": "How is the session runtime composed?",
                                "reason": "The runtime dependency needs classification.",
                                "parent_ids": ["scope-root"],
                                "seed_files": ["pyproject.toml"],
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        wave = discovery / "wave-0002"
        receipt = self.cli(
            "discovery-packets",
            str(discovery / "discovery-seed.json"),
            str(frontier),
            str(wave),
        )
        child_packet = Path(receipt["packets"][0])
        child_result = results / child_packet.relative_to(discovery.resolve())
        child_result.parent.mkdir(parents=True)
        child_result.write_text(
            json.dumps(
                {
                    "lead_id": "session-runtime-manifest",
                    "status": "leaf",
                    "reason": "The manifest is supporting composition evidence.",
                    "inspected": {
                        "files": ["pyproject.toml"],
                        "queries": ["project"],
                    },
                    "topics": [],
                    "supporting": [
                        {
                            "reason": "Supporting runtime manifest.",
                            "files": ["pyproject.toml"],
                        }
                    ],
                    "child_leads": [],
                }
            ),
            encoding="utf-8",
        )
        corpus = self.run / "topic-corpus.json"
        collected = self.cli(
            "discovery-collect",
            str(discovery / "discovery-seed.json"),
            str(discovery),
            str(results),
            str(corpus),
        )
        self.assertEqual("topic", collected["scope_kind"])
        self.assertEqual(2, collected["leads"])
        self.assertEqual(2, collected["evidence_files"])

    def test_synthesis_open_leads_reopen_discovery_and_block_source_pass(self):
        plan = self.run / "open-topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [],
                    "covered": [],
                    "supporting": [],
                    "open_leads": [
                        {
                            "id": "session-recovery",
                            "title": "Session recovery",
                            "question": "Who owns session recovery?",
                            "reason": "Discovery exposed an unexpanded failure boundary.",
                            "seed_files": ["src/identity/session.py"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        corpus = self.discovery_corpus_path()
        error = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(corpus),
            "--topic-plan",
            str(plan),
            expected=2,
        )
        self.assertIn("open discovery leads", error["error"])
        reopened = self.cli(
            "discovery-reopen",
            str(self.run / "discovery/discovery-seed.json"),
            str(plan),
            str(self.run / "discovery/wave-0002"),
        )
        self.assertEqual(1, reopened["reopened"])

    def test_source_pass_rejects_incomplete_or_conflicting_topic_plan(self):
        incomplete = self.run / "incomplete-topic-plan.json"
        incomplete.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "id": "sessions",
                            "title": "Sessions",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Session implementation evidence.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "covered": [],
                    "supporting": [],
                    "open_leads": [],
                }
            ),
            encoding="utf-8",
        )
        error = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(incomplete),
            expected=2,
        )
        self.assertIn("leaves evidence files uncovered", error["error"])

        conflict = self.run / "conflicting-topic-plan.json"
        conflict.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "id": "sessions",
                            "title": "Sessions",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Session implementation evidence.",
                            "files": ["src/identity/session.py"],
                        }
                    ],
                    "covered": [],
                    "supporting": [
                        {
                            "reason": "Manifest supporting context.",
                            "files": ["src/identity/session.py", "pyproject.toml"],
                        }
                    ],
                    "open_leads": [],
                }
            ),
            encoding="utf-8",
        )
        error = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(conflict),
            expected=2,
        )
        self.assertIn("both topic-covered and supporting", error["error"])

    def test_source_pass_allows_file_in_multiple_semantic_topics(self):
        plan = self.run / "overlapping-topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [
                        {
                            "id": "session-lifecycle",
                            "title": "Session lifecycle",
                            "responsibility": "Owns session lifecycle.",
                            "reason": "Session implementation evidence.",
                            "files": ["src/identity/session.py"],
                        },
                        {
                            "id": "runtime-composition",
                            "title": "Runtime composition",
                            "responsibility": "Composes runtime identity behavior.",
                            "reason": "Manifest and session module jointly configure runtime.",
                            "files": [
                                "pyproject.toml",
                                "src/identity/session.py",
                            ],
                        },
                    ],
                    "covered": [],
                    "supporting": [],
                    "open_leads": [],
                }
            ),
            encoding="utf-8",
        )

        receipt = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(plan),
        )
        self.assertEqual(2, receipt["topics"])
        self.assertEqual(2, receipt["verification_todo"])

    def test_source_pass_skips_topics_covered_by_existing_spine_claims(self):
        plan = self.run / "covered-topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [],
                    "covered": [
                        {
                            "id": "existing-architecture",
                            "title": "Existing architecture",
                            "responsibility": "Owns the fixture architecture.",
                            "reason": "The responsibility is architecturally durable.",
                            "files": [
                                "pyproject.toml",
                                "src/identity/session.py",
                            ],
                            "coverage_reason": (
                                "The canonical architecture observation already "
                                "describes this responsibility."
                            ),
                            "coverage": [
                                {
                                    "document": "README.md",
                                    "claims": ["OBS-architecture-root"],
                                }
                            ],
                        }
                    ],
                    "supporting": [],
                    "open_leads": [],
                }
            ),
            encoding="utf-8",
        )

        receipt = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(plan),
        )

        self.assertEqual(0, receipt["topics"])
        self.assertEqual(1, receipt["covered_topics"])
        self.assertEqual(0, receipt["verification_todo"])
        ledger = self.ledger_value()
        self.assertEqual({}, ledger["source_pass"]["topic_tasks"])
        self.assertEqual([], ledger["source_pass"]["todo"])

    def test_source_pass_rejects_covered_topic_without_defined_claim(self):
        plan = self.run / "invalid-covered-topic-plan.json"
        plan.write_text(
            json.dumps(
                {
                    "topics": [],
                    "covered": [
                        {
                            "id": "existing-architecture",
                            "title": "Existing architecture",
                            "responsibility": "Owns the fixture architecture.",
                            "reason": "The responsibility is architecturally durable.",
                            "files": [
                                "pyproject.toml",
                                "src/identity/session.py",
                            ],
                            "coverage_reason": "An unsupported coverage decision.",
                            "coverage": [
                                {
                                    "document": "README.md",
                                    "claims": ["OBS-not-defined"],
                                }
                            ],
                        }
                    ],
                    "supporting": [],
                    "open_leads": [],
                }
            ),
            encoding="utf-8",
        )

        error = self.cli(
            "source-pass",
            str(self.ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(plan),
            expected=2,
        )

        self.assertIn("claim is not defined", error["error"])

    def test_inventory_does_not_group_unrelated_sibling_directories(self):
        for relative in (
            "pkg/apimachinery/common/types.go",
            "pkg/apis/iam/types.go",
            "pkg/apiserver/filters/request.go",
        ):
            path = self.repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("package fixture\n", encoding="utf-8")

        inventory = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        self.assertTrue(
            {
                "pkg/apimachinery/common/types.go",
                "pkg/apis/iam/types.go",
                "pkg/apiserver/filters/request.go",
            }.issubset(inventory["production_files"])
        )
        self.assertNotIn("areas", inventory)

    def test_generated_protobuf_and_mock_files_are_not_queued(self):
        root = self.repository / "src/identity"
        (root / "messages.pb.go").write_text("package identity", encoding="utf-8")
        (root / "service_mock.go").write_text("package identity", encoding="utf-8")

        inventory = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        generated = inventory["excluded"]["generated"]

        self.assertIn("src/identity/messages.pb.go", generated)
        self.assertIn("src/identity/service_mock.go", generated)

    def test_nested_tests_fixtures_and_generated_files_are_not_queued(self):
        root = self.repository / "src/identity"
        (root / "testdata").mkdir()
        (root / "test-data").mkdir()
        (root / "generated").mkdir()
        (root / "testdata/case.json").write_text("{}", encoding="utf-8")
        (root / "test-data/case.json").write_text("{}", encoding="utf-8")
        (root / "generated/client.ts").write_text("export {}", encoding="utf-8")
        (root / "session_test.go").write_text("package identity", encoding="utf-8")
        source = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        terminal_members = {
            path for values in source["excluded"].values() for path in values
        }
        self.assertIn("src/identity/testdata/case.json", terminal_members)
        self.assertIn("src/identity/test-data/case.json", terminal_members)
        self.assertIn("src/identity/generated/client.ts", terminal_members)
        self.assertIn("src/identity/session_test.go", terminal_members)
        self.assertEqual(
            ["pyproject.toml", "src/identity/session.py"],
            source["production_files"],
        )

    def test_static_assets_locks_and_github_files_are_not_production_topics(self):
        additions = {
            "public/img/icon.svg": "<svg/>",
            "public/locales/en-US/messages.json": "{}",
            "go.sum": "checksum",
            ".github/workflows/build.yml": "name: build",
            ".gitignore": "dist/",
            "packages/ui/LICENSE_APACHE2": "license",
            "packages/ui/src/Button.mdx": "# Button",
            "packages/ui/tsconfig.build.json": "{}",
        }
        for relative, body in additions.items():
            path = self.repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

        inventory = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )

        self.assertIn("public/img/icon.svg", inventory["excluded"]["opaque-asset"])
        self.assertIn(
            "public/locales/en-US/messages.json",
            inventory["excluded"]["opaque-asset"],
        )
        self.assertIn("go.sum", inventory["excluded"]["dependency-lock"])
        self.assertIn(
            ".github/workflows/build.yml",
            inventory["excluded"]["repository-support"],
        )
        for relative in (
            ".gitignore",
            "packages/ui/LICENSE_APACHE2",
            "packages/ui/src/Button.mdx",
            "packages/ui/tsconfig.build.json",
        ):
            self.assertIn(relative, inventory["excluded"]["repository-support"])

    def test_candidate_owner_search_uses_every_member_not_only_samples(self):
        root = self.repository / "src/identity"
        for index in range(25):
            (root / f"module_{index:02d}.py").write_text(
                f"VALUE = {index}\n",
                encoding="utf-8",
            )
        self.add_spine_candidate(
            "late-owner.md",
            "late-owner",
            "src/identity/module_24.py",
        )
        self.source_pass()
        _, task = self.task_for_unit("src/identity")
        self.assertIn("late-owner.md", task["documents"])
        self.assertTrue(task["evidence_strata"])
        self.assertEqual(26, len(task["evidence_strata"]))
        self.assertEqual(
            task["evidence"],
            [value["sample"] for value in task["evidence_strata"]],
        )

    def test_candidate_owner_packet_is_bounded(self):
        for index in range(20):
            self.add_spine_candidate(
                f"candidate-{index:02d}.md",
                f"candidate-{index:02d}",
                "src/identity",
            )
        self.source_pass()
        _, task = self.task_for_unit("src/identity")
        self.assertGreaterEqual(len(task["documents"]), 1)
        self.assertLessEqual(len(task["documents"]), 12)

    def test_local_editor_directories_are_repository_support(self):
        editor = self.repository / ".vscode"
        editor.mkdir()
        (editor / "settings.json").write_text("{}", encoding="utf-8")
        source = self.cli(
            "inventory",
            str(self.repository),
            "--spine-root",
            str(self.spine),
        )
        self.assertIn(
            ".vscode/settings.json",
            source["excluded"]["repository-support"],
        )
        self.assertNotIn(".vscode/settings.json", source["production_files"])

    def test_broad_existing_owner_cannot_eliminate_verification_todo(self):
        self.source_pass()
        task_id, task = self.task_for_unit("src/identity")
        self.assertIn("README.md", task["documents"])
        self.assertEqual("todo", task["state"])
        self.assertIn(task_id, self.cli("ready", str(self.ledger))["ready"])
        packet = self.cli("packet", str(self.ledger), task_id)
        self.assertEqual(task_id, packet["task"]["id"])
        self.assertEqual(5, packet["producer_contract"]["version"])
        self.assertEqual(
            self.ledger_value()["producer_contract_digest"],
            packet["producer_contract"]["digest"],
        )
        self.assertTrue(packet["task"]["evidence_strata"])
        packet_path = self.run / "packets" / f"{task_id}.json"
        receipt = self.cli(
            "packet",
            str(self.ledger),
            task_id,
            "--output",
            str(packet_path),
        )
        self.assertEqual("written", receipt["status"])
        self.assertEqual(task_id, json.loads(packet_path.read_text())["task"]["id"])

    def test_discover_recent_incomplete_campaign_recommends_operator_resume(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)

        result = self.cli(
            "discover",
            str(self.root),
            str(self.repository),
        )

        self.assertTrue(result["requires_operator_choice"])
        self.assertEqual(1, len(result["campaigns"]))
        campaign = result["campaigns"][0]
        self.assertEqual(str(self.ledger.resolve()), campaign["ledger"])
        self.assertEqual("recent", campaign["recency"])
        self.assertTrue(campaign["source_current"])
        self.assertTrue(campaign["resume_allowed"])
        self.assertEqual("resume", campaign["recommendation"])
        self.assertTrue(campaign["requires_operator_choice"])
        self.assertEqual(1, campaign["states"]["assigned"])

    def test_discover_finds_campaign_interrupted_before_source_pass(self):
        early_ledger = self.root / "early" / "campaign.json"
        self.cli(
            "init",
            str(early_ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
            "--repository-root",
            str(self.repository),
        )

        result = self.cli(
            "discover",
            str(self.root),
            str(self.repository),
        )

        self.assertEqual(1, len(result["campaigns"]))
        campaign = result["campaigns"][0]
        self.assertEqual(str(early_ledger.resolve()), campaign["ledger"])
        self.assertEqual("source_pass_missing", campaign["incomplete_reason"])
        self.assertIsNone(campaign["source_current"])
        self.assertTrue(campaign["resume_allowed"])

    def test_discover_stale_campaign_recommends_new_but_requires_choice(self):
        self.source_pass()
        ledger = self.ledger_value()
        ledger["updated_at"] = "2000-01-01T00:00:00Z"
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        result = self.cli(
            "discover",
            str(self.root),
            str(self.repository),
        )

        campaign = result["campaigns"][0]
        self.assertEqual("stale", campaign["recency"])
        self.assertEqual("new", campaign["recommendation"])
        self.assertTrue(campaign["requires_operator_choice"])

    def test_resume_session_releases_orphaned_assigned_producers(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)

        receipt = self.cli("resume-session", str(self.ledger))

        self.assertEqual("resumed", receipt["status"])
        self.assertEqual([task_id], receipt["released_orphaned_tasks"])
        ledger = self.ledger_value()
        self.assertEqual("todo", ledger["tasks"][task_id]["state"])
        self.assertIsNone(ledger["tasks"][task_id]["owner"])
        self.assertEqual(
            [task_id],
            ledger["resume_history"][-1]["released_orphaned_tasks"],
        )

    def test_resume_session_rejects_missing_contract_metadata(self):
        ledger = self.ledger_value()
        del ledger["producer_contract_version"]
        del ledger["producer_contract_digest"]
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        error = self.cli("resume-session", str(self.ledger), expected=2)
        self.assertIn(
            "campaign does not use the current producer contract",
            error["error"],
        )

    def test_previous_campaign_schema_is_rejected_without_migration(self):
        ledger = self.ledger_value()
        ledger["schema_version"] = 10
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        error = self.cli("summary", str(self.ledger), expected=2)

        self.assertIn("unsupported campaign schema", error["error"])
        self.assertIn("expected 11", error["error"])

    def test_contract_change_requires_new_campaign(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        ledger = self.ledger_value()
        ledger["producer_contract_digest"] = "0" * 64
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        packet_error = self.cli(
            "packet",
            str(self.ledger),
            task_id,
            expected=2,
        )
        self.assertIn("start a new campaign", packet_error["error"])
        error = self.cli("resume-session", str(self.ledger), expected=2)
        self.assertIn("start a new campaign", error["error"])

    def test_changed_source_disables_and_refuses_resume(self):
        self.source_pass()
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = False\n",
            encoding="utf-8",
        )

        result = self.cli(
            "discover",
            str(self.root),
            str(self.repository),
        )
        campaign = result["campaigns"][0]
        self.assertFalse(campaign["source_current"])
        self.assertFalse(campaign["resume_allowed"])
        self.assertEqual("new", campaign["recommendation"])
        error = self.cli("resume-session", str(self.ledger), expected=2)
        self.assertIn("source snapshot changed", error["error"])

    def test_discover_excludes_unrelated_repository_campaign(self):
        self.source_pass()
        unrelated = self.root / "unrelated"
        unrelated.mkdir()

        result = self.cli("discover", str(self.root), str(unrelated))

        self.assertFalse(result["requires_operator_choice"])
        self.assertEqual([], result["campaigns"])

    def test_campaign_records_and_updates_activity_timestamps(self):
        before = self.ledger_value()
        self.assertIsNotNone(before["created_at"])
        self.assertEqual(before["created_at"], before["updated_at"])

        self.source_pass()

        after = self.ledger_value()
        self.assertEqual(before["created_at"], after["created_at"])
        self.assertGreaterEqual(after["updated_at"], before["updated_at"])

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
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(self.topic_plan_path()),
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
        self.assertEqual(2, receipt["documents"])
        self.assertEqual([], receipt["added_todo"])
        self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(self.topic_plan_path()),
        )

    def test_documentation_seed_rejects_non_v3_spine(self):
        ledger = self.run / "invalid-existing.json"
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
            "--spine-state",
            "existing",
            "--repository-root",
            str(self.repository),
        )
        manifest_path = self.spine / "specspine.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["specspine"] = 2
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        error = self.cli(
            "seed-from-spine",
            str(ledger),
            str(self.spine),
            expected=2,
        )

        self.assertIn("current SpecSpine v3", error["error"])
        self.assertIn("MANIFEST_VERSION", error["error"])

    def test_documentation_seed_records_current_v3_defects_as_baseline(self):
        ledger = self.run / "defective-v3.json"
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
            "--spine-state",
            "existing",
            "--repository-root",
            str(self.repository),
        )
        with (self.spine / "README.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## Coverage\n\nNon-semantic status in a v3 document.\n")

        receipt = self.cli("seed-from-spine", str(ledger), str(self.spine))

        self.assertGreater(receipt["checker_baseline_findings"], 0)
        baseline = json.loads(ledger.read_text(encoding="utf-8"))
        self.assertIn(
            "COMPLETENESS_IN_MARKDOWN",
            {
                finding["code"]
                for finding in baseline["documentation_seed"]["checker_baseline"]
            },
        )
        self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(self.topic_plan_path()),
        )

    def test_old_producer_contract_version_is_rejected(self):
        ledger = self.ledger_value()
        ledger["producer_contract_version"] = 1
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        error = self.cli("resume-session", str(self.ledger), expected=2)

        self.assertIn("current producer contract", error["error"])
        self.assertIn("start a new campaign", error["error"])

    def test_source_pass_rejects_checker_finding_added_after_seed(self):
        ledger = self.run / "new-defect-after-seed.json"
        self.cli(
            "init",
            str(ledger),
            "--scope",
            "whole repository",
            "--root-question",
            "Map repository",
            "--spine-state",
            "existing",
            "--repository-root",
            str(self.repository),
        )
        self.cli("seed-from-spine", str(ledger), str(self.spine))
        with (self.spine / "README.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## Coverage\n\nNew non-semantic status.\n")

        error = self.cli(
            "source-pass",
            str(ledger),
            str(self.repository),
            str(self.spine),
            "--discovery-corpus",
            str(self.discovery_corpus_path()),
            "--topic-plan",
            str(self.topic_plan_path()),
            expected=2,
        )

        self.assertIn("COMPLETENESS_IN_MARKDOWN", error["error"])

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
        self.assertIn("every evidence stratum", error["error"])

    def test_covered_by_owner_waits_for_root_integration(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        receipt = self.covered(task_id, "src/identity/session.py")
        self.assertEqual("review", receipt["task_state"])
        summary = self.cli("summary", str(self.ledger))
        self.assertFalse(summary["terminal_gates"]["publications_integrated"])

    def test_harvest_is_read_only_and_accept_rejects_changed_handoff(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        staged = self.staging / "identity.md"
        staged.write_text(
            "# Identity\n\n- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        self.checkpoint.write_text(
            json.dumps(
                self.checkpoint_payload(
                    outcome="draft",
                    evidence=["src/identity/session.py"],
                )
            ),
            encoding="utf-8",
        )
        receipt_path = self.run / "harvest.json"
        before = self.ledger_value()
        receipt = self.cli(
            "harvest",
            str(self.ledger),
            task_id,
            str(self.checkpoint),
            str(self.staging),
            str(self.spine),
            "--owner",
            "/root/producer-1",
            "--output",
            str(receipt_path),
            "--checker",
            str(self.checker),
        )
        self.assertEqual(before, self.ledger_value())
        self.assertEqual("harvested", receipt["status"])
        repeated = self.cli(
            "harvest",
            str(self.ledger),
            task_id,
            str(self.checkpoint),
            str(self.staging),
            str(self.spine),
            "--owner",
            "/root/producer-1",
            "--output",
            str(receipt_path),
            "--checker",
            str(self.checker),
        )
        self.assertEqual("already_harvested", repeated["status"])
        self.assertEqual(before, self.ledger_value())
        staged.write_text("# Changed after harvest\n", encoding="utf-8")
        error = self.cli(
            "accept",
            str(self.ledger),
            task_id,
            str(self.checkpoint),
            str(self.staging),
            str(self.spine),
            "--owner",
            "/root/producer-1",
            "--harvest-receipt",
            str(receipt_path),
            "--checker",
            str(self.checker),
            expected=2,
        )
        self.assertIn("changed after harvest", error["error"])
        self.assertEqual("assigned", self.ledger_value()["tasks"][task_id]["state"])

    def test_wave_commands_derive_paths_without_shell_parsing(self):
        self.source_pass()
        ledger = self.ledger_value()
        handoffs = self.run / "handoffs with spaces"
        harvest = self.run / "harvest receipts"
        assigned = []
        for index, task in enumerate(ledger["tasks"].values()):
            owner = f"/root/producer-{index}"
            self.assign(task["id"], owner)
            package = handoffs / f"{task['id']}-1"
            staging = package / "staging"
            staging.mkdir(parents=True)
            evidence = task["evidence"]
            (package / "checkpoint.json").write_text(
                json.dumps(
                    self.checkpoint_payload(
                        outcome="covered",
                        evidence=evidence,
                    )
                ),
                encoding="utf-8",
            )
            assigned.append(task["id"])

        before = self.ledger_value()
        harvested = self.cli(
            "harvest-wave",
            str(self.ledger),
            str(handoffs),
            str(self.spine),
            str(harvest),
            "--checker",
            str(self.checker),
        )
        self.assertEqual(2, harvested["harvested"])
        self.assertEqual(0, harvested["pending"])
        self.assertEqual(before, self.ledger_value())

        repeated = self.cli(
            "harvest-wave",
            str(self.ledger),
            str(handoffs),
            str(self.spine),
            str(harvest),
            "--checker",
            str(self.checker),
        )
        self.assertEqual(2, repeated["already_harvested"])
        accepted = self.cli(
            "accept-wave",
            str(self.ledger),
            str(handoffs),
            str(self.spine),
            str(harvest),
            "--checker",
            str(self.checker),
        )
        self.assertEqual(2, accepted["accepted"])
        self.assertEqual(
            {task_id: "review" for task_id in assigned},
            accepted["task_states"],
        )

    def test_harvest_wave_reports_invalid_handoff_without_hiding_valid_sibling(self):
        self.source_pass()
        ledger = self.ledger_value()
        handoffs = self.run / "handoffs"
        harvest = self.run / "harvest"
        tasks = list(ledger["tasks"].values())
        for index, task in enumerate(tasks):
            owner = f"/root/producer-{index}"
            self.assign(task["id"], owner)
            package = handoffs / f"{task['id']}-1"
            (package / "staging").mkdir(parents=True)
            evidence = task["evidence"]
            outcome = "answered" if index == 0 else "covered"
            (package / "checkpoint.json").write_text(
                json.dumps(
                    self.checkpoint_payload(
                        outcome=outcome,
                        evidence=evidence,
                    )
                ),
                encoding="utf-8",
            )

        result = self.cli(
            "harvest-wave",
            str(self.ledger),
            str(handoffs),
            str(self.spine),
            str(harvest),
            "--checker",
            str(self.checker),
        )

        self.assertEqual(1, result["harvested"])
        self.assertEqual(1, result["rejected"])
        self.assertIn(
            "integration-derived",
            result["rejected_tasks"][0]["error"],
        )

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
            "# Identity\n\n- **OBS-identity-owner** — owner.\n"
            + self.draft_evidence(task_id),
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

    def test_normative_suggestion_can_be_preserved_without_map_todo(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        question = "What recovery guarantee should the system provide?"
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
                directions=[question],
            ),
        )
        workspace = self.prepare_integration()
        with (workspace / "README.md").open("a", encoding="utf-8") as stream:
            stream.write(f"\n- {question}\n")
        report = self.integration_report(workspace=workspace)
        suggestion = self.ledger_value()["tasks"][task_id]["producer_suggestions"][0]
        report["suggestion_reviews"] = [
            {
                "task": task_id,
                "suggestion": suggestion["id"],
                "disposition": "preserved",
                "document": "README.md",
                "reason": "Repository evidence cannot decide required policy",
            }
        ]

        self.integrate(report, workspace=workspace)

        review = self.ledger_value()["tasks"][task_id]["suggestion_reviews"][
            suggestion["id"]
        ]
        self.assertEqual("preserved", review["disposition"])
        self.assertNotIn(suggestion["id"], self.ledger_value()["tasks"])

    def test_accept_keeps_draft_private_until_checked_integration(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        self.assertFalse((self.spine / "identity.md").exists())
        workspace = self.prepare_integration()
        self.assertTrue((workspace / "identity.md").is_file())
        self.assertFalse((self.spine / "identity.md").exists())
        self.integrate(workspace=workspace)
        self.assertTrue((self.spine / "identity.md").is_file())

    def test_integration_derived_answer_uses_distinct_outcome(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        question = {
            "id": "session-runtime-owner",
            "question": "Who owns the session runtime?",
            "reason": "The owner must be addressed explicitly",
            "evidence": ["src/identity/session.py"],
            "documents": ["README.md"],
            "excludes": [],
            "anchor": {
                "document": "README.md",
                "location": "Architecture map",
                "known": "The repository root cites the session source",
            },
        }
        first_workspace = self.prepare_integration()
        with (first_workspace / "README.md").open("a", encoding="utf-8") as stream:
            stream.write("\nWho owns the session runtime?\n")
        self.integrate(
            self.integration_report(todo=[question], workspace=first_workspace),
            workspace=first_workspace,
        )
        self.assign("session-runtime-owner", "/root/producer-answer")
        receipt = self.accept(
            "session-runtime-owner",
            self.checkpoint_payload(
                outcome="answered",
                evidence=["src/identity/session.py"],
            ),
            owner="/root/producer-answer",
        )
        self.assertEqual("review", receipt["task_state"])
        report = self.integration_report()
        self.assertEqual(
            "answered_canonical",
            report["task_reviews"][0]["disposition"],
        )
        error = self.integrate(report, expected=2)
        self.assertIn("resolved anchor question remains", error["error"])
        workspace = self.prepare_integration()
        readme = workspace / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "\nWho owns the session runtime?\n",
                "\n",
            ),
            encoding="utf-8",
        )
        self.integrate(
            self.integration_report(workspace=workspace),
            workspace=workspace,
        )
        self.assertEqual(
            "complete",
            self.ledger_value()["tasks"]["session-runtime-owner"]["state"],
        )

    def test_refined_anchor_requires_named_narrower_todo(self):
        task_id = self.unresolved_anchored_task()
        report = self.integration_report()
        report["task_reviews"][0]["anchor_disposition"] = {
            "status": "refined",
            "reason": "Recovery ownership is now narrowed to retry exhaustion",
            "todo": "session-retry-owner",
        }
        error = self.integrate(report, expected=2)
        self.assertIn("needs matching integration ToDo", error["error"])

        successor = {
            "id": "session-retry-owner",
            "question": "Who owns recovery after retries are exhausted?",
            "reason": "The broader recovery question was narrowed",
            "evidence": ["src/identity/session.py"],
            "documents": ["README.md"],
            "excludes": [],
            "anchor": {
                "document": "README.md",
                "location": "Architecture map",
                "known": "Normal and failed session ownership were separated",
            },
        }
        report = self.integration_report(todo=[successor])
        report["task_reviews"][0]["anchor_disposition"] = {
            "status": "refined",
            "reason": "Recovery ownership is now narrowed to retry exhaustion",
            "todo": successor["id"],
        }
        self.integrate(report)
        self.assertEqual(
            "todo",
            self.ledger_value()["tasks"][successor["id"]]["state"],
        )

    def test_blocking_anchor_requires_owner_oq_and_manifest_registration(self):
        self.unresolved_anchored_task()
        report = self.integration_report()
        workspace = self.current_workspace
        report["task_reviews"][0]["anchor_disposition"] = {
            "status": "blocking",
            "reason": "A reconstruction agent cannot choose recovery ownership",
            "blocker": "OQ-session-recovery-owner",
        }
        error = self.integrate(report, expected=2)
        self.assertIn("must define OQ-session-recovery-owner", error["error"])

        readme = workspace / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "<!-- specspine:semantic-ids:end -->",
                "- **OQ-session-recovery-owner** — Who owns failed session recovery?\n"
                "<!-- specspine:semantic-ids:end -->",
            ),
            encoding="utf-8",
        )
        manifest_path = workspace / "specspine.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["areas"].append(
            {
                "owner": "project-architecture",
                "facets": {},
                "blockers": ["OQ-session-recovery-owner"],
            }
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        report = self.integration_report(workspace=workspace)
        report["task_reviews"][0]["anchor_disposition"] = {
            "status": "blocking",
            "reason": "A reconstruction agent cannot choose recovery ownership",
            "blocker": "OQ-session-recovery-owner",
        }
        self.integrate(report, workspace=workspace)

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

    def test_integration_checker_failure_preserves_live_spine(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        source = self.staging / "identity.md"
        source.write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
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
        )
        report = self.integration_report()
        error = self.integrate(report, expected=2)
        self.assertIn("checker rejected", error["error"])
        self.assertTrue(source.exists())
        self.assertFalse((self.spine / "identity.md").exists())
        self.assertEqual("published", self.ledger_value()["tasks"][task_id]["state"])

    def test_candidate_checker_receives_live_root_and_staging_path(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
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
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
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
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        workspace = self.prepare_integration()
        (workspace / "identity.md").unlink()
        report = self.integration_report(workspace=workspace)
        error = self.integrate(report, expected=2)
        self.assertIn("cannot discard producer publications", error["error"])

    def test_new_owner_requires_typed_graph_connection(self):
        neighbor_source = self.repository / "src/neighbor/service.py"
        neighbor_source.parent.mkdir(parents=True)
        neighbor_source.write_text("SERVICE = True\n", encoding="utf-8")
        self.add_spine_candidate(
            "neighbor.md",
            "neighbor",
            "src/neighbor/service.py",
        )
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "**ID:** `identity` · **Kind:** `component`\n\n"
            "Observed identity boundary.\n\n"
            "## Responsibility\n\n"
            "Owns observed session handling.\n\n"
            f"{self.ledger_value()['tasks'][task_id]['evidence_baseline']}\n"
            "<!-- specspine:semantic-ids:begin -->\n"
            "## Observed\n\n"
            "- **OBS-identity-owner** — Session code exists. "
            "Evidence: `src/identity/session.py`.\n"
            "<!-- specspine:semantic-ids:end -->\n",
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        workspace = self.prepare_integration()
        report = self.integration_report(workspace=workspace)

        error = self.integrate(report, workspace=workspace, expected=2)

        self.assertIn("typed relationship", error["error"])

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

    def test_integration_todo_must_match_visible_anchor_question(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        workspace = self.prepare_integration()
        todo = {
            "id": "session-recovery",
            "question": "What recovery behavior is currently observed?",
            "reason": "Recovery evidence remains incomplete",
            "basis": "repository-observation",
            "evidence": ["src/identity/session.py"],
            "documents": ["README.md"],
            "excludes": [],
            "anchor": {
                "document": "README.md",
                "location": "Architecture map",
                "known": "Normal session ownership is documented",
                "question": "What recovery behavior should be guaranteed?",
            },
        }

        report = self.integration_report(todo=[todo], workspace=workspace)
        error = self.integrate(report, workspace=workspace, expected=2)

        self.assertIn("exactly match anchor question", error["error"])

    def test_integration_rejects_normative_map_todo_basis(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        workspace = self.prepare_integration()
        todo = {
            "id": "session-policy",
            "question": "What recovery guarantee should be accepted?",
            "reason": "Policy remains undecided",
            "basis": "normative-policy",
            "evidence": ["src/identity/session.py"],
            "documents": ["README.md"],
            "excludes": [],
            "anchor": {
                "document": "README.md",
                "location": "Architecture map",
                "known": "Current behavior is observed",
                "question": "What recovery guarantee should be accepted?",
            },
        }

        report = self.integration_report(todo=[todo], workspace=workspace)
        error = self.integrate(report, workspace=workspace, expected=2)

        self.assertIn("basis must be repository-observation", error["error"])

    def test_integration_records_and_returns_exact_live_document_changes(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.assign(task_id)
        (self.staging / "identity.md").write_text(
            "# Identity\n\n"
            "- **OBS-identity-owner** — `src/identity/session.py`.\n"
            + self.draft_evidence(task_id),
            encoding="utf-8",
        )
        self.accept(
            task_id,
            self.checkpoint_payload(
                outcome="draft",
                evidence=["src/identity/session.py"],
            ),
        )
        workspace = self.prepare_integration()
        (workspace / "README.md").write_text(
            (workspace / "README.md").read_text(encoding="utf-8")
            + "\nSee [Identity](identity.md).\n",
            encoding="utf-8",
        )
        result = self.integrate(workspace=workspace)
        expected = [
            {"path": "README.md", "operation": "changed"},
            {"path": "identity.md", "operation": "created"},
        ]
        self.assertEqual(expected, result["changed_documents"])
        ledger = self.ledger_value()
        self.assertEqual(
            [
                {"publication_epoch": 1, **change}
                for change in expected
            ],
            ledger["document_change_history"],
        )
        summary = self.cli("summary", str(self.ledger))
        self.assertEqual(
            ledger["document_change_history"],
            summary["document_change_history"],
        )

    def test_integration_rejects_incomplete_document_change_report(self):
        self.source_pass()
        workspace = self.prepare_integration()
        (workspace / "README.md").write_text(
            "# Architecture\n\nChanged by root.\n",
            encoding="utf-8",
        )
        report = self.integration_report(workspace=workspace)
        report["changed_documents"] = []
        error = self.integrate(report, expected=2)
        self.assertIn(
            "does not match workspace changes",
            error["error"],
        )

    def test_integration_rejects_missing_spine_snapshot(self):
        self.source_pass()
        self.integrate()
        ledger = self.ledger_value()
        ledger.pop("spine_snapshot")
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")
        error = self.cli(
            "prepare-integration",
            str(self.ledger),
            str(self.spine),
            str(self.run / "invalid-workspace"),
            expected=2,
        )
        self.assertIn("campaign Spine snapshot is invalid", error["error"])

    def test_integration_must_review_every_covered_task(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        report = self.integration_report()
        report["task_reviews"] = []
        error = self.integrate(report, expected=2)
        self.assertIn("every settled producer task", error["error"])

    def test_scope_verified_requires_every_unit_and_empty_integration(self):
        self.verify_all_source_units()
        summary = self.cli("summary", str(self.ledger))
        self.assertEqual("scope_verified", summary["terminal"])
        self.assertTrue(all(summary["terminal_gates"].values()))
        next_action = self.cli("next-action", str(self.ledger))
        self.assertTrue(next_action["may_finish"])
        self.assertEqual("finalize", next_action["action"])
        coverage = self.cli("coverage-report", str(self.ledger))
        self.assertEqual("scope_verified", coverage["coverage_claim"])

    def test_unclean_v3_integration_requires_repair_before_finalize(self):
        self.verify_all_source_units()
        ledger = self.ledger_value()
        ledger["integration_pass"]["checker_clean"] = False
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")

        summary = self.cli("summary", str(self.ledger))
        next_action = self.cli("next-action", str(self.ledger))

        self.assertFalse(summary["terminal_gates"]["spine_v3_clean"])
        self.assertIsNone(summary["terminal"])
        self.assertEqual("repair", next_action["action"])
        self.assertFalse(next_action["may_finish"])

    def test_next_action_for_active_campaign_forbids_finishing(self):
        self.source_pass()
        next_action = self.cli("next-action", str(self.ledger))
        self.assertFalse(next_action["may_finish"])
        self.assertEqual("dispatch", next_action["action"])
        self.assertEqual(
            "continue_in_same_turn_no_final_response",
            next_action["response_policy"],
        )
        self.assertGreater(next_action["counts"]["todo"], 0)

    def test_integration_evidence_may_be_relevant_live_subset(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        report = self.integration_report()
        report["evidence_inspected"] = ["README.md"]
        result = self.integrate(report)
        self.assertEqual("integrated", result["status"])

    def test_integration_evidence_rejects_unknown_document(self):
        self.source_pass()
        task_id, _ = self.task_for_unit("src/identity")
        self.covered(task_id, "src/identity/session.py")
        report = self.integration_report()
        report["evidence_inspected"] = ["missing.md"]
        error = self.integrate(report, expected=2)
        self.assertIn("only workspace Markdown documents", error["error"])

    def test_repository_content_change_invalidates_scope_snapshot(self):
        self.verify_all_source_units()
        (self.repository / "src/identity/session.py").write_text(
            "SESSION = False\nRECOVERY = True\n",
            encoding="utf-8",
        )
        summary = self.cli("summary", str(self.ledger))
        self.assertFalse(summary["terminal_gates"]["scope_snapshot_current"])
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

    def test_finalize_requires_scope_verified(self):
        self.verify_all_source_units()
        receipt = self.cli(
            str(self.ledger),
            str(self.spine),
            "--checker",
            str(self.checker),
            script=FINALIZE,
        )
        self.assertEqual("finalized", receipt["status"])
        self.assertEqual("scope_verified", receipt["terminal"])
        self.assertEqual([], receipt["changed_documents"])
        self.assertEqual([], receipt["document_change_history"])

    def test_finalize_passes_recorded_repository_root_to_checker(self):
        self.verify_all_source_units()
        ledger = self.ledger_value()
        ledger["repository_root"] = str(self.repository.resolve())
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")
        checker = self.root / "repository-aware-checker.py"
        checker.write_text(
            "import json, pathlib, sys\n"
            "valid = '--repository-root' in sys.argv and "
            "pathlib.Path(sys.argv[sys.argv.index('--repository-root') + 1]).is_dir()\n"
            "print(json.dumps([] if valid else [{'code':'MISSING_REPOSITORY_ROOT'}]))\n"
            "raise SystemExit(0 if valid else 1)\n",
            encoding="utf-8",
        )

        receipt = self.cli(
            str(self.ledger),
            str(self.spine),
            "--checker",
            str(checker),
            script=FINALIZE,
        )

        self.assertEqual("finalized", receipt["status"])


if __name__ == "__main__":
    unittest.main()
