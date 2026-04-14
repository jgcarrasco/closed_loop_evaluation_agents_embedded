# Embedded Agent Experiments

This directory holds the operator-facing benchmark workflow built on top of the same QEMU-backed task harness.

Use this `experiments/` flow when you want to evaluate an agent through a realistic visible workspace while keeping the harness, plant, and scoring logic hidden.

The direct workflow in the repo root is still useful for harness development and debugging. Use `experiments/` when you specifically want:

- a generated visible workspace
- a hidden harness snapshot
- recorded per-agent result directories
- configurable benchmark modes and grader visibility

## Source Of Truth

Each task packet is derived from a structured spec under `specs/`.

Current task packets:

- `tank_fill_drain`
- `thermal_chamber_hysteresis`
- `pressure_vessel_interlock`
- `mixing_tank_fill_heat`
- `filter_tank_sequence`

The generated workspace receives:

- common instructions
- a prose task brief
- an optional public task contract JSON ablation
- a visible `experiment.json` contract with editable paths and evaluator metadata
- the editable task files plus any fixed task-specific sync files needed for the hidden harness
- visible build and self-test tools
- a small `tools/run_eval.py` submission bridge

The hidden harness keeps:

- the structured task spec
- build logic
- QEMU runtime
- plant simulator
- integration scenarios
- raw feedback artifacts

## Layout

- `common/`: shared instructions visible to agents/operators.
- `base_workspace/`: files copied into every visible workspace.
- `tasks/<task_id>/`: task manifests plus visible editable files.
- `results/`: recorded evaluation outputs.

## Standard Workflow

1. Generate a visible workspace:

   ```bash
   ./tools/prepare_agent_eval.sh thermal_chamber_hysteresis qwen35 --benchmark-mode realistic_self_verify
   source /tmp/embedded_agent_eval/thermal_chamber_hysteresis/qwen35/.embedded_eval_env.sh
   ```

   This helper skips `git init` in the visible workspace by default, so editor source-control views do not get cluttered with temporary mini-repos.
   If the host does not have a native ESP-IDF/QEMU install, build the repo's Docker toolchain image first and export `AI_EMBEDDED_USE_DOCKER=1` before starting the agent. The agent still runs on the host; only the hidden build/QEMU commands are containerized.

2. `cd /tmp/embedded_agent_eval/thermal_chamber_hysteresis/qwen35`
3. Start the evaluated agent in that workspace only.
4. If the selected benchmark mode exposes visible self-verification helpers, let the agent iterate with `python3 tools/run_build.py` and `python3 tools/run_self_tests.py`.
   Ask it to turn each explicit acceptance bullet in `docs/10_task.md` into a visible test or runtime probe.
   Ask it to include at least one firmware-level end-to-end runtime probe through UART, not just controller-only unit tests.
5. Let the agent submit with `python3 tools/run_eval.py`.
6. Inspect visible submission feedback under `artifacts/latest/`.
7. Inspect recorded hidden results under `experiments/results/`.

If you want the lower-level manual path, this is the equivalent command:

```bash
eval "$(python3 tools/prepare_experiment_run.py thermal_chamber_hysteresis /tmp/embedded_agent_eval/thermal_chamber_hysteresis/qwen35 --agent-name qwen35 --shell-exports --force --skip-git-init)"
```

To expose the machine-readable public contract as an ablation:

```bash
./tools/prepare_agent_eval.sh thermal_chamber_hysteresis qwen35 --public-task-contract json
```

## Hidden/Visible Contract

For a proper benchmark run:

- expose only the generated workspace to the evaluated agent
- do not expose the hidden harness tree
- do not expose the plant implementation
- do not expose the hidden run root
- let `tools/run_eval.py` be the only bridge back into the hidden evaluator
- keep hidden host/integration checks out of the visible loop unless the benchmark mode explicitly calls for it

## Run Metadata

Recorded `evaluation.json` files now capture benchmark mode plus optional launcher metadata for standardizing cross-model runs.

If your outer runner knows them, export any of these before launching the agent:

- `EMBEDDED_EVAL_FRAMEWORK`
- `EMBEDDED_EVAL_PROVIDER`
- `EMBEDDED_EVAL_MODEL`
- `EMBEDDED_EVAL_FRAMEWORK_RUN_ID`
- `EMBEDDED_EVAL_PROMPT_TOKENS`
- `EMBEDDED_EVAL_COMPLETION_TOKENS`
- `EMBEDDED_EVAL_TOTAL_TOKENS`
- `EMBEDDED_EVAL_COST_USD`

That makes it straightforward to drive the same benchmark through a single framework such as `pi` while keeping the recorded schema consistent.

## Benchmark Design Rules

- Hidden host-side checks should validate only the published task contract at the visible interface.
- Prefer a prose-first visible task packet. Keep structured specs internal unless the benchmark explicitly wants to test schema use.
- Do not make benchmark success depend on private helper names, internal file layout, or other implementation details unless those are explicitly part of the task contract.
- Give the agent enough visible tooling to build and self-test without needing hidden grader detail.
- Give the agent a prose task brief that is specific enough to derive a visible self-test checklist without exposing the hidden grader.
- For dynamic control tasks, require at least one firmware-level end-to-end runtime probe through the visible interface. Unit tests alone are not a realistic self-verification story.
- Keep benchmark mode separate from raw feedback formatting. The important axis is what the hidden grader reveals, not just how markdown is rendered.
- Avoid exposing raw hidden filesystem paths when a stable label will do.
- If a task needs fixed visible scaffolding beyond the graded edit surface, sync it into the hidden harness separately instead of forcing the agent to edit it.
