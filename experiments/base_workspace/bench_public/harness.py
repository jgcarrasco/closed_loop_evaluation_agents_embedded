from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_PATH = WORKSPACE_ROOT / "experiment.json"
TASK_CONTRACT_PATH = WORKSPACE_ROOT / "docs" / "20_task_contract.json"
PUBLIC_ARTIFACT_ROOT = WORKSPACE_ROOT / "artifacts" / "public"
SELF_TEST_RUN_ROOT_ENV = "EMBEDDED_EVAL_SELF_TEST_RUN_ROOT"


def _required_env_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. This workspace was launched without the hidden evaluator configured. "
            "That is an operator setup issue."
        )
    return Path(value).resolve()


def _hidden_root() -> Path:
    return _required_env_path("EMBEDDED_EVAL_HARNESS_ROOT")


def _hidden_run_root() -> Path:
    return _required_env_path("EMBEDDED_EVAL_RUN_ROOT")


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value).strip())
    slug = slug.strip(".-")
    return slug or "unspecified"


def _hidden_module(module_name: str) -> Any:
    hidden_root = _hidden_root()
    if str(hidden_root) not in sys.path:
        sys.path.insert(0, str(hidden_root))
    return importlib.import_module(module_name)


def sanitize_text(value: str) -> str:
    sanitized = str(value)
    replacements = {
        str(_hidden_root()): "hidden_harness",
        str(_hidden_run_root()): "hidden_runs",
    }
    for source, target in replacements.items():
        sanitized = sanitized.replace(source, target)
    return sanitized


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sanitize_file(path: Path) -> None:
    if not path.exists():
        return
    path.write_text(sanitize_text(path.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")


def _read_tail(path: Path, line_count: int = 40) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-line_count:])


def _extract_problem_lines(text: str, tokens: tuple[str, ...], limit: int = 20) -> list[str]:
    matches = [line.strip() for line in text.splitlines() if any(token in line.lower() for token in tokens)]
    return matches[-limit:]


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_experiment() -> dict[str, Any]:
    return json.loads(EXPERIMENT_PATH.read_text(encoding="utf-8"))


def load_task_contract() -> dict[str, Any]:
    if not TASK_CONTRACT_PATH.exists():
        return {}
    return json.loads(TASK_CONTRACT_PATH.read_text(encoding="utf-8"))


def create_visible_artifact_dir(kind: str, label: str = "") -> Path:
    safe_kind = _safe_slug(kind)
    suffix = f"-{_safe_slug(label)}" if label else ""
    artifact_dir = PUBLIC_ARTIFACT_ROOT / safe_kind / f"{_timestamp()}{suffix}"
    counter = 1
    while artifact_dir.exists():
        artifact_dir = PUBLIC_ARTIFACT_ROOT / safe_kind / f"{_timestamp()}{suffix}-{counter}"
        counter += 1
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir


def refresh_latest_artifact(kind: str, artifact_dir: Path) -> Path:
    latest_dir = PUBLIC_ARTIFACT_ROOT / _safe_slug(kind) / "latest"
    if latest_dir.exists() or latest_dir.is_symlink():
        if latest_dir.is_symlink() or latest_dir.is_file():
            latest_dir.unlink()
        else:
            shutil.rmtree(latest_dir)
    shutil.copytree(artifact_dir, latest_dir)
    return latest_dir


def self_test_artifact_dir(label: str) -> Path:
    root = os.environ.get(SELF_TEST_RUN_ROOT_ENV, "").strip()
    if root:
        artifact_dir = Path(root) / _safe_slug(label)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir
    return create_visible_artifact_dir("self_tests", label)


def sync_visible_sources() -> list[str]:
    experiment = load_experiment()
    sync_paths = [str(path) for path in experiment.get("sync_paths", experiment["editable_paths"])]
    hidden_root = _hidden_root()
    for relative in sync_paths:
        source = WORKSPACE_ROOT / relative
        target = hidden_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return sync_paths


