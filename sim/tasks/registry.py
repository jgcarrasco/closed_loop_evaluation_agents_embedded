from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

from sim.task_spec import TaskSpec


TASKS_ROOT = Path(__file__).resolve().parent


def available_task_ids() -> list[str]:
    task_ids: list[str] = []
    for child in TASKS_ROOT.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name == "__pycache__":
            continue
        if (child / "runtime.py").exists():
            task_ids.append(child.name)
    return sorted(task_ids)


def _runtime_module_name(task_id: str) -> str:
    return f"sim.tasks.{task_id}.runtime"


def load_task_runtime(task_spec: TaskSpec | str) -> ModuleType:
    task_id = task_spec.task_id if isinstance(task_spec, TaskSpec) else str(task_spec)
    if task_id not in available_task_ids():
        available = ", ".join(available_task_ids())
        raise ValueError(f"unknown task runtime: {task_id}. available task ids: {available}")
    return importlib.import_module(_runtime_module_name(task_id))

