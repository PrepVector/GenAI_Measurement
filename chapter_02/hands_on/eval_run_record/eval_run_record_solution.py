"""
Chapter 2 — Section 5: Versioned evaluation run record
Reference solution

Read this only after attempting the exercises yourself.
Every non-trivial decision is explained in an inline comment.
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ── Data structures (identical to starter) ───────────────────────────────────

@dataclass
class ArtifactVersions:
    model_version: str
    prompt_hash: str
    index_id: str
    embedding_model: str
    dataset_hash: str
    judge_prompt_hash: str


@dataclass
class AggregateMetrics:
    goal_metric_score: float
    guardrail_passed: bool
    hallucination_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    cost_per_query_usd: float


@dataclass
class EvalRunRecord:
    run_id: str
    timestamp: str
    artifact_versions: ArtifactVersions
    aggregate_metrics: AggregateMetrics
    freshness: Optional[Dict] = None
    per_example_results_path: str = ""
    notes: str = ""


# ── Exercise 1: Content hashing ───────────────────────────────────────────────

def hash_file_content(content: str) -> str:
    # SHA-256 is collision-resistant enough for our purposes and is
    # available in the Python standard library. We encode to UTF-8
    # explicitly rather than relying on the default encoding, which
    # may vary across platforms and would produce different hashes
    # for the same logical content.
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def hash_dataset(examples: List[Dict]) -> str:
    # sort_keys=True is the critical line here. Without it, two dicts
    # with the same key-value pairs but different insertion orders
    # produce different JSON strings and therefore different hashes.
    # separators=(',', ':') removes whitespace to produce a compact,
    # deterministic representation.
    serialised = json.dumps(examples, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


# ── Exercise 2: Building a run record ────────────────────────────────────────

def build_run_record(
    run_id: str,
    artifact_versions: ArtifactVersions,
    aggregate_metrics: AggregateMetrics,
    freshness: Optional[Dict] = None,
    per_example_results_path: str = "",
    notes: str = "",
) -> EvalRunRecord:
    # The timestamp is set at construction time, not at the end of the run.
    # This means it records when the artifacts were locked, not when the
    # results were computed — which is the semantically correct moment for
    # versioning purposes.
    return EvalRunRecord(
        run_id=run_id,
        timestamp=datetime.utcnow().isoformat(),
        artifact_versions=artifact_versions,
        aggregate_metrics=aggregate_metrics,
        freshness=freshness,
        per_example_results_path=per_example_results_path,
        notes=notes,
    )


def run_record_to_dict(record: EvalRunRecord) -> dict:
    av = record.artifact_versions
    am = record.aggregate_metrics
    return {
        "run_id": record.run_id,
        "timestamp": record.timestamp,
        "artifact_versions": {
            "model_version":    av.model_version,
            "prompt_hash":      av.prompt_hash,
            "index_id":         av.index_id,
            "embedding_model":  av.embedding_model,
            "dataset_hash":     av.dataset_hash,
            "judge_prompt_hash": av.judge_prompt_hash,
        },
        "aggregate_metrics": {
            "goal_metric_score":  round(am.goal_metric_score, 4),
            "guardrail_passed":   am.guardrail_passed,
            "hallucination_rate": round(am.hallucination_rate, 4),
            "latency_p50_ms":     round(am.latency_p50_ms, 4),
            "latency_p95_ms":     round(am.latency_p95_ms, 4),
            "cost_per_query_usd": round(am.cost_per_query_usd, 4),
        },
        "freshness": record.freshness,
        "per_example_results_path": record.per_example_results_path,
        "notes": record.notes,
    }


# ── Exercise 3: Diff ─────────────────────────────────────────────────────────

_NUMERIC_METRICS = [
    "goal_metric_score",
    "hallucination_rate",
    "latency_p50_ms",
    "latency_p95_ms",
    "cost_per_query_usd",
]


def diff_run_records(record_a: dict, record_b: dict) -> dict:
    av_a = record_a["artifact_versions"]
    av_b = record_b["artifact_versions"]

    # Identify changed artifacts. String comparison is exact here —
    # any character difference counts as a change. This is intentional:
    # a model version bump from "claude-sonnet-4-6" to "claude-sonnet-4-7"
    # should always be flagged, even if the performance difference is small.
    changed_artifacts = [
        key for key in av_a
        if av_a[key] != av_b[key]
    ]

    am_a = record_a["aggregate_metrics"]
    am_b = record_b["aggregate_metrics"]

    # Compute deltas for numeric metrics only. guardrail_passed is boolean
    # and handled separately through guardrail_status.
    metric_deltas = {
        m: round(am_b[m] - am_a[m], 4)
        for m in _NUMERIC_METRICS
        if m in am_a and m in am_b
    }

    # Guardrail status uses a four-way classification rather than a simple
    # boolean delta because the transition from passing to failing (or vice
    # versa) is qualitatively different from a numeric shift — it represents
    # a launch gate boundary crossing.
    a_passed = am_a.get("guardrail_passed", False)
    b_passed = am_b.get("guardrail_passed", False)

    if a_passed and b_passed:
        guardrail_status = "both_passed"
    elif not a_passed and not b_passed:
        guardrail_status = "both_failed"
    elif not a_passed and b_passed:
        guardrail_status = "newly_passed"
    else:
        guardrail_status = "newly_failed"

    return {
        "changed_artifacts": changed_artifacts,
        "metric_deltas": metric_deltas,
        "guardrail_status": guardrail_status,
    }


# ── Exercise 4: Run history ───────────────────────────────────────────────────

def find_regression(
    run_history: List[dict],
    metric: str,
    threshold: float,
) -> Optional[dict]:
    # Linear scan is correct here — run histories are typically short
    # (tens to hundreds of runs) and chronological order is preserved.
    # We return the first occurrence rather than the worst, because the
    # first regression is the actionable event: the change that caused it.
    for record in run_history:
        value = record.get("aggregate_metrics", {}).get(metric)
        if value is not None and value < threshold:
            return record
    return None


def attribute_regression(run_a: dict, run_b: dict) -> str:
    diff = diff_run_records(run_a, run_b)
    changed = diff["changed_artifacts"]

    if len(changed) == 0:
        return (
            "No artifact changes detected. Check for distribution shift "
            "or tool/infrastructure changes."
        )

    if len(changed) == 1:
        artifact = changed[0]
        old_val = run_a["artifact_versions"][artifact]
        new_val = run_b["artifact_versions"][artifact]
        return (
            f"Likely cause: {artifact} changed "
            f"({old_val} → {new_val})"
        )

    # Multiple changes make root cause analysis ambiguous. The correct
    # response is to isolate: re-run with only one artifact changed at
    # a time until the responsible change is identified.
    return (
        f"Multiple artifacts changed: {', '.join(changed)}. "
        f"Isolate changes and re-run to identify root cause."
    )


# ── Sample data (identical to starter) ───────────────────────────────────────

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
    prompt_hash=hash_file_content(SAMPLE_PROMPT_TEMPLATE),
    index_id="index_v42_20240601",
    embedding_model="text-embedding-3-large-v1",
    dataset_hash=hash_dataset(SAMPLE_DATASET),
    judge_prompt_hash=hash_file_content(SAMPLE_JUDGE_PROMPT),
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

    # Expected output:
    # Changed artifacts: ['model_version']
    # Metric deltas: {
    #   'goal_metric_score':  -0.03,
    #   'hallucination_rate':  0.02,
    #   'latency_p50_ms':     140.0,
    #   'latency_p95_ms':    1100.0,
    #   'cost_per_query_usd': 0.0008
    # }
    # Guardrail status: both_passed
    #
    # Regression attribution: Likely cause: model_version changed
    #   (claude-sonnet-4-6 → claude-sonnet-4-7)
    #
    # First run below 0.86 goal score: run_002
    #
    # A fully populated run record looks like:
    # {
    #   "run_id": "run_001",
    #   "timestamp": "2024-06-01T12:00:00",
    #   "artifact_versions": {
    #     "model_version":      "claude-sonnet-4-6",
    #     "prompt_hash":        "a3f2...",
    #     "index_id":           "index_v42_20240601",
    #     "embedding_model":    "text-embedding-3-large-v1",
    #     "dataset_hash":       "c8d1...",
    #     "judge_prompt_hash":  "f9e4..."
    #   },
    #   "aggregate_metrics": {
    #     "goal_metric_score":  0.87,
    #     "guardrail_passed":   true,
    #     "hallucination_rate": 0.04,
    #     "latency_p50_ms":     1240.0,
    #     "latency_p95_ms":     3100.0,
    #     "cost_per_query_usd": 0.0023
    #   },
    #   "freshness": null,
    #   "per_example_results_path": "",
    #   "notes": "Baseline run"
    # }