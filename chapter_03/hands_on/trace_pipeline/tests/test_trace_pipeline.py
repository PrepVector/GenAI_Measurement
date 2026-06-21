"""
Tests for Chapter 3 Section 4 — Trace-based diagnostic pipeline.

Run from the exercise folder:
    pytest tests/ -v

Tests are grouped by exercise:
    pytest tests/ -v -k "TestExercise1"

Note: Exercises 2 and 3 make live Anthropic API calls.
      Set ANTHROPIC_API_KEY before running those test classes.
"""

import time
import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from trace_pipeline_starter import (
    TraceCapture,
    route_query,
    generate_response,
    run_traced_agent,
    attribute_trace_failure,
    build_diagnostic_report,
    trace_to_run_record,
    summarise_traces,
    simulate_retrieve_documents,
    AgentTrace,
    TraceStep,
    ToolEvent,
    FailureAttribution,
    DiagnosticReport,
    SAMPLE_TASKS,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_trace(
    task_id="task_001",
    routing="policy",
    tokens=300,
    cost=0.0009,
    wall_ms=1200.0,
    steps=None,
) -> AgentTrace:
    if steps is None:
        steps = [
            TraceStep(0, datetime.utcnow().isoformat(),
                      "Routing.", None, "routing"),
            TraceStep(1, datetime.utcnow().isoformat(),
                      "Retrieving.",
                      ToolEvent("retrieve_documents", {"query": "q"}, "docs", 52.0),
                      "tool_execution"),
            TraceStep(2, datetime.utcnow().isoformat(),
                      "Synthesising.", None, "synthesis"),
        ]
    t = AgentTrace(
        trace_id="abc123",
        task_id=task_id,
        task_description="Test task",
        routing_decision=routing,
        steps=steps,
        final_response="The answer is X.",
        total_tokens=tokens,
        total_cost_usd=cost,
        wall_clock_ms=wall_ms,
    )
    return t


def make_attribution(layer: str, task_id="task_001") -> FailureAttribution:
    return FailureAttribution(
        trace_id="abc123",
        task_id=task_id,
        failed_layer=layer,
        failed_step_index=1 if layer != "none" else None,
        evidence="Test evidence.",
    )


# ── Exercise 1: TraceCapture ──────────────────────────────────────────────────

class TestExercise1TraceCapture:

    def test_init_creates_empty_steps(self):
        capture = TraceCapture("t1", "Test task")
        assert capture.steps == []

    def test_init_records_start_time(self):
        before = time.time()
        capture = TraceCapture("t1", "Test task")
        after = time.time()
        assert before <= capture.start_time <= after

    def test_init_generates_trace_id(self):
        capture = TraceCapture("t1", "Test task")
        assert isinstance(capture.trace_id, str)
        assert len(capture.trace_id) > 0

    def test_record_step_without_tool(self):
        capture = TraceCapture("t1", "Test task")
        capture.record_step("Deciding what to do.", layer="routing")
        assert len(capture.steps) == 1
        assert capture.steps[0].tool_event is None
        assert capture.steps[0].layer == "routing"

    def test_record_step_with_tool(self):
        capture = TraceCapture("t1", "Test task")
        capture.record_step(
            "Retrieving docs.",
            tool_name="retrieve_documents",
            parameters={"query": "test"},
            response="Doc 42",
            latency_ms=55.0,
            layer="tool_execution",
        )
        assert capture.steps[0].tool_event is not None
        assert capture.steps[0].tool_event.tool_name == "retrieve_documents"
        assert capture.steps[0].tool_event.latency_ms == 55.0

    def test_step_indices_increment(self):
        capture = TraceCapture("t1", "Test task")
        for _ in range(3):
            capture.record_step("Step.", layer="synthesis")
        indices = [s.step_index for s in capture.steps]
        assert indices == [0, 1, 2]

    def test_finalise_returns_agent_trace(self):
        capture = TraceCapture("t1", "Test task")
        capture.record_step("Step 1.", layer="routing")
        trace = capture.finalise("Final answer.", "policy", 200, 0.0006)
        assert isinstance(trace, AgentTrace)
        assert trace.task_id == "t1"
        assert trace.routing_decision == "policy"
        assert trace.total_tokens == 200
        assert trace.final_response == "Final answer."

    def test_finalise_computes_wall_clock(self):
        capture = TraceCapture("t1", "Test task")
        time.sleep(0.05)
        trace = capture.finalise("Done.", "general", 100, 0.0003)
        assert trace.wall_clock_ms >= 50.0

    def test_finalise_includes_all_steps(self):
        capture = TraceCapture("t1", "Test task")
        for layer in ["routing", "tool_execution", "synthesis"]:
            capture.record_step(f"Step in {layer}.", layer=layer)
        trace = capture.finalise("Done.", "policy", 100, 0.0003)
        assert len(trace.steps) == 3

    def test_step_has_timestamp(self):
        capture = TraceCapture("t1", "Test task")
        capture.record_step("Step.", layer="routing")
        ts = capture.steps[0].timestamp
        datetime.fromisoformat(ts)   # raises if not valid ISO format


# ── Exercise 2: Two-model pipeline ───────────────────────────────────────────

class TestExercise2Pipeline:
    """These tests make live API calls. Requires ANTHROPIC_API_KEY."""

    def test_route_query_returns_valid_category(self):
        category, reasoning = route_query("What is the remote work policy?")
        assert category in ("policy", "pricing", "general")
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0

    def test_route_query_policy_category(self):
        category, _ = route_query("What is the EU remote work policy?")
        assert category == "policy"

    def test_route_query_pricing_category(self):
        category, _ = route_query("What are the Q3 pricing tiers?")
        assert category == "pricing"

    def test_generate_response_returns_string_and_tokens(self):
        context = "[Doc 42: EU Remote Work Policy — 3 days/week]"
        response, tokens = generate_response(
            "What is the remote work policy?", context, "policy"
        )
        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_simulate_retrieve_returns_docs(self):
        result, latency = simulate_retrieve_documents("remote work policy")
        assert "Doc 42" in result
        assert latency >= 40.0

    def test_simulate_retrieve_unknown_returns_no_docs(self):
        result, _ = simulate_retrieve_documents("completely unknown query xyz")
        assert "No relevant documents found" in result

    def test_run_traced_agent_returns_agent_trace(self):
        trace = run_traced_agent(
            "task_001", "Test", SAMPLE_TASKS[0]["query"]
        )
        assert isinstance(trace, AgentTrace)

    def test_run_traced_agent_has_three_steps(self):
        trace = run_traced_agent(
            "task_001", "Test", SAMPLE_TASKS[0]["query"]
        )
        assert len(trace.steps) == 3

    def test_run_traced_agent_layer_labels(self):
        trace = run_traced_agent(
            "task_001", "Test", SAMPLE_TASKS[0]["query"]
        )
        layers = [s.layer for s in trace.steps]
        assert layers == ["routing", "tool_execution", "synthesis"]

    def test_run_traced_agent_routing_decision_set(self):
        trace = run_traced_agent(
            "task_001", "Test", SAMPLE_TASKS[0]["query"]
        )
        assert trace.routing_decision in ("policy", "pricing", "general")

    def test_run_traced_agent_cost_positive(self):
        trace = run_traced_agent(
            "task_001", "Test", SAMPLE_TASKS[0]["query"]
        )
        assert trace.total_cost_usd > 0


# ── Exercise 3: Failure attribution ──────────────────────────────────────────

class TestExercise3Attribution:
    """These tests make live API calls. Requires ANTHROPIC_API_KEY."""

    def test_attribute_returns_failure_attribution(self):
        trace = make_trace()
        result = attribute_trace_failure(
            trace, "Response must cite Doc 42 and state the 3-day allowance."
        )
        assert isinstance(result, FailureAttribution)

    def test_attribute_valid_layer(self):
        trace = make_trace()
        result = attribute_trace_failure(
            trace, "Response must cite Doc 42 and state the 3-day allowance."
        )
        assert result.failed_layer in (
            "routing", "tool_execution", "synthesis", "none"
        )

    def test_attribute_has_evidence(self):
        trace = make_trace()
        result = attribute_trace_failure(
            trace, "Response must cite Doc 42."
        )
        assert isinstance(result.evidence, str)
        assert len(result.evidence) > 10

    def test_attribute_correct_response_returns_none(self):
        trace = make_trace()
        trace = AgentTrace(
            trace_id="abc",
            task_id="t1",
            task_description="Test",
            routing_decision="policy",
            steps=trace.steps,
            final_response=(
                "According to Doc 42: EU Remote Work Policy v2.1, "
                "EU employees may work remotely up to 3 days per week."
            ),
            total_tokens=300,
            total_cost_usd=0.0009,
            wall_clock_ms=1200.0,
        )
        result = attribute_trace_failure(
            trace,
            "Response must cite Doc 42 and state the 3-day allowance."
        )
        assert result.failed_layer == "none"

    def test_attribute_empty_retrieval_flags_tool_execution(self):
        steps = [
            TraceStep(0, datetime.utcnow().isoformat(),
                      "Routing.", None, "routing"),
            TraceStep(1, datetime.utcnow().isoformat(),
                      "Retrieving.",
                      ToolEvent("retrieve_documents", {"query": "q"},
                                "[No relevant documents found]", 52.0),
                      "tool_execution"),
            TraceStep(2, datetime.utcnow().isoformat(),
                      "Synthesising.", None, "synthesis"),
        ]
        trace = AgentTrace(
            trace_id="abc",
            task_id="t1",
            task_description="What is the EU remote work policy?",
            routing_decision="policy",
            steps=steps,
            final_response="I could not find relevant information.",
            total_tokens=200,
            total_cost_usd=0.0006,
            wall_clock_ms=1100.0,
        )
        result = attribute_trace_failure(
            trace,
            "Response must cite Doc 42 and state the 3-day allowance."
        )
        assert result.failed_layer == "tool_execution"


# ── Exercise 4: Diagnostic report ────────────────────────────────────────────

class TestExercise4DiagnosticReport:

    def test_empty_returns_zero_traces(self):
        report = build_diagnostic_report([])
        assert report.total_traces == 0
        assert report.failure_rates == {}
        assert report.most_common_failure == "none"

    def test_total_traces_correct(self):
        attributions = [make_attribution("none") for _ in range(5)]
        report = build_diagnostic_report(attributions)
        assert report.total_traces == 5

    def test_failure_rates_computed(self):
        attributions = [
            make_attribution("routing"),
            make_attribution("routing"),
            make_attribution("tool_execution"),
            make_attribution("none"),
        ]
        report = build_diagnostic_report(attributions)
        assert report.failure_rates["routing"]["count"] == 2
        assert abs(report.failure_rates["routing"]["rate"] - 0.5) < 0.01

    def test_rates_sum_to_one(self):
        attributions = [
            make_attribution("routing"),
            make_attribution("tool_execution"),
            make_attribution("synthesis"),
            make_attribution("none"),
        ]
        report = build_diagnostic_report(attributions)
        total = sum(v["rate"] for v in report.failure_rates.values())
        assert abs(total - 1.0) < 0.01

    def test_most_common_failure_excludes_none(self):
        attributions = [
            make_attribution("none"),
            make_attribution("none"),
            make_attribution("none"),
            make_attribution("routing"),
            make_attribution("routing"),
        ]
        report = build_diagnostic_report(attributions)
        assert report.most_common_failure == "routing"

    def test_all_none_returns_none_as_most_common(self):
        attributions = [make_attribution("none") for _ in range(3)]
        report = build_diagnostic_report(attributions)
        assert report.most_common_failure == "none"

    def test_sorted_by_count_descending(self):
        attributions = [
            make_attribution("routing"),
            make_attribution("synthesis"),
            make_attribution("synthesis"),
            make_attribution("tool_execution"),
        ]
        report = build_diagnostic_report(attributions)
        counts = [v["count"] for v in report.failure_rates.values()]
        assert counts == sorted(counts, reverse=True)

    def test_returns_diagnostic_report_type(self):
        report = build_diagnostic_report([make_attribution("none")])
        assert isinstance(report, DiagnosticReport)


# ── Exercise 5: Serialisation ─────────────────────────────────────────────────

class TestExercise5Serialisation:

    def test_run_record_required_keys(self):
        trace = make_trace()
        record = trace_to_run_record(trace)
        for key in [
            "trace_id", "task_id", "captured_at", "routing_decision",
            "total_tokens", "total_cost_usd", "wall_clock_ms", "steps"
        ]:
            assert key in record

    def test_run_record_steps_count(self):
        trace = make_trace()
        record = trace_to_run_record(trace)
        assert len(record["steps"]) == 3

    def test_run_record_step_with_tool(self):
        trace = make_trace()
        record = trace_to_run_record(trace)
        tool_step = next(s for s in record["steps"] if s["tool"] is not None)
        assert "name" in tool_step["tool"]
        assert "latency_ms" in tool_step["tool"]

    def test_run_record_step_without_tool(self):
        trace = make_trace()
        record = trace_to_run_record(trace)
        routing_step = record["steps"][0]
        assert routing_step["tool"] is None

    def test_run_record_cost_rounded(self):
        trace = make_trace(cost=0.000123456789)
        record = trace_to_run_record(trace)
        assert record["total_cost_usd"] == round(0.000123456789, 6)

    def test_run_record_json_serialisable(self):
        trace = make_trace()
        record = trace_to_run_record(trace)
        json.dumps(record)

    def test_summarise_traces_empty(self):
        result = summarise_traces([])
        assert result["total_traces"] == 0
        assert result["total_tokens"] == 0

    def test_summarise_traces_total_tokens(self):
        traces = [make_trace(tokens=100), make_trace(tokens=200)]
        result = summarise_traces(traces)
        assert result["total_tokens"] == 300

    def test_summarise_traces_mean_cost(self):
        traces = [make_trace(cost=0.001), make_trace(cost=0.003)]
        result = summarise_traces(traces)
        assert abs(result["mean_cost_usd"] - 0.002) < 0.000001

    def test_summarise_traces_p95_latency(self):
        traces = [make_trace(wall_ms=float(i * 100)) for i in range(1, 21)]
        result = summarise_traces(traces)
        # 20 traces, p95_idx = int(0.95*20) = 19, sorted[19] = 2000.0
        assert result["p95_wall_clock_ms"] == 2000.0

    def test_summarise_traces_count(self):
        traces = [make_trace() for _ in range(5)]
        result = summarise_traces(traces)
        assert result["total_traces"] == 5