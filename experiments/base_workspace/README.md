# Visible Evaluation Workspace

This is the agent-visible side of the experiment.

Follow `START_HERE.md`.

The intended loop in modes with visible self-verification is:

1. implement the task
2. use `tools/run_build.py`
3. write tests under `agent_tests/`
4. run `tools/run_self_tests.py`
5. submit with `tools/run_eval.py`

In `oneshot_blind`, the public self-verification surface is intentionally omitted and the agent only gets the submission bridge.
The machine-readable task contract is optional and only appears when the operator enables that ablation.
