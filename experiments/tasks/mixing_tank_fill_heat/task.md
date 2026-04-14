# Mixing Tank Fill-and-Heat Controller

Write a controller for a mixing tank with a fill inlet and a heater.

## Objective

Fill the tank into the working level region, then heat it into the temperature band without energizing the heater on a low-fill vessel.

Treat `51 C` as a hard temperature ceiling for closed-loop runs. A controller that exceeds it fails the task even if it later recovers.

## Machine and I/O

- The target is ESP32 firmware running in QEMU.
- The firmware talks over `UART0` at `115200`.
- The protocol is newline-delimited ASCII.

Incoming sensor lines use:

- `SENSE TEMP <integer>`
- `SENSE LEVEL <integer>`
- `FAULT SENSOR_TIMEOUT`

Outgoing actuator lines must be exactly:

- `ACT INLET OPEN`
- `ACT INLET CLOSED`
- `ACT HEATER ON`
- `ACT HEATER OFF`

## Sensor semantics

- Temperature and level arrive as separate lines.
- A valid temperature line refreshes only temperature freshness.
- A valid level line refreshes only level freshness.
- Stay in the safe all-off state until both sensors have been seen validly.
- If either sensor becomes stale for more than `1000 ms`, go to the safe all-off state.

## Control policy

- On boot, keep the inlet closed and the heater off.
- If `LEVEL < 60`, command `INLET OPEN` and `HEATER OFF`.
- If `LEVEL > 75`, command `INLET CLOSED`.
- If `LEVEL < 55` at any time, keep `HEATER OFF`.
- If `60 <= LEVEL <= 75` and `TEMP < 45`, command `INLET CLOSED` and `HEATER ON`.
- If `45 <= TEMP < 47`, command `INLET CLOSED` and hold the previous safe heater state.
- If `47 <= TEMP <= 48` and temperature is rising compared with the previous valid temperature sample, command `HEATER OFF` early.
- If `47 <= TEMP <= 48` and temperature is not rising, hold the previous safe heater state.
- If `TEMP > 48`, command `INLET CLOSED` and `HEATER OFF`.
- On malformed input or timeout, command the safe all-off state.

## State expectations

- `SAFE_IDLE` is the fail-safe all-off state.
- `FILLING` means the inlet is open because level is too low.
- `HEATING` means the level is safe and the heater is actively on.
- `HOLDING` means the controller is preserving a safe output inside the working region.

## Self-Verification Checklist

- Boot leaves the inlet closed and the heater off.
- The controller stays in the safe all-off state until both temperature and level have been seen validly.
- A low level such as `50` commands `INLET OPEN` and `HEATER OFF`.
- A safe level with low temperature such as `LEVEL 65`, `TEMP 40` commands `INLET CLOSED` and `HEATER ON`.
- If `LEVEL < 55`, the heater remains off even when temperature is low.
- Near the upper band, rising temperature data causes an early `ACT HEATER OFF`.
- Malformed input or stale sensor data for more than `1000 ms` forces `INLET CLOSED` and `HEATER OFF`.
- Closed-loop tests keep the vessel at or below `51 C`.
- A firmware-level end-to-end runtime probe can boot the firmware, drive a nominal fill-then-heat sequence through UART, and observe inlet fill, heater enable only at safe level, and heater-off near the upper band.

## Editable files

- Only change the controller implementation.
- `components/controller/controller.c`
- `components/controller/include/controller.h`

## Success

- Use `python3 tools/run_build.py` and your own tests under `agent_tests/` to iterate.
- In self-verifying modes, cover the checklist above with your own visible tests or runtime probes before submitting.
- In self-verifying modes, do not stop at controller-only unit tests: include at least one firmware-level end-to-end runtime probe through UART.
- Use `python3 tools/run_eval.py` to submit to the hidden grader. What it reveals depends on the benchmark mode in `experiment.json`.
- Hidden checks will validate the visible actuator contract, low-level heater guard, and closed-loop temperature behavior.
- Treat this markdown as the behavior source of truth.
