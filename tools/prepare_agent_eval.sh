#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
    cat <<'EOF'
Prepare a fresh visible evaluation workspace for an agent.

Usage:
  ./tools/prepare_agent_eval.sh <task_id> <agent_name> [options]

Options:
  -w, --workspace <path>      Visible workspace path.
                              Default: /tmp/embedded_agent_eval/<task_id>/<agent_name>
      --benchmark-mode <mode> Optional benchmark mode override written into the visible workspace.
      --public-task-contract <mode>
                              Optional visible task-contract mode override.
                              Modes: prose_only (default), json
      --run-label <label>     Optional run label forwarded to the evaluator.
      --results-root <path>   Optional results root override.
      --git-init              Initialize a git repo in the visible workspace.
      --no-force              Fail if the workspace already exists.
  -h, --help                  Show this help.

This helper writes the hidden-evaluator environment exports to:
  <workspace>/.embedded_eval_env.sh

Typical flow:
  ./tools/prepare_agent_eval.sh thermal_chamber_hysteresis qwen35
  source /tmp/embedded_agent_eval/thermal_chamber_hysteresis/qwen35/.embedded_eval_env.sh
  cd /tmp/embedded_agent_eval/thermal_chamber_hysteresis/qwen35
  <launch agent here and tell it to follow START_HERE.md>
EOF
}

task_id=""
agent_name=""
workspace=""
benchmark_mode=""
public_task_contract=""
run_label=""
results_root=""
git_init=0
force=1

while [[ $# -gt 0 ]]; do
    case "$1" in
        -w|--workspace)
            workspace="${2:?missing value for $1}"
            shift 2
            ;;
        --run-label)
            run_label="${2:?missing value for $1}"
            shift 2
            ;;
        --benchmark-mode)
            benchmark_mode="${2:?missing value for $1}"
            shift 2
            ;;
        --public-task-contract)
            public_task_contract="${2:?missing value for $1}"
            shift 2
            ;;
        --results-root)
            results_root="${2:?missing value for $1}"
            shift 2
            ;;
        --git-init)
            git_init=1
            shift
            ;;
        --no-force)
            force=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
        *)
            if [[ -z "$task_id" ]]; then
                task_id="$1"
            elif [[ -z "$agent_name" ]]; then
                agent_name="$1"
            else
                echo "unexpected positional argument: $1" >&2
                usage >&2
                exit 2
            fi
            shift
            ;;
    esac
done

if [[ -z "$task_id" || -z "$agent_name" ]]; then
    usage >&2
    exit 2
fi

if [[ -z "$workspace" ]]; then
    workspace="/tmp/embedded_agent_eval/${task_id}/${agent_name}"
fi

prepare_cmd=(
    python3
    "$repo_root/tools/prepare_experiment_run.py"
    "$task_id"
    "$workspace"
    --agent-name
    "$agent_name"
    --shell-exports
)

if [[ "$force" -eq 1 ]]; then
    prepare_cmd+=(--force)
fi

if [[ "$git_init" -eq 0 ]]; then
    prepare_cmd+=(--skip-git-init)
fi

if [[ -n "$run_label" ]]; then
    prepare_cmd+=(--run-label "$run_label")
fi

if [[ -n "$benchmark_mode" ]]; then
    prepare_cmd+=(--benchmark-mode "$benchmark_mode")
fi

if [[ -n "$public_task_contract" ]]; then
    prepare_cmd+=(--public-task-contract "$public_task_contract")
fi

if [[ -n "$results_root" ]]; then
    prepare_cmd+=(--results-root "$results_root")
fi

exports_text="$("${prepare_cmd[@]}")"
workspace_abs="$(cd "$workspace" && pwd)"
env_file="$workspace_abs/.embedded_eval_env.sh"

printf '%s\n' "$exports_text" > "$env_file"

cat <<EOF
Prepared visible workspace: $workspace_abs
Saved evaluator environment: $env_file

Next:
  source $env_file
  cd $workspace_abs
  <launch agent here and tell it to follow START_HERE.md>

Notes:
  - The visible workspace does not get git-initialized by default.
  - Use --git-init only if you explicitly want a mini-repo in that workspace.
  - The hidden harness still lives outside the visible workspace.
EOF
