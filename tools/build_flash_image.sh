#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="${FLASH_IMAGE_ARTIFACT_DIR:-${repo_root}/artifacts/stage4}"
log_file="${artifact_dir}/flash_image.log"
build_dir="${repo_root}/build"

tool_runner() {
  "${repo_root}/tools/with_idf_env.sh" "$@"
}

mkdir -p "${artifact_dir}"

set +e
(
  cd "${repo_root}"
  tool_runner idf.py build
  [[ -d "${build_dir}" ]] || { echo "Missing ${build_dir}" >&2; exit 1; }
  cd "${build_dir}"
  [[ -f flash_args ]] || { echo "Missing ${build_dir}/flash_args" >&2; exit 1; }
  flash_size="$(sed -n 's/^CONFIG_ESPTOOLPY_FLASHSIZE=\"\\(.*\\)\"$/\\1/p' "${repo_root}/sdkconfig" | head -n 1)"
  [[ -n "${flash_size}" ]] || flash_size="2MB"
  tool_runner esptool.py --chip esp32 merge_bin --fill-flash-size "${flash_size}" -o flash_image.bin @flash_args
  [[ -f flash_image.bin ]] || { echo "Missing ${build_dir}/flash_image.bin after merge" >&2; exit 1; }
) >"${log_file}" 2>&1
status=$?
set -e

cat "${log_file}"

if [[ ${status} -ne 0 ]]; then
  echo "Flash-image build failed. Expected build outputs or required tools are missing." >&2
fi

exit "${status}"
