#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <tag>" >&2
  exit 1
fi

tag="$1"
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
eval_root="$repo_root/artifacts/evaluations"
router_log="$eval_root/qwen_eval_router_${tag}.log"
router_pid="$eval_root/qwen_eval_router_${tag}.pid"
campaign_log="$eval_root/paper_repeat_campaign_${tag}.log"
router_launch_cmd="${QWEN_EVAL_ROUTER_LAUNCH:-qwen-eval-router-launch}"

mkdir -p "$eval_root"

if ! curl -sf http://127.0.0.1:8081/health >/dev/null 2>&1; then
  nohup "$router_launch_cmd" \
    --thinking off \
    --host 127.0.0.1 \
    --port 8081 \
    --sleep-idle-seconds 600 \
    >"$router_log" 2>&1 &
  echo $! >"$router_pid"

  for _ in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8081/health >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  if ! curl -sf http://127.0.0.1:8081/health >/dev/null 2>&1; then
    echo "Failed to start llama-cpp-eval router on 127.0.0.1:8081" >&2
    exit 1
  fi
fi

{
  echo "[campaign] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "[campaign] repo: $repo_root"
  echo "[campaign] tag: $tag"

  "$repo_root/tools/run_paper_repeat_sweeps.sh" "${tag}_rep1"
  "$repo_root/tools/run_paper_repeat_sweeps.sh" "${tag}_rep2"
  python3 "$repo_root/tools/analyze_paper_repeats.py" --tag "$tag"

  echo "[campaign] finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} 2>&1 | tee -a "$campaign_log"
