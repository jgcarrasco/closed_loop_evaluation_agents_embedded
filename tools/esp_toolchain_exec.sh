#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${AI_EMBEDDED_ESP_IMAGE:-ai-embedded-espidf-qemu:v5.5}"
cache_home="${AI_EMBEDDED_ESP_HOME:-${HOME}/.cache/ai_embedded_esp_toolchain/home}"
host_home="${HOME}"
container_name="ai-embedded-esp-$(id -u)-$$-$(date +%s%N)"

mkdir -p "${cache_home}"

if ! docker image inspect "${image}" >/dev/null 2>&1; then
  echo "Missing Docker image ${image}." >&2
  echo "Build it with: ${repo_root}/tools/build_esp_toolchain_image.sh" >&2
  exit 1
fi

if [[ $# -eq 0 ]]; then
  set -- bash
fi

extra_env=()
for var_name in QEMU_UART_PORT; do
  if [[ -v "${var_name}" ]]; then
    extra_env+=(-e "${var_name}")
  fi
done

docker_pid=""

cleanup() {
  docker rm -f "${container_name}" >/dev/null 2>&1 || true
  if [[ -n "${docker_pid}" ]]; then
    wait "${docker_pid}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

docker run --rm \
  --name "${container_name}" \
  --network host \
  --user "$(id -u):$(id -g)" \
  -e HOME=/home/dev \
  -e IDF_TOOLS_PATH=/opt/espressif-tools \
  -e AI_EMBEDDED_IN_CONTAINER=1 \
  -e AI_EMBEDDED_USE_DOCKER=0 \
  "${extra_env[@]}" \
  -v "${cache_home}:/home/dev" \
  -v "${host_home}:${host_home}" \
  -v /tmp:/tmp \
  -w "${PWD}" \
  "${image}" \
  bash -lc 'source "$IDF_PATH/export.sh" >/dev/null 2>&1 && exec "$@"' _ "$@" &
docker_pid=$!
wait "${docker_pid}"
status=$?
trap - EXIT INT TERM
cleanup
exit "${status}"