def _run_hidden_command(
    command: list[str],
    artifact_dir: Path,
    *,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(extra_env or {})
    completed = subprocess.run(
        command,
        cwd=_hidden_root(),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout_text = sanitize_text(completed.stdout)
    stderr_text = sanitize_text(completed.stderr)
    stdout_path = artifact_dir / "stdout.log"
    stderr_path = artifact_dir / "stderr.log"
    _write_text(stdout_path, stdout_text)
    _write_text(stderr_path, stderr_text)

    payload = {
        "command": command,
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "stdout_path": str(stdout_path.relative_to(WORKSPACE_ROOT)),
        "stderr_path": str(stderr_path.relative_to(WORKSPACE_ROOT)),
        "stdout_tail": _read_tail(stdout_path),
        "stderr_tail": _read_tail(stderr_path),
        "errors": _extract_problem_lines("\n".join([stdout_text, stderr_text]), ("error", "failed", "timeout", "traceback")),
        "warnings": _extract_problem_lines("\n".join([stdout_text, stderr_text]), ("warning",)),
    }
    _write_json(artifact_dir / "result.json", payload)
    return payload


def build_firmware(artifact_dir: Path | str | None = None, *, include_flash_image: bool = False) -> dict[str, Any]:
    sync_paths = sync_visible_sources()
    artifact_root = Path(artifact_dir) if artifact_dir is not None else create_visible_artifact_dir("builds")
    artifact_root.mkdir(parents=True, exist_ok=True)

    build_result = _run_hidden_command(
        ["./tools/with_idf_env.sh", "idf.py", "build"],
        artifact_root / "build",
    )
    summary: dict[str, Any] = {
        "success": build_result["success"],
        "artifact_dir": str(artifact_root),
        "sync_paths": sync_paths,
        "build": build_result,
    }

    if include_flash_image:
        if build_result["success"]:
            flash_result = _run_hidden_command(
                ["./tools/build_flash_image.sh"],
                artifact_root / "flash_image",
                extra_env={"FLASH_IMAGE_ARTIFACT_DIR": str(artifact_root / "flash_image")},
            )
        else:
            flash_result = {
                "command": ["./tools/build_flash_image.sh"],
                "returncode": None,
                "success": False,
                "skipped": True,
                "stdout_path": "",
                "stderr_path": "",
                "stdout_tail": "",
                "stderr_tail": "",
                "errors": ["flash-image step skipped because the firmware build failed"],
                "warnings": [],
            }
        summary["flash_image"] = flash_result
        summary["success"] = summary["success"] and flash_result["success"]

    _write_json(artifact_root / "summary.json", summary)
    return summary


class FirmwareSession:
    def __init__(
        self,
        artifact_dir: Path | str | None = None,
        *,
        port: int = 5555,
        uart_deadline_s: float = 5.0,
    ) -> None:
        self.artifact_dir = Path(artifact_dir) if artifact_dir is not None else create_visible_artifact_dir("sessions")
        self.port = port
        self.uart_deadline_s = uart_deadline_s
        self.preparation: dict[str, Any] = {}
        self._process: subprocess.Popen[str] | None = None
        self._client: Any = None
        self._stdout_handle: Any = None
        self._stderr_handle: Any = None
        self._transcript_handle: Any = None
        self._started_monotonic = 0.0
        self._connection_closed_error: type[BaseException] | None = None
        self._qemu_return_code: int | None = None

    def __enter__(self) -> "FirmwareSession":
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self._started_monotonic = time.monotonic()
        self._transcript_handle = (self.artifact_dir / "transcript.log").open("w", encoding="utf-8")
        self._record("harness", "PREPARE runtime")
        self.preparation = build_firmware(self.artifact_dir / "prepare", include_flash_image=True)
        if not self.preparation.get("success", False):
            self._record("harness", "STOP qemu status=not_started")
            self._transcript_handle.close()
            self._transcript_handle = None
            self._write_summary()
            raise RuntimeError(
                "firmware preparation failed; inspect "
                f"{self.artifact_dir / 'prepare' / 'summary.json'} for build details"
            )

        qemu_runtime = _hidden_module("sim.qemu_runtime")
        self._connection_closed_error = getattr(qemu_runtime, "ConnectionClosedError")
        self._process, self._stdout_handle, self._stderr_handle = qemu_runtime.start_qemu(_hidden_root(), self.artifact_dir, self.port)
        self._record("harness", f"START qemu port={self.port}")
        self._client = qemu_runtime.wait_for_uart(
            port=self.port,
            deadline=time.monotonic() + self.uart_deadline_s,
            artifact_dir=self.artifact_dir,
        )
        self._record("harness", f"CONNECTED tcp:{self.port}")
        return self

    def __exit__(self, exc_type: object, exc: object, exc_tb: object) -> None:
        self.close()

    def _record(self, direction: str, line: str) -> None:
        if self._transcript_handle is None:
            return
        elapsed_s = time.monotonic() - self._started_monotonic if self._started_monotonic else 0.0
        self._transcript_handle.write(f"{elapsed_s:7.3f} {direction} {sanitize_text(line)}\n")
        self._transcript_handle.flush()

    def _consume_pending_lines(self) -> list[str]:
        if self._client is None:
            return []
        try:
            lines = [sanitize_text(line) for line in self._client.read_pending_lines()]
        except Exception as exc:
            if self._connection_closed_error is not None and isinstance(exc, self._connection_closed_error):
                self._record("harness", f"ERROR {exc}")
            raise
        for line in lines:
            self._record("fw->test", line)
        return lines

    def send_line(self, payload: str) -> None:
        if self._client is None:
            raise RuntimeError("firmware session is not connected")
        sanitized_payload = sanitize_text(payload.rstrip("\r\n"))
        self._client.send_line(payload)
        self._record("test->fw", sanitized_payload)

    def read_lines(self, timeout_s: float = 0.0, poll_interval_s: float = 0.01) -> list[str]:
        deadline = time.monotonic() + max(timeout_s, 0.0)
        lines: list[str] = []
        while True:
            lines.extend(self._consume_pending_lines())
            if lines or time.monotonic() >= deadline:
                return lines
            time.sleep(poll_interval_s)

    def read_until(self, predicate: Callable[[str], bool], *, timeout_s: float = 1.0) -> list[str]:
        deadline = time.monotonic() + timeout_s
        lines: list[str] = []
        while time.monotonic() < deadline:
            for line in self.read_lines(timeout_s=0.05):
                lines.append(line)
                if predicate(line):
                    return lines
        raise TimeoutError(f"predicate was not satisfied within {timeout_s:.2f} s")

    def wait_for_boot(self, timeout_s: float = 2.0) -> list[str]:
        return self.read_until(
            lambda line: line == "DBG BOOTED"
            or "main_task: Calling app_main()" in line
            or "main_task: Returned from app_main()" in line,
            timeout_s=timeout_s,
        )

    def close(self) -> None:
        try:
            if self._client is not None:
                self._client._sock.close()
                self._client = None

            qemu_status = "not_started"
            if self._process is not None:
                if self._process.poll() is None:
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=5.0)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                        self._process.wait(timeout=5.0)
                self._qemu_return_code = self._process.returncode
                qemu_status = str(self._qemu_return_code)
                self._process = None

            self._record("harness", f"STOP qemu status={qemu_status}")
        finally:
            if self._stdout_handle is not None:
                self._stdout_handle.close()
                self._stdout_handle = None
            if self._stderr_handle is not None:
                self._stderr_handle.close()
                self._stderr_handle = None
            if self._transcript_handle is not None:
                self._transcript_handle.close()
                self._transcript_handle = None

        for artifact_name in ("qemu_stdout.log", "qemu_stderr.log", "port_probe.log", "transcript.log"):
            _sanitize_file(self.artifact_dir / artifact_name)

        self._write_summary()

    def _write_summary(self) -> None:
        summary = {
            "artifact_dir": str(self.artifact_dir),
            "port": self.port,
            "preparation": self.preparation,
            "qemu_return_code": self._qemu_return_code,
        }
        _write_json(self.artifact_dir / "summary.json", summary)
