"""
Chapter 2 — Section 4: Freshness monitoring pipeline
Starter file

Work through the five exercises in the book to implement each function
marked with TODO. Run pytest tests/ to validate your implementation.

No Anthropic API key required — standard library only.
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class IndexedDocument:
    doc_id: str
    domain: str
    source_updated_at: datetime    # when the source was last modified
    ingested_at: datetime          # when the document was last indexed


@dataclass
class DomainFreshnessConfig:
    """Per-domain thresholds. These are product decisions, not technical ones.
    Agree on them with domain owners before running the monitor."""
    staleness_threshold_hours: float   # docs older than this are stale
    alert_on_staleness_rate: float     # alert if this fraction is stale
    suppress_on_staleness_rate: float = 0.5  # suppress domain at this fraction


@dataclass
class DomainFreshnessReport:
    domain: str
    total_docs: int
    stale_docs: int
    staleness_rate: float
    mean_staleness_hours: float
    ingestion_lag_hours: float
    threshold_exceeded: bool
    computed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FreshnessMonitorResult:
    index_freshness_score: float       # weighted average staleness rate (0.0–1.0)
    domain_reports: Dict[str, DomainFreshnessReport]
    alerts: List[str]
    suppressed_domains: List[str]
    computed_at: datetime = field(default_factory=datetime.utcnow)


# ── Exercise 1: Staleness computation ────────────────────────────────────────

def staleness_hours(doc: IndexedDocument, now: datetime) -> float:
    """
    Compute the staleness of a single document in hours.

    TODO (Exercise 1):
      Staleness is the time since the document was last in sync with
      its source. Return (now - doc.ingested_at) in hours.

      Note: even if source_updated_at <= ingested_at (source unchanged),
      we still measure staleness from ingested_at — this captures how
      long it has been since the document was refreshed regardless of
      whether the source changed.
    """
    raise NotImplementedError("Implement staleness_hours() — Exercise 1")


def ingestion_lag_hours(docs: List[IndexedDocument], now: datetime) -> float:
    """
    Time in hours since the most recent ingestion run for this domain.

    TODO (Exercise 1):
      Return (now - max(ingested_at)) in hours across all docs.
      If docs is empty, return float("inf") — an empty domain has
      never been ingested.
    """
    raise NotImplementedError("Implement ingestion_lag_hours() — Exercise 1")


# ── Exercise 2: Per-domain report ────────────────────────────────────────────

def compute_domain_report(
    domain: str,
    docs: List[IndexedDocument],
    config: DomainFreshnessConfig,
    now: datetime,
) -> DomainFreshnessReport:
    """
    Compute the freshness report for a single domain.

    TODO (Exercise 2):
      1. Compute staleness_hours() for every document.
      2. Count docs whose staleness exceeds config.staleness_threshold_hours.
      3. Compute staleness_rate = stale_docs / total_docs.
      4. Compute mean_staleness_hours across all documents.
      5. Compute ingestion_lag_hours() for this domain.
      6. Set threshold_exceeded = staleness_rate > config.alert_on_staleness_rate.
      7. Return a DomainFreshnessReport.
    """
    raise NotImplementedError("Implement compute_domain_report() — Exercise 2")


# ── Exercise 3: Full monitor run ─────────────────────────────────────────────

def run_freshness_monitor(
    documents: List[IndexedDocument],
    domain_configs: Dict[str, DomainFreshnessConfig],
    query_volume_weights: Optional[Dict[str, float]] = None,
    now: Optional[datetime] = None,
) -> FreshnessMonitorResult:
    """
    Run the freshness monitor across all domains.

    TODO (Exercise 3):
      1. Group documents by domain using a defaultdict.
      2. For each domain call compute_domain_report() using its config.
         If a domain has no entry in domain_configs, use these defaults:
           staleness_threshold_hours=24
           alert_on_staleness_rate=0.1
           suppress_on_staleness_rate=0.5
      3. Compute index_freshness_score: weighted average of staleness rates
         across domains. Weight each domain by query_volume_weights.get(domain, 1.0).
         Formula: sum(rate * weight) / sum(weight)
      4. Build alerts: one string per domain where threshold_exceeded is True.
         Format: "[ALERT] Domain '{domain}': staleness rate {rate:.1%} exceeds
                  threshold. Mean staleness: {mean:.1f}h. Ingestion lag: {lag:.1f}h."
      5. Build suppressed_domains: domains where staleness_rate exceeds
         config.suppress_on_staleness_rate. Add a [SUPPRESS] alert for each.
      6. Return a FreshnessMonitorResult.
    """
    raise NotImplementedError("Implement run_freshness_monitor() — Exercise 3")


# ── Exercise 4: Serialisation ────────────────────────────────────────────────

def freshness_to_run_record(result: FreshnessMonitorResult) -> dict:
    """
    Serialise the freshness result for inclusion in the eval run record.

    TODO (Exercise 4):
      Return a dict with these keys:
        "freshness_computed_at": result.computed_at.isoformat()
        "index_freshness_score": float rounded to 4 decimal places
        "alerts": list of alert strings
        "suppressed_domains": list of suppressed domain names
        "domain_reports": {
            domain: {
                "total_docs": int,
                "stale_docs": int,
                "staleness_rate": float (4dp),
                "mean_staleness_hours": float (2dp),
                "ingestion_lag_hours": float (2dp),
                "threshold_exceeded": bool,
            }
        }
    """
    raise NotImplementedError("Implement freshness_to_run_record() — Exercise 4")


# ── Exercise 5: Diff ─────────────────────────────────────────────────────────

def diff_freshness(run_a: dict, run_b: dict) -> dict:
    """
    Compare the freshness profiles of two eval run records.

    TODO (Exercise 5):
      Each run record contains a "freshness" key produced by
      freshness_to_run_record(). Compare the domain_reports in each.

      Return a dict with three keys:
        "degraded": list of strings — domains where staleness_rate
                    increased by more than 0.05 between run_a and run_b.
        "improved": list of strings — domains where staleness_rate
                    decreased by more than 0.05.
        "new_alerts": list of strings — domains that newly exceeded
                      their threshold in run_b (threshold_exceeded was
                      False in run_a, True in run_b).

      Handle missing domains gracefully — a domain that appears only
      in run_b should be noted in new_alerts if its threshold is exceeded.
    """
    raise NotImplementedError("Implement diff_freshness() — Exercise 5")


# ── Sample data ───────────────────────────────────────────────────────────────

SAMPLE_NOW = datetime(2024, 6, 1, 12, 0, 0)

SAMPLE_DOCUMENTS = [
    # Pricing domain — source updated recently but not yet re-ingested
    IndexedDocument("doc_001", "pricing",
                    datetime(2024, 5, 31, 8, 0), datetime(2024, 5, 28, 0, 0)),
    IndexedDocument("doc_002", "pricing",
                    datetime(2024, 5, 30, 8, 0), datetime(2024, 5, 28, 0, 0)),
    IndexedDocument("doc_003", "pricing",
                    datetime(2024, 5, 25, 8, 0), datetime(2024, 5, 28, 0, 0)),
    # Policy domain — recently ingested, mostly fresh
    IndexedDocument("doc_004", "policy",
                    datetime(2024, 5, 20, 8, 0), datetime(2024, 5, 31, 0, 0)),
    IndexedDocument("doc_005", "policy",
                    datetime(2024, 5, 18, 8, 0), datetime(2024, 5, 31, 0, 0)),
    IndexedDocument("doc_006", "policy",
                    datetime(2024, 4, 1,  8, 0), datetime(2024, 5, 31, 0, 0)),
]

SAMPLE_CONFIGS = {
    "pricing": DomainFreshnessConfig(
        staleness_threshold_hours=24,     # pricing must be refreshed daily
        alert_on_staleness_rate=0.1,
        suppress_on_staleness_rate=0.5,
    ),
    "policy": DomainFreshnessConfig(
        staleness_threshold_hours=720,    # 30 days for policy documents
        alert_on_staleness_rate=0.2,
        suppress_on_staleness_rate=0.8,
    ),
}

SAMPLE_WEIGHTS = {"pricing": 3.0, "policy": 1.0}


if __name__ == "__main__":
    result = run_freshness_monitor(
        SAMPLE_DOCUMENTS, SAMPLE_CONFIGS, SAMPLE_WEIGHTS, now=SAMPLE_NOW
    )
    for alert in result.alerts:
        print(alert)
    print(f"\nSuppressed domains: {result.suppressed_domains}")
    print(f"Index freshness score: {result.index_freshness_score:.4f}")
    print(json.dumps(freshness_to_run_record(result), indent=2))