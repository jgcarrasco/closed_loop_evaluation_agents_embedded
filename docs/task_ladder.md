# Task Ladder

The benchmark now has five task packets with a deliberate difficulty progression:

1. `tank_fill_drain`
   - One sensor, one actuator, simple bang-bang control, single-stream freshness.
2. `thermal_chamber_hysteresis`
   - One sensor, one actuator, thermal lag, trend-aware early shutoff.
3. `pressure_vessel_interlock`
   - Two sensor streams, two actuators, safe-state interlock, asynchronous freshness.
4. `mixing_tank_fill_heat`
   - Two sensor streams, two actuators, phase coupling, level-gated heating, trend-aware early shutoff.
5. `filter_tank_sequence`
   - Two sensor streams, two actuators, explicit state machine, consecutive-sample evidence, settle timer, and disturbance recovery.

Design rule:

- Evaluated agents receive the prose task packet in `docs/10_task.md`.
- The structured JSON spec remains hidden and is used only by the harness and evaluator.
- New task difficulty is intended to come from control logic and state handling, not from missing instructions or hidden interface tricks.

Validation snapshot (2026-03-20):

- The prose-first path is active: `tools/create_experiment_workspace.py` copies each task's `task.md` into visible `docs/10_task.md`, and `experiments/base_workspace/START_HERE.md` tells the agent to treat that markdown as the behavior contract.
- `filter_tank_sequence` is currently the hardest task in the ladder and is solvable by Codex in a fresh visible workspace; the resulting visible status was `PASS`.
- A hosted `opencode` model (`opencode/minimax-m2.5-free`) stayed at visible status `HOST_TEST_FAILED` on the same hardest task. Its failures stayed on controller-state logic exposed by the visible feedback, especially entering `SETTLING`, opening the drain after settling, and timeout-safe-idle behavior.
- The local `llama.cpp` deployment of Qwen 3.5 9B is reachable through `opencode` as `llamacpp9b/qwen3.5-9b-ud-q6-k-xl`, and a simple smoke edit succeeded. On the hardest benchmark task, though, the run aborted before the first visible evaluation with `Invalid diff: now finding less tool calls!`, so that specific run should not yet be counted as a task-difficulty result.
