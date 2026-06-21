"""
Tests for Chapter 3 Section 2 — Freshness monitoring pipeline.

Run from the exercise folder:
    pytest tests/ -v

Tests are grouped by exercise:
    pytest tests/ -v -k "exercise_1"
"""

import pytest
from datetime import datetime
from freshness_pipeline_starter import (
    staleness_hours,
    ingestion_lag_hours,
    domain_report,
    run_monitor,
    to_run_record,
    diff_freshness,
    IndexedDocument,
    DomainFreshnessConfig,
    DomainFreshnessReport,
    FreshnessMonitorResult,
    SAMPLE_DOCUMENTS,
    SAMPLE_CONFIGS,
    SAMPLE_WEIGHTS,
    SAMPLE_NOW,
)

NOW = SAMPLE_NOW


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_doc(domain, source_hours_ago, ingested_hours_ago):
    """Create a document with timestamps relative to NOW."""
    from datetime import timedelta
    return IndexedDocument(
        doc_id=f"{domain}_{source_hours_ago}_{ingested_hours_ago}",
        domain=domain,
        source_updated_at=NOW - timedelta(hours=source_hours_ago),
        ingested_at=NOW - timedelta(hours=ingested_hours_ago),
    )


# ── Exercise 1 ────────────────────────────────────────────────────────────────

class TestExercise1:

    def test_staleness_hours_fresh_doc(self):
        """Document ingested 2 hours ago has staleness of 2 hours."""
        doc = make_doc("pricing", source_hours_ago=48, ingested_hours_ago=2)
        assert abs(staleness_hours(doc, NOW) - 2.0) < 0.01

    def test_staleness_hours_stale_doc(self):
        """Document ingested 84 hours ago has staleness of 84 hours."""
        doc = make_doc("pricing", source_hours_ago=90, ingested_hours_ago=84)
        assert abs(staleness_hours(doc, NOW) - 84.0) < 0.01

    def test_staleness_source_newer_than_ingestion(self):
        """Source updated after ingestion — staleness measured from ingestion."""
        doc = make_doc("pricing", source_hours_ago=10, ingested_hours_ago=50)
        assert abs(staleness_hours(doc, NOW) - 50.0) < 0.01

    def test_ingestion_lag_returns_min_staleness(self):
        """Ingestion lag is time since the most recent ingestion."""
        docs = [
            make_doc("pricing", 48, 84),   # ingested 84h ago
            make_doc("pricing", 48, 12),   # ingested 12h ago
        ]
        assert abs(ingestion_lag_hours(docs, NOW) - 12.0) < 0.01

    def test_ingestion_lag_empty_domain(self):
        """Empty domain returns infinity."""
        assert ingestion_lag_hours([], NOW) == float("inf")


# ── Exercise 2 ────────────────────────────────────────────────────────────────

class TestExercise2:

    def test_all_stale_domain(self):
        """All docs stale → staleness_rate=1.0, threshold_exceeded=True."""
        docs = [make_doc("pricing", 90, 84) for _ in range(3)]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = domain_report("pricing", docs, config, NOW)
        assert report.staleness_rate == 1.0
        assert report.threshold_exceeded is True
        assert report.stale_docs == 3

    def test_no_stale_docs(self):
        """All docs fresh → staleness_rate=0.0, threshold_exceeded=False."""
        docs = [make_doc("policy", 90, 2) for _ in range(3)]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = domain_report("policy", docs, config, NOW)
        assert report.staleness_rate == 0.0
        assert report.threshold_exceeded is False

    def test_partial_staleness(self):
        """One of three docs stale → staleness_rate≈0.33."""
        docs = [
            make_doc("pricing", 90, 84),   # stale
            make_doc("pricing", 90, 2),    # fresh
            make_doc("pricing", 90, 2),    # fresh
        ]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = domain_report("pricing", docs, config, NOW)
        assert abs(report.staleness_rate - 1/3) < 0.01

    def test_threshold_not_exceeded_below_alert_rate(self):
        """Staleness rate below alert_on_staleness_rate → not exceeded."""
        docs = [
            make_doc("p", 90, 84),    # stale
            make_doc("p", 90, 2),
            make_doc("p", 90, 2),
            make_doc("p", 90, 2),
            make_doc("p", 90, 2),
            make_doc("p", 90, 2),
            make_doc("p", 90, 2),
            make_doc("p", 90, 2),
            make_doc("p", 90, 2),
            make_doc("p", 90, 2),
        ]
        config = DomainFreshnessConfig(24, 0.2, 0.5)
        report = domain_report("p", docs, config, NOW)
        assert report.threshold_exceeded is False

    def test_report_contains_correct_fields(self):
        docs = [make_doc("pricing", 90, 84)]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = domain_report("pricing", docs, config, NOW)
        assert isinstance(report, DomainFreshnessReport)
        assert report.domain == "pricing"
        assert report.total_docs == 1


