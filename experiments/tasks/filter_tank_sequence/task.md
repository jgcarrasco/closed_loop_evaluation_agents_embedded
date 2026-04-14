# Filter Tank Sequence Controller

Write a controller for a filter tank that must clarify, settle, and then drain a batch.

## Objective

Filter a cloudy tank until it is clearly clean, wait a short settle window, then drain it without draining early or ignoring later disturbances.

## Machine and I/O

- The target is ESP32 firmware running in QEMU.
- The firmware talks over `UART0` at `115200`.
- The protocol is newline-delimited ASCII.

Incoming sensor lines use:

- `SENSE TURB <integer>`
- `SENSE LEVEL <integer>`
- `FAULT SENSOR_TIMEOUT`

Outgoing actuator lines must be exactly:

- `ACT FILTER ON`
- `ACT FILTER OFF`
- `ACT DRAIN OPEN`
- `ACT DRAIN CLOSED`

## Sensor semantics

- Turbidity and level arrive as separate lines.
- A valid turbidity line refreshes only turbidity freshness.
- A valid level line refreshes only level freshness.
- Stay in the safe all-off state until both sensors have been seen validly.
- If either sensor becomes stale for more than `1000 ms`, go to the safe all-off state.

## Control policy

- On boot, keep the filter off and the drain closed.
- If `LEVEL < 15`, keep the filter off and the drain closed and remain in `COMPLETE`.
- If `TURB > 35` and `LEVEL >= 40`, command `FILTER ON` and `DRAIN CLOSED`.
- Count the clear streak using valid `TURB` inputs only.
- A valid `TURB <= 35` increments the clear streak.
- A valid `TURB > 35` resets the clear streak to zero.
- When the clear streak reaches `3` while `LEVEL >= 40`, command `FILTER OFF` and `DRAIN CLOSED` and enter `SETTLING`.
- While `SETTLING`, if a valid `TURB > 40` arrives, reset the clear streak and return to `FILTERING`.
- When `SETTLING` has lasted at least `400 ms`, the latest `TURB <= 35`, and `LEVEL >= 40`, command `DRAIN OPEN` and enter `DRAINING`.
- While `DRAINING`, if a valid `TURB > 50` arrives and `LEVEL >= 40`, close the drain, turn the filter back on, reset the clear streak, and return to `FILTERING`.
- On malformed input or timeout, command the safe all-off state.

## State expectations

- `SAFE_IDLE` is the fail-safe all-off state.
- `FILTERING` means the filter is actively reducing turbidity.
- `SETTLING` means the filter is off, the drain is closed, and the controller is waiting out the settle timer.
- `DRAINING` means the drain is open after the clear-and-settle conditions were satisfied.
- `COMPLETE` means the remaining level is below the minimum drain threshold.

## Self-Verification Checklist

- Boot leaves the filter off and the drain closed.
- The controller stays in `SAFE_IDLE` until both turbidity and level have been seen validly.
- Cloudy input with sufficient level starts `FILTERING`.
- Three valid clear turbidity samples while `LEVEL >= 40` enter `SETTLING`.
- A `TURB > 40` disturbance during `SETTLING` returns the controller to `FILTERING`.
- The controller does not open the drain before `400 ms` of settling have elapsed with a latest clear sample and `LEVEL >= 40`.
- A `TURB > 50` disturbance during `DRAINING` closes the drain, restarts filtering, and resets the clear streak.
- `LEVEL < 15` leaves the controller in `COMPLETE` with filter off and drain closed.
- Malformed input or stale sensor data for more than `1000 ms` forces the safe all-off state.
- A firmware-level end-to-end runtime probe can boot the firmware, drive a nominal clarification batch through UART, and observe `FILTERING`, `SETTLING`, `DRAINING`, and `COMPLETE` without early drain.

## Editable files

- Only change the controller implementation.
- `components/controller/controller.c`
- `components/controller/include/controller.h`

## Success

- Use `python3 tools/run_build.py` and your own tests under `agent_tests/` to iterate.
- In self-verifying modes, cover the checklist above with your own visible tests or runtime probes before submitting.
- In self-verifying modes, do not stop at controller-only unit tests: include at least one firmware-level end-to-end runtime probe through UART.
- Use `python3 tools/run_eval.py` to submit to the hidden grader. What it reveals depends on the benchmark mode in `experiment.json`.
- Hidden checks will validate the clear streak logic, settle timing, disturbance recovery, and closed-loop cycle behavior.
- Treat this markdown as the behavior source of truth.
