from __future__ import annotations

import os
import select
import shutil
import socket
import subprocess
import time
from pathlib import Path


class ConnectionClosedError(RuntimeError):
    pass


class UartTcpClient:
    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._buffer = ""

    def send_line(self, payload: str) -> None:
        self._sock.sendall((payload.rstrip("\r\n") + "\n").encode("ascii"))

    def read_pending_lines(self) -> list[str]:
        lines: list[str] = []
        while True:
            readable, _, _ = select.select([self._sock], [], [], 0.0)
            if not readable:
                return lines
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionClosedError("firmware closed the UART TCP socket")
            self._buffer += chunk.decode("ascii", errors="replace")
            while "\n" in self._buffer:
                raw_line, self._buffer = self._buffer.split("\n", 1)
                lines.append(raw_line.rstrip("\r"))


def available_runtime(repo_root: Path) -> tuple[bool, str]:
    if os.environ.get("AI_EMBEDDED_USE_DOCKER") == "1" and os.environ.get("AI_EMBEDDED_IN_CONTAINER") != "1":
        if shutil.which("docker") is None:
            return False, "docker is not on PATH; install Docker or disable AI_EMBEDDED_USE_DOCKER"
        image = os.environ.get("AI_EMBEDDED_ESP_IMAGE", "ai-embedded-espidf-qemu:v5.5")
        completed = subprocess.run(
            ["docker", "image", "inspect", image],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return False, f"Docker image {image} is missing; run ./tools/build_esp_toolchain_image.sh first"
    else:
        export_script = Path.home() / "esp" / "esp-idf" / "export.sh"
        if shutil.which("qemu-system-xtensa") is None and not export_script.exists():
            return False, f"qemu-system-xtensa is not on PATH and {export_script} is missing"
    if not (repo_root / "build" / "flash_image.bin").exists():
        return False, "build/flash_image.bin is missing; run ./tools/build_flash_image.sh first"
    return True, ""


def start_qemu(repo_root: Path, artifact_dir: Path, port: int) -> tuple[subprocess.Popen[str], object, object]:
    stdout_path = artifact_dir / "qemu_stdout.log"
    stderr_path = artifact_dir / "qemu_stderr.log"
    stdout_handle = stdout_path.open("w", encoding="ascii")
    stderr_handle = stderr_path.open("w", encoding="ascii")
    env = os.environ.copy()
    env["QEMU_UART_PORT"] = str(port)
    process = subprocess.Popen(
        [str(repo_root / "tools" / "run_qemu.sh")],
        cwd=repo_root,
        env=env,
        stdout=stdout_handle,
        stderr=stderr_handle,
        text=True,
    )
    return process, stdout_handle, stderr_handle


def wait_for_uart(port: int, deadline: float, artifact_dir: Path) -> UartTcpClient:
    port_probe_log = artifact_dir / "port_probe.log"
    attempt = 0

    with port_probe_log.open("w", encoding="ascii") as log:
        while time.monotonic() < deadline:
            attempt += 1
            try:
                sock = socket.create_connection(("127.0.0.1", port), timeout=0.5)
                sock.setblocking(False)
                log.write(f"attempt {attempt}: connected\n")
                return UartTcpClient(sock)
            except OSError as exc:
                log.write(f"attempt {attempt}: {exc}\n")
                time.sleep(0.2)

    raise TimeoutError(f"UART TCP port {port} did not become reachable")
