# Thermal Chamber Hysteresis Controller

Write a controller for a thermal chamber with a binary heater and a laggy plant.

## Objective

Warm the chamber into the working band, avoid overshooting near the upper edge, and fail safe to heater-off on bad input.

## Machine and I/O

- The target is ESP32 firmware running in QEMU.
- The firmware talks over `UART0` at `115200`.
- The protocol is newline-delimited ASCII.

Incoming sensor lines use:

- `SENSE TEMP <integer>`
- `FAULT SENSOR_TIMEOUT`

Outgoing actuator lines must be exactly:

- `ACT HEATER ON`
- `ACT HEATER OFF`

## Plant behavior

- The sensor reports integer temperatures in the expected operating range.
- The heater is binary: on or off.
- The chamber stores residual heat, so temperature can keep rising for a while after the heater is switched off.
- A controller that waits too long to turn the heater off can still overshoot after the actuator change.
- Treat `56 C` as a hard safety ceiling for closed-loop runs. A controller that exceeds it fails the task even if it later recovers.

## Timing

- The controller step period is `50 ms`.
- Valid sensor frames arrive every `100 ms`.
- A lack of a new frame on one controller step is not automatically a fault.
- If no valid sensor frame arrives for more than `1000 ms`, treat that as a timeout and fail safe.

## Control policy

- On boot, keep the heater off.
- If `TEMP < 47`, turn the heater on.
- If `TEMP > 52`, turn the heater off.
- If `47 <= TEMP < 50`, hold the previous safe actuator state.
- If `50 <= TEMP <= 52` and the temperature is rising compared with the previous valid temperature sample, turn the heater off early and treat that anticipatory heater-off as `HOLDING`, not `SAFE_OFF`.
- If `50 <= TEMP <= 52` and the temperature is not rising, hold the previous safe actuator state.
- On malformed input, turn the heater off.
- On explicit sensor timeout input, turn the heater off.
- On stale sensor data for more than `1000 ms`, turn the heater off.

## State expectations

- `SAFE_OFF` is the fail-safe off state and the state used above the upper band.
- `HEATING` means the controller is actively driving the heater on because temperature is low.
- `HOLDING` means the controller is inside the working region while preserving the previous safe actuator state.

## Self-Verification Checklist

- Boot leaves the heater off.
- A low temperature such as `35` drives `ACT HEATER ON`.
- A temperature above the upper band such as `53` drives `ACT HEATER OFF`.
- Inside `47..49`, the controller preserves the previous safe actuator state.
- Near the upper band, rising temperature data causes an early `ACT HEATER OFF`, and that anticipatory off state still counts as `HOLDING`.
- Malformed input forces `ACT HEATER OFF`.
- Stale sensor data for more than `1000 ms` forces `ACT HEATER OFF`.
- Closed-loop tests keep the chamber at or below `56 C`.
- A firmware-level end-to-end runtime probe can boot the firmware, drive a nominal warm-up sequence through UART, and observe heater-on at low temperature plus heater-off near the upper band.

## Editable files

- Only change the controller implementation.
- `components/controller/controller.c`
- `components/controller/include/controller.h`

## Success

- Use `python3 tools/run_build.py` and your own tests under `agent_tests/` to iterate.
- In self-verifying modes, cover the checklist above with your own visible tests or runtime probes before submitting.
- In self-verifying modes, do not stop at controller-only unit tests: include at least one firmware-level end-to-end runtime probe through UART.
- Use `python3 tools/run_eval.py` to submit to the hidden grader. What it reveals depends on the benchmark mode in `experiment.json`.
- Hidden checks will validate the visible public behavior and closed-loop runtime behavior.
- Treat this markdown as the behavior source of truth.
