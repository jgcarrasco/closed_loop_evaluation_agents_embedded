# Final Closed-Loop Eval Summary

Date: 2026-03-18
Task: `tank_fill_drain`

## Outcome

After the evaluator feedback, packet clarity, and closed-loop guidance improvements, the benchmark behaves as intended: strong models solve it quickly, and weaker models can also solve it by iterating on visible feedback rather than getting stuck on harness opacity.

## Final Results

| Framework | Model | Final status | Notes |
| --- | --- | --- | --- |
| Codex | `gpt-5.4` | PASS | Solves quickly and reliably. |
| Opencode | `gpt-5-nano` | PASS | Needed clearer timing semantics and richer visible feedback, then converged. |
| Opencode | `nemotron-3-super-free` | PASS | Improved from early stalling to a clean closed-loop solve once feedback became actionable. |
| Opencode | `big-pickle` | PASS | Converged after multiple visible eval cycles. |
| Opencode | `mimo-v2-flash-free` | PASS | Solved on the first visible eval in the final packet. |
| Opencode | `minimax-m2.5-free` | PASS | Solved after multiple feedback iterations. |
| pi | `qwen35-35b-a3b-ud-q4kxl` | PASS | Local/llama.cpp-backed path solved cleanly. |
| pi | `qwen35-9b-ud-q6-k-xl` | PASS | Solved locally with more iterations than the 35B. |
| Opencode | `qwen3-coder-tools-long` | FAIL | Stayed distracted by hidden-test hunting and never became a reliable closed-loop solver. |
| Opencode | local `Qwen3.5-9B` via llama.cpp | FAIL | Failed for agent/tooling reasons before a valid benchmark solve; the same local family passed under `pi`. |

## Main Takeaways

- The benchmark is no longer mainly measuring harness confusion.
- Concrete visible assertions, compiler errors, and integration symptoms materially improve weaker-agent performance.
- Local models are viable here when the agent runtime does not become the bottleneck.
- The 9B result is especially important: this task is simple enough that a smaller local model can solve it through the intended feedback loop.
