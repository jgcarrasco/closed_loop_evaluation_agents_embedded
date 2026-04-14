from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    feedback_path = REPO_ROOT / "artifacts" / "latest" / "feedback.md"
    if not feedback_path.exists():
        print("No feedback is available yet. Run `python3 tools/run_eval.py` first.")
        return 1

    print(feedback_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
