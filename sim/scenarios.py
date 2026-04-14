from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.task_spec import TaskSpec, load_task_spec
from sim.tasks.base import ScenarioResult
from sim.tasks.registry import load_task_runtime


DEFAULT_TASK_SPEC_PATH = Path(__file__).resolve().parents[1] / "specs" / "tank_fill_drain.json"


def _resolve_task_spec(task_spec: TaskSpec | Path | str | None) -> TaskSpec:
    if isinstance(task_spec, TaskSpec):
        return task_spec
    if task_spec is None:
        return load_task_spec(DEFAULT_TASK_SPEC_PATH)
    return load_task_spec(task_spec)


def available_runtime(repo_root: Path, task_spec: TaskSpec | Path | str | None = None) -> tuple[bool, str]:
    resolved_task_spec = _resolve_task_spec(task_spec)
    runtime = load_task_runtime(resolved_task_spec.runtime_id)
    return runtime.available_runtime(repo_root)


def scenario_specs(task_spec: TaskSpec | Path | str | None = None) -> dict[str, object]:
    resolved_task_spec = _resolve_task_spec(task_spec)
    runtime = load_task_runtime(resolved_task_spec.runtime_id)
    return runtime.scenario_specs(resolved_task_spec)


def run_scenario(
    name: str,
    artifact_dir: Path,
    task_spec: TaskSpec | Path | str | None = None,
    port: int = 5555,
    timeout_s: float = 20.0,
) -> ScenarioResult:
    resolved_task_spec = _resolve_task_spec(task_spec)
    runtime = load_task_runtime(resolved_task_spec.runtime_id)
    return runtime.run_scenario(name, artifact_dir, task_spec=resolved_task_spec, port=port, timeout_s=timeout_s)


def run_many(
    names: Iterable[str],
    artifact_root: Path,
    task_spec: TaskSpec | Path | str | None = None,
    port: int = 5555,
) -> list[ScenarioResult]:
    resolved_task_spec = _resolve_task_spec(task_spec)
    runtime = load_task_runtime(resolved_task_spec.runtime_id)
    return runtime.run_many(names, artifact_root, task_spec=resolved_task_spec, port=port)
