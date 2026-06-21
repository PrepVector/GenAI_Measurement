# Section 5: Versioned evaluation run record

## What you will build

A versioned evaluation run record system that:

- Computes deterministic content hashes for prompt templates and
  evaluation datasets using SHA-256
- Builds structured run records that link every metric score to the
  exact set of artifacts (model, prompt, index, dataset, judge prompt)
  that produced it
- Serialises run records to JSON for storage alongside evaluation results
- Diffs two run records to identify which artifacts changed and how
  metrics shifted between them
- Scans a run history to find the first run where a metric regressed
  below a threshold and attributes the regression to the most likely
  changed artifact

## Why this matters

Without versioning, the question "did quality actually improve or did
we just change the evaluation set?" has no answer. The run record makes
every number traceable to the exact configuration that produced it.
When a metric moves unexpectedly, the diff function turns root cause
analysis from guesswork into a structured comparison.

## Files

| File | Description |
|------|-------------|
| `eval_run_record_starter.py` | Start here — stub functions with TODOs |
| `eval_run_record_solution.py` | Reference solution with explanations |
| `tests/test_eval_run_record.py` | Pytest tests grouped by exercise |

## Exercises

| Exercise | Function(s) to implement | Concepts |
|----------|--------------------------|---------|
| 1 | `hash_file_content()`, `hash_dataset()` | SHA-256, deterministic serialisation |
| 2 | `build_run_record()`, `run_record_to_dict()` | Dataclass construction, serialisation |
| 3 | `diff_run_records()` | Artifact comparison, metric deltas, guardrail status |
| 4 | `find_regression()`, `attribute_regression()` | History scanning, root cause attribution |

## Running the tests

```bash
cd chapter_02/hands_on/section_5_eval_run_record
pytest tests/ -v

# Run one exercise at a time
pytest tests/ -v -k "TestExercise1"
pytest tests/ -v -k "TestExercise2"
```

## Verifying your implementation

Run the solution's `__main__` block to see the expected output:

```bash
python eval_run_record_solution.py
```

You can verify your own implementation produces the same output:

```bash
python eval_run_record_starter.py
```

The expected output of the `__main__` block is embedded directly in
`eval_run_record_solution.py` as inline comments at the bottom of the
file. Search for `# Expected output:` to find it.

## How this connects to Frshness Monitor

The `freshness` field in `EvalRunRecord` is designed to hold the output
of `freshness_to_run_record()` from Section 4. A complete run record
looks like this — and this snippet is also in the solution file as a
comment so you can copy it directly:

```python
# A fully populated run record (from eval_run_record_solution.py):
# {
#   "run_id": "run_001",
#   "timestamp": "2024-06-01T12:00:00",
#   "artifact_versions": {
#     "model_version": "claude-sonnet-4-6",
#     "prompt_hash":   "a3f2...",
#     "index_id":      "index_v42_20240601",
#     "embedding_model": "text-embedding-3-large-v1",
#     "dataset_hash":  "c8d1...",
#     "judge_prompt_hash": "f9e4..."
#   },
#   "aggregate_metrics": {
#     "goal_metric_score":  0.87,
#     "guardrail_passed":   true,
#     "hallucination_rate": 0.04,
#     "latency_p50_ms":     1240.0,
#     "latency_p95_ms":     3100.0,
#     "cost_per_query_usd": 0.0023
#   },
#   "freshness": {
#     "index_freshness_score": 0.5003,
#     "domain_reports": { ... }
#   },
#   "per_example_results_path": "results/run_001_examples.json",
#   "notes": "Baseline run after pricing index refresh"
# }
```

When `freshness` is `None` (the default), it means freshness monitoring
was not run for that evaluation.

## Key design decisions to understand

**Why `sort_keys=True` in `hash_dataset()`?** Python dicts do not
guarantee insertion order consistency across versions. Two logically
identical dicts with different insertion orders produce different JSON
strings without `sort_keys=True`, which would produce different hashes
for the same dataset content — breaking the entire versioning guarantee.

**Why set the timestamp at construction time, not at the end of the run?**
The timestamp should record when the artifacts were locked, not when the
results were computed. A run that took three hours to complete should
still record the moment the configuration was fixed.

**Why is `guardrail_status` a four-way enum rather than a boolean delta?**
Crossing a guardrail threshold is qualitatively different from a numeric
metric shift — it represents a launch gate boundary. Naming the four
transitions explicitly (`both_passed`, `both_failed`, `newly_passed`,
`newly_failed`) makes the status immediately actionable.

**Why return all changed artifacts in `diff_run_records()`, not just one?**
Returning only the first changed artifact would silently hide compounding
changes. The full list is what makes it possible to say with confidence
"exactly one thing changed between these two runs."