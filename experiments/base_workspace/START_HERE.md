# Start Here

Read these files first:

1. `docs/00_common_instructions.md`
2. `docs/10_task.md`
3. `docs/20_task_contract.json` if it is present in this workspace
4. `experiment.json`

Then:

1. Implement the required behavior in the editable source files.
2. If this workspace includes visible self-verification helpers, turn each explicit acceptance bullet in `docs/10_task.md` into a visible test or runtime check before your first hidden submission, and include at least one firmware-level end-to-end runtime probe through UART.
3. If this workspace includes `tools/run_build.py`, use it to check the visible build path.
4. If this workspace includes `agent_tests/`, write your own visible tests there.
5. If this workspace includes `tools/run_self_tests.py`, use it to run your visible tests.
6. Use `python3 tools/run_eval.py` only to submit to the hidden grader.
7. Read `artifacts/latest/feedback.md` for the submission result that this benchmark mode exposes.

Treat this workspace as the complete visible task packet.
The task behavior contract is described in prose in `docs/10_task.md`.
In `oneshot_blind`, the public self-verification surface is intentionally absent.
