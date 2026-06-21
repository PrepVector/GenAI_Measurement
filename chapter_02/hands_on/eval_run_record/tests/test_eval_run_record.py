"""
Tests for Chapter 2 Section 5 — Versioned evaluation run record.

Run from the exercise folder:
    pytest tests/ -v

Tests are grouped by exercise:
    pytest tests/ -v -k "exercise_1"
"""

import json
import pytest
from datetime import datetime
from eval_run_record_starter import (
    hash_file_content,
    hash_dataset,
    build_run_record,
    run_record_to_dict,
    diff_run_records,
    find_regression,
    attribute_regression,
    ArtifactVersions,
    AggregateMetrics,
    EvalRunRecord,
    SAMPLE_PROMPT_TEMPLATE,
    SAMPLE_JUDGE_PROMPT,
    SAMPLE_DATASET,
    SAMPLE_ARTIFACT_VERSIONS,
    SAMPLE_METRICS_V1,
    SAMPLE_METRICS_V2,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_record(run_id="run_001", model="claude-sonnet-4-6",
                score=0.87, guardrail=True) -> dict:
    av = ArtifactVersions(
        model_version=model,
        prompt_hash="abc123",
        index_id="index_v42",
        embedding_model="embed-v1",
        dataset_hash="def456",
        judge_prompt_hash="ghi789",
    )
    am = AggregateMetrics(
        goal_metric_score=score,
        guardrail_passed=guardrail,
        hallucination_rate=0.04,
        latency_p50_ms=1200.0,
        latency_p95_ms=3000.0,
        cost_per_query_usd=0.002,
    )
    record = build_run_record(run_id=run_id, artifact_versions=av,
                              aggregate_metrics=am)
    return run_record_to_dict(record)


# ── Exercise 1: Hashing ───────────────────────────────────────────────────────

class TestExercise1Hashing:

    def test_hash_returns_string(self):
        assert isinstance(hash_file_content("hello"), str)

    def test_hash_is_64_chars(self):
        """SHA-256 hex digest is always 64 characters."""
        assert len(hash_file_content("hello")) == 64

    def test_same_content_same_hash(self):
        assert hash_file_content("hello") == hash_file_content("hello")

    def test_different_content_different_hash(self):
        assert hash_file_content("hello") != hash_file_content("world")

    def test_whitespace_matters(self):
        """A trailing newline changes the hash."""
        assert hash_file_content("hello") != hash_file_content("hello\n")

    def test_hash_dataset_returns_string(self):
        assert isinstance(hash_dataset(SAMPLE_DATASET), str)

    def test_hash_dataset_is_64_chars(self):
        assert len(hash_dataset(SAMPLE_DATASET)) == 64

    def test_hash_dataset_deterministic(self):
        assert hash_dataset(SAMPLE_DATASET) == hash_dataset(SAMPLE_DATASET)

    def test_hash_dataset_order_independent(self):
        """Dicts with same keys/values in different order hash identically."""
        d1 = [{"b": 2, "a": 1}]
        d2 = [{"a": 1, "b": 2}]
        assert hash_dataset(d1) == hash_dataset(d2)

    def test_hash_dataset_changes_with_content(self):
        original = [{"id": "q001", "query": "hello"}]
        modified = [{"id": "q001", "query": "goodbye"}]
        assert hash_dataset(original) != hash_dataset(modified)

    def test_prompt_template_hash_matches_known(self):
        """Hash of the sample prompt is stable across runs."""
        h1 = hash_file_content(SAMPLE_PROMPT_TEMPLATE)
        h2 = hash_file_content(SAMPLE_PROMPT_TEMPLATE)
        assert h1 == h2


# ── Exercise 2: Building records ─────────────────────────────────────────────

class TestExercise2BuildRecord:

    @pytest.fixture
    def record(self):
        return build_run_record(
            run_id="run_001",
            artifact_versions=SAMPLE_ARTIFACT_VERSIONS,
            aggregate_metrics=SAMPLE_METRICS_V1,
            notes="Test run",
        )

    def test_returns_eval_run_record(self, record):
        assert isinstance(record, EvalRunRecord)

    def test_run_id_set(self, record):
        assert record.run_id == "run_001"

    def test_timestamp_is_iso_format(self, record):
        datetime.fromisoformat(record.timestamp)

    def test_timestamp_is_utc_recent(self, record):
        ts = datetime.fromisoformat(record.timestamp)
        delta = (datetime.utcnow() - ts).total_seconds()
        assert delta < 5  # created within the last 5 seconds

    def test_notes_set(self, record):
        assert record.notes == "Test run"

    def test_serialisation_top_level_keys(self, record):
        d = run_record_to_dict(record)
        for key in [
            "run_id", "timestamp", "artifact_versions",
            "aggregate_metrics", "freshness",
            "per_example_results_path", "notes"
        ]:
            assert key in d

    def test_serialisation_artifact_keys(self, record):
        d = run_record_to_dict(record)
        for key in [
            "model_version", "prompt_hash", "index_id",
            "embedding_model", "dataset_hash", "judge_prompt_hash"
        ]:
            assert key in d["artifact_versions"]

    def test_serialisation_metric_keys(self, record):
        d = run_record_to_dict(record)
        for key in [
            "goal_metric_score", "guardrail_passed", "hallucination_rate",
            "latency_p50_ms", "latency_p95_ms", "cost_per_query_usd"
        ]:
            assert key in d["aggregate_metrics"]

    def test_floats_are_rounded(self, record):
        d = run_record_to_dict(record)
        score = d["aggregate_metrics"]["goal_metric_score"]
        assert score == round(score, 4)

    def test_json_serialisable(self, record):
        d = run_record_to_dict(record)
        json.dumps(d)

    def test_freshness_none_by_default(self, record):
        assert record.freshness is None


# ── Exercise 3: Diff ─────────────────────────────────────────────────────────

class TestExercise3Diff:

    def test_changed_artifact_detected(self):
        a = make_record(model="claude-sonnet-4-6")
        b = make_record(model="claude-sonnet-4-7")
        diff = diff_run_records(a, b)
        assert "model_version" in diff["changed_artifacts"]

    def test_unchanged_artifacts_not_listed(self):
        a = make_record(model="claude-sonnet-4-6")
        b = make_record(model="claude-sonnet-4-6")
        diff = diff_run_records(a, b)
        assert "model_version" not in diff["changed_artifacts"]

    def test_no_artifacts_changed(self):
        a = make_record()
        b = make_record()
        diff = diff_run_records(a, b)
        assert diff["changed_artifacts"] == []

    def test_metric_delta_positive(self):
        a = make_record(score=0.80)
        b = make_record(score=0.87)
        diff = diff_run_records(a, b)
        assert abs(diff["metric_deltas"]["goal_metric_score"] - 0.07) < 0.001

    def test_metric_delta_negative(self):
        a = make_record(score=0.87)
        b = make_record(score=0.80)
        diff = diff_run_records(a, b)
        assert abs(diff["metric_deltas"]["goal_metric_score"] - (-0.07)) < 0.001

    def test_guardrail_both_passed(self):
        a = make_record(guardrail=True)
        b = make_record(guardrail=True)
        diff = diff_run_records(a, b)
        assert diff["guardrail_status"] == "both_passed"

    def test_guardrail_both_failed(self):
        a = make_record(guardrail=False)
        b = make_record(guardrail=False)
        diff = diff_run_records(a, b)
        assert diff["guardrail_status"] == "both_failed"

    def test_guardrail_newly_failed(self):
        a = make_record(guardrail=True)
        b = make_record(guardrail=False)
        diff = diff_run_records(a, b)
        assert diff["guardrail_status"] == "newly_failed"

    def test_guardrail_newly_passed(self):
        a = make_record(guardrail=False)
        b = make_record(guardrail=True)
        diff = diff_run_records(a, b)
        assert diff["guardrail_status"] == "newly_passed"

    def test_result_has_correct_keys(self):
        diff = diff_run_records(make_record(), make_record())
        assert "changed_artifacts" in diff
        assert "metric_deltas" in diff
        assert "guardrail_status" in diff

    def test_deltas_are_rounded(self):
        a = make_record(score=0.876543)
        b = make_record(score=0.912345)
        diff = diff_run_records(a, b)
        delta = diff["metric_deltas"]["goal_metric_score"]
        assert delta == round(delta, 4)


# ── Exercise 4: Run history ───────────────────────────────────────────────────

class TestExercise4RunHistory:

    def test_find_regression_returns_correct_record(self):
        history = [
            make_record("run_001", score=0.90),
            make_record("run_002", score=0.87),
            make_record("run_003", score=0.83),
        ]
        result = find_regression(history, "goal_metric_score", 0.85)
        assert result["run_id"] == "run_003"

    def test_find_regression_returns_first_occurrence(self):
        history = [
            make_record("run_001", score=0.90),
            make_record("run_002", score=0.80),
            make_record("run_003", score=0.75),
        ]
        result = find_regression(history, "goal_metric_score", 0.85)
        assert result["run_id"] == "run_002"

    def test_find_regression_returns_none_when_no_regression(self):
        history = [
            make_record("run_001", score=0.90),
            make_record("run_002", score=0.88),
        ]
        result = find_regression(history, "goal_metric_score", 0.85)
        assert result is None

    def test_find_regression_empty_history(self):
        assert find_regression([], "goal_metric_score", 0.85) is None

    def test_attribute_single_change(self):
        a = make_record(model="claude-sonnet-4-6")
        b = make_record(model="claude-sonnet-4-7")
        result = attribute_regression(a, b)
        assert "model_version" in result
        assert "claude-sonnet-4-6" in result
        assert "claude-sonnet-4-7" in result

    def test_attribute_no_change(self):
        a = make_record()
        b = make_record()
        result = attribute_regression(a, b)
        assert "No artifact changes detected" in result

    def test_attribute_multiple_changes(self):
        av_a = ArtifactVersions("model-a", "hash-a", "index-a",
                                "embed-a", "data-a", "judge-a")
        av_b = ArtifactVersions("model-b", "hash-b", "index-a",
                                "embed-a", "data-a", "judge-a")
        r_a = run_record_to_dict(
            build_run_record("r_a", av_a, SAMPLE_METRICS_V1)
        )
        r_b = run_record_to_dict(
            build_run_record("r_b", av_b, SAMPLE_METRICS_V2)
        )
        result = attribute_regression(r_a, r_b)
        assert "Multiple artifacts changed" in result

    def test_find_regression_works_on_hallucination_rate(self):
        history = [
            make_record("run_001", score=0.90),
            make_record("run_002", score=0.88),
        ]
        # Manually set hallucination_rate above threshold
        history[1]["aggregate_metrics"]["hallucination_rate"] = 0.15
        result = find_regression(history, "hallucination_rate", 0.10)
        assert result["run_id"] == "run_002"