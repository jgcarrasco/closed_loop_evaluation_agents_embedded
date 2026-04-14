# Closed-Loop Evaluation of LLM Agents for Embedded Software Development

This repository is the codebase and artifact bundle for the paper "Closed-Loop Evaluation of LLM Agents for Embedded Software Development."

It benchmarks coding agents on embedded-control tasks in a closed loop. An evaluated agent receives a constrained workspace, reads a prose engineering brief, edits only the allowed firmware files, uses whatever visible build and self-test surface the benchmark mode permits, and submits through `tools/run_eval.py` to a hidden evaluator that scores the run with host tests and deterministic plant/runtime checks.

The primary benchmark condition is `realistic_self_verify`: the agent must decide when its solution is ready using only visible local evidence rather than hidden grader messages.

## Repository Contents

- Embedded firmware code used by the benchmark (`main/`, `components/`).
- Hidden evaluator, plant models, and task runtimes (`sim/`, `specs/`).
- Operator workflow for generating visible agent workspaces (`experiments/`, `tools/`).
- The curated results reported in the paper (`artifacts/evaluations/`).
- The manuscript source used for submission (`docs/latex/main.tex`).

## Tasks

The current benchmark contains five tasks with a deliberate difficulty ladder:

1. `tank_fill_drain`
   Baseline threshold control with timeout-safe behavior.
2. `thermal_chamber_hysteresis`
   Adds plant lag and trend-aware heater shutoff.
3. `pressure_vessel_interlock`
   Adds asynchronous sensor freshness and safety interlocks.
4. `mixing_tank_fill_heat`
   Adds coupled fill/heat behavior across two sensors and two actuators.
5. `filter_tank_sequence`
   Adds timer-driven sequencing, evidence accumulation, and disturbance recovery.

The public task packets live under `experiments/tasks/<task_id>/task.md`. The hidden structured source of truth lives under `specs/<task_id>.json`.

## Benchmark Modes

The harness supports four visibility regimes:

- `oneshot_blind`: one submission, no hidden feedback, no public self-verification helpers.
- `realistic_self_verify`: repeated local iteration, but hidden grader details stay hidden.
- `ci_red_green`: repeated submissions with pass/fail-only hidden feedback.
- `oracle_full`: repeated submissions with detailed hidden feedback.

These modes are complementary analyses over the same task suite, not a single monotone leaderboard.

## Results

The authoritative paper bundle is:

- `artifacts/evaluations/paper_closed_loop_eval_420/`

That directory contains:

- `summary.md`, `summary.json`, `summary.csv`, and `aggregate_metrics.json` for the curated official bundle.
- `official_run_index.csv` with one row per official paper run.
- `official_summary_by_model.csv` and `official_summary_by_model_mode.csv`.
- `runs/` with the copied per-run prompts, transcripts, logs, and summaries used for the paper.

In this public repository, `artifacts/evaluations/` contains only that unified official bundle. Intermediate sweep roots and staging outputs are not included.

If you run new evaluations locally, the default operator path writes fresh result records under:

- `experiments/results/`

## Quick Start

Cheap validation checks:

```bash
./tools/run_host_tests.sh
python3 tools/run_plant_tests.py
```

The QEMU-backed loop expects:

- `idf.py`
- `qemu-system-xtensa`
- `esptool.py`

If you do not have a native ESP-IDF/QEMU toolchain installed, build the Docker image and run with `AI_EMBEDDED_USE_DOCKER=1`:

```bash
./tools/build_esp_toolchain_image.sh
export AI_EMBEDDED_USE_DOCKER=1
```

To generate a visible workspace for an evaluated agent:

```bash
./tools/prepare_agent_eval.sh tank_fill_drain my-agent --benchmark-mode realistic_self_verify
source /tmp/embedded_agent_eval/tank_fill_drain/my-agent/.embedded_eval_env.sh
cd /tmp/embedded_agent_eval/tank_fill_drain/my-agent
```

Then launch the agent in that generated workspace and have it follow `START_HERE.md`.

## Evaluation Paths

There are two supported ways to run the benchmark.

### Method 1: Built-in matrix runner

Use this method when you want a reproducible sweep driven by the tooling already included in this repository.

Typical use:

```bash
python3 tools/run_pi_matrix.py \
  --model-preset initial \
  --tasks tank_fill_drain thermal_chamber_hysteresis \
  --modes realistic_self_verify ci_red_green
```

This method is the right choice when:

- you want paper-style matrix runs from the same harness
- you are happy to use model presets defined in `tools/run_pi_matrix.py`
- you want outputs written directly into `artifacts/evaluations/`

To add more built-in model options for this method, extend `MODEL_PRESETS` in `tools/run_pi_matrix.py`.

### Method 2: External harness or agent runner

Use this method when you want to evaluate a different framework, launcher, or agent implementation while keeping the same visible task packets and hidden evaluator.

Workflow:

1. Generate a visible workspace with `tools/prepare_agent_eval.sh` or `tools/prepare_experiment_run.py`.
2. Launch your own harness inside that generated workspace only.
3. Let the agent follow the visible workflow and submit through `python3 tools/run_eval.py`.

This method is the right choice when:

- you already have your own agent runner
- you want to compare multiple frameworks against the same benchmark contract
- you do not want to modify the repository's sweep driver

If your outer harness knows the framework/model metadata, export these so they are recorded in `evaluation.json`:

- `EMBEDDED_EVAL_FRAMEWORK`
- `EMBEDDED_EVAL_PROVIDER`
- `EMBEDDED_EVAL_MODEL`
- `EMBEDDED_EVAL_FRAMEWORK_RUN_ID`
- `EMBEDDED_EVAL_PROMPT_TOKENS`
- `EMBEDDED_EVAL_COMPLETION_TOKENS`
- `EMBEDDED_EVAL_TOTAL_TOKENS`
- `EMBEDDED_EVAL_COST_USD`

This makes it possible to compare different outer harnesses while keeping the task packet and hidden evaluator fixed.

## Adding Tasks

To add a new benchmark task, follow the existing task layout:

1. Add the hidden structured spec at `specs/<task_id>.json`.
2. Add the visible task packet under `experiments/tasks/<task_id>/`.
3. Create `experiments/tasks/<task_id>/task.json` with at least:
   `task_id`, `task_name`, `task_version`, `task_spec_path`, and `editable_paths`.
4. Write the prose brief in `experiments/tasks/<task_id>/task.md`.
5. If the visible workspace needs fixed scaffolding, place it in `experiments/tasks/<task_id>/visible_files/`.
6. Add host-side task checks under `host_tests/tasks/<task_id>/`.
7. Add the runtime or plant implementation under `sim/tasks/<task_id>/` and register it in `sim/tasks/registry.py`.

After that, validate the task with:

```bash
./tools/run_host_tests.sh
python3 tools/run_plant_tests.py
python3 tools/create_experiment_workspace.py <task_id> /tmp/<task_id> --force --skip-git-init
```

The generated workspace should contain the exact public contract you intend agents to see.

## Repository Layout

- `components/`: controller logic and protocol code.
- `main/`: ESP-IDF app wiring and UART transport.
- `host_tests/`: native C tests for task behavior and protocol correctness.
- `sim/`: evaluator logic, plants, runtimes, scenarios, and feedback projection.
- `specs/`: hidden task specifications.
- `experiments/`: visible workspace templates, task packets, and operator workflow.
- `tools/`: workspace generation, build, QEMU, and evaluation entrypoints.
- `artifacts/evaluations/`: committed paper artifact bundle.
- `docs/latex/`: manuscript source and generated paper figures.
