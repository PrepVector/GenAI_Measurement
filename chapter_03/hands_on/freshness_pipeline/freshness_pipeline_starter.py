"""
Chapter 3 — Section 2: Freshness monitoring pipeline
Starter file

Work through the five exercises in the book to implement
each function marked with TODO. Run pytest tests/ to validate
your implementation.

No Anthropic API key required — this exercise uses only the
Python standard library.
"""

import json
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
    staleness_threshold_hours: float   # max acceptable staleness in hours
    alert_on_staleness_rate: float     # alert if this fraction of docs is stale
    suppress_on_staleness_rate: float = 0.5  # suppress domain if this fraction stale


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


# ── Exercise 1: Core staleness computation ────────────────────────────────────

def staleness_hours(doc: IndexedDocument, now: datetime) -> float:
    """
    Compute the staleness of a single document in hours.

    TODO (Exercise 1):
      Staleness is defined as the time since the document was last
      in sync with its source:
        - If source_updated_at > ingested_at: the source has been
          modified since the last ingestion. Staleness = time since
          ingested_at (how long the index has been out of date).
        - Otherwise: staleness = time since ingested_at (how long
          since the document was refreshed).

      Return the staleness as a float number of hours.
    """
    raise NotImplementedError("Implement staleness_hours() — Exercise 1")


def ingestion_lag_hours(docs: List[IndexedDocument], now: datetime) -> float:
    """
    Compute the ingestion lag for a domain in hours.

    TODO (Exercise 1):
      Ingestion lag = time since the most recent ingestion run
      for this domain (i.e. the maximum ingested_at across all docs).
      If docs is empty, return float("inf").
    """
    raise NotImplementedError("Implement ingestion_lag_hours() — Exercise 1")


# ── Exercise 2: Per-domain report ─────────────────────────────────────────────

def domain_report(
    domain: str,
    docs: List[IndexedDocument],
    config: DomainFreshnessConfig,
    now: datetime,
) -> DomainFreshnessReport:
    """
    Compute the freshness report for a single domain.

    TODO (Exercise 2):
      1. Compute staleness_hours() for every document in docs.
      2. Count stale_docs: documents whose staleness exceeds
         config.staleness_threshold_hours.
      3. Compute staleness_rate = stale_docs / total_docs.
      4. Compute mean_staleness_hours across all documents.
      5. Compute ingestion_lag_hours() for the domain.
      6. Set threshold_exceeded = staleness_rate > config.alert_on_staleness_rate.
      7. Return a DomainFreshnessReport.
    """
    raise NotImplementedError("Implement domain_report() — Exercise 2")


# ── Exercise 3: Monitor run ───────────────────────────────────────────────────

def run_monitor(
    documents: List[IndexedDocument],
    domain_configs: Dict[str, DomainFreshnessConfig],
    query_volume_weights: Optional[Dict[str, float]] = None,
    now: Optional[datetime] = None,
) -> FreshnessMonitorResult:
    """
    Run the freshness monitor across all domains.

    TODO (Exercise 3):
      1. Group documents by domain.
      2. For each domain, call domain_report() using the config from
         domain_configs. If a domain has no config entry, use defaults:
         staleness_threshold_hours=24, alert_on_staleness_rate=0.1,
         suppress_on_staleness_rate=0.5.
      3. Compute the index_freshness_score: a weighted average of
         staleness rates across all domains, weighted by
         query_volume_weights (default weight = 1.0 per domain).
      4. Build the alerts list — one alert string per domain where
         threshold_exceeded is True.
      5. Build suppressed_domains — domains where staleness_rate
         exceeds config.suppress_on_staleness_rate.
      6. Return a FreshnessMonitorResult.
    """
    raise NotImplementedError("Implement run_monitor() — Exercise 3")


# ── Exercise 4: Serialisation ─────────────────────────────────────────────────

def to_run_record(result: FreshnessMonitorResult) -> dict:
    """
    Serialise the freshness result for the Chapter 2 eval run record.

    TODO (Exercise 4):
      Return a dict with:
        "freshness_computed_at": ISO format timestamp string
        "index_freshness_score": float rounded to 4 decimal places
        "alerts": list of alert strings
        "suppressed_domains": list of suppressed domain names
        "domain_reports": dict of domain → {
            "total_docs": int,
            "stale_docs": int,
            "staleness_rate": float (4dp),
            "mean_staleness_hours": float (2dp),
            "ingestion_lag_hours": float (2dp),
            "threshold_exceeded": bool,
        }
    """
    raise NotImplementedError("Implement to_run_record() — Exercise 4")


# ── Exercise 5: Diff ──────────────────────────────────────────────────────────

def diff_freshness(
    run_a: dict,
    run_b: dict,
) -> dict:
    """
    Compare the freshness profiles of two eval run records.

    TODO (Exercise 5):
      Compare the "freshness" key in each run record.
      Return a dict with three keys:
        "degraded": list of strings describing domains where
                    staleness_rate increased by more than 0.05
        "improved": list of strings describing domains where
                    staleness_rate decreased by more than 0.05
        "new_alerts": list of strings describing domains that
                      newly exceeded their threshold in run_b
                      (threshold_exceeded was False in run_a,
                      True in run_b)
    """
    raise NotImplementedError("Implement diff_freshness() — Exercise 5")


# ── Sample data ───────────────────────────────────────────────────────────────

SAMPLE_NOW = datetime(2024, 6, 1, 12, 0, 0)

SAMPLE_DOCUMENTS = [
    # Pricing domain — source updated, not re-ingested (stale)
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
        staleness_threshold_hours=24,
        alert_on_staleness_rate=0.1,
        suppress_on_staleness_rate=0.5,
    ),
    "policy": DomainFreshnessConfig(
        staleness_threshold_hours=720,
        alert_on_staleness_rate=0.2,
        suppress_on_staleness_rate=0.8,
    ),
}

SAMPLE_WEIGHTS = {"pricing": 3.0, "policy": 1.0}


if __name__ == "__main__":
    result = run_monitor(
        SAMPLE_DOCUMENTS, SAMPLE_CONFIGS, SAMPLE_WEIGHTS, now=SAMPLE_NOW
    )
    for alert in result.alerts:
        print(alert)
    print(f"\nSuppressed domains: {result.suppressed_domains}")
    print(f"Index freshness score: {result.index_freshness_score:.4f}")
    print(json.dumps(to_run_record(result), indent=2))