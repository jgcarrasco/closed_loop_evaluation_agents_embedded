# Pressure Vessel Interlock Controller

Write a controller for a sealed pressure vessel with a compressor, a relief vent, and a door interlock.

## Objective

Keep the vessel in the working pressure band while sealed, vent it safely whenever the door opens, and fail safe when either sensor stream goes stale.

## Machine and I/O

- The target is ESP32 firmware running in QEMU.
- The firmware talks over `UART0` at `115200`.
- The protocol is newline-delimited ASCII.

Incoming sensor lines use:

- `SENSE PRESS <integer>`
- `SENSE DOOR OPEN`
- `SENSE DOOR CLOSED`
- `FAULT SENSOR_TIMEOUT`

Outgoing actuator lines must be exactly:

- `ACT COMPRESSOR ON`
- `ACT COMPRESSOR OFF`
- `ACT VENT OPEN`
- `ACT VENT CLOSED`

## Sensor semantics

- Pressure and door arrive as separate lines.
- A valid pressure line refreshes only pressure freshness.
- A valid door line refreshes only door freshness.
- Stay in the safe vent-open state until both sensors have been seen validly.
- If either sensor becomes stale for more than `1000 ms`, go to the safe vent-open state.

## Control policy

- On boot, keep the compressor off and the vent open.
- If the door is open, keep the compressor off and the vent open.
- If the door is closed and `PRESS < 40`, command `COMPRESSOR ON` and `VENT CLOSED`.
- If the door is closed and `PRESS > 60`, command `COMPRESSOR OFF` and `VENT OPEN`.
- If the door is closed and `40 <= PRESS <= 60`, hold the previous safe output.
- On malformed input or timeout, command the safe vent-open state.
- Never command `COMPRESSOR ON` and `VENT OPEN` at the same time.

## State expectations

- `SAFE_VENT` is the safe vent-open state.
- `PRESSURIZING` means the vessel is sealed and the compressor is active.
- `HOLDING` means the controller is inside the working band while preserving the previous safe output.
- `RELIEVING` means the controller is venting pressure above the band.

## Self-Verification Checklist

- Boot leaves the compressor off and the vent open.
- The controller stays in the safe vent-open state until both door and pressure have been seen validly.
- With door closed and low pressure such as `35`, the controller commands `COMPRESSOR ON` and `VENT CLOSED`.
- With door closed and high pressure such as `65`, the controller commands `COMPRESSOR OFF` and `VENT OPEN`.
- In the `40..60` band, the controller preserves the previous safe output.
- A door-open event immediately forces the safe vent-open output.
- Malformed input or stale sensor data for more than `1000 ms` forces the safe vent-open output.
- The controller never commands `COMPRESSOR ON` and `VENT OPEN` together.
- A firmware-level end-to-end runtime probe can boot the firmware, drive a nominal sealed-pressure cycle through UART, and observe pressurizing, holding, relieving, and immediate safe venting when the door opens.

## Editable files

- Only change the controller implementation.
- `components/controller/controller.c`
- `components/controller/include/controller.h`

## Success

- Use `python3 tools/run_build.py` and your own tests under `agent_tests/` to iterate.
- In self-verifying modes, cover the checklist above with your own visible tests or runtime probes before submitting.
- In self-verifying modes, do not stop at controller-only unit tests: include at least one firmware-level end-to-end runtime probe through UART.
- Use `python3 tools/run_eval.py` to submit to the hidden grader. What it reveals depends on the benchmark mode in `experiment.json`.
- Hidden checks will validate the visible actuator contract, stale-sensor handling, and closed-loop interlock behavior.
- Treat this markdown as the behavior source of truth.
