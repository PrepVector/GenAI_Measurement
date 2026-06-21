"""
Chapter 3 — Section 4: Trace-based diagnostic pipeline
Reference solution

Read this only after attempting the exercises yourself.
Every non-trivial decision is explained in an inline comment.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from anthropic import Anthropic

client = Anthropic()


# ── Data structures (identical to starter) ───────────────────────────────────

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
    layer: str


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
    failed_layer: str
    failed_step_index: Optional[int]
    evidence: str


@dataclass
class DiagnosticReport:
    total_traces: int
    failure_rates: Dict[str, Dict]
    most_common_failure: str


# ── Exercise 1: Trace capture ─────────────────────────────────────────────────

class TraceCapture:

    def __init__(self, task_id: str, task_description: str):
        # A short UUID prefix is enough for a unique trace ID within a run.
        # If you need globally unique IDs across runs, use the full UUID.
        self.trace_id = str(uuid.uuid4())[:8]
        self.task_id = task_id
        self.task_description = task_description
        self.steps: List[TraceStep] = []
        self.start_time = time.time()

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
        tool_event = None
        if tool_name:
            tool_event = ToolEvent(
                tool_name=tool_name,
                parameters=parameters or {},
                response=response,
                latency_ms=latency_ms,
                error=error,
            )
        self.steps.append(TraceStep(
            step_index=len(self.steps),
            timestamp=datetime.utcnow().isoformat(),
            agent_reasoning=agent_reasoning,
            tool_event=tool_event,
            layer=layer,
        ))

    def finalise(
        self,
        final_response: str,
        routing_decision: str,
        total_tokens: int,
        cost_usd: float,
    ) -> AgentTrace:
        wall_clock_ms = (time.time() - self.start_time) * 1000
        return AgentTrace(
            trace_id=self.trace_id,
            task_id=self.task_id,
            task_description=self.task_description,
            routing_decision=routing_decision,
            steps=self.steps,
            final_response=final_response,
            total_tokens=total_tokens,
            total_cost_usd=cost_usd,
            wall_clock_ms=wall_clock_ms,
        )


# ── Exercise 2: Two-model pipeline ───────────────────────────────────────────

# The routing prompt uses explicit JSON-only output to make parsing
# deterministic. Three categories are enough for the demonstration —
# in production you would expand this to match your domain taxonomy.
ROUTING_SYSTEM = """You are a query router for an enterprise knowledge assistant.
Classify the incoming query into exactly one of these categories:
  policy    — questions about HR, legal, or compliance policies
  pricing   — questions about product pricing or commercial terms
  general   — all other questions

