"""
Chapter 2 — Section 5: Versioned evaluation run record
Starter file

Work through the four exercises in the book to implement each function
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
    """
    The complete set of versioned artifacts used in one evaluation run.
    Every field here must be recorded before the run starts — not after.
    Pre-registration prevents retroactive rationalisation of which version
    was used.
    """
    model_version: str          # e.g. "claude-sonnet-4-6"
    prompt_hash: str            # SHA-256 of the prompt template file
    index_id: str               # identifier of the retrieval index snapshot
    embedding_model: str        # embedding model name and version
    dataset_hash: str           # SHA-256 of the evaluation dataset contents
    judge_prompt_hash: str      # SHA-256 of the judge prompt template


@dataclass
class AggregateMetrics:
    """Goal metrics, guardrail results, and cost/latency for one run."""
    goal_metric_score: float       # primary quality score (e.g. answer satisfaction)
    guardrail_passed: bool         # True if all guardrail thresholds were met
    hallucination_rate: float      # fraction of responses with unsupported claims
    latency_p50_ms: float          # median response latency
    latency_p95_ms: float          # 95th percentile latency
    cost_per_query_usd: float      # mean cost per query in USD


@dataclass
class EvalRunRecord:
    """
    The central artifact of the versioning system. Every evaluation run
    produces exactly one of these. It links every metric score to the
    exact set of artifacts that produced it.
    """
    run_id: str
    timestamp: str                           # ISO format
    artifact_versions: ArtifactVersions
    aggregate_metrics: AggregateMetrics
    freshness: Optional[Dict] = None         # output of freshness_to_run_record()
    per_example_results_path: str = ""       # path to the per-example results file
    notes: str = ""                          # free-text annotation


# ── Exercise 1: Content hashing ───────────────────────────────────────────────

def hash_file_content(content: str) -> str:
    """
    Compute the SHA-256 hash of a string's UTF-8 encoding.

    TODO (Exercise 1):
      Use hashlib to compute the SHA-256 hash of content encoded as UTF-8.
      Return the hex digest string.

      This is used to version prompt templates and evaluation datasets
      by content rather than by filename or timestamp. Content-based
      versioning makes it immediately detectable if anything changed —
      the hash changes — without requiring a separate version numbering
      system.
    """
    raise NotImplementedError("Implement hash_file_content() — Exercise 1")


def hash_dataset(examples: List[Dict]) -> str:
    """
    Compute a deterministic content hash for a list of evaluation examples.

    TODO (Exercise 1):
      1. Serialise examples to a JSON string with sort_keys=True and
         separators=(',', ':') to ensure deterministic output regardless
         of key insertion order.
      2. Return the SHA-256 hex digest of the UTF-8 encoded string.

      Using sort_keys=True is critical: two dicts with the same keys and
      values but different insertion orders must produce the same hash.
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
      Build and return an EvalRunRecord. The timestamp should be set to
      datetime.utcnow().isoformat() at the moment the record is created.
      All other fields come directly from the parameters.
    """
    raise NotImplementedError("Implement build_run_record() — Exercise 2")


def run_record_to_dict(record: EvalRunRecord) -> dict:
    """
    Serialise an EvalRunRecord to a JSON-serialisable dict.

    TODO (Exercise 2):
      Return a dict with these top-level keys:
        "run_id"
        "timestamp"
        "artifact_versions": {
            "model_version", "prompt_hash", "index_id",
            "embedding_model", "dataset_hash", "judge_prompt_hash"
        }
        "aggregate_metrics": {
            "goal_metric_score", "guardrail_passed",
            "hallucination_rate", "latency_p50_ms",
            "latency_p95_ms", "cost_per_query_usd"
        }
        "freshness": the freshness dict, or None
        "per_example_results_path"
        "notes"

      All float values should be rounded to 4 decimal places.
    """
    raise NotImplementedError("Implement run_record_to_dict() — Exercise 2")


# ── Exercise 3: Diff ─────────────────────────────────────────────────────────

def diff_run_records(record_a: dict, record_b: dict) -> dict:
    """
    Compare two serialised run records and identify what changed.

    TODO (Exercise 3):
      Compare the artifact_versions and aggregate_metrics sections of
      two run records produced by run_record_to_dict().

      Return a dict with three keys:
        "changed_artifacts": list of artifact field names where the
                             values differ between record_a and record_b.
        "metric_deltas": dict of metric_name → delta (b_value - a_value)
                         for all numeric metrics in aggregate_metrics.
                         Round each delta to 4 decimal places.
        "guardrail_status": one of:
                             "both_passed"   — both runs passed guardrails
                             "both_failed"   — both runs failed
                             "newly_passed"  — a failed, b passed
                             "newly_failed"  — a passed, b failed
    """
    raise NotImplementedError("Implement diff_run_records() — Exercise 3")


# ── Exercise 4: Run history ───────────────────────────────────────────────────

def find_regression(
    run_history: List[dict],
    metric: str,
    threshold: float,
) -> Optional[dict]:
    """
    Scan a chronological list of run records to find the first run where
    a metric dropped below a threshold.

    TODO (Exercise 4):
      run_history is a list of dicts produced by run_record_to_dict(),
      ordered chronologically (oldest first).

      Scan through the list and return the first run record where
      aggregate_metrics[metric] < threshold.

      Return None if no such run exists.

      This is how you answer the question: "when did quality first
      drop below our launch gate?"
    """
    raise NotImplementedError("Implement find_regression() — Exercise 4")


def attribute_regression(
    run_a: dict,
    run_b: dict,
) -> str:
    """
    Given two consecutive run records where a metric regressed, return
    a human-readable string identifying the most likely cause.

    TODO (Exercise 4):
      1. Call diff_run_records() to find what changed.
      2. If exactly one artifact changed, return:
           "Likely cause: {artifact_name} changed
            ({old_value} → {new_value})"
      3. If multiple artifacts changed, return:
           "Multiple artifacts changed: {comma-separated list}.
            Isolate changes and re-run to identify root cause."
      4. If no artifacts changed, return:
           "No artifact changes detected. Check for
            distribution shift or tool/infrastructure changes."
    """
    raise NotImplementedError("Implement attribute_regression() — Exercise 4")


# ── Sample data ───────────────────────────────────────────────────────────────

SAMPLE_PROMPT_TEMPLATE = """You are a helpful enterprise assistant.
Answer the user's question based only on the provided context.
If the context does not contain enough information, say so.

