"""
Chapter 3 — Section 5: Versioned eval run record and offline gate
Starter file

Work through the five exercises in the book to implement each function
marked with TODO. Run pytest tests/ to validate your implementation.

No Anthropic API key required — standard library only.
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ArtifactVersions:
    """Every artifact that can change between evaluation runs."""
    model_version: str
    prompt_hash: str
    index_id: str
    embedding_model: str
    dataset_hash: str
    judge_prompt_hash: str


@dataclass
class AggregateMetrics:
    """Goal metrics, guardrail results, and cost/latency for one run."""
    goal_metric_score: float
    guardrail_passed: bool
    hallucination_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    cost_per_query_usd: float


@dataclass
class EvalRunRecord:
    """Links every metric score to the exact artifacts that produced it."""
    run_id: str
    timestamp: str
    artifact_versions: ArtifactVersions
    aggregate_metrics: AggregateMetrics
    freshness: Optional[Dict] = None
    per_example_results_path: str = ""
    notes: str = ""


@dataclass
class GateCondition:
    """
    A single offline gate condition.

    TODO (Exercise 5):
      Implement __post_init__() to compute:
        passed: bool
          direction="min" → observed >= threshold
          direction="max" → observed <= threshold
        gap: float
          direction="min" → observed - threshold
            (positive = within floor, negative = below floor)
          direction="max" → threshold - observed
            (positive = within ceiling, negative = above ceiling)
    """
    name: str
    observed: float
    threshold: float
    direction: str        # "min" | "max"
    passed: bool = field(init=False)
    gap: float = field(init=False)

    def __post_init__(self):
        raise NotImplementedError(
            "Implement GateCondition.__post_init__() — Exercise 5"
        )


@dataclass
class GateDecision:
    """Structured result of an offline gate evaluation."""
    passed: bool
    conditions: Dict[str, GateCondition]
    annotation: str


# ── Exercise 1: Content hashing ───────────────────────────────────────────────

def hash_file_content(content: str) -> str:
    """
    Compute the SHA-256 hash of a string's UTF-8 encoding.

    TODO (Exercise 1):
      Use hashlib to compute the SHA-256 hash of content encoded as UTF-8.
      Return the hex digest string (64 characters).

      This is used to version prompt templates and judge prompts by
      content rather than filename or timestamp — any change is
      immediately detectable because the hash changes.
    """
    raise NotImplementedError("Implement hash_file_content() — Exercise 1")


def hash_dataset(examples: List[Dict]) -> str:
    """
    Compute a deterministic content hash for a list of evaluation examples.

    TODO (Exercise 1):
      1. Serialise examples to JSON with sort_keys=True and
         separators=(',', ':') — deterministic regardless of dict
         insertion order.
      2. Return the SHA-256 hex digest of the UTF-8 encoded string.

      Test: hash_dataset([{"b":2,"a":1}]) == hash_dataset([{"a":1,"b":2}])
      must be True.
    """
    raise NotImplementedError("Implement hash_dataset() — Exercise 1")


# ── Exercise 2: Building a run record ────────────────────────────────────────

def build_run_record(
    run_id: str,
    artifact_versions: ArtifactVersions,
    aggregate_metrics: AggregateMetrics,
    freshness: Optional[Dict] = None,
    per_example_results_path: str = "",
    notes: str = "",
) -> EvalRunRecord:
    """
    Construct a complete evaluation run record.

    TODO (Exercise 2):
      Set timestamp to datetime.utcnow().isoformat() at construction time
      — recording when the artifacts were locked, not when results were
      computed. All other fields come directly from the parameters.
    """
    raise NotImplementedError("Implement build_run_record() — Exercise 2")


def run_record_to_dict(record: EvalRunRecord) -> dict:
    """
    Serialise an EvalRunRecord to a JSON-serialisable dict.

    TODO (Exercise 2):
      Return a dict with keys:
        run_id, timestamp,
        artifact_versions: {model_version, prompt_hash, index_id,
                            embedding_model, dataset_hash, judge_prompt_hash}
        aggregate_metrics: {goal_metric_score, guardrail_passed,
                            hallucination_rate, latency_p50_ms,
                            latency_p95_ms, cost_per_query_usd}
        freshness, per_example_results_path, notes

      Round all float values to 4 decimal places.
    """
    raise NotImplementedError("Implement run_record_to_dict() — Exercise 2")


# ── Exercise 3: Diff ─────────────────────────────────────────────────────────

def diff_run_records(record_a: dict, record_b: dict) -> dict:
    """
    Compare two serialised run records and identify what changed.

    TODO (Exercise 3):
      Return a dict with:
        "changed_artifacts": list of artifact field names that differ
        "metric_deltas": dict of metric → (b_value - a_value) rounded to 4dp
                         for all numeric metrics in aggregate_metrics
        "guardrail_status": one of:
          "both_passed"  — both passed
          "both_failed"  — both failed
          "newly_passed" — a failed, b passed
          "newly_failed" — a passed, b failed
    """
    raise NotImplementedError("Implement diff_run_records() — Exercise 3")


# ── Exercise 4: Run history ───────────────────────────────────────────────────

def find_regression(
    run_history: List[dict],
    metric: str,
    threshold: float,
) -> Optional[dict]:
    """
    Find the first run where a metric dropped below a threshold.

    TODO (Exercise 4):
      Scan run_history (chronological, oldest first) and return the
      first record where aggregate_metrics[metric] < threshold.
      Return None if no such run exists or the list is empty.
    """
    raise NotImplementedError("Implement find_regression() — Exercise 4")


def attribute_regression(run_a: dict, run_b: dict) -> str:
    """
    Attribute a metric regression to the most likely changed artifact.

    TODO (Exercise 4):
      1. Call diff_run_records() to find what changed.
      2. Return one of:
           One artifact changed:
             "Likely cause: {artifact} changed ({old} → {new})"
           Multiple changed:
             "Multiple artifacts changed: {list}. Isolate changes
              and re-run to identify root cause."
           None changed:
             "No artifact changes detected. Check for distribution
              shift or tool/infrastructure changes."
    """
    raise NotImplementedError("Implement attribute_regression() — Exercise 4")


# ── Exercise 5: Offline gate ──────────────────────────────────────────────────

def evaluate_gate(
    run_record: dict,
    quality_floor: float,
    hallucination_ceiling: float,
    cost_ceiling_usd: float,
    latency_p95_ceiling_ms: float,
) -> GateDecision:
    """
    Apply the four offline gate conditions to an evaluation run record.

    TODO (Exercise 5):
      1. Extract metrics from run_record["aggregate_metrics"].
         Safe defaults if a key is missing:
           goal_metric_score  → 0.0
           hallucination_rate → 1.0
           cost_per_query_usd → 999.0
           latency_p95_ms     → 999999.0

      2. Construct one GateCondition per dimension:
           quality_floor:         direction="min"
           hallucination_ceiling: direction="max"
           cost_ceiling:          direction="max"
           latency_ceiling:       direction="max"

      3. passed = all(c.passed for c in conditions.values())

      4. Build annotation:
           All pass:    "All four gate conditions passed. System approved
                         to advance to shadow deployment."
           One fails:   "Gate blocked on {name}. Observed {observed:.4f}
                         is {above ceiling|below floor} {threshold:.4f}
                         by {abs(gap):.4f}. Close this gap before
                         re-evaluation."
           Multi-fail:  "Gate blocked on {n} conditions: {names}. All
                         failures must be resolved before re-evaluation."

      5. Return a GateDecision.
    """
    raise NotImplementedError("Implement evaluate_gate() — Exercise 5")


def print_gate_report(decision: GateDecision) -> None:
    """
    Print a human-readable gate report to stdout.

    TODO (Exercise 5):
      Format:
        ======================================================
          Offline gate: PASS ✓  (or BLOCK ✗)
        ======================================================
          ✓ Quality floor
            Observed: 4.1000  Threshold: 3.8000  (0.3000 within threshold)
          ✗ Latency P95 ceiling
            Observed: 4340.0000  Threshold: 4000.0000  (340.0000 above ceiling)
          ...
          {annotation}
    """
    raise NotImplementedError("Implement print_gate_report() — Exercise 5")


def gate_and_record(
    run_record: dict,
    quality_floor: float,
    hallucination_ceiling: float,
    cost_ceiling_usd: float,
    latency_p95_ceiling_ms: float,
) -> dict:
    """
    Evaluate the gate and write the decision into the run record.

    TODO (Exercise 5):
      1. Call evaluate_gate() with the run_record and thresholds.
      2. Work on a COPY of run_record — do not mutate the original.
      3. Add a "gate_decision" key:
         {
           "passed": bool,
           "annotation": str,
           "conditions": {
             key: {
               "name": str, "observed": float (4dp),
               "threshold": float (4dp), "passed": bool, "gap": float (4dp)
             }
           }
         }
      4. Return the enriched copy.
    """
    raise NotImplementedError("Implement gate_and_record() — Exercise 5")


# ── Sample data ───────────────────────────────────────────────────────────────

SAMPLE_PROMPT_TEMPLATE = """You are a helpful enterprise assistant.
Answer the user's question based only on the provided context.
If the context does not contain enough information, say so.