Respond with JSON only — no preamble, no markdown fences:
{"category": "<category>", "reasoning": "<one sentence>"}"""

# The generation prompt explicitly forbids hallucination by tying the
# answer to the provided context. The "say so explicitly" instruction
# is important: without it the model will often attempt an answer
# rather than admitting the context is insufficient.
GENERATION_SYSTEM = """You are a helpful enterprise knowledge assistant.
Answer the user's question using ONLY the provided context documents.
If the context does not contain sufficient information to answer, say so explicitly.
Always cite the specific document you are drawing from in your response."""


def simulate_retrieve_documents(query: str) -> tuple:
    """Provided — do not modify."""
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
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        system=ROUTING_SYSTEM,
        messages=[{"role": "user", "content": query}],
    )
    result = json.loads(response.content[0].text.strip())
    return result["category"], result["reasoning"]


def generate_response(query: str, context: str, category: str) -> tuple:
    user_prompt = (
        f"Query category: {category}\n\n"
        f"Context documents:\n{context}\n\n"
        f"Question: {query}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=GENERATION_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return response.content[0].text, tokens


def run_traced_agent(
    task_id: str,
    task_description: str,
    query: str,
) -> AgentTrace:
    capture = TraceCapture(task_id, task_description)

    # Step 1: Route (routing layer — no tool event)
    category, routing_reasoning = route_query(query)
    capture.record_step(
        agent_reasoning=f"Routing decision: {routing_reasoning}",
        layer="routing",
    )

    # Step 2: Retrieve (tool execution layer)
    context, retrieval_latency = simulate_retrieve_documents(query)
    capture.record_step(
        agent_reasoning=f"Retrieving documents for category '{category}'.",
        tool_name="retrieve_documents",
        parameters={"query": query, "top_k": 3},
        response=context,
        latency_ms=retrieval_latency,
        layer="tool_execution",
    )

    # Step 3: Generate (synthesis layer — no tool event)
    final_response, tokens = generate_response(query, context, category)
    capture.record_step(
        agent_reasoning="Synthesising response from retrieved context.",
        layer="synthesis",
    )

    # $3 per million tokens is a rough estimate for claude-sonnet-4-6.
    # Replace with the actual pricing for your chosen model.
    cost = (tokens / 1_000_000) * 3.0

    return capture.finalise(
        final_response=final_response,
        routing_decision=category,
        total_tokens=tokens,
        cost_usd=cost,
    )


# ── Exercise 3: Failure attribution judge ────────────────────────────────────

# The four-way classification is deliberate: "none" is a valid output
# because not every trace contains a failure. Without it, the judge is
# forced to assign blame even when the response is correct, which
# inflates failure rates and makes the diagnostic report misleading.
ATTRIBUTION_SYSTEM = """You are a diagnostic evaluator for AI agent pipeline failures.
Given a task, its success criteria, and a structured trace of the agent's execution,
identify which layer of the pipeline caused the failure, if any.

Layers:
  routing        — the query was sent to the wrong specialist path
  tool_execution — retrieval returned irrelevant, empty, or incorrect results
  synthesis      — the agent had good context but produced a wrong or incomplete response
  none           — the response is not actually a failure; it satisfies the success criteria

