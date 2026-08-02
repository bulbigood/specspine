from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
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
    def test_feature_parser_preserves_ordered_operator_replies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "setup.feature"
            feature.write_text(
                'Feature: Setup\n'
                '  Scenario: Guided setup\n'
                '    Given preparation "setup-new-custom-scope"\n'
                '    And skills "iwe-spec-setup"\n'
                '    When the operator asks:\n'
                '      """\nrequest\n      """\n'
                '    And the operator replies:\n'
                '      """\nfirst\n      """\n'
                '    And the operator replies:\n'
                '      """\nsecond\n      """\n'
                '    Then the AI judge verifies:\n'
                '      """\nrubric\n      """\n',
                encoding="utf-8",
            )

            scenarios = EVAL_RUN.parse_feature(feature)

            self.assertEqual(len(scenarios), 1)
            self.assertEqual(scenarios[0].replies, ("first", "second"))

    def test_multi_turn_codex_commands_preserve_required_options(self) -> None:
        command = (
            'codex exec --json --ephemeral --ignore-user-config '
            '--skip-git-repo-check -s workspace-write -m model -c key=value -'
        )

        persistent = EVAL_RUN.persistent_agent_command(command)
        resumed = EVAL_RUN.resume_agent_command(persistent, "thread-123")

        self.assertNotIn("--ephemeral", persistent)
        self.assertIn("codex exec resume", resumed)
        self.assertIn("--json", resumed)
        self.assertIn("--ignore-user-config", resumed)
        self.assertIn('sandbox_mode="workspace-write"', resumed)
        self.assertIn("thread-123 -", resumed)

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

    def test_setup_judge_prompt_includes_ordered_interaction_context(self) -> None:
        scenario = EVAL_RUN.Scenario(
            "feature",
            "scenario",
            "setup-new-custom-scope",
            ("iwe-spec-setup",),
            "request",
            "rubric",
            ("first choice", "second choice"),
        )

        prompt = EVAL_RUN.judge_prompt(scenario, "transcript", "", {})

        self.assertIn("interactive setup scenario", prompt)
        self.assertIn("IWE was already installed", prompt)
        self.assertIn("1. first choice", prompt)
        self.assertIn("2. second choice", prompt)
        self.assertIn("iwe-spec-setup", prompt)
        self.assertIn("Do not\npenalize that inherent overhead", prompt)

    def test_setup_scenarios_target_only_the_setup_skill(self) -> None:
        setup_scenarios = [
            scenario
            for scenario in EVAL_RUN.load_scenarios()
            if scenario.preparation.startswith("setup-")
        ]

        self.assertEqual(len(setup_scenarios), 4)
        for scenario in setup_scenarios:
            self.assertEqual(scenario.skills, ("iwe-spec-setup",))
            self.assertNotIn("iwe-spec-specify", scenario.rubric)
        existing = next(
            item for item in setup_scenarios
            if item.preparation == "setup-existing-workspace"
        )
        self.assertEqual(existing.replies, ())
        self.assertIn("fast path", existing.rubric)
        self.assertTrue(
            all(
                item.replies
                for item in setup_scenarios
                if item.preparation != "setup-existing-workspace"
            )
        )

    def test_setup_scenarios_do_not_require_the_application_runtime(self) -> None:
        scenarios = EVAL_RUN.load_scenarios()

        setup = [item for item in scenarios if item.preparation.startswith("setup-")]
        operational = [item for item in scenarios if not item.preparation.startswith("setup-")]

        self.assertTrue(setup)
        self.assertTrue(operational)
        self.assertFalse(any(EVAL_RUN.requires_application_runtime(item) for item in setup))
        self.assertTrue(all(EVAL_RUN.requires_application_runtime(item) for item in operational))

    @unittest.skipUnless(shutil.which("iwe"), "IWE is required")
    def test_setup_postconditions_accept_confirmed_nested_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(
                EVAL_RUN.FIXTURE,
                workspace,
                ignore=shutil.ignore_patterns("node_modules"),
            )
            EVAL_RUN.prepare(workspace, "setup-new-custom-scope")
            before = EVAL_RUN.files(workspace)
            initialized = subprocess.run(
                ["iwe", "init", "--auto", "--library", "knowledge"],
                cwd=workspace,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                initialized.returncode,
                0,
                initialized.stderr + initialized.stdout,
            )
            intermediate = EVAL_RUN.files(workspace)
            canonical_config = (
                EVAL_RUN.ROOT / "shared/assets/iwe/config.toml"
            ).read_text(encoding="utf-8")
            fragment = canonical_config[
                canonical_config.index("[templates.specification]") :
            ].replace(
                'key_template = "specs/{{slug}}"',
                'key_template = "architecture/specs/{{slug}}"',
            ).replace('match = "specs/**"', 'match = "architecture/specs/**"')
            config = workspace / ".iwe/config.toml"
            config.write_text(
                config.read_text(encoding="utf-8").rstrip() + "\n\n" + fragment,
                encoding="utf-8",
            )
            schema = workspace / ".iwe/schemas/specification.yaml"
            schema.parent.mkdir(parents=True)
            shutil.copy2(
                EVAL_RUN.ROOT / "shared/assets/iwe/schemas/specification.yaml",
                schema,
            )
            (workspace / "knowledge/architecture/specs").mkdir(parents=True)
            final = EVAL_RUN.files(workspace)
            scenario = EVAL_RUN.Scenario(
                "feature",
                "Configure a new workspace with a nested custom scope",
                "setup-new-custom-scope",
                ("iwe-spec-setup",),
                "request",
                "rubric",
                ("reply",),
            )

            errors = EVAL_RUN.setup_postcondition_errors(
                scenario, workspace, before, [intermediate, final]
            )

            self.assertEqual(errors, [])

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
        self.assertIn("preinstalled in the isolated workspace", prompt)
        self.assertIn(
            "higher authority than repository skill instructions, skill\n"
            "references, and the scenario rubric",
            prompt,
        )
        self.assertIn("do not reward literal skill or rubric compliance", prompt)
        self.assertIn("do not penalize the agent for rejecting", prompt)

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
            self.assertFalse((installed / "iwe-spec-map/assets").exists())
            self.assertTrue(
                (installed / "iwe-spec-map/references/specspine-format.md").is_file()
            )
            self.assertTrue(
                (installed / "iwe-spec-map/references/specspine-semantics.md").is_file()
            )
            self.assertEqual(
                {
                    path.name
                    for path in (installed / "iwe-spec-map/references").iterdir()
                },
                {"specspine-format.md", "specspine-semantics.md"},
            )

    def test_eval_workspace_installs_resolved_setup_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            official = workspace / "official/iwe-memory-system"
            official.mkdir(parents=True)
            (official / "SKILL.md").write_text("---\nname: iwe-memory-system\n---\n")
            scenario = EVAL_RUN.Scenario(
                "feature",
                "scenario",
                "setup-new-custom-scope",
                ("iwe-spec-setup",),
                "request",
                "rubric",
            )

            installed_names = EVAL_RUN.install_project_skills(
                workspace, scenario, official
            )

            installed = workspace / ".agents/skills/iwe-spec-setup"
            self.assertEqual(
                installed_names,
                ("iwe-spec-setup", "iwe-memory-system"),
            )
            self.assertEqual(
                (installed / "assets/iwe/config.toml").read_bytes(),
                (EVAL_RUN.ROOT / "shared/assets/iwe/config.toml").read_bytes(),
            )
            self.assertEqual(
                (
                    installed / "assets/iwe/schemas/specification.yaml"
                ).read_bytes(),
                (
                    EVAL_RUN.ROOT
                    / "shared/assets/iwe/schemas/specification.yaml"
                ).read_bytes(),
            )

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
