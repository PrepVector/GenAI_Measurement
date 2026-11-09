# Sections 2–4: Design calculators

## What you will build

Three short calculators that put numbers on the designs in Sections 2 to 4:

- The completion rate of a routing policy, from traffic mix and per-type rates
- The number of decisive judgments a pairwise preference test needs
- The share of an A/B test's queries that interleaving needs

## Why this matters

Each design buys speed or sensitivity at a price. Computing the numbers
yourself shows where the gain comes from: a router is only as good as its
worst-routed query type, a small preference needs thousands of judgments,
and interleaving saves the most when queries differ a lot in difficulty.

## Files

| File | Description |
|------|-------------|
| `design_calculators_starter.py` | Start here — stub functions with TODOs |
| `design_calculators_solution.py` | Reference solution with explanations |
| `tests/test_design_calculators.py` | Pytest tests grouped by exercise |

## Exercises

| Exercise | What to implement | Key concept |
|----------|------------------|-------------|
| 4 | `policy_completion_rate()` | Traffic-weighted routing value (Table 9.4) |
| 5 | `decisive_judgments()` | Sample size for a sign test (Table 9.8) |
| 6 | `interleaving_query_fraction()` | Paired versus independent variance (Section 3.1) |

## Running the tests

```bash
cd chapter_09/hands_on/design_calculators
pytest tests/ -v

# One exercise at a time
pytest tests/ -v -k "TestExercise4"
```

## Prerequisites

- Python 3.9+
- `pip install pytest`

## Verifying your implementation

Run the solution to see the expected output:
```bash
python design_calculators_solution.py
```

Expected output is embedded as `# Expected output:` comments at the
bottom of the solution file.
