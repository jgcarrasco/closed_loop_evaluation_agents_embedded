# Tank Fill/Drain Controller

Write a controller that keeps the pump behavior simple and safe.

## Objective

Control the pump from a level sensor so the tank fills when it is low, stops when it is high, and fails safe on bad input.

## Machine and I/O

- The target is ESP32 firmware running in QEMU.
- The firmware talks over `UART0` at `115200`.
- The protocol is newline-delimited ASCII.

Incoming sensor lines look like:

- `SENSE LEVEL <n>`
- `FAULT SENSOR_TIMEOUT`

Outgoing actuator lines must be exactly:

- `ACT PUMP ON`
- `ACT PUMP OFF`

## Control policy

- default to `PUMP OFF` on boot
- turn the pump on when `LEVEL < 30`
- turn the pump off when `LEVEL > 80`
- hold the previous safe output while `30 <= LEVEL <= 80`
- fail safe to `PUMP OFF` on malformed input or timeout

## Timing

- The controller can be stepped between valid sensor frames during normal execution.
- Short idle gaps with no new frame are not faults by themselves.
- Timeout handling is part of the required behavior.

## Self-Verification Checklist

- Boot leaves the pump off before any valid sensor input arrives.
- A low level such as `20` produces `ACT PUMP ON`.
- A high level such as `85` produces `ACT PUMP OFF`.
- A mid-band level such as `50` preserves the previous safe actuator output instead of forcing a new one.
- Short idle controller steps do not trip the timeout path immediately.
- Malformed input forces `ACT PUMP OFF`.
- Loss of valid input for more than `1000 ms` forces `ACT PUMP OFF`.
- A firmware-level end-to-end runtime probe can boot the firmware, send a nominal low-to-high level sequence through UART, and observe `ACT PUMP ON` followed by `ACT PUMP OFF` without tripping the timeout path.

## Editable files

- Only change the controller implementation.

- `components/controller/controller.c`
- `components/controller/include/controller.h`

## Success

- Use `python3 tools/run_build.py` and your own tests under `agent_tests/` to iterate.
- In self-verifying modes, cover the checklist above with your own visible tests or runtime probes before submitting.
- In self-verifying modes, do not stop at controller-only unit tests: include at least one firmware-level end-to-end runtime probe through UART.
- Use `python3 tools/run_eval.py` to submit to the hidden grader. What it reveals depends on the benchmark mode in `experiment.json`.
- Hidden checks will validate the visible public behavior, not private helper names or local refactors.
- Treat this markdown as the behavior source of truth.
