from __future__ import annotations

import importlib.util
import json
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
        self.assertIn("Expected repository-local skill selection", prompt)
        self.assertIn("iwe-spec-verify", prompt)

    def test_workspace_exposes_repository_and_global_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)

            EVAL_RUN.install_project_skills(workspace)

            installed = workspace / ".agents/skills"
            expected = {
                path.parent.name
                for root in (EVAL_RUN.ROOT / "skills", EVAL_RUN.GLOBAL_SKILLS)
                if root.is_dir()
                for path in root.glob("*/SKILL.md")
            }
            self.assertTrue(expected)
            self.assertTrue(expected <= {path.name for path in installed.iterdir()})

    def test_operator_requests_do_not_expose_internal_workflow(self) -> None:
        forbidden = ("$iwe-", "iwe ", ".agents/", "REQ-", "VER-", "OBS-", "INF-")

        scenarios = EVAL_RUN.load_scenarios()

        self.assertTrue(scenarios)
        for scenario in scenarios:
            with self.subTest(scenario=scenario.name):
                self.assertTrue(scenario.skills)
                for value in forbidden:
                    self.assertNotIn(value, scenario.request)


if __name__ == "__main__":
    unittest.main()
