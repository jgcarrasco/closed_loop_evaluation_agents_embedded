#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export_script="${IDF_EXPORT_SCRIPT:-${HOME}/esp/esp-idf/export.sh}"

if [[ "${AI_EMBEDDED_USE_DOCKER:-0}" == "1" && "${AI_EMBEDDED_IN_CONTAINER:-0}" != "1" ]]; then
  exec "${repo_root}/tools/esp_toolchain_exec.sh" "$@"
fi

if ! command -v idf.py >/dev/null 2>&1 || ! command -v qemu-system-xtensa >/dev/null 2>&1 || ! command -v esptool.py >/dev/null 2>&1; then
  [[ -f "${export_script}" ]] || { echo "Missing ${export_script}" >&2; exit 1; }
  # shellcheck disable=SC1090
  . "${export_script}" >/dev/null 2>&1
fi

exec "$@"
