# Scoring

The v0 benchmark score is the existing test suite:

- pass/fail for the smoke scenario
- pass/fail for the happy-path scenario
- pass/fail for the sensor-timeout scenario
- pass/fail for the malformed-frame scenario

Secondary metrics:

- iterations to first green run
- number of failed runs by terminal status

Infrastructure failures and task failures should be separated by the terminal status emitted by `tools/agent_loop.py`.