# ── Exercise 3 ────────────────────────────────────────────────────────────────

class TestExercise3:

    @pytest.fixture(scope="class")
    def result(self):
        return run_monitor(
            SAMPLE_DOCUMENTS, SAMPLE_CONFIGS, SAMPLE_WEIGHTS, now=SAMPLE_NOW
        )

    def test_returns_freshness_monitor_result(self, result):
        assert isinstance(result, FreshnessMonitorResult)

    def test_reports_for_both_domains(self, result):
        assert "pricing" in result.domain_reports
        assert "policy" in result.domain_reports

    def test_pricing_threshold_exceeded(self, result):
        assert result.domain_reports["pricing"].threshold_exceeded is True

    def test_policy_threshold_not_exceeded(self, result):
        assert result.domain_reports["policy"].threshold_exceeded is False

    def test_pricing_suppressed(self, result):
        """Pricing staleness >50% → domain should be suppressed."""
        assert "pricing" in result.suppressed_domains

    def test_policy_not_suppressed(self, result):
        assert "policy" not in result.suppressed_domains

    def test_alerts_non_empty(self, result):
        assert len(result.alerts) > 0

    def test_freshness_score_between_zero_and_one(self, result):
        assert 0.0 <= result.index_freshness_score <= 1.0

    def test_freshness_score_weighted(self, result):
        """With pricing weight=3, policy weight=1, score should be >0.4."""
        assert result.index_freshness_score > 0.4

    def test_default_config_applied_for_unknown_domain(self):
        """Unknown domain falls back to default 24h threshold."""
        docs = [make_doc("unknown", 30, 30)]
        result = run_monitor(docs, {}, now=NOW)
        assert "unknown" in result.domain_reports


# ── Exercise 4 ────────────────────────────────────────────────────────────────

class TestExercise4:

    @pytest.fixture(scope="class")
    def record(self):
        result = run_monitor(
            SAMPLE_DOCUMENTS, SAMPLE_CONFIGS, SAMPLE_WEIGHTS, now=SAMPLE_NOW
        )
        return to_run_record(result)

    def test_required_top_level_keys(self, record):
        assert "freshness_computed_at" in record
        assert "index_freshness_score" in record
        assert "alerts" in record
        assert "suppressed_domains" in record
        assert "domain_reports" in record

    def test_score_is_rounded(self, record):
        score = record["index_freshness_score"]
        assert score == round(score, 4)

    def test_domain_report_keys(self, record):
        pricing = record["domain_reports"]["pricing"]
        for key in [
            "total_docs", "stale_docs", "staleness_rate",
            "mean_staleness_hours", "ingestion_lag_hours", "threshold_exceeded"
        ]:
            assert key in pricing

    def test_serialisable_to_json(self, record):
        """The run record must be JSON-serialisable."""
        json.dumps(record)   # raises if not serialisable

    def test_timestamp_is_iso_format(self, record):
        """Timestamp must be parseable ISO format."""
        datetime.fromisoformat(record["freshness_computed_at"])


import json


# ── Exercise 5 ────────────────────────────────────────────────────────────────

class TestExercise5:

    def _make_record(self, pricing_staleness: float, pricing_exceeded: bool,
                     policy_staleness: float, policy_exceeded: bool) -> dict:
        return {
            "freshness": {
                "domain_reports": {
                    "pricing": {
                        "staleness_rate": pricing_staleness,
                        "threshold_exceeded": pricing_exceeded,
                    },
                    "policy": {
                        "staleness_rate": policy_staleness,
                        "threshold_exceeded": policy_exceeded,
                    },
                }
            }
        }

    def test_degraded_domain_detected(self):
        a = self._make_record(0.1, False, 0.0, False)
        b = self._make_record(0.8, True,  0.0, False)
        result = diff_freshness(a, b)
        assert any("pricing" in d for d in result["degraded"])

    def test_improved_domain_detected(self):
        a = self._make_record(0.8, True,  0.0, False)
        b = self._make_record(0.1, False, 0.0, False)
        result = diff_freshness(a, b)
        assert any("pricing" in d for d in result["improved"])

    def test_new_alert_detected(self):
        a = self._make_record(0.05, False, 0.0, False)
        b = self._make_record(0.8,  True,  0.0, False)
        result = diff_freshness(a, b)
        assert any("pricing" in d for d in result["new_alerts"])

    def test_no_change_produces_empty_lists(self):
        a = self._make_record(0.1, False, 0.0, False)
        b = self._make_record(0.1, False, 0.0, False)
        result = diff_freshness(a, b)
        assert result["degraded"] == []
        assert result["improved"] == []
        assert result["new_alerts"] == []

    def test_result_has_correct_keys(self):
        a = self._make_record(0.1, False, 0.0, False)
        b = self._make_record(0.1, False, 0.0, False)
        result = diff_freshness(a, b)
        assert "degraded" in result
        assert "improved" in result
        assert "new_alerts" in result