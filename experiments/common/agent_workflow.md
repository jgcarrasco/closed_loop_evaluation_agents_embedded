# Common Agent Instructions

You are working inside the only filesystem surface that is visible for this task.

## What you should do

- Read `START_HERE.md`.
- Read `docs/00_common_instructions.md`.
- Read `docs/10_task.md`.
- Read `docs/20_task_contract.json` if present.
- Read `experiment.json` if you need the editable-path contract for the workspace.
- Implement the required behavior in the editable source files.
- If this workspace includes `tools/run_build.py`, use it for the visible build loop.
- If this workspace includes `agent_tests/`, write your own tests there.
- If this workspace includes `tools/run_self_tests.py`, use it to run your own visible tests.
- In self-verifying modes, turn each explicit acceptance bullet in `docs/10_task.md` into a visible test or an explicit runtime probe before relying on `tools/run_eval.py`.
- In self-verifying modes, include at least one firmware-level end-to-end runtime probe through UART, not just controller-only unit tests.
- Use `python3 tools/run_eval.py` to submit to the hidden grader.
- After each submission, inspect `artifacts/latest/feedback.md`.
- Use `artifacts/latest/feedback.json` if you want the same submission result in structured form.

## What `tools/run_eval.py` does

`python3 tools/run_eval.py` is the supported submission bridge.

It syncs your visible source files into the hidden harness and runs the hidden evaluator, which checks, in order:

- host-side logic checks
- firmware build
- runtime boot/smoke behavior
- closed-loop behavior against the hidden plant

Do not treat `tools/run_eval.py` as your only debugging loop when the workspace provides visible self-verification helpers. In those modes, use the visible tools first:

- `python3 tools/run_build.py`
- `python3 tools/run_self_tests.py`
- `bench_public` helpers from your own tests in `agent_tests/`

`tools/run_eval.py` always records a submission and updates `artifacts/latest/`, but what it reveals depends on the benchmark mode in `experiment.json`.

The built-in benchmark modes are:

- `oneshot_blind`
  - one submission
  - hidden grader output withheld
  - public self-verification helpers intentionally omitted
- `realistic_self_verify`
  - repeated submissions
  - hidden grader output withheld
  - use the visible build loop and your own tests for iteration
- `ci_red_green`
  - repeated submissions
  - hidden grader returns pass/fail only
- `oracle_full`
  - repeated submissions
  - hidden grader detail is mirrored back into the visible workspace

Treat any `hidden_harness:...` or `hidden_runs:...` references in visible artifacts as evaluator labels, not as files you should try to open.

## How to work

- Prefer small, direct edits.
- Keep public interfaces intact unless the task explicitly says otherwise.
- Treat `docs/10_task.md` as the source of truth for the required behavior, timing notes, and success criteria.
- Treat the `Self-Verification Checklist` in `docs/10_task.md` as a minimum visible test plan whenever the workspace exposes self-verification helpers.
- If present, use `docs/20_task_contract.json` as the machine-readable version of the public task contract.
- Use `experiment.json` as the source of truth for the editable paths and visible evaluator contract.
- Compare the controller step period and the sensor frame period before deciding how to handle idle steps. Valid sensor frames may arrive less often than controller steps.
- Normal short gaps with no new sensor frame are not faults by themselves. Treat idle/no-new-frame inputs differently from malformed input and true timeout conditions.
- The hidden host-side and integration checks validate the published task contract at the visible interface. Internal helper names, local refactors, and private code organization are not graded.
- Prefer to debug with your own tests, not by relying on hidden grader detail.
- A good default is one visible test or runtime probe per acceptance bullet, plus one firmware-level end-to-end runtime probe that exercises a nominal task path through `FirmwareSession(...)`.
- If present, `agent_tests/README.md` shows the supported public test helpers.
- If present, `bench_public.FirmwareSession(...)` lets you boot the firmware in QEMU, exchange UART frames, and inspect a transcript from your own test code.
- If present, `artifacts/public/builds/latest/` contains the latest visible build run.
- If present, `artifacts/public/self_tests/latest/` contains the latest visible self-test run.
- `artifacts/latest/` contains the latest hidden-grader submission result.
- If `python3 tools/run_eval.py` fails with a sandbox-related environment error, rerun the same command with unrestricted permissions.
- Typical signs of this are:
  - `PermissionError` while writing under `/home/.../experiments/results/...`
  - smoke-check failure saying `UART TCP port 5560 did not become reachable`
- Those failures indicate the evaluator could not access its normal runtime environment, not that the controller logic is wrong. Use the unrestricted rerun result as the actual evaluation signal.
- If the build already succeeds and your own runtime tests start, the likely remaining problem is controller logic rather than toolchain setup.
- Edits outside the allowed task files and local test paths will be rejected by the visible evaluator.

## Editable surface

The exact allowed edits are listed in `experiment.json`.

- `editable_paths` are graded and synced into the hidden harness.
- `local_paths` are visible-only helper paths such as `agent_tests/` when the benchmark mode includes them.

Do not modify evaluator tooling or task instructions unless the task explicitly asks for it.
