# Section 1: Thompson Sampling for model selection

## What you will build

The experiments behind Figures 9.1 to 9.3 and Section 1.4:

- An exploration floor that reserves part of the traffic for a uniform split
- A floor sweep that shows what the floor costs in regret
- An experiment in which the two leading models tie
- A comparison of daily and weekly posterior updates

## Why this matters

A bandit loses far fewer task completions than a balanced A/B test while it
learns which model is best, but the savings depend on choices the algorithm
does not make for you: how much traffic to keep exploring, how close the
candidates are, and how quickly feedback reaches the posterior.

## Files

| File | Description |
|------|-------------|
| `bandit_model_selection_starter.py` | Start here — stub functions with TODOs and a provided simulator |
| `bandit_model_selection_solution.py` | Reference solution with explanations |
| `tests/test_bandit_model_selection.py` | Pytest tests grouped by exercise |

## Exercises

| Exercise | What to implement | Key concept |
|----------|------------------|-------------|
| 1 | `route_with_floor()`, `floor_sweep()` | Exploration floor, regret versus coverage |
| 2 | `tied_leaders_experiment()`, `top_two_share()` | Regret when the best options tie |
| 3 | `update_cadence_experiment()` | Delayed feedback, batch updates |

## Running the tests

```bash
cd chapter_09/hands_on/bandit_model_selection
pytest tests/ -v

# One exercise at a time
pytest tests/ -v -k "TestExercise1"
```

The simulations in the tests run 100 repetitions, so the whole suite takes
under half a minute against the solution.

## Prerequisites

- Python 3.9+
- `pip install numpy pytest`

## Verifying your implementation

Run the solution to see the expected output:
```bash
python bandit_model_selection_solution.py
```

Expected output is embedded as `# Expected output:` comments at the
bottom of the solution file.
