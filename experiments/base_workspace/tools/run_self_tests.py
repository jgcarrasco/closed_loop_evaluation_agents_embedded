from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


from bench_public import create_visible_artifact_dir, refresh_latest_artifact


def _test_targets(args: list[str]) -> list[str]:
    if args:
        return args
    return ["discover", "-s", "agent_tests", "-p", "test*.py", "-v"]


def _has_agent_tests() -> bool:
    agent_tests_dir = WORKSPACE_ROOT / "agent_tests"
    if not agent_tests_dir.exists():
        return False
    return any(path.is_file() and path.name.startswith("test") and path.suffix == ".py" for path in agent_tests_dir.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run agent-authored self-tests in agent_tests/.")
    parser.add_argument("targets", nargs="*", help="Optional unittest targets. Defaults to discovery under agent_tests/.")
    args = parser.parse_args()

    artifact_dir = create_visible_artifact_dir("self_tests")
    stdout_path = artifact_dir / "stdout.log"
    stderr_path = artifact_dir / "stderr.log"

    if not _has_agent_tests():
        message = "No agent-authored tests were found under agent_tests/."
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(message + "\n", encoding="utf-8")
        result = {
            "success": False,
            "returncode": 1,
            "artifact_dir": str(artifact_dir),
            "command": ["python3", "-m", "unittest", *(_test_targets(args.targets))],
            "commentary": message,
        }
        (artifact_dir / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        refresh_latest_artifact("self_tests", artifact_dir)
        print(message)
        return 1

    env = os.environ.copy()
    env["EMBEDDED_EVAL_SELF_TEST_RUN_ROOT"] = str(artifact_dir / "cases")
    completed = subprocess.run(
        ["python3", "-m", "unittest", *(_test_targets(args.targets))],
        cwd=WORKSPACE_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    result = {
        "success": completed.returncode == 0,
        "returncode": completed.returncode,
        "artifact_dir": str(artifact_dir),
        "command": ["python3", "-m", "unittest", *(_test_targets(args.targets))],
        "stdout_path": str(stdout_path.relative_to(WORKSPACE_ROOT)),
        "stderr_path": str(stderr_path.relative_to(WORKSPACE_ROOT)),
    }
    (artifact_dir / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    refresh_latest_artifact("self_tests", artifact_dir)

    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
