# Agent Self-Tests

Write your own tests here.

Recommended workflow:

- Read the `Self-Verification Checklist` in `docs/10_task.md`.
- Add at least one test or runtime probe for each checklist bullet.
- Include at least one firmware-level end-to-end runtime probe with `bench_public.FirmwareSession(...)`, not just controller-only unit tests.
- Keep one quick smoke test and a few narrow behavior tests instead of one giant end-to-end test only.

Use the public helpers from `bench_public`:

- `python3 tools/run_build.py` for a visible firmware build loop
- `python3 tools/run_self_tests.py` to run your own Python `unittest` tests
- `bench_public.build_firmware(...)` to build from a test
- `bench_public.FirmwareSession(...)` to boot QEMU, exchange UART frames, and inspect the transcript

Example:

```python
import unittest

from bench_public import FirmwareSession, self_test_artifact_dir


class FirmwareSmokeTest(unittest.TestCase):
    def test_boot_and_first_actuator_response(self) -> None:
        artifact_dir = self_test_artifact_dir("smoke")
        with FirmwareSession(artifact_dir=artifact_dir) as session:
            session.wait_for_boot()
            session.send_line("SENSE LEVEL 20")
            lines = session.read_until(lambda line: line.startswith("ACT "), timeout_s=1.0)
            self.assertTrue(lines)
```

For dynamic tasks, add a second firmware-level end-to-end runtime probe that drives a nominal scenario through UART from boot to the expected steady-state or completed outcome.