Context: {context}
Question: {question}
"""

SAMPLE_JUDGE_PROMPT = """You are an expert evaluator assessing AI assistant
response quality. Rate on a 1-5 scale for answer satisfaction, groundedness,
and citation quality. Return a JSON object with these three scores and reasoning.
"""

SAMPLE_DATASET = [
    {"id": "q001", "query": "What is the EU remote work allowance?",
     "domain": "policy"},
    {"id": "q002", "query": "What are the Q3 pricing tiers?",
     "domain": "pricing"},
    {"id": "q003", "query": "How do I submit an expense report?",
     "domain": "hr"},
]

SAMPLE_ARTIFACT_VERSIONS = ArtifactVersions(
    model_version="claude-sonnet-4-6",
    prompt_hash="abc123",
    index_id="index_v42_20240601",
    embedding_model="text-embedding-3-large-v1",
    dataset_hash="def456",
    judge_prompt_hash="ghi789",
)

SAMPLE_METRICS_V1 = AggregateMetrics(
    goal_metric_score=0.87,
    guardrail_passed=True,
    hallucination_rate=0.04,
    latency_p50_ms=1240.0,
    latency_p95_ms=3100.0,
    cost_per_query_usd=0.0023,
)

SAMPLE_METRICS_V2 = AggregateMetrics(
    goal_metric_score=0.84,
    guardrail_passed=True,
    hallucination_rate=0.06,
    latency_p50_ms=1380.0,
    latency_p95_ms=4200.0,
    cost_per_query_usd=0.0031,
)

# Gate scenario from Section 5.2 — three conditions pass, latency fails
GATE_SAMPLE_RECORD = {
    "run_id": "run_042",
    "aggregate_metrics": {
        "goal_metric_score":  4.1,
        "hallucination_rate": 0.052,
        "latency_p95_ms":     4340.0,
        "cost_per_query_usd": 0.0047,
    },
}

GATE_SAMPLE_THRESHOLDS = dict(
    quality_floor=3.8,
    hallucination_ceiling=0.08,
    cost_ceiling_usd=0.005,
    latency_p95_ceiling_ms=4000.0,
)


if __name__ == "__main__":
    # Exercises 1–4: run record and diff
    record_v1 = build_run_record("run_001", SAMPLE_ARTIFACT_VERSIONS,
                                 SAMPLE_METRICS_V1, notes="Baseline")
    record_v2 = build_run_record(
        "run_002",
        ArtifactVersions(**{**vars(SAMPLE_ARTIFACT_VERSIONS),
                            "model_version": "claude-sonnet-4-7"}),
        SAMPLE_METRICS_V2, notes="Model bump",
    )
    dict_v1 = run_record_to_dict(record_v1)
    dict_v2 = run_record_to_dict(record_v2)
    diff = diff_run_records(dict_v1, dict_v2)
    print("Changed artifacts:", diff["changed_artifacts"])
    print("Metric deltas:", diff["metric_deltas"])
    print("Guardrail status:", diff["guardrail_status"])
    print("Attribution:", attribute_regression(dict_v1, dict_v2))
    print("First regression:", find_regression(
        [dict_v1, dict_v2], "goal_metric_score", 0.86
    )["run_id"])

    # Exercise 5: offline gate
    print("\n--- Offline gate ---")
    decision = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
    print_gate_report(decision)
    enriched = gate_and_record(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
    print("Gate decision in run record:")
    print(json.dumps(enriched["gate_decision"], indent=2))