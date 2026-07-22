import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("adapters") / "codex.py"
SPEC = importlib.util.spec_from_file_location("specspine_codex_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ADAPTER
SPEC.loader.exec_module(ADAPTER)


class CodexAdapterTests(unittest.TestCase):
    def test_relative_files_excludes_eval_and_git_internals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("pass\n", encoding="utf-8")
            (root / ".eval").mkdir()
            (root / ".eval" / "trace.json").write_text("{}\n", encoding="utf-8")
            (root / ".git" / "objects").mkdir(parents=True)
            (root / ".git" / "objects" / "fixture").write_bytes(b"fixture")

            self.assertEqual(["src/app.py"], ADAPTER.relative_files(root))

    def test_traces_explicit_file_reads(self):
        candidates = ["src/users/model.js", "src/billing/private.js"]
        self.assertEqual(
            {"src/users/model.js"},
            ADAPTER.traced_files("sed -n '1,80p' src/users/model.js", candidates),
        )

    def test_treats_repo_wide_content_search_as_reading_all_candidates(self):
        candidates = ["src/users/model.js", "src/billing/private.js"]
        self.assertEqual(set(candidates), ADAPTER.traced_files("rg TODO .", candidates))

    def test_does_not_treat_file_listing_as_content_read(self):
        candidates = ["src/users/model.js", "src/billing/private.js"]
        self.assertEqual(set(), ADAPTER.traced_files("find . -type f", candidates))

    def test_does_not_treat_rg_file_listing_glob_as_content_read(self):
        candidates = ["README.md", "specspine/README.md"]
        command = "sed -n '1,20p' .eval/skill/SKILL.md && rg --files -g 'README.md'"
        self.assertEqual(set(), ADAPTER.traced_files(command, candidates))

    def test_traces_files_read_through_shell_glob_loop(self):
        candidates = ["specspine/README.md", "specspine/payments.md", "README.md"]
        command = "for f in specspine/*.md; do sed -n '1,200p' \"$f\"; done"
        self.assertEqual(
            {"specspine/README.md", "specspine/payments.md"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_traces_files_read_from_rg_listing_loop(self):
        candidates = ["src/api.ts", "src/payments/settlement.ts", "README.md"]
        command = "for f in $(rg --files src | sort); do sed -n '1,200p' \"$f\"; done"
        self.assertEqual(
            {"src/api.ts", "src/payments/settlement.ts"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_traces_spine_read_by_doctor_checker(self):
        candidates = ["specspine/README.md", "specspine/payments.md", "src/payment.ts"]
        command = "python3 .eval/skill/scripts/check_spine.py specspine --json"
        self.assertEqual(
            {"specspine/README.md", "specspine/payments.md"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_rg_pattern_and_glob_do_not_count_named_out_of_scope_files(self):
        candidates = ["README.md", "package.json", "specspine/README.md", "specspine/payment.md"]
        command = (
            "/bin/zsh -lc \"rg -n --glob '!README.md' "
            "'payment-webhook-retry|package.json' specspine\""
        )
        self.assertEqual(
            {"specspine/README.md", "specspine/payment.md"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_does_not_treat_echoed_path_as_content_read(self):
        candidates = ["README.md", "specspine/README.md"]
        command = "sed -n '1,40p' specspine/README.md\necho 'README.md -> payments.md'"
        self.assertEqual(
            {"specspine/README.md"},
            ADAPTER.traced_files(command, candidates),
        )

    def test_parses_commands_reads_and_agent_messages(self):
        stdout = "\n".join(
            [
                '{"item":{"type":"command_execution","command":"sed -n 1,80p src/users/model.js"}}',
                '{"item":{"type":"agent_message","text":"Finished"}}',
            ]
        )
        reads, commands, messages = ADAPTER.parse_events(stdout, ["src/users/model.js", "src/billing.js"])
        self.assertEqual({"src/users/model.js"}, reads)
        self.assertEqual(["sed -n 1,80p src/users/model.js"], commands)
        self.assertEqual(["Finished"], messages)

    def test_records_only_completed_items_once_by_id(self):
        stdout = "\n".join(
            [
                '{"type":"item.started","item":{"id":"cmd-1","type":"command_execution","command":"sed -n 1,80p src/users/model.js"}}',
                '{"type":"item.completed","item":{"id":"cmd-1","type":"command_execution","command":"sed -n 1,80p src/users/model.js"}}',
                '{"type":"item.completed","item":{"id":"cmd-1","type":"command_execution","command":"sed -n 1,80p src/users/model.js"}}',
                '{"type":"item.completed","item":{"id":"cmd-2","type":"command_execution","command":"sed -n 1,80p src/users/model.js"}}',
            ]
        )
        reads, commands, messages = ADAPTER.parse_events(
            stdout, ["src/users/model.js"]
        )
        self.assertEqual({"src/users/model.js"}, reads)
        self.assertEqual(
            [
                "sed -n 1,80p src/users/model.js",
                "sed -n 1,80p src/users/model.js",
            ],
            commands,
        )
        self.assertEqual([], messages)

    def test_parses_latest_cumulative_token_usage(self):
        stdout = "\n".join(
            [
                '{"type":"turn.completed","usage":{"input_tokens":120,"output_tokens":30}}',
                '{"type":"turn.completed","usage":{"input_tokens":200,"cached_input_tokens":80,"output_tokens":50}}',
            ]
        )
        self.assertEqual(
            {"input_tokens": 200, "cached_input_tokens": 80, "output_tokens": 50},
            ADAPTER.parse_token_usage(stdout),
        )

    def test_detects_bwrap_namespace_failure_as_environment_error(self):
        stdout = json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "status": "failed",
                    "exit_code": 1,
                    "aggregated_output": (
                        "bwrap: No permissions to create a new namespace, likely because "
                        "the kernel does not allow non-privileged user namespaces.\n"
                    ),
                },
            }
        )
        self.assertEqual(
            [
                "Codex command sandbox unavailable: "
                "bwrap: No permissions to create a new namespace, likely because "
                "the kernel does not allow non-privileged user namespaces."
            ],
            ADAPTER.environment_errors(stdout),
        )

    def test_detects_bwrap_mount_failures_from_run_005(self):
        for output in (
            "bwrap: Can't find source path /runtime/specspine-runtime-x/.agents: No such file or directory\n",
            'bwrap: Can\'t remount readonly on /newroot/workspace/.codex: Unable to find "..." in mount table\n',
        ):
            stdout = json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "status": "failed",
                        "exit_code": 1,
                        "aggregated_output": output,
                    },
                }
            )
            self.assertEqual(1, len(ADAPTER.environment_errors(stdout)))

    def test_does_not_classify_ordinary_command_failure_as_environment_error(self):
        stdout = json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "status": "failed",
                    "exit_code": 1,
                    "aggregated_output": "AssertionError: expected auditor role\n",
                },
            }
        )
        self.assertEqual([], ADAPTER.environment_errors(stdout))

    def test_does_not_classify_successful_output_mention_as_environment_error(self):
        stdout = json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "status": "completed",
                    "exit_code": 0,
                    "aggregated_output": "bwrap: No permissions to create a new namespace\n",
                },
            }
        )
        self.assertEqual([], ADAPTER.environment_errors(stdout))

    def test_archives_unfiltered_codex_streams_and_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            events = '{"type":"item.completed","item":{"type":"reasoning","text":"summary"}}\n'
            ADAPTER.write_codex_artifacts(
                target,
                prompt="Do the work.\n",
                command=["codex", "exec", "--json", "-"],
                stdout=events,
                stderr="diagnostic\n",
                returncode=7,
                duration_seconds=1.25,
            )
            self.assertEqual(events, (target / "codex-events.jsonl").read_text())
            self.assertEqual("diagnostic\n", (target / "codex-stderr.txt").read_text())
            self.assertEqual("Do the work.\n", (target / "codex-prompt.md").read_text())
            invocation = json.loads((target / "codex-invocation.json").read_text())
            self.assertEqual(7, invocation["returncode"])
            self.assertEqual(["codex", "exec", "--json", "-"], invocation["command"])

    def test_scope_audit_allows_workspace_and_rejects_external_paths(self):
        root = Path("/Users/example/.cache/specspine-eval/workspaces/run-1")
        commands = [
            f"sed -n '1,80p' {root}/src/app.py",
            "rg secret /private/var/folders/shared",
            "cat ../sibling/HANDOFF.md",
            "find / -name ARCHITECTURE.md",
            "rg --files -g '!../*'",
            "cat .eval/trace.json",
            "cat .eval/skill/SKILL.md",
        ]
        violations = ADAPTER.scope_violations(commands, root)
        self.assertEqual(3, len(violations))
        self.assertIn("/private/var/", violations[0])
        self.assertIn("filesystem-root traversal", violations[1])
        self.assertIn("evaluator internals", violations[2])

    def test_scope_audit_does_not_parse_patch_content_as_path_access(self):
        root = Path("/workspace")
        command = """/usr/bin/bash -c "apply_patch <<'PATCH'
*** Begin Patch
*** Update File: src/validations/user.validation.js
+const { roles } = require('../config/roles');
*** End Patch
PATCH"""
        self.assertEqual([], ADAPTER.scope_violations([command], root))

    def test_scope_audit_allows_eval_exclusion_filters(self):
        root = Path("/Users/example/.cache/specspine-eval/workspaces/run-1")
        commands = [
            "find . -type f -not -path './.eval/*' -print",
            "find . -type f ! -path './.eval/*' -print",
            "grep -RIn --exclude-dir=.eval TODO .",
            "grep -RIn --exclude-dir '.eval' TODO .",
            "find . -path './.eval' -prune -o -type f -print",
            "rg --files -g '!.eval/**'",
            "rg --files -g '! .eval/**'",
            (
                "/usr/bin/bash -c \"pwd && rg --files "
                "-g '\"'\"'!* .eval*'\"'\"' -g '\"'\"'! .eval/**'\"'\"' "
                "| sed -n '1,200p'\""
            ),
            "/bin/zsh -c 'find . -type f ! -path '\"'\"'./.eval/*' -print\"",
            (
                "/bin/zsh -c 'find . -type f ! -path '\"'\"'./.git/*' "
                "\"'! -path '\"'\"'./.eval/*' -print | sort\""
            ),
        ]
        self.assertEqual([], ADAPTER.scope_violations(commands, root))

    def test_sandbox_mountpoints_are_created_and_only_empty_placeholders_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            runtime = base / "runtime"
            workspace.mkdir()
            runtime.mkdir()
            (workspace / ".git").mkdir()

            created = ADAPTER.prepare_sandbox_mountpoints(workspace, runtime)

            self.assertEqual(
                [workspace / ".agents", workspace / ".codex"], created
            )
            for parent in (workspace, runtime):
                for name in ADAPTER.SANDBOX_PROTECTED_NAMES:
                    self.assertTrue((parent / name).is_dir())

            (workspace / ".agents" / "created-by-agent").write_text("keep\n")
            ADAPTER.remove_empty_mountpoints(created)
            self.assertTrue((workspace / ".agents").is_dir())
            self.assertFalse((workspace / ".codex").exists())
            self.assertTrue((workspace / ".git").is_dir())

    def test_scope_audit_still_rejects_direct_eval_access(self):
        root = Path("/Users/example/.cache/specspine-eval/workspaces/run-1")
        commands = [
            "cat .eval/trace.json",
            "find .eval -type f",
            "rg secret .eval",
            "sed -n '1,20p' .eval/codex-events.jsonl",
        ]
        violations = ADAPTER.scope_violations(commands, root)
        self.assertEqual(4, len(violations))
        self.assertTrue(all("evaluator internals" in item for item in violations))

    def test_private_codex_home_copies_only_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            runtime = root / "runtime"
            source.mkdir()
            runtime.mkdir()
            (source / "auth.json").write_text('{"token":"secret"}\n', encoding="utf-8")
            (source / "models_cache.json").write_text("stale\n", encoding="utf-8")
            (source / "config.toml").write_text("untrusted\n", encoding="utf-8")

            with mock.patch.dict(os.environ, {"CODEX_HOME": str(source)}):
                target = ADAPTER.prepare_codex_home(runtime)

            self.assertEqual('{"token":"secret"}\n', (target / "auth.json").read_text())
            self.assertEqual(0o600, (target / "auth.json").stat().st_mode & 0o777)
            self.assertEqual(["auth.json"], sorted(path.name for path in target.iterdir()))

    def test_codex_command_uses_restricted_permission_profile(self):
        command = ADAPTER.build_codex_command(
            "agent-model", "medium", Path("/workspace"), Path("/runtime")
        )
        rendered = " ".join(command)
        self.assertIn('default_permissions="specspine_eval"', command)
        self.assertIn('permissions.specspine_eval.network.enabled=false', command)
        self.assertIn('shell_environment_policy.inherit="core"', command)
        environment_argument = next(
            item for item in command if item.startswith("shell_environment_policy.set=")
        )
        self.assertIn('HOME="/runtime/home"', environment_argument)
        self.assertIn('TMPDIR="/runtime/tmp"', environment_argument)
        self.assertIn(
            'PYTHONPYCACHEPREFIX="/runtime/pycache"', environment_argument
        )
        self.assertIn(
            'GIT_CONFIG_GLOBAL="/runtime/gitconfig"', environment_argument
        )
        path_setting = environment_argument.split('PATH="', 1)[1].split('"', 1)[0]
        self.assertNotIn(str(Path.home()), path_setting)
        self.assertNotIn("pyenv", path_setting.lower())
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ignore-rules", command)
        self.assertIn("allow_login_shell=false", command)
        self.assertNotIn("workspace-write", rendered)
        self.assertNotIn('.agents"="read', rendered)
        self.assertNotIn('.codex"="read', rendered)

    def test_main_uses_and_removes_external_private_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            observed_runtime: Path | None = None

            def complete(command, **kwargs):
                nonlocal observed_runtime
                environment_argument = next(
                    item for item in command if item.startswith("shell_environment_policy.set=")
                )
                home = environment_argument.split('HOME="', 1)[1].split('"', 1)[0]
                observed_runtime = Path(home).parent
                self.assertNotEqual(root / ".eval", observed_runtime)
                self.assertEqual(root.parent.resolve(), observed_runtime.parent.resolve())
                self.assertTrue((observed_runtime / "gitconfig").is_file())
                self.assertTrue((observed_runtime / "home" / ".zprofile").is_file())
                self.assertTrue((observed_runtime / "bin" / "python").is_symlink())
                process_environment = kwargs["env"]
                private_codex_home = Path(process_environment["CODEX_HOME"])
                self.assertEqual(
                    (observed_runtime / "codex-home").resolve(),
                    private_codex_home.resolve(),
                )
                self.assertTrue(private_codex_home.is_dir())
                return ADAPTER.subprocess.CompletedProcess([], 0, "", "")

            with mock.patch.object(Path, "cwd", return_value=root), mock.patch.object(
                sys, "argv", ["codex.py"]
            ), mock.patch("sys.stdin.read", return_value="prompt"), mock.patch.object(
                ADAPTER.subprocess,
                "run",
                side_effect=complete,
            ):
                self.assertEqual(0, ADAPTER.main())

            self.assertIsNotNone(observed_runtime)
            self.assertFalse(observed_runtime.exists())
            self.assertTrue((root / ".eval" / "trace.json").is_file())

    def test_main_returns_environment_failure_for_bwrap_error(self):
        event = json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "id": "command-1",
                    "type": "command_execution",
                    "command": "/usr/bin/bash -c pwd",
                    "status": "failed",
                    "exit_code": 1,
                    "aggregated_output": "bwrap: No permissions to create a new namespace\n",
                },
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            completed = ADAPTER.subprocess.CompletedProcess([], 0, event + "\n", "")
            with mock.patch.object(Path, "cwd", return_value=root), mock.patch.object(
                sys, "argv", ["codex.py"]
            ), mock.patch("sys.stdin.read", return_value="prompt"), mock.patch.object(
                ADAPTER.subprocess, "run", return_value=completed
            ):
                self.assertEqual(70, ADAPTER.main())

            trace = json.loads((root / ".eval" / "trace.json").read_text())
            self.assertTrue(trace["environment_invalid"])
            self.assertEqual(1, len(trace["environment_errors"]))


if __name__ == "__main__":
    unittest.main()
