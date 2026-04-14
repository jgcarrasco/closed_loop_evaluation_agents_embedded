# Benchmark Findings

This file captures working findings from the benchmark design and early evaluation passes.
It is intended as paper-facing notes rather than polished prose.

## Benchmark Design

- Hidden checks must trace back to the visible task contract.
  If a hidden assertion cannot be justified by a visible sentence in the prose brief, the benchmark is grading undocumented behavior rather than task performance.

- Prose-only task packets are more realistic than exposing a structured public contract by default.
  A machine-readable contract is useful as an ablation, but it gives the agent a cleaner and more formal problem statement than many real engineering tasks provide.

- Realistic self-verification requires visible tooling, not just instructions.
  If the agent is told to "write tests" but is not given a visible build loop, a visible test location, and a public runtime harness, the benchmark is under-specified rather than realistic.

- A one-shot benchmark must physically remove self-verification affordances.
  It is not enough to tell the agent not to use them. If build/test helpers are present, capable agents will often use them before their single hidden submission.

- Public task prose needs an explicit self-verification checklist.
  Smaller models benefit from a visible checklist that translates the prose contract into concrete behaviors to test, while still keeping the setup realistic and non-oracular.

- Dynamic tasks also need an explicit firmware-level end-to-end runtime probe requirement.
  Asking for one test per prose bullet still allows false greens if the agent writes only controller-level unit tests and never exercises a nominal scenario through the visible UART interface.

- Hidden grader visibility and feedback formatting are different axes.
  The important benchmark condition is what the hidden evaluator reveals (`none`, `red/green`, `full`), not just how feedback is rendered in markdown or JSON.

## Contract Alignment Lessons

- The initial prose-only `tank_fill_drain` task was underspecified relative to the hidden host tests.
  The host tests asserted controller state semantics and `timed_out` behavior that were not promised in the visible brief.

- The right maintainer rule is:
  If a hidden check matters, put it in the visible prose.
  If you do not want to expose it in the visible prose, do not grade it.

- Runtime thresholds also need prose visibility.
  Hidden thermal and mixing safety ceilings were reasonable acceptance conditions, but they needed to be stated explicitly in the public task briefs to remain benchmark-valid.

- State labels should be documented at the decision-point level, not only listed globally.
  If a hidden host test expects a specific state label for an edge case such as anticipatory heater-off, the prose should say that explicitly where the behavior is introduced.

## Feedback Mode Lessons

- `oracle_full` is useful as an upper bound, not as the primary realism claim.
  It measures how well a model can repair code with direct oracle feedback from hidden tests and scenarios.

- `realistic_self_verify` is the most representative primary condition.
  The agent should rely on visible build/test/runtime feedback plus its own tests, while the hidden grader remains purely evaluative.

- For `realistic_self_verify`, unit tests alone are not enough.
  The public packet should explicitly require at least one nominal firmware-level runtime probe through the visible interface, or strong models can still stop early after a false green.

- `ci_red_green` appears to be a particularly informative middle ground.
  It does not leak hidden assertions, but it still supplies enough external signal to help models escape false greens or local search failures.

## Early Model Behavior

These observations are provisional and come from the in-progress first sweep.

- Strong frontier models can pass hard tasks even in `oneshot_blind`.
  In the early `filter_tank_sequence` runs, `gpt-5.4` and `gpt-5.4-mini` both passed the one-shot condition.

- Smaller/local models can solve the task family, but often need external search signal.
  `qwen35-27b-q4km` failed `filter_tank_sequence` in `oneshot_blind` and `realistic_self_verify`, then passed in `ci_red_green` after repeated hidden pass/fail iterations.

- False greens are a real phenomenon in realistic self-verification.
  Models can pass their own tests and still fail the hidden evaluator, which makes self-test quality an important metric rather than a side detail.

- One observed false green came from incomplete self-verification shape, not just model weakness.
  A strong model covered many checklist bullets with controller/unit tests but omitted a nominal end-to-end runtime probe, then failed hidden integration on cycle completion.

- `ci_red_green` can help models that are not strong enough to self-diagnose from public evidence alone.
  The local qwen run suggests that compact external search feedback can matter even when the model is capable of eventually reaching a correct solution.

## Measurement Lessons

- Cross-framework instrumentation is brittle.
  The initial `pi` matrix parser assumed token usage lived at the top level of session messages, but the installed `pi` version stored it under `message.usage`.

- Parallel sweeps need isolated result namespaces per task/mode/model cell.
  Reusing the same agent identifier across multiple modes of the same task is safe only in sequential runs. Once remote-model runs are parallelized, each cell needs its own hidden-results namespace to avoid attribution races.

- Fixed QEMU/UART ports currently make concurrent evaluator runs invalid.
  Even with isolated result namespaces, the hidden harness still hardcodes smoke and integration ports. Until per-run port allocation exists, benchmark sweeps should remain sequential.

- Raw session logs should always be preserved.
  They allow later repair of token/tool accounting without rerunning expensive experiments.

- Submission timing and token split matter.
  Time-to-first-submission and tokens-before-vs-after-first-submission separate self-verification-heavy behavior from hidden-feedback-driven search.

- Generic self-test counts are not enough for dynamic tasks.
  It is useful to track whether the agent actually authored and executed at least one firmware-level runtime probe, not just how many unit tests it wrote.

- Infrastructure noise should be labeled separately from model logic failures.
  Connection resets, unreachable UART ports, and similar harness/runtime faults should not be conflated with host-test or integration logic failures.

- Useful benchmark outputs should include:
  final hidden outcome,
  stage reached,
  failure category,
  failure family,
  infra-failure labeling,
  wall-clock time,
  time to first hidden submission,
  hidden eval count,
  build attempts,
  tool-call count,
  files touched,
  lines changed,
  self-tests written,
  self-test runs,
  runtime-probe authored/executed flags,
  false-green rate,
  prompt/completion/total tokens,
  token split before vs after the first hidden submission,
  and cost if available.

## Open Questions

- How much task prose detail improves realistic self-verification before it starts to look too much like an oracle or a public test plan?
- Should `ci_red_green` be treated as a realistic industrial CI condition or as a separate semi-oracular ablation?
- How many repeats per task/mode/model cell are needed before differences in pass rate and efficiency become stable enough for paper claims?
