"""
Tests for Chapter 2 Section 4 — Freshness monitoring pipeline.

Run from the exercise folder:
    pytest tests/ -v

Tests are grouped by exercise:
    pytest tests/ -v -k "exercise_1"
"""

import json
import pytest
from datetime import datetime, timedelta
from freshness_monitor_starter import (
    staleness_hours,
    ingestion_lag_hours,
    compute_domain_report,
    run_freshness_monitor,
    freshness_to_run_record,
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

def make_doc(domain, source_hours_ago, ingested_hours_ago, doc_id=None):
    return IndexedDocument(
        doc_id=doc_id or f"{domain}_{ingested_hours_ago}",
        domain=domain,
        source_updated_at=NOW - timedelta(hours=source_hours_ago),
        ingested_at=NOW - timedelta(hours=ingested_hours_ago),
    )


def make_freshness_record(domain_data: dict) -> dict:
    """Build a minimal run record containing a freshness section."""
    return {
        "freshness": {
            "domain_reports": {
                domain: {
                    "staleness_rate": data["rate"],
                    "threshold_exceeded": data["exceeded"],
                }
                for domain, data in domain_data.items()
            }
        }
    }


# ── Exercise 1 ────────────────────────────────────────────────────────────────

class TestExercise1StalenessHours:

    def test_recently_ingested_doc_is_fresh(self):
        doc = make_doc("pricing", source_hours_ago=48, ingested_hours_ago=2)
        assert abs(staleness_hours(doc, NOW) - 2.0) < 0.01

    def test_stale_doc(self):
        doc = make_doc("pricing", source_hours_ago=100, ingested_hours_ago=84)
        assert abs(staleness_hours(doc, NOW) - 84.0) < 0.01

    def test_source_newer_than_ingestion(self):
        """Source updated after ingestion — staleness from ingested_at."""
        doc = make_doc("pricing", source_hours_ago=5, ingested_hours_ago=50)
        assert abs(staleness_hours(doc, NOW) - 50.0) < 0.01

    def test_just_ingested(self):
        doc = make_doc("pricing", source_hours_ago=10, ingested_hours_ago=0)
        assert staleness_hours(doc, NOW) < 0.01

    def test_returns_float(self):
        doc = make_doc("pricing", 48, 24)
        assert isinstance(staleness_hours(doc, NOW), float)


class TestExercise1IngestionLag:

    def test_single_doc(self):
        docs = [make_doc("pricing", 48, 12)]
        assert abs(ingestion_lag_hours(docs, NOW) - 12.0) < 0.01

    def test_picks_most_recent_ingestion(self):
        docs = [
            make_doc("pricing", 48, 84, "old"),
            make_doc("pricing", 48, 12, "new"),
        ]
        assert abs(ingestion_lag_hours(docs, NOW) - 12.0) < 0.01

    def test_empty_domain_returns_infinity(self):
        assert ingestion_lag_hours([], NOW) == float("inf")

    def test_returns_float(self):
        docs = [make_doc("pricing", 48, 24)]
        assert isinstance(ingestion_lag_hours(docs, NOW), float)


# ── Exercise 2 ────────────────────────────────────────────────────────────────

class TestExercise2DomainReport:

    def test_all_stale(self):
        docs = [make_doc("pricing", 90, 84) for _ in range(3)]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = compute_domain_report("pricing", docs, config, NOW)
        assert report.staleness_rate == 1.0
        assert report.stale_docs == 3
        assert report.threshold_exceeded is True

    def test_all_fresh(self):
        docs = [make_doc("policy", 90, 2) for _ in range(3)]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = compute_domain_report("policy", docs, config, NOW)
        assert report.staleness_rate == 0.0
        assert report.threshold_exceeded is False

    def test_partial_staleness(self):
        docs = [
            make_doc("pricing", 90, 84, "a"),  # stale
            make_doc("pricing", 90, 2,  "b"),  # fresh
            make_doc("pricing", 90, 2,  "c"),  # fresh
        ]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = compute_domain_report("pricing", docs, config, NOW)
        assert abs(report.staleness_rate - 1/3) < 0.01

    def test_alert_rate_boundary(self):
        """Staleness rate exactly at alert threshold does not exceed it."""
        docs = [make_doc("p", 90, 84, "a"), make_doc("p", 90, 2, "b")]
        # staleness_rate = 0.5, alert_on = 0.5 → strictly greater required
        config = DomainFreshnessConfig(24, 0.5, 0.8)
        report = compute_domain_report("p", docs, config, NOW)
        assert report.threshold_exceeded is False

    def test_report_type(self):
        docs = [make_doc("pricing", 90, 84)]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = compute_domain_report("pricing", docs, config, NOW)
        assert isinstance(report, DomainFreshnessReport)

    def test_total_docs_correct(self):
        docs = [make_doc("p", 90, 2, str(i)) for i in range(5)]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = compute_domain_report("p", docs, config, NOW)
        assert report.total_docs == 5

    def test_mean_staleness_computed(self):
        docs = [
            make_doc("p", 90, 10, "a"),
            make_doc("p", 90, 30, "b"),
        ]
        config = DomainFreshnessConfig(24, 0.1, 0.5)
        report = compute_domain_report("p", docs, config, NOW)
        assert abs(report.mean_staleness_hours - 20.0) < 0.01


# ── Exercise 3 ────────────────────────────────────────────────────────────────

class TestExercise3MonitorRun:

    @pytest.fixture(scope="class")
    def result(self):
        return run_freshness_monitor(
            SAMPLE_DOCUMENTS, SAMPLE_CONFIGS, SAMPLE_WEIGHTS, now=SAMPLE_NOW
        )

    def test_returns_correct_type(self, result):
        assert isinstance(result, FreshnessMonitorResult)

    def test_both_domains_present(self, result):
        assert "pricing" in result.domain_reports
        assert "policy" in result.domain_reports

    def test_pricing_alert_raised(self, result):
        assert result.domain_reports["pricing"].threshold_exceeded is True
        assert any("[ALERT]" in a and "pricing" in a for a in result.alerts)

    def test_policy_no_alert(self, result):
        assert result.domain_reports["policy"].threshold_exceeded is False

    def test_pricing_suppressed(self, result):
        assert "pricing" in result.suppressed_domains
        assert any("[SUPPRESS]" in a and "pricing" in a for a in result.alerts)

    def test_policy_not_suppressed(self, result):
        assert "policy" not in result.suppressed_domains

    def test_score_between_zero_and_one(self, result):
        assert 0.0 <= result.index_freshness_score <= 1.0

    def test_score_reflects_weighting(self, result):
        """pricing (weight=3) is fully stale → score should be well above 0.4."""
        assert result.index_freshness_score > 0.4

    def test_default_config_for_unknown_domain(self):
        docs = [make_doc("unknown", 30, 30)]
        result = run_freshness_monitor(docs, {}, now=NOW)
        assert "unknown" in result.domain_reports

    def test_no_documents_returns_empty(self):
        result = run_freshness_monitor([], {}, now=NOW)
        assert result.domain_reports == {}
        assert result.index_freshness_score == 0.0


# ── Exercise 4 ────────────────────────────────────────────────────────────────

class TestExercise4Serialisation:

    @pytest.fixture(scope="class")
    def record(self):
        result = run_freshness_monitor(
            SAMPLE_DOCUMENTS, SAMPLE_CONFIGS, SAMPLE_WEIGHTS, now=SAMPLE_NOW
        )
        return freshness_to_run_record(result)

    def test_top_level_keys(self, record):
        for key in [
            "freshness_computed_at", "index_freshness_score",
            "alerts", "suppressed_domains", "domain_reports"
        ]:
            assert key in record

    def test_score_is_rounded_to_4dp(self, record):
        score = record["index_freshness_score"]
        assert score == round(score, 4)

    def test_domain_report_keys(self, record):
        pricing = record["domain_reports"]["pricing"]
        for key in [
            "total_docs", "stale_docs", "staleness_rate",
            "mean_staleness_hours", "ingestion_lag_hours", "threshold_exceeded"
        ]:
            assert key in pricing, f"Missing key: {key}"

    def test_json_serialisable(self, record):
        dumped = json.dumps(record)
        assert len(dumped) > 0

    def test_timestamp_parseable(self, record):
        datetime.fromisoformat(record["freshness_computed_at"])

    def test_staleness_rate_rounded(self, record):
        rate = record["domain_reports"]["pricing"]["staleness_rate"]
        assert rate == round(rate, 4)


# ── Exercise 5 ────────────────────────────────────────────────────────────────

class TestExercise5Diff:

    def test_degraded_domain_detected(self):
        a = make_freshness_record({"pricing": {"rate": 0.1, "exceeded": False}})
        b = make_freshness_record({"pricing": {"rate": 0.8, "exceeded": True}})
        result = diff_freshness(a, b)
        assert any("pricing" in d for d in result["degraded"])

    def test_improved_domain_detected(self):
        a = make_freshness_record({"pricing": {"rate": 0.8, "exceeded": True}})
        b = make_freshness_record({"pricing": {"rate": 0.1, "exceeded": False}})
        result = diff_freshness(a, b)
        assert any("pricing" in d for d in result["improved"])

    def test_new_alert_detected(self):
        a = make_freshness_record({"pricing": {"rate": 0.05, "exceeded": False}})
        b = make_freshness_record({"pricing": {"rate": 0.8,  "exceeded": True}})
        result = diff_freshness(a, b)
        assert any("pricing" in d for d in result["new_alerts"])

    def test_no_change_produces_empty_lists(self):
        a = make_freshness_record({"pricing": {"rate": 0.1, "exceeded": False}})
        b = make_freshness_record({"pricing": {"rate": 0.1, "exceeded": False}})
        result = diff_freshness(a, b)
        assert result == {"degraded": [], "improved": [], "new_alerts": []}

    def test_small_delta_ignored(self):
        """Changes under 0.05 should not appear as degraded or improved."""
        a = make_freshness_record({"pricing": {"rate": 0.10, "exceeded": False}})
        b = make_freshness_record({"pricing": {"rate": 0.13, "exceeded": False}})
        result = diff_freshness(a, b)
        assert result["degraded"] == []
        assert result["improved"] == []

    def test_new_domain_in_run_b_with_exceeded_threshold(self):
        a = make_freshness_record({})
        b = make_freshness_record({"new_domain": {"rate": 0.9, "exceeded": True}})
        result = diff_freshness(a, b)
        assert any("new_domain" in d for d in result["new_alerts"])

    def test_result_has_correct_keys(self):
        result = diff_freshness({}, {})
        assert "degraded" in result
        assert "improved" in result
        assert "new_alerts" in result

    def test_multiple_domains_independently_assessed(self):
        a = make_freshness_record({
            "pricing": {"rate": 0.1,  "exceeded": False},
            "policy":  {"rate": 0.8,  "exceeded": True},
        })
        b = make_freshness_record({
            "pricing": {"rate": 0.8,  "exceeded": True},
            "policy":  {"rate": 0.05, "exceeded": False},
        })
        result = diff_freshness(a, b)
        assert any("pricing" in d for d in result["degraded"])
        assert any("policy"  in d for d in result["improved"])