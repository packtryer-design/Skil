# Plugin evals

Cases in the native `claude plugin eval` layout: one directory per case with `prompt.md` (the user prompt) and `graders/criteria.md` (what a grader checks, one criterion per line). Run with `claude plugin eval .` when the command is available on your account (it was in early access when these were written); the default ablation compares the plugin against a no-plugin baseline.

| Case | Exercises |
| --- | --- |
| `compile-repository-prompt` | A HIGH-risk repository change: checkpoints, testing, safety boundaries, completion criteria |
| `create-output-style-skill` | A skill artifact: frontmatter, rules with bad/good pairs, scope, exceptions |
| `clarify-ambiguous-request` | The clarification gate: ask at most three questions with defaults, then stop |
| `compile-for-small-model` | Model tier `small`: worked examples, a literal output template, MUST/MUST NOT only, one job |
| `compile-with-capability-gap` | A blocking capability gap on Open WebUI: honest degradation, a Compatibility section, no faked execution |

The broader, deterministic suite lives in `tests/` (40 cases, offline grading of the worked examples, fixtures) and runs with `python tests/run_tests.py`.
