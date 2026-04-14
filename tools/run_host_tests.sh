#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
task_id="${HOST_TEST_TASK_ID:-tank_fill_drain}"
build_dir="${repo_root}/build-host-tests/${task_id}"
artifact_dir="${HOST_TEST_ARTIFACT_DIR:-${repo_root}/artifacts/stage3}"
log_file="${artifact_dir}/host_tests.log"

reset_stale_build_dir() {
  local cache_file="${build_dir}/CMakeCache.txt"
  local expected_source="CMAKE_HOME_DIRECTORY:INTERNAL=${repo_root}/host_tests"
  local expected_cache_dir="CMAKE_CACHEFILE_DIR:INTERNAL=${build_dir}"

  if [[ ! -f "${cache_file}" ]]; then
    return
  fi

  # Repo moves leave CMake pointing at the previous checkout path. Recreate the
  # per-task build directory so host tests remain self-contained and repeatable.
  if grep -Fqx "${expected_source}" "${cache_file}" && grep -Fqx "${expected_cache_dir}" "${cache_file}"; then
    return
  fi

  rm -rf "${build_dir}"
}

mkdir -p "${artifact_dir}"
reset_stale_build_dir

set +e
{
  echo "[run_host_tests] configuring"
  cmake -S "${repo_root}/host_tests" -B "${build_dir}" -DTASK_ID="${task_id}"
  echo "[run_host_tests] building"
  cmake --build "${build_dir}"
  echo "[run_host_tests] running"
  ctest --test-dir "${build_dir}" --output-on-failure
} >"${log_file}" 2>&1
status=$?
set -e

cat "${log_file}"
exit "${status}"
