from __future__ import annotations

import importlib.util
import json
import os
import shlex
import shutil
import tempfile
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("specspine_eval_run", ROOT / "tests/eval/run.py")
assert SPEC is not None and SPEC.loader is not None
EVAL_RUN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EVAL_RUN
SPEC.loader.exec_module(EVAL_RUN)


def critique(**scores: int) -> dict[str, object]:
    dimensions = {
        name: {
            "score": scores.get(name, 100),
            "rationale": "test",
            "evidence": [],
        }
        for name in EVAL_RUN.DIMENSION_WEIGHTS
    }
    return {"rationale": "test", "evidence": [], "dimensions": dimensions}


class EvalScoringTests(unittest.TestCase):
    def test_bootstrap_matrix_is_executable(self) -> None:
        bootstrap = [
            scenario
            for scenario in EVAL_RUN.load_scenarios()
            if scenario.feature == "Bootstrap Specspine skills in existing workspaces"
        ]

        self.assertEqual(len(bootstrap), 7)
        self.assertEqual(
            {scenario.preparation for scenario in bootstrap},
            {
                "bootstrap-existing-docs",
                "bootstrap-custom-library",
                "bootstrap-partial-iwe",
                "bootstrap-mixed-library",
                "bootstrap-config-collision",
                "bootstrap-ambiguous-roots",
                "bootstrap-missing-iwe",
            },
        )
        ambiguous = next(
            scenario
            for scenario in bootstrap
            if scenario.preparation == "bootstrap-ambiguous-roots"
        )
        self.assertIn("Use package-a", ambiguous.reply or "")

    def test_multi_turn_codex_command_is_persistent_and_resumable(self) -> None:
        initial = EVAL_RUN.persistent_agent_command(EVAL_RUN.DEFAULT_AGENT)
        self.assertNotIn("--ephemeral", shlex.split(initial))

        resumed = shlex.split(
            EVAL_RUN.resume_agent_command(initial, "thread-123")
        )
        self.assertEqual(resumed[:3], ["codex", "exec", "resume"])
        self.assertIn("thread-123", resumed)
        self.assertNotIn("workspace-write", resumed)
        self.assertIn('sandbox_mode="workspace-write"', resumed)

    @unittest.skipUnless(shutil.which("iwe"), "IWE is required")
    def test_missing_iwe_environment_removes_only_its_binary_directory(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "feature",
            "scenario",
            "bootstrap-missing-iwe",
            ("iwe-spec-specify",),
            "request",
            "rubric",
            "missing-iwe-cli",
        )
        iwe_path = shutil.which("iwe")
        self.assertIsNotNone(iwe_path)
        environment = EVAL_RUN.environment_for_scenario(os.environ.copy(), scenario)

        self.assertIsNone(shutil.which("iwe", path=environment["PATH"]))

    def test_missing_iwe_cli_still_preinstalls_the_official_iwe_skill(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "feature",
            "scenario",
            "bootstrap-missing-iwe",
            ("iwe-spec-specify",),
            "request",
            "rubric",
            "missing-iwe-cli",
        )

        self.assertEqual(
            EVAL_RUN.required_skill_names(scenario),
            ("iwe-spec-specify", "iwe-memory-system"),
        )

    def test_bootstrap_no_change_postcondition_is_deterministic(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "feature",
            "scenario",
            "bootstrap-config-collision",
            ("iwe-spec-specify",),
            "request",
            "rubric",
        )
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / ".iwe").mkdir()
            (workspace / ".iwe/config.toml").write_text("owner config\n")
            before = EVAL_RUN.files(workspace)
            self.assertEqual(
                EVAL_RUN.bootstrap_postcondition_errors(
                    scenario, workspace, before, dict(before)
                ),
                [],
            )
            after = dict(before)
            after["created.md"] = "unexpected"
            self.assertTrue(
                EVAL_RUN.bootstrap_postcondition_errors(
                    scenario, workspace, before, after
                )
            )

    def test_fallback_postcondition_requires_real_schema_binding(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "feature",
            "scenario",
            "bootstrap-existing-docs",
            ("iwe-spec-specify",),
            "request",
            "rubric",
        )
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / ".iwe").mkdir()
            (workspace / "docs/specs").mkdir(parents=True)
            (workspace / ".iwe/config.toml").write_text(
                'version = 3\n[library]\npath = "docs"\n'
            )
            (workspace / "docs/specs/existing-owner-marker.txt").write_text("preserve me\n")

            errors = EVAL_RUN.bootstrap_postcondition_errors(
                scenario, workspace, {}, EVAL_RUN.files(workspace)
            )

            self.assertIn("bootstrap did not install the specification template", errors)
            self.assertIn("bootstrap did not bind the specification schema", errors)
            self.assertIn("bootstrap did not install the specification schema file", errors)

    def test_codex_telemetry_extracts_thread_id(self) -> None:
        raw = "\n".join(
            (
                json.dumps({"type": "thread.started", "thread_id": "thread-123"}),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": "done"},
                    }
                ),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {"input_tokens": 10, "cached_input_tokens": 4, "output_tokens": 2},
                    }
                ),
            )
        )

        final, metrics, event_log, thread_id = EVAL_RUN.parse_codex_jsonl(raw)

        self.assertEqual(final, "done")
        self.assertEqual(thread_id, "thread-123")
        self.assertEqual(metrics["total_tokens"], 12)
        self.assertEqual(event_log, raw)

    def test_command_telemetry_persists_debug_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = EVAL_RUN.CommandResult(
                0,
                "final",
                "warning",
                {},
                '{"type":"thread.started"}',
                "thread-123",
                '{"type":"thread.started"}',
                ("codex", "exec", "--ephemeral"),
                "/workspace",
                "/codex-home",
                "/codex-home/sessions",
                True,
                False,
            )

            metadata = EVAL_RUN.write_command_telemetry(directory, "agent", result, "request")

            self.assertEqual(metadata["thread_id"], "thread-123")
            self.assertFalse(metadata["session_persisted"])
            self.assertFalse(metadata["timed_out"])
            self.assertEqual((directory / "agent.jsonl").read_text(), result.raw_stdout)
            self.assertEqual((directory / "agent.stderr.txt").read_text(), "warning")
            self.assertEqual((directory / "agent.prompt.txt").read_text(), "request")

    def test_tool_inefficiency_cannot_be_hidden_by_correctness(self) -> None:
        verdict = EVAL_RUN.derive_verdict(critique(tool_efficiency=69))

        self.assertGreaterEqual(verdict["score"], EVAL_RUN.PASS_SCORE)
        self.assertFalse(verdict["pass"])
        self.assertEqual(
            verdict["floor_failures"]["tool_efficiency"],
            {"score": 69, "required": 70},
        )

    def test_resource_inefficiency_has_an_independent_floor(self) -> None:
        verdict = EVAL_RUN.derive_verdict(critique(resource_efficiency=59))

        self.assertGreaterEqual(verdict["score"], EVAL_RUN.PASS_SCORE)
        self.assertFalse(verdict["pass"])
        self.assertEqual(
            verdict["floor_failures"]["resource_efficiency"],
            {"score": 59, "required": 60},
        )

    def test_efficiency_at_the_floors_can_pass(self) -> None:
        verdict = EVAL_RUN.derive_verdict(
            critique(tool_efficiency=70, resource_efficiency=60)
        )

        self.assertTrue(verdict["pass"])
        self.assertEqual(verdict["floor_failures"], {})

    def test_agent_prompt_discloses_non_git_workspace(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "feature", "scenario", "baseline", ("iwe-spec-verify",), "request", "rubric"
        )

        prompt = EVAL_RUN.agent_prompt(scenario)

        self.assertIn("intentionally has no .git directory", prompt)
        self.assertNotIn("iwe-spec-verify", prompt)
        for hint in (
            "IWE",
            "Jest",
            ".agents/",
            "focused file inspection",
            "Git commands",
            "Act autonomously",
            "edit when requested",
            "do not install",
        ):
            self.assertNotIn(hint, prompt)

    def test_judge_prompt_ignores_only_environment_failures(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "feature", "scenario", "baseline", ("iwe-spec-verify",), "request", "rubric"
        )

        prompt = EVAL_RUN.judge_prompt(scenario, "transcript", "", {})

        self.assertIn("Ignore an attempted read-only Git", prompt)
        self.assertIn("Do not ignore destructive", prompt)
        self.assertIn("or remote Git attempts", prompt)
        self.assertIn("All other invalid commands, including incorrect IWE syntax", prompt)
        self.assertIn("Expected skill selection", prompt)
        self.assertIn("iwe-spec-verify", prompt)
        self.assertIn("iwe-memory-system", prompt)
        self.assertNotIn("calibrate tool and resource efficiency to setup work", prompt)

    def test_judge_prompt_loads_authoritative_specspine_and_skill_context(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "feature", "scenario", "baseline", ("iwe-spec-map",), "request", "rubric"
        )

        prompt = EVAL_RUN.judge_prompt(scenario, "transcript", "", {})

        self.assertIn("<specspine_framework_context>", prompt)
        self.assertIn("--- README.md ---", prompt)
        self.assertIn("--- docs/reference/format.md ---", prompt)
        self.assertIn("--- docs/reference/semantics.md ---", prompt)
        self.assertIn("--- docs/reference/conformance.md ---", prompt)
        self.assertIn("IWE owns documents, stable keys, links", prompt)
        self.assertIn("task-relevant references linked by their `SKILL.md`", prompt)
        self.assertIn("`CODEX_HOME`", prompt)
        self.assertIn(
            "higher authority than repository skill instructions, skill\n"
            "references, and the scenario rubric",
            prompt,
        )
        self.assertIn("do not reward literal skill or rubric compliance", prompt)
        self.assertIn("do not penalize the agent for rejecting", prompt)

    def test_bootstrap_judge_uses_setup_aware_efficiency_calibration(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "Bootstrap Specspine skills in existing workspaces",
            "scenario",
            "bootstrap-existing-docs",
            ("iwe-spec-specify",),
            "request",
            "rubric",
        )

        prompt = EVAL_RUN.judge_prompt(scenario, "transcript", "", {})

        self.assertIn("calibrate tool and resource efficiency to setup work", prompt)
        self.assertIn("Do not apply unusually strict", prompt)
        self.assertIn("Still penalize clearly redundant", prompt)
        self.assertIn("custom `library.path` is authoritative", prompt)
        self.assertIn("does not require\nloading the setup reference", prompt)

    def test_workspace_exposes_only_task_bounded_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            official = workspace / "official/iwe-memory-system"
            official.mkdir(parents=True)
            (official / "SKILL.md").write_text("---\nname: iwe-memory-system\n---\n")
            scenario = EVAL_RUN.Scenario(
                "feature", "scenario", "baseline", ("iwe-spec-map",), "request", "rubric"
            )

            installed_names = EVAL_RUN.install_project_skills(workspace, scenario, official)

            installed = workspace / ".agents/skills"
            self.assertEqual(installed_names, ("iwe-spec-map", "iwe-memory-system"))
            self.assertEqual(
                {path.name for path in installed.iterdir()},
                {"iwe-spec-map", "iwe-memory-system"},
            )
            bootstrap = installed / "iwe-spec-map/references/iwe-bootstrap.md"
            self.assertTrue(bootstrap.is_file())
            self.assertIn("library.path", bootstrap.read_text())
            self.assertTrue(
                (installed / "iwe-spec-map/references/specspine-format.md").is_file()
            )
            self.assertTrue(
                (installed / "iwe-spec-map/references/specspine-semantics.md").is_file()
            )

    def test_iwe_skills_require_the_shared_setup_reference(self) -> None:
        expected = "[IWE project setup](references/iwe-bootstrap.md)"
        canonical = (EVAL_RUN.ROOT / "shared/references/iwe-bootstrap.md").read_text()
        canonical_words = " ".join(canonical.split())
        self.assertIn("iwe init --auto --library docs", canonical)
        self.assertIn("existing `library.path` as authoritative", canonical)
        self.assertIn("official installation guide", canonical)
        self.assertIn("Leave the workspace unchanged while waiting", canonical_words)
        self.assertIn('key_template = "specs/{{slug}}"', canonical)
        self.assertIn('match = "specs/**"', canonical)
        self.assertIn("ask which root to use", canonical)
        self.assertIn("Do not add bootstrap scripts", canonical)
        for name in ("map", "specify", "verify", "implement"):
            skill_dir = EVAL_RUN.ROOT / f"skills/iwe-spec-{name}"
            skill = (skill_dir / "SKILL.md").read_text()
            self.assertIn(expected, skill)
            self.assertIn(
                "[Specspine format](references/specspine-format.md)", skill
            )
            self.assertIn(
                "[Specspine semantics](references/specspine-semantics.md)", skill
            )
            self.assertNotIn("iwe-readiness.sh", skill)
            self.assertIn("template, binding, or schema is missing", skill)
            self.assertIn("bundled `assets/iwe`", skill)
            self.assertEqual(
                canonical,
                (skill_dir / "references/iwe-bootstrap.md").read_text(),
            )
            self.assertTrue((skill_dir / "assets/iwe/config.toml").is_file())
            self.assertTrue(
                (skill_dir / "assets/iwe/schemas/specification.yaml").is_file()
            )
            for reference in ("format", "semantics"):
                self.assertEqual(
                    (EVAL_RUN.ROOT / f"docs/reference/{reference}.md").read_text(),
                    (skill_dir / f"references/specspine-{reference}.md").read_text(),
                )

        for name in ("verify", "implement"):
            skill_dir = EVAL_RUN.ROOT / f"skills/iwe-spec-{name}"
            skill = (skill_dir / "SKILL.md").read_text()
            self.assertIn(
                "[Specspine conformance](references/specspine-conformance.md)",
                skill,
            )
            self.assertEqual(
                (EVAL_RUN.ROOT / "docs/reference/conformance.md").read_text(),
                (skill_dir / "references/specspine-conformance.md").read_text(),
            )

    def test_shared_skill_resources_are_live_symlinks(self) -> None:
        shared = EVAL_RUN.ROOT / "shared"
        self.assertTrue((shared / "references/iwe-bootstrap.md").is_file())
        for reference in ("format", "semantics", "conformance"):
            self.assertTrue(
                (shared / f"references/specspine-{reference}.md").is_file()
            )
            documentation = EVAL_RUN.ROOT / f"docs/reference/{reference}.md"
            self.assertTrue(documentation.is_symlink())
            self.assertTrue(documentation.exists())
        self.assertTrue((shared / "assets/iwe/config.toml").is_file())
        self.assertTrue((shared / "assets/iwe/schemas/specification.yaml").is_file())

        for name in ("map", "specify", "verify", "implement"):
            skill_dir = EVAL_RUN.ROOT / f"skills/iwe-spec-{name}"
            for relative in (
                "references/iwe-bootstrap.md",
                "references/specspine-format.md",
                "references/specspine-semantics.md",
                "assets/iwe",
            ):
                link = skill_dir / relative
                self.assertTrue(link.is_symlink(), f"expected symlink: {link}")
                self.assertTrue(link.exists(), f"broken symlink: {link}")
            if name in {"verify", "implement"}:
                conformance = skill_dir / "references/specspine-conformance.md"
                self.assertTrue(conformance.is_symlink())
                self.assertTrue(conformance.exists())

        self.assertFalse((shared / "scripts").exists())
        for name in ("map", "specify", "verify", "implement"):
            self.assertFalse(
                (EVAL_RUN.ROOT / f"skills/iwe-spec-{name}/scripts").exists()
            )

    def test_iwe_skills_require_the_official_iwe_skill(self) -> None:
        for name in ("map", "specify", "verify", "implement"):
            skill = (EVAL_RUN.ROOT / f"skills/iwe-spec-{name}/SKILL.md").read_text()
            skill_words = " ".join(skill.split())
            self.assertIn("`iwe-memory-system`", skill)
            self.assertIn("official `iwe-org/skills` distribution", skill_words)
            self.assertIn("supported skill installer", skill_words)
            self.assertIn("read it before continuing", skill_words)

    def test_iwe_skills_are_agent_runtime_agnostic(self) -> None:
        forbidden = (
            "$CODEX_HOME",
            "CODEX_HOME",
            ".codex/",
            ".agents/",
            "Codex",
            "Claude",
            "Gemini",
            "isolated",
            "../iwe-spec-",
        )
        for skill_file in (EVAL_RUN.ROOT / "skills").glob("*/SKILL.md"):
            skill = skill_file.read_text()
            for value in forbidden:
                self.assertNotIn(value, skill, f"{skill_file}: {value}")

    def test_installation_scenario_starts_without_iwe_memory_skill(self) -> None:
        scenario = next(
            item
            for item in EVAL_RUN.load_scenarios()
            if item.skill_setup == "install-iwe-memory-system"
        )

        self.assertNotIn("iwe-memory-system", EVAL_RUN.required_skill_names(scenario))
        self.assertIn("iwe-memory-system", EVAL_RUN.expected_skill_names(scenario))
        command = EVAL_RUN.agent_command_for_scenario(
            EVAL_RUN.DEFAULT_AGENT, scenario, Path("/isolated-codex-home")
        )
        self.assertIn("--enable standalone_web_search", command)
        self.assertIn("sandbox_workspace_write.network_access=true", command)
        self.assertIn("--add-dir /isolated-codex-home", command)

    def test_verify_and_implement_are_independent_and_structured(self) -> None:
        verify = (EVAL_RUN.ROOT / "skills/iwe-spec-verify/SKILL.md").read_text()
        implement = (EVAL_RUN.ROOT / "skills/iwe-spec-implement/SKILL.md").read_text()

        for section in ("Scope", "Claims checked", "Findings", "Test evidence", "Verdict"):
            self.assertIn(section, verify)
        self.assertIn("pre-change assessment", implement)
        self.assertIn("post-change", implement)
        self.assertIn("Finding transitions", implement)
        self.assertNotIn("iwe-spec-verify", implement)
        self.assertIn("Pre-change assessment", implement)
        self.assertIn("Post-change assessment", implement)

    def test_implement_does_not_install_verify_as_a_dependency(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "feature", "scenario", "baseline", ("iwe-spec-implement",), "request", "rubric"
        )
        self.assertEqual(
            EVAL_RUN.required_skill_names(scenario),
            ("iwe-spec-implement", "iwe-memory-system"),
        )

    def test_map_uses_schema_valid_observation_and_inspection_shapes(self) -> None:
        skill = (EVAL_RUN.ROOT / "skills/iwe-spec-map/SKILL.md").read_text()

        self.assertIn("`## Observed`", skill)
        self.assertIn("`## Inferred`", skill)
        for mode in ("survey", "deepen", "refresh", "drift"):
            self.assertIn(f"`{mode}`", skill)
        self.assertIn("observed-only state", skill)
        self.assertIn("Observations do not make a normative facet complete", skill)

    def test_operator_requests_do_not_expose_internal_workflow(self) -> None:
        forbidden = ("$iwe-", "iwe ", ".agents/", "REQ-", "VER-", "OBS-", "INF-")

        scenarios = EVAL_RUN.load_scenarios()

        self.assertTrue(scenarios)
        for scenario in scenarios:
            with self.subTest(scenario=scenario.name):
                self.assertTrue(scenario.skills)
                for value in forbidden:
                    self.assertNotIn(value, scenario.request)

    def test_owner_local_collision_exists_before_the_agent_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            shutil.copytree(EVAL_RUN.FIXTURE / "docs/specs", workspace / "docs/specs")

            EVAL_RUN.prepare(workspace, "owner-local-id-collision")

            authentication = (workspace / "docs/specs/authentication.md").read_text()
            user_management = (workspace / "docs/specs/user-management.md").read_text()
            self.assertIn("REQ-login-policy", authentication)
            self.assertIn("REQ-login-policy", user_management)


if __name__ == "__main__":
    unittest.main()
