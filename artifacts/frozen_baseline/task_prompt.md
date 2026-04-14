# Frozen Evaluation Task

Implement a controller that keeps the tank level in the safe band using the provided UART protocol and fail-safe requirements.

## Allowed edits

- `components/controller/controller.c`
- `components/controller/include/controller.h`
- optionally `components/protocol/protocol.c` if the task explicitly requires it

## Forbidden edits

- tests
- plant dynamics
- thresholds
- scoring scripts
- artifact-generation scripts

## Success condition

The score is determined entirely by the existing host tests, smoke test, and integration scenarios.

