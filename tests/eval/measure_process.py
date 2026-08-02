#!/usr/bin/env python3
"""Execute a command and write wait4 resource usage as JSON."""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        raise SystemExit("usage: measure_process.py METRICS_PATH COMMAND [ARG ...]")
    metrics_path = Path(sys.argv[1])
    command = sys.argv[2:]
    child = os.fork()
    if child == 0:
        os.execvp(command[0], command)
    _, status, usage = os.wait4(child, 0)
    rss_multiplier = 1 if platform.system() == "Darwin" else 1024
    metrics_path.write_text(
        json.dumps(
            {
                "user_cpu_seconds": usage.ru_utime,
                "system_cpu_seconds": usage.ru_stime,
                "peak_rss_bytes": usage.ru_maxrss * rss_multiplier,
            }
        ),
        encoding="utf-8",
    )
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return 128 + os.WTERMSIG(status)
    return 1


if __name__ == "__main__":
    sys.exit(main())
