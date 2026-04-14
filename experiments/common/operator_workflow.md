# Operator Workflow

This document is for the human running evaluations, not for the evaluated agent.

## Goal

Expose only a realistic task packet to the agent while keeping:

- the plant implementation hidden
- the tests hidden
- the scoring harness hidden

## Recommended procedure

1. Prepare a fresh workspace and hidden evaluator environment:

   ```bash
   ./tools/prepare_agent_eval.sh thermal_chamber_hysteresis qwen35 --benchmark-mode realistic_self_verify
   source /tmp/embedded_agent_eval/thermal_chamber_hysteresis/qwen35/.embedded_eval_env.sh
   ```

2. If needed, create the workspace explicitly with:

   ```bash
   python3 tools/create_experiment_workspace.py thermal_chamber_hysteresis /tmp/thermal_eval_workspace --force --skip-git-init
   ```

3. Launch the agent with its working directory set to that generated workspace.
4. `cd /tmp/embedded_agent_eval/thermal_chamber_hysteresis/qwen35`
5. Tell the agent to follow `START_HERE.md`.
6. Let the agent use the visible build and self-test tools in that workspace.
7. Keep the hidden harness and plant outside the agent sandbox.

The preparation tool sets:

- `EMBEDDED_EVAL_HARNESS_ROOT`
- `EMBEDDED_EVAL_RUN_ROOT`
- `EMBEDDED_EVAL_RESULTS_ROOT`
- optionally `EMBEDDED_EVAL_AGENT_NAME`
- optionally `EMBEDDED_EVAL_BENCHMARK_MODE`
- optionally `EMBEDDED_EVAL_RUN_LABEL`

By default it also creates a detached hidden harness snapshot so evaluations do not dirty the main repository checkout.
The recommended helper also skips git initialization in the visible workspace, which avoids the temporary `/tmp` workspaces showing up as separate repositories in editor git views.

## Why the preparation tool exists

The visible workspace should not require the agent to discover hidden evaluator paths.

If `tools/run_eval.py` reports missing `EMBEDDED_EVAL_*` variables, that is an operator setup problem. The correct fix is to relaunch the agent with `tools/prepare_experiment_run.py`, not to make the agent guess hidden paths.

## Sandboxing requirements

The generated visible evaluator also checks that the agent did not modify files outside the allowed task surface.

For a proper benchmark runner:

- mount or copy only the generated workspace into the agent sandbox
- do not expose the hidden harness filesystem
- do not expose the plant implementation
- do not expose the hidden run root

## Recorded results

Each evaluation run writes:

- visible feedback into the workspace under `artifacts/`
- hidden run artifacts into `EMBEDDED_EVAL_RUN_ROOT`
- a per-run result record under `EMBEDDED_EVAL_RESULTS_ROOT/<task_id>/<agent_name>/<timestamp>/`

Use `python3 tools/list_experiment_runs.py` from the hidden harness to inspect completed runs.
