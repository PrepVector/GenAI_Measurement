# Chapter 2: Offline Metric Design for GenAI Products

This chapter builds the measurement foundation for everything that follows
in the book. By the end you will have a complete offline evaluation
infrastructure: a metric hierarchy, a versioned evaluation set, an LLM
judge, a human annotation pipeline, cost and latency instrumentation, and
the versioning system that ties it all together.

## What this chapter covers

**Section 1 — Designing a metric hierarchy**
Goal metrics, guardrail metrics, and debugging metrics. Goodhart's Law and
how to resist it. The goal → proxy → metric translation chain.

**Section 2 — Building evaluation sets that reflect real usage**
Sourcing from production logs, synthetic generation, and expert curation.
Multi-turn and agentic evaluation. Preventing data leakage.

**Section 3 — LLM-as-a-judge: implementation and bias mitigation**
Judge prompt design, rubric-based evaluation, chain-of-thought scoring.
Position bias, verbosity bias, and self-preference bias. Calibration
against human annotations.

**Section 4 — Human evaluation at scale and cost/latency as first-class metrics**
When human evaluation is unavoidable. Hybrid annotation pipelines. Cost
as a Pareto frontier problem. Latency at P50/P90/P99.
→ **Hands-on exercise**: build the freshness monitoring pipeline.

**Section 5 — Versioning prompts, model configs, and measurement artifacts**
The reproducibility problem. What to version and how. Connecting versioning
to the measurement pipeline. Diff-based debugging.
→ **Hands-on exercise**: build the versioned evaluation run record.

## Hands-on exercises

| Section | Exercise | Folder | API key needed |
|---------|----------|--------|---------------|
| 4 | Freshness monitoring pipeline | `hands_on/section_4_freshness_monitor/` | No |
| 5 | Versioned eval run record | `hands_on/section_5_eval_run_record/` | No |

## Prerequisites

- Python 3.9 or above
- No external dependencies for these exercises (standard library only)
- For chapters that use the Anthropic API: `pip install anthropic`

## Getting started

From the repo root:
```bash
# Run all Chapter 2 tests
pytest chapter_02/ -v

# Run a specific exercise
cd chapter_02/hands_on/section_4_freshness_monitor
pytest tests/ -v
```

## How the two exercises connect

The freshness monitor (Section 4) produces a dict via
`freshness_to_run_record()`. That dict slots directly into the `freshness`
field of the `EvalRunRecord` built in Section 5. Work through Section 4
before Section 5 so the schema is familiar when you encounter it in the
run record.

## Key concepts introduced in this chapter

- **Metric hierarchy** — goal metrics (what success looks like), guardrail
  metrics (what failure looks like), debugging metrics (where to look when
  things go wrong).
- **Eval run record** — a structured JSON artifact that links every metric
  score to the exact model, prompt, index, dataset, and judge prompt that
  produced it. The foundation of reproducible measurement.
- **Content hashing** — versioning datasets and prompt templates by their
  SHA-256 hash rather than by filename or timestamp, so any change is
  immediately detectable.
- **Diff-based debugging** — when a metric moves unexpectedly, compare the
  run records of the two surrounding runs to identify which artifact changed.
- **Freshness monitoring** — tracking staleness rates per domain, raising
  alerts when thresholds are breached, and suppressing domains that are too
  stale to serve safely.