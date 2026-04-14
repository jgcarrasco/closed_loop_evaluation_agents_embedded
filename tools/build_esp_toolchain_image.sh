#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dockerfile="${AI_EMBEDDED_ESP_DOCKERFILE:-${repo_root}/docker/espidf-qemu/Dockerfile}"
context_dir="${AI_EMBEDDED_ESP_CONTEXT:-$(dirname "${dockerfile}")}"
image="${AI_EMBEDDED_ESP_IMAGE:-ai-embedded-espidf-qemu:v5.5}"

exec docker build -t "${image}" -f "${dockerfile}" "${context_dir}"
