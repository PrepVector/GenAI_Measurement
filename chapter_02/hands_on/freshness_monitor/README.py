# Section 4: Freshness monitoring pipeline

## What you will build

A freshness monitoring pipeline that tracks how stale the documents in
your retrieval index are, per domain. The pipeline:

- Computes staleness in hours for every document in the index
- Aggregates staleness into per-domain reports (staleness rate, mean
  staleness, ingestion lag)
- Compares per-domain staleness rates against configurable thresholds
- Raises alerts for domains that have breached their threshold
- Suppresses domains whose staleness is too severe to serve safely
- Serialises results into a JSON structure that integrates with the
  eval run record built in Section 5
- Provides a diff function for comparing the freshness profiles of two
  consecutive runs

## Why this matters

A RAG system that consistently produces well-grounded, relevant responses
— but grounds them in documents that are six months out of date — is not
providing accurate information. Standard quality metrics will not catch
this. Freshness monitoring is the measurement layer that catches it.

## Files

| File | Description |
|------|-------------|
| `freshness_monitor_starter.py` | Start here — stub functions with TODOs |
| `freshness_monitor_solution.py` | Reference solution with explanations |
| `tests/test_freshness_monitor.py` | Pytest tests grouped by exercise |

## Exercises

| Exercise | Function(s) to implement | Concepts |
|----------|--------------------------|---------|
| 1 | `staleness_hours()`, `ingestion_lag_hours()` | Time delta arithmetic, sentinel values |
| 2 | `compute_domain_report()` | Aggregation, threshold comparison |
| 3 | `run_freshness_monitor()` | Grouping, weighted averaging, alert generation |
| 4 | `freshness_to_run_record()` | Serialisation, rounding |
| 5 | `diff_freshness()` | Set operations, delta thresholds |

## Running the tests

```bash
cd chapter_02/hands_on/section_4_freshness_monitor
pytest tests/ -v

# Run one exercise at a time
pytest tests/ -v -k "TestExercise1"
pytest tests/ -v -k "TestExercise2"
```

## Verifying your implementation

Run the solution's `__main__` block to see the expected output:

```bash
python freshness_monitor_solution.py
```

You can verify your own implementation produces the same output:

```bash
python freshness_monitor_starter.py
```

The expected output of the `__main__` block is embedded directly in
`freshness_monitor_solution.py` as inline comments at the bottom of
the file. Search for `# Expected output:` to find it.