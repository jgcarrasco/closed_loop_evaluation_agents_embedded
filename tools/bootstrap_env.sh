#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="${BOOTSTRAP_ARTIFACT_DIR:-${repo_root}/artifacts/bootstrap}"
stdout_log="${artifact_dir}/stdout.log"
stderr_log="${artifact_dir}/stderr.log"

tool_runner() {
  "${repo_root}/tools/with_idf_env.sh" "$@"
}

mkdir -p "${artifact_dir}"

set +e
(
  cd "${repo_root}"
  tool_runner idf.py --version
  tool_runner qemu-system-xtensa --version
  tool_runner esptool.py version
  tool_runner idf.py set-target esp32
) >"${stdout_log}" 2>"${stderr_log}"
status=$?
set -e

cat "${stdout_log}"
if [[ -s "${stderr_log}" ]]; then
  cat "${stderr_log}" >&2
fi

if [[ ${status} -ne 0 ]]; then
  echo "Bootstrap failed. Install ESP-IDF, QEMU for Xtensa, and esptool.py before retrying." >&2
fi

exit "${status}"
