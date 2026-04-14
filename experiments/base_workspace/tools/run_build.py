from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


from bench_public import build_firmware, create_visible_artifact_dir, refresh_latest_artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the current visible firmware against the hidden harness.")
    parser.add_argument(
        "--flash-image",
        action="store_true",
        help="Also build the QEMU flash image after a successful firmware build.",
    )
    args = parser.parse_args()

    artifact_dir = create_visible_artifact_dir("builds")
    result = build_firmware(artifact_dir, include_flash_image=args.flash_image)
    refresh_latest_artifact("builds", artifact_dir)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