Respond with JSON only — no preamble, no markdown fences:
{
  "failed_layer": "<layer>",
  "failed_step_index": <integer index of the failed step, or null>,
  "evidence": "<one to two sentences citing specific trace events>"
}"""


def attribute_trace_failure(
    trace: AgentTrace,
    success_criteria: str,
) -> FailureAttribution:
    # Truncating reasoning and response in the summary keeps the prompt
    # compact without losing the information the judge needs to attribute
    # failures. 100 chars of reasoning is enough to see what the agent
    # intended; 120 chars of response is enough to see what the tool returned.
    trace_summary = "\n".join([
        f"Step {s.step_index} [{s.layer}]: {s.agent_reasoning[:100]}"
        + (
            f" → Tool: {s.tool_event.tool_name}"
            f"({json.dumps(s.tool_event.parameters)})"
            f" → Response: {(s.tool_event.response or '')[:120]}"
            if s.tool_event else ""
        )
        for s in trace.steps
    ])

    user_prompt = (
        f"Task: {trace.task_description}\n\n"
        f"Success criteria: {success_criteria}\n\n"
        f"Routing decision: {trace.routing_decision}\n\n"
        f"Trace:\n{trace_summary}\n\n"
        f"Final response:\n{trace.final_response}\n\n"
        f"Identify which layer caused the failure, if any."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=ATTRIBUTION_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    result = json.loads(response.content[0].text.strip())
    return FailureAttribution(
        trace_id=trace.trace_id,
        task_id=trace.task_id,
        failed_layer=result["failed_layer"],
        failed_step_index=result.get("failed_step_index"),
        evidence=result["evidence"],
    )


# ── Exercise 4: Diagnostic report ────────────────────────────────────────────

def build_diagnostic_report(
    attributions: List[FailureAttribution],
) -> DiagnosticReport:
    if not attributions:
        return DiagnosticReport(0, {}, "none")

    total = len(attributions)
    counts: Dict[str, int] = {}
    for a in attributions:
        counts[a.failed_layer] = counts.get(a.failed_layer, 0) + 1

    failure_rates = {
        layer: {
            "count": count,
            "rate": round(count / total, 4),
        }
        for layer, count in sorted(counts.items(), key=lambda x: -x[1])
    }

    # Exclude "none" when finding the most common failure layer —
    # "none" means no failure, so reporting it as the most common
    # failure would be misleading.
    most_common = max(
        (l for l in counts if l != "none"),
        key=lambda l: counts[l],
        default="none",
    )

    return DiagnosticReport(
        total_traces=total,
        failure_rates=failure_rates,
        most_common_failure=most_common,
    )


# ── Exercise 5: Serialisation ─────────────────────────────────────────────────

def trace_to_run_record(trace: AgentTrace) -> dict:
    return {
        "trace_id": trace.trace_id,
        "task_id": trace.task_id,
        "captured_at": trace.captured_at,
        "routing_decision": trace.routing_decision,
        "total_tokens": trace.total_tokens,
        "total_cost_usd": round(trace.total_cost_usd, 6),
        "wall_clock_ms": round(trace.wall_clock_ms, 1),
        "steps": [
            {
                "step_index": s.step_index,
                "layer": s.layer,
                "reasoning": s.agent_reasoning,
                "tool": {
                    "name": s.tool_event.tool_name,
                    "latency_ms": round(s.tool_event.latency_ms, 1),
                    "error": s.tool_event.error,
                } if s.tool_event else None,
            }
            for s in trace.steps
        ],
    }


def summarise_traces(traces: List[AgentTrace]) -> dict:
    if not traces:
        return {
            "total_traces": 0,
            "total_tokens": 0,
            "mean_cost_usd": 0.0,
            "p95_cost_usd": 0.0,
            "mean_wall_clock_ms": 0.0,
            "p95_wall_clock_ms": 0.0,
        }

    costs = sorted(t.total_cost_usd for t in traces)
    latencies = sorted(t.wall_clock_ms for t in traces)
    n = len(traces)
    # P95 index: we use int(0.95 * n) capped at n-1. For small lists
    # this gives the highest value — which is the conservative choice
    # for a performance bound.
    p95_idx = min(int(0.95 * n), n - 1)

    return {
        "total_traces": n,
        "total_tokens": sum(t.total_tokens for t in traces),
        "mean_cost_usd": round(sum(costs) / n, 6),
        "p95_cost_usd": round(costs[p95_idx], 6),
        "mean_wall_clock_ms": round(sum(latencies) / n, 1),
        "p95_wall_clock_ms": round(latencies[p95_idx], 1),
    }


# ── Sample tasks (identical to starter) ──────────────────────────────────────

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

    # Expected output (approximate — LLM responses vary):
    #
    # Running: task_001
    #   Routing: policy
    #   Steps:   3
    #   Tokens:  ~350
    #   Response: According to the EU Remote Work Policy v2.1 (amended Jan 2024)...
    #   Failed layer: none
    #   Evidence: The response correctly cites Doc 42 and states the 3-day allowance.
    #
    # Running: task_002
    #   Routing: pricing
    #   Steps:   3
    #   Tokens:  ~300
    #   Response: According to the Q3 Pricing Tiers (Doc 88)...
    #   Failed layer: none
    #   Evidence: All three tiers with correct thresholds are present.
    #
    # Diagnostic report:
    # {
    #   "total_traces": 2,
    #   "failure_rates": {
    #     "none": {"count": 2, "rate": 1.0}
    #   },
    #   "most_common_failure": "none"
    # }
    #
    # Trace summary:
    # {
    #   "total_traces": 2,
    #   "total_tokens": ~650,
    #   "mean_cost_usd": ~0.000002,
    #   "p95_cost_usd": ~0.000002,
    #   "mean_wall_clock_ms": ~1200.0,
    #   "p95_wall_clock_ms": ~1300.0
    # }