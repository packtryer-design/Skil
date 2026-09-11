# Plugin evals

Cases in the native `claude plugin eval` layout: one directory per case with `prompt.md` (the user prompt) and `graders/criteria.md` (what a grader checks). Run with `claude plugin eval .` when the command is available on your account (it was in early access when these were written); the default ablation compares the plugin against a no-plugin baseline.

The broader, deterministic suite lives in `tests/` and runs with `python tests/run_tests.py`.
