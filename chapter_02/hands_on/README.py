# Chapter 2 — Hands-on exercises

## Overview

Two exercises in this chapter, each in its own subfolder:

| Folder | Exercise | Depends on |
|--------|----------|------------|
| `section_4_freshness_monitor/` | Freshness monitoring pipeline | Nothing |
| `section_5_eval_run_record/` | Versioned eval run record | Section 4 output format |

Work through them in order. The run record in Section 5 incorporates
the freshness output from Section 4 as a nested field — understanding
the freshness schema first makes the run record structure clearer.

## Exercise structure

Each exercise folder contains three things:

**`*_starter.py`** — start here. Data structures and sample data are
provided in full. Functions are stubbed with `TODO` comments that describe
exactly what to implement, including the expected inputs, outputs, and any
edge cases to handle.

**`*_solution.py`** — the reference solution. Every non-trivial decision
is explained in an inline comment. Open this only after attempting the
exercise — the process of working through the implementation is itself
a core part of what this chapter teaches.

**`tests/test_*.py`** — pytest tests grouped by exercise class. Run all
tests at once (`pytest tests/ -v`) or run one exercise at a time
(`pytest tests/ -v -k "Exercise1"`).

## Running the tests

From the repo root:
```bash
# All Chapter 2 tests
pytest chapter_02/ -v

# One exercise
cd chapter_02/hands_on/section_4_freshness_monitor
pytest tests/ -v

# One exercise class only
pytest tests/ -v -k "TestExercise3"
```

## Running tests against the solution

Each test file imports from the starter by default. To run the tests
against the reference solution, change the import at the top of the
test file:

```python
# Default (your implementation)
from freshness_monitor_starter import ...

# Reference solution
from freshness_monitor_solution import ...
```

All tests should pass against the solution file. If your implementation
passes all tests, it is correct for the purposes of this chapter.

## Common mistakes

**Section 4:**
- Forgetting `sort_keys=True` in `hash_dataset()` — without it, two
  dicts with the same content but different key insertion order produce
  different hashes, breaking reproducibility.
- Returning `0` instead of `float("inf")` for an empty domain in
  `ingestion_lag_hours()` — `float("inf")` correctly signals that the
  domain has never been ingested.
- Using `>=` instead of `>` in `threshold_exceeded` — the threshold is
  a strict upper bound, not an inclusive one.

**Section 5:**
- Setting the timestamp at the end of a run rather than the beginning —
  the timestamp should record when the artifacts were locked, not when
  results were computed.
- Hardcoding `float("inf")` in the JSON output — `float("inf")` is not
  JSON-serialisable. Convert infinite ingestion lag values to `null` or
  a large sentinel integer before serialising.
- Returning the first artifact that changed rather than all changed
  artifacts in `diff_run_records()` — the diff must report every
  changed artifact, not just the first.