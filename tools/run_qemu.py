from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


DEFAULT_EFUSE_HEX = (
    "00000000000000000000000000800000000000000000100000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000000000000000000000"
    "00000000"
)
SUPPORTED_FLASH_SIZES = {
    2 * 1024 * 1024,
    4 * 1024 * 1024,
    8 * 1024 * 1024,
    16 * 1024 * 1024,
}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    flash_image = repo_root / "build" / "flash_image.bin"
    efuse_image = repo_root / "build" / "qemu_efuse.bin"
    uart_port = os.environ.get("QEMU_UART_PORT", "5555")
    qemu_binary = shutil.which("qemu-system-xtensa")

    if qemu_binary is None:
        print("qemu-system-xtensa is not installed or not on PATH", file=sys.stderr)
        return 1

    if not flash_image.exists():
        print(f"Missing {flash_image}. Run ./tools/build_flash_image.sh first.", file=sys.stderr)
        return 1

    if flash_image.stat().st_size not in SUPPORTED_FLASH_SIZES:
        print(
            "flash_image.bin must be padded to 2, 4, 8, or 16 MB for QEMU; rerun ./tools/build_flash_image.sh",
            file=sys.stderr,
        )
        return 1

    if not efuse_image.exists():
        efuse_image.write_bytes(bytes.fromhex(DEFAULT_EFUSE_HEX))

    os.execvp(
        qemu_binary,
        [
            qemu_binary,
            "-M",
            "esp32",
            "-m",
            "4M",
            "-drive",
            f"file={flash_image},if=mtd,format=raw",
            "-drive",
            f"file={efuse_image},if=none,format=raw,id=efuse",
            "-global",
            "driver=nvram.esp32.efuse,property=drive,value=efuse",
            "-global",
            "driver=timer.esp32.timg,property=wdt_disable,value=true",
            "-nic",
            "none",
            "-nographic",
            "-serial",
            f"tcp::{uart_port},server,nowait",
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())

