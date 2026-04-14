#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <tag>" >&2
  exit 1
fi

tag="$1"
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
output_base="$repo_root/artifacts/evaluations"

mixed_root="$output_base/pi_matrix_paper_mixed_${tag}"
local_root="$output_base/pi_matrix_paper_local_${tag}"
two_b_root="$output_base/pi_matrix_paper_2b_${tag}"

run_matrix() {
  local preset="$1"
  local root="$2"

  if [[ -e "$root" ]]; then
    echo "[paper-repeat] resuming existing output root: $root"
  else
    echo "[paper-repeat] creating output root: $root"
  fi

  python3 "$repo_root/tools/run_pi_matrix.py" \
    --model-preset "$preset" \
    --timeout-sec 3600 \
    --output-root "$root" \
    --skip-existing \
    --cleanup-temp
}

run_matrix initial "$mixed_root"
run_matrix paper_local_qwen "$local_root"
run_matrix local_qwen_2b_only "$two_b_root"
