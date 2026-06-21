# Section 4: Trace-based diagnostic pipeline

## What you will build

A fully instrumented two-model agent pipeline that:

- Captures structured traces at every step of agent execution
- Records reasoning, tool calls, latency, and layer attribution per step
- Routes queries through a classification model to a generation model
- Attributes pipeline failures to the specific layer that caused them
- Aggregates failure attributions into a diagnostic report
- Serialises trace data into the Chapter 2 eval run record format

## Why this matters

Without traces, agent failures are unattributable. A wrong final answer
could originate in the routing layer, the tool execution layer, or the
synthesis layer — and each requires a completely different fix. Traces
make the failure location visible; the attribution judge makes it named.

## Files

| File | Description |
|------|-------------|
| `trace_pipeline_starter.py` | Start here — stub functions with TODOs |
| `trace_pipeline_solution.py` | Reference solution with explanations |
| `tests/test_trace_pipeline.py` | Pytest tests grouped by exercise |

## Exercises

| Exercise | What to implement | Key concept |
|----------|------------------|-------------|
| 1 | `TraceCapture` class | Instrumentation, wall-clock timing |
| 2 | `route_query()`, `generate_response()`, `run_traced_agent()` | Two-model pipeline, layer tagging |
| 3 | `attribute_trace_failure()` | LLM attribution judge |
| 4 | `build_diagnostic_report()` | Failure rate aggregation |
| 5 | `trace_to_run_record()`, `summarise_traces()` | Serialisation, P95 latency |

## Running the tests

```bash
cd chapter_03/hands_on/section_4_trace_pipeline
pytest tests/ -v

# One exercise at a time
pytest tests/ -v -k "TestExercise1"
```

## Prerequisites

- Python 3.9+
- `pip install anthropic`
- `export ANTHROPIC_API_KEY=your_key_here`

## Verifying your implementation

Run the solution to see expected output:
```bash
python trace_pipeline_solution.py
```

Expected output is embedded as `# Expected output:` comments
at the bottom of the solution file.