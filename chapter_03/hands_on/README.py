# Chapter 3 — Hands-on exercises

## Exercise structure

Each exercise folder contains three things:

1. `*_starter.py` — start here. Functions are stubbed with TODO
   comments explaining exactly what to implement. Data structures
   and test trajectories are provided.

2. `*_solution.py` — the reference solution. Open this only after
   attempting the exercise. Every non-trivial decision is explained
   in an inline comment.

3. `tests/test_*.py` — pytest tests that validate your implementation.
   Run `pytest tests/ -v` from inside the exercise folder. All tests
   should pass before you consider the exercise complete.

## Running the tests

From the repo root:
```bash
pytest chapter_03/ -v
```

From inside a specific exercise folder:
```bash
cd chapter_03/hands_on/section_3_agent_evaluator
pytest tests/ -v
```

## Order of exercises

Work through the exercises in the order they appear in the book:

1. `section_2_freshness_pipeline/` — no Anthropic API calls required
2. `section_3_agent_evaluator/` — requires an Anthropic API key