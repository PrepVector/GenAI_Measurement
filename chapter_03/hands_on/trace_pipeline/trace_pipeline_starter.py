"""
Chapter 3 — Section 4: Trace-based diagnostic pipeline
Starter file

Work through the five exercises in the book to implement each function
marked with TODO. Run pytest tests/ to validate your implementation.

Prerequisites:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from anthropic import Anthropic

client = Anthropic()


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ToolEvent:
    tool_name: str
    parameters: Dict[str, Any]
    response: Optional[str]
    latency_ms: float
    error: Optional[str] = None


@dataclass
class TraceStep:
    step_index: int
    timestamp: str
    agent_reasoning: str
    tool_event: Optional[ToolEvent]
    layer: str          # "routing" | "tool_execution" | "synthesis"


@dataclass
class AgentTrace:
    trace_id: str
    task_id: str
    task_description: str
    routing_decision: str
    steps: List[TraceStep]
    final_response: str
    total_tokens: int
    total_cost_usd: float
    wall_clock_ms: float
    captured_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


@dataclass
class FailureAttribution:
    trace_id: str
    task_id: str
    failed_layer: str       # "routing"|"tool_execution"|"synthesis"|"none"
    failed_step_index: Optional[int]
    evidence: str


@dataclass
class DiagnosticReport:
    total_traces: int
    failure_rates: Dict[str, Dict]  # layer → {"count": int, "rate": float}
    most_common_failure: str


# ── Exercise 1: Trace capture ─────────────────────────────────────────────────

class TraceCapture:
    """
    Instruments a single agent execution and captures a structured trace.

    TODO (Exercise 1):
      Implement __init__(), record_step(), and finalise().

    __init__(task_id, task_description):
      - Generate a unique trace_id using str(uuid.uuid4())[:8]
      - Store task_id and task_description
      - Initialise an empty steps list
      - Record the wall-clock start time using time.time()

    record_step(agent_reasoning, tool_name=None, parameters=None,
                response=None, latency_ms=0.0, error=None, layer="synthesis"):
      - Build a ToolEvent if tool_name is provided, otherwise None
      - Append a TraceStep to self.steps with:
          step_index = len(self.steps)
          timestamp  = datetime.utcnow().isoformat()
          the provided agent_reasoning, tool_event, and layer

    finalise(final_response, routing_decision, total_tokens, cost_usd):
      - Compute wall_clock_ms = (time.time() - self.start_time) * 1000
      - Return a complete AgentTrace with all fields populated
    """
    def __init__(self, task_id: str, task_description: str):
        raise NotImplementedError("Implement TraceCapture.__init__() — Exercise 1")

    def record_step(
        self,
        agent_reasoning: str,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict] = None,
        response: Optional[str] = None,
        latency_ms: float = 0.0,
        error: Optional[str] = None,
        layer: str = "synthesis",
    ) -> None:
        raise NotImplementedError("Implement TraceCapture.record_step() — Exercise 1")

    def finalise(
        self,
        final_response: str,
        routing_decision: str,
        total_tokens: int,
        cost_usd: float,
    ) -> AgentTrace:
        raise NotImplementedError("Implement TraceCapture.finalise() — Exercise 1")


# ── Exercise 2: Two-model pipeline ───────────────────────────────────────────

# TODO (Exercise 2): Write a system prompt for the routing model.
# It must:
#   - Define three categories: policy, pricing, general
#   - Instruct the model to return JSON only:
#     {"category": "<category>", "reasoning": "<one sentence>"}
ROUTING_SYSTEM = """
TODO: Write your routing system prompt here.
"""

# TODO (Exercise 2): Write a system prompt for the generation model.
# It must:
#   - Instruct the model to answer using only the provided context
#   - Require source citation in the response
#   - State explicitly what to do when context is insufficient
GENERATION_SYSTEM = """
TODO: Write your generation system prompt here.
"""


def simulate_retrieve_documents(query: str) -> tuple:
    """
    Simulates document retrieval with ~50ms latency.
    Returns (result_string, latency_ms).
    PROVIDED — do not modify.
    """
    start = time.time()
    time.sleep(0.05)
    latency = (time.time() - start) * 1000
    results = {
        "remote work": (
            "[Doc 42: EU Remote Work Policy v2.1 — "
            "EU employees: up to 3 days remote/week. Amended Jan 2024.]\n"
            "[Doc 17: General HR Policy — applies to all employees]"
        ),
        "pricing": (
            "[Doc 88: Q3 Pricing Tiers — "
            "Tier 1: <$10k, Tier 2: $10k-$50k, Tier 3: >$50k]"
        ),
    }
    for key, result in results.items():
        if key.lower() in query.lower():
            return result, latency
    return "[No relevant documents found]", latency


def route_query(query: str) -> tuple:
    """
    Route a query using the routing model.

    TODO (Exercise 2):
      1. Call client.messages.create() with ROUTING_SYSTEM and the query.
         Use model="claude-sonnet-4-6", max_tokens=100.
      2. Parse the JSON response.
      3. Return (category, reasoning) as a tuple of strings.
    """
    raise NotImplementedError("Implement route_query() — Exercise 2")


def generate_response(query: str, context: str, category: str) -> tuple:
    """
    Generate a grounded response using the generation model.

    TODO (Exercise 2):
      1. Build a user prompt combining category, context, and query.
      2. Call client.messages.create() with GENERATION_SYSTEM.
         Use model="claude-sonnet-4-6", max_tokens=500.
      3. Return (response_text, total_tokens) as a tuple.
         total_tokens = input_tokens + output_tokens from response.usage.
    """
    raise NotImplementedError("Implement generate_response() — Exercise 2")


def run_traced_agent(
    task_id: str,
    task_description: str,
    query: str,
) -> AgentTrace:
    """
    Execute the two-model pipeline with full trace capture.

    TODO (Exercise 2):
      1. Initialise a TraceCapture for this task.
      2. Call route_query() and record the result as a routing step
         (layer="routing", no tool_event).
      3. Call simulate_retrieve_documents() and record as a tool step
         (layer="tool_execution", tool_name="retrieve_documents").
      4. Call generate_response() and record as a synthesis step
         (layer="synthesis", no tool_event).
      5. Estimate cost: (total_tokens / 1_000_000) * 3.0
      6. Call capture.finalise() and return the AgentTrace.
    """
    raise NotImplementedError("Implement run_traced_agent() — Exercise 2")


# ── Exercise 3: Failure attribution judge ────────────────────────────────────

# TODO (Exercise 3): Write a system prompt for the attribution judge.
# It must:
#   - Define all four outcomes precisely:
#       routing        — query sent to wrong specialist path
#       tool_execution — retrieval returned irrelevant or empty results
#       synthesis      — good context but wrong or incomplete response
#       none           — the response is not actually a failure
#   - Require the judge to cite specific trace events as evidence
#   - Return JSON only:
#     {"failed_layer": "...", "failed_step_index": <int|null>,
#      "evidence": "..."}
ATTRIBUTION_SYSTEM = """
TODO: Write your attribution judge system prompt here.
"""


def attribute_trace_failure(
    trace: AgentTrace,
    success_criteria: str,
) -> FailureAttribution:
    """
    Attribute a task failure to a specific pipeline layer.

    TODO (Exercise 3):
      1. Build a trace summary string — for each step include:
           "Step N [layer]: <first 100 chars of reasoning>"
           + " → Tool: <tool_name>(<params>)"
             " → Response: <first 120 chars of response>"
           (only if step has a tool_event)
      2. Build a user prompt with:
           - task_description and success_criteria
           - routing_decision
           - trace summary
           - final_response
      3. Call client.messages.create() with ATTRIBUTION_SYSTEM.
         Use model="claude-sonnet-4-6", max_tokens=300.
      4. Parse the JSON response and return a FailureAttribution.
    """
    raise NotImplementedError("Implement attribute_trace_failure() — Exercise 3")


# ── Exercise 4: Diagnostic report ────────────────────────────────────────────

def build_diagnostic_report(
    attributions: List[FailureAttribution],
) -> DiagnosticReport:
    """
    Aggregate failure attributions into a diagnostic report.

    TODO (Exercise 4):
      1. Count occurrences of each failed_layer across attributions.
      2. Compute failure_rates: for each layer, store
           {"count": int, "rate": round(count/total, 4)}
         Sort by count descending.
      3. Find most_common_failure: the layer with the highest count,
         excluding "none". Return "none" if all attributions are "none".
      4. Return a DiagnosticReport.
      Handle the empty list case: return DiagnosticReport(0, {}, "none").
    """
    raise NotImplementedError("Implement build_diagnostic_report() — Exercise 4")


# ── Exercise 5: Serialisation ─────────────────────────────────────────────────

def trace_to_run_record(trace: AgentTrace) -> dict:
    """
    Serialise a trace for inclusion in the Chapter 2 eval run record.

    TODO (Exercise 5):
      Return a dict with these keys:
        "trace_id", "task_id", "captured_at"
        "routing_decision"
        "total_tokens", "total_cost_usd" (6dp), "wall_clock_ms" (1dp)
        "steps": list of {
            "step_index": int,
            "layer": str,
            "reasoning": str,
            "tool": {"name": str, "latency_ms": float (1dp), "error": str|None}
                     or None if no tool_event
        }
    """
    raise NotImplementedError("Implement trace_to_run_record() — Exercise 5")


def summarise_traces(traces: List[AgentTrace]) -> dict:
    """
    Aggregate cost, latency, and token statistics across many traces.

    TODO (Exercise 5):
      Return a dict with:
        "total_traces": int
        "total_tokens": int
        "mean_cost_usd": float (6dp)
        "p95_cost_usd": float (6dp)
        "mean_wall_clock_ms": float (1dp)
        "p95_wall_clock_ms": float (1dp)

      P95 = value at the 95th percentile (sort the list, take index
      at int(0.95 * len) — use 0-based indexing).
      Handle the empty list case gracefully.
    """
    raise NotImplementedError("Implement summarise_traces() — Exercise 5")


# ── Sample tasks ──────────────────────────────────────────────────────────────

SAMPLE_TASKS = [
    {
        "task_id": "task_001",
        "description": "EU remote work policy query",
        "query": "What is our current remote work policy for EU employees?",
        "success_criteria": (
            "Response cites EU Remote Work Policy v2.1, "
            "states the 3-day allowance, and notes the Jan 2024 amendment."
        ),
    },
    {
        "task_id": "task_002",
        "description": "Q3 pricing query",
        "query": "What are the Q3 pricing tiers?",
        "success_criteria": (
            "Response correctly states all three pricing tiers "
            "with their dollar thresholds."
        ),
    },
]


if __name__ == "__main__":
    traces = []
    attributions = []

    for task in SAMPLE_TASKS:
        print(f"\nRunning: {task['task_id']}")
        trace = run_traced_agent(
            task["task_id"], task["description"], task["query"]
        )
        traces.append(trace)
        print(f"  Routing: {trace.routing_decision}")
        print(f"  Steps:   {len(trace.steps)}")
        print(f"  Tokens:  {trace.total_tokens}")
        print(f"  Response: {trace.final_response[:100]}...")

        attribution = attribute_trace_failure(trace, task["success_criteria"])
        attributions.append(attribution)
        print(f"  Failed layer: {attribution.failed_layer}")
        print(f"  Evidence: {attribution.evidence}")

    report = build_diagnostic_report(attributions)
    print(f"\nDiagnostic report:")
    print(json.dumps({
        "total_traces": report.total_traces,
        "failure_rates": report.failure_rates,
        "most_common_failure": report.most_common_failure,
    }, indent=2))

    print(f"\nTrace summary:")
    print(json.dumps(summarise_traces(traces), indent=2))