Context:
{context}

Question:
{question}
"""

SAMPLE_JUDGE_PROMPT = """You are an expert evaluator assessing the quality
of AI assistant responses. Rate the response on a 1-5 scale for:
- Answer satisfaction
- Groundedness
- Citation quality
Return a JSON object with these three scores and a brief reasoning.
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
    prompt_hash=hash_file_content(SAMPLE_PROMPT_TEMPLATE)
    if callable(hash_file_content) else "abc123",
    index_id="index_v42_20240601",
    embedding_model="text-embedding-3-large-v1",
    dataset_hash=hash_dataset(SAMPLE_DATASET)
    if callable(hash_dataset) else "def456",
    judge_prompt_hash=hash_file_content(SAMPLE_JUDGE_PROMPT)
    if callable(hash_file_content) else "ghi789",
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
    goal_metric_score=0.84,    # regressed
    guardrail_passed=True,
    hallucination_rate=0.06,   # regressed
    latency_p50_ms=1380.0,
    latency_p95_ms=4200.0,     # regressed
    cost_per_query_usd=0.0031,
)


if __name__ == "__main__":
    record_v1 = build_run_record(
        run_id="run_001",
        artifact_versions=SAMPLE_ARTIFACT_VERSIONS,
        aggregate_metrics=SAMPLE_METRICS_V1,
        notes="Baseline run",
    )
    record_v2 = build_run_record(
        run_id="run_002",
        artifact_versions=ArtifactVersions(
            **{**vars(SAMPLE_ARTIFACT_VERSIONS),
               "model_version": "claude-sonnet-4-7"}
        ),
        aggregate_metrics=SAMPLE_METRICS_V2,
        notes="Model version bump",
    )

    dict_v1 = run_record_to_dict(record_v1)
    dict_v2 = run_record_to_dict(record_v2)

    diff = diff_run_records(dict_v1, dict_v2)
    print("Changed artifacts:", diff["changed_artifacts"])
    print("Metric deltas:", diff["metric_deltas"])
    print("Guardrail status:", diff["guardrail_status"])

    attribution = attribute_regression(dict_v1, dict_v2)
    print("\nRegression attribution:", attribution)

    history = [dict_v1, dict_v2]
    first_regression = find_regression(history, "goal_metric_score", 0.86)
    print("\nFirst run below 0.86 goal score:", first_regression["run_id"])