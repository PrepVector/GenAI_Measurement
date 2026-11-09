# Chapter 9 — Hands-on exercises

## Exercise structure

Each exercise folder contains three things:

1. `*_starter.py` — start here. Functions are stubbed with TODO
   comments explaining exactly what to implement. The scenario data
   and, where the book asks you to run experiments, the simulator
   are provided.

2. `*_solution.py` — the reference solution. Open this only after
   attempting the exercise. Every non-trivial decision is explained
   in an inline comment, and the expected output is embedded as
   `# Expected output:` comments at the bottom of the file.

3. `tests/test_*.py` — pytest tests that validate your implementation.
   Run `pytest tests/ -v` from inside the exercise folder. All tests
   should pass before you consider the exercise complete.

## Running the tests

From inside a specific exercise folder:
```bash
cd chapter_09/hands_on/bandit_model_selection
pytest tests/ -v
```

## Order of exercises

Work through the exercises in the order they appear in the book:

1. `bandit_model_selection/` — Exercises 1–3 (Section 1)
2. `design_calculators/` — Exercises 4–6 (Sections 2–4)

Neither exercise requires an Anthropic API key. All results are
simulated for illustration, not measured on a real system.
