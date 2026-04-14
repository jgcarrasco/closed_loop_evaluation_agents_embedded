from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class VisibleRunEvalTests(unittest.TestCase):
    REPO_ROOT = Path(__file__).resolve().parents[1]

    @classmethod
    def setUpClass(cls) -> None:
        module_path = cls.REPO_ROOT / "experiments" / "base_workspace" / "tools" / "run_eval.py"
        spec = importlib.util.spec_from_file_location("visible_run_eval", module_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.run_eval = module

    def test_record_result_promotes_evaluation_context_fields(self) -> None:
        experiment = {
            "task_id": "tank_fill_drain",
            "task_name": "Tank Fill/Drain",
            "task_version": "1.0.0",
            "editable_paths": ["components/controller/controller.c"],
            "sync_paths": ["components/controller/controller.c"],
            "local_paths": [],
            "feedback": {},
        }
        benchmark = {
            "mode": "realistic_self_verify",
            "submission_feedback": "none",
            "max_submissions": None,
        }
        visible_status = {"status": "SUBMISSION_RECORDED"}

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            visible_run_dir = temp_root / "visible_run"
            visible_run_dir.mkdir()
            results_root = temp_root / "results"
            hidden_run_dir = temp_root / "hidden_run"
            hidden_run_dir.mkdir()

            with mock.patch.dict(
                os.environ,
                {
                    "EMBEDDED_EVAL_FRAMEWORK": "pi",
                    "EMBEDDED_EVAL_PROVIDER": "llama-cpp",
                    "EMBEDDED_EVAL_MODEL": "qwen35-27b-q4km",
                    "EMBEDDED_EVAL_TOTAL_TOKENS": "1234",
                },
                clear=False,
            ):
                result_dir = self.run_eval._record_result(
                    results_root=results_root,
                    experiment=experiment,
                    resolved_task_spec_path="specs/tank_fill_drain.json",
                    benchmark_config=benchmark,
                    agent_name="pi-qwen35-27b-q4km",
                    run_label="test-run",
                    notes="metadata plumbing test",
                    hidden_run_dir=hidden_run_dir,
                    visible_run_dir=visible_run_dir,
                    visible_status=visible_status,
                    submission_index=1,
                )

            record = self.run_eval._load_json_if_exists(result_dir / "evaluation.json")

        self.assertEqual(record["framework"], "pi")
        self.assertEqual(record["provider"], "llama-cpp")
        self.assertEqual(record["model"], "qwen35-27b-q4km")
        self.assertEqual(record["total_tokens"], 1234)
        self.assertEqual(record["evaluation_context"]["framework"], "pi")
        self.assertEqual(record["evaluation_context"]["model"], "qwen35-27b-q4km")
