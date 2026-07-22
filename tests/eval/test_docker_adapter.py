import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("adapters") / "docker.py"
LAUNCHER_PATH = Path(__file__).with_name("docker") / "run-comparisons.sh"
SPEC = importlib.util.spec_from_file_location("specspine_docker_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ADAPTER
SPEC.loader.exec_module(ADAPTER)


class DockerAdapterTests(unittest.TestCase):
    def test_launcher_forwards_comparison_arguments_unchanged(self):
        launcher = LAUNCHER_PATH.read_text(encoding="utf-8")
        self.assertIn('compare_args=("$@")', launcher)
        self.assertIn('"${compare_args[@]}"', launcher)
        self.assertIn("SPECSPINE_EVAL_DOCKER_CONTROLLER=1", launcher)
        for option in ("--agent-command=*", "--judge-command=*", "--experiment=*", "--comparison=*"):
            self.assertIn(option, launcher)

    def test_image_reference_is_content_addressed(self):
        reference = ADAPTER.image_reference()
        self.assertRegex(reference, r"^specspine-eval-agent:[0-9a-f]{16}$")
        self.assertEqual(64, len(ADAPTER.image_source_hash()))

    def test_security_args_are_restrictive_and_ephemeral(self):
        arguments = ADAPTER.common_security_args(123, 456)
        rendered = " ".join(arguments)
        self.assertIn("--read-only", arguments)
        self.assertIn("--cap-drop=ALL", rendered)
        self.assertIn("--security-opt=seccomp=unconfined", arguments)
        self.assertIn("no-new-privileges", rendered)
        self.assertIn("/runtime:rw,nosuid,nodev", rendered)
        self.assertIn("uid=123,gid=456", rendered)

    def test_environment_failure_is_machine_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ADAPTER.write_environment_failure(root, "node unavailable")
            trace = json.loads((root / ".eval" / "trace.json").read_text(encoding="utf-8"))
            self.assertTrue(trace["environment_invalid"])
            self.assertEqual(["node unavailable"], trace["environment_errors"])

    def test_cached_image_is_reused_under_a_lock(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            ADAPTER, "cache_root", return_value=Path(directory)
        ), mock.patch.object(
            ADAPTER, "inspect_image", return_value="sha256:image"
        ) as inspect, mock.patch.object(
            ADAPTER, "run_preflight"
        ) as preflight, mock.patch.object(
            ADAPTER.shutil, "which", return_value="/usr/bin/docker"
        ), mock.patch.object(
            ADAPTER.subprocess, "run"
        ) as run:
            reference, image_id = ADAPTER.ensure_image()
            self.assertEqual(ADAPTER.image_reference(), reference)
            self.assertEqual("sha256:image", image_id)
            inspect.assert_called_once_with(reference)
            preflight.assert_called_once()
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
