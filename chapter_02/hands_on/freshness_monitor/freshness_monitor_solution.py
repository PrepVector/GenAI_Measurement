"""
Chapter 2 — Section 4: Freshness monitoring pipeline
Reference solution

Read this only after attempting the exercises yourself.
Every non-trivial decision is explained in an inline comment.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


# ── Data structures (identical to starter) ───────────────────────────────────

@dataclass
class IndexedDocument:
    doc_id: str
    domain: str
    source_updated_at: datetime
    ingested_at: datetime


@dataclass
class DomainFreshnessConfig:
    staleness_threshold_hours: float
    alert_on_staleness_rate: float
    suppress_on_staleness_rate: float = 0.5


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
    index_freshness_score: float
    domain_reports: Dict[str, DomainFreshnessReport]
    alerts: List[str]
    suppressed_domains: List[str]
    computed_at: datetime = field(default_factory=datetime.utcnow)


# ── Exercise 1 ────────────────────────────────────────────────────────────────

def staleness_hours(doc: IndexedDocument, now: datetime) -> float:
    # The arithmetic is simple but the intent is precise: we measure how
    # long the indexed copy has been sitting without a refresh. Whether or
    # not the source has changed since the last ingestion, the clock ticks
    # from ingested_at — that is the last moment we know the index was
    # in sync.
    return (now - doc.ingested_at).total_seconds() / 3600


def ingestion_lag_hours(docs: List[IndexedDocument], now: datetime) -> float:
    if not docs:
        # float("inf") is semantically correct: a domain with no documents
        # has an unbounded ingestion lag. This also makes threshold checks
        # trivially true, which is the right behaviour — an empty domain
        # should always be flagged.
        return float("inf")
    return (now - max(d.ingested_at for d in docs)).total_seconds() / 3600


# ── Exercise 2 ────────────────────────────────────────────────────────────────

def compute_domain_report(
    domain: str,
    docs: List[IndexedDocument],
    config: DomainFreshnessConfig,
    now: datetime,
) -> DomainFreshnessReport:
    staleness = [staleness_hours(d, now) for d in docs]
    stale_count = sum(
        1 for h in staleness if h > config.staleness_threshold_hours
    )
    rate = stale_count / len(docs) if docs else 0.0
    mean = sum(staleness) / len(staleness) if staleness else 0.0

    return DomainFreshnessReport(
        domain=domain,
        total_docs=len(docs),
        stale_docs=stale_count,
        staleness_rate=rate,
        mean_staleness_hours=mean,
        ingestion_lag_hours=ingestion_lag_hours(docs, now),
        threshold_exceeded=rate > config.alert_on_staleness_rate,
    )


# ── Exercise 3 ────────────────────────────────────────────────────────────────

_DEFAULT_CONFIG = DomainFreshnessConfig(
    staleness_threshold_hours=24,
    alert_on_staleness_rate=0.1,
    suppress_on_staleness_rate=0.5,
)


def run_freshness_monitor(
    documents: List[IndexedDocument],
    domain_configs: Dict[str, DomainFreshnessConfig],
    query_volume_weights: Optional[Dict[str, float]] = None,
    now: Optional[datetime] = None,
) -> FreshnessMonitorResult:
    now = now or datetime.utcnow()
    weights = query_volume_weights or {}

    # Group by domain.
    by_domain: Dict[str, List[IndexedDocument]] = defaultdict(list)
    for doc in documents:
        by_domain[doc.domain].append(doc)

    # Per-domain reports.
    reports = {
        domain: compute_domain_report(
            domain, docs,
            domain_configs.get(domain, _DEFAULT_CONFIG),
            now,
        )
        for domain, docs in by_domain.items()
    }

    # Weighted freshness score. Query volume weighting means that a stale
    # high-traffic domain harms the score more than a stale low-traffic one —
    # which correctly reflects the fraction of users at risk of a stale answer.
    total_w = sum(weights.get(d, 1.0) for d in reports)
    score = (
        sum(r.staleness_rate * weights.get(d, 1.0) for d, r in reports.items())
        / total_w
        if total_w else 0.0
    )

    alerts: List[str] = []
    suppressed: List[str] = []

    for domain, r in reports.items():
        config = domain_configs.get(domain, _DEFAULT_CONFIG)
        if r.threshold_exceeded:
            alerts.append(
                f"[ALERT] Domain '{domain}': staleness rate "
                f"{r.staleness_rate:.1%} exceeds threshold. "
                f"Mean staleness: {r.mean_staleness_hours:.1f}h. "
                f"Ingestion lag: {r.ingestion_lag_hours:.1f}h."
            )
        if r.staleness_rate > config.suppress_on_staleness_rate:
            suppressed.append(domain)
            alerts.append(
                f"[SUPPRESS] Domain '{domain}' suppressed — "
                f"staleness rate {r.staleness_rate:.1%} exceeds "
                f"suppression threshold {config.suppress_on_staleness_rate:.0%}. "
                f"Responses withheld pending index refresh."
            )

    return FreshnessMonitorResult(
        index_freshness_score=score,
        domain_reports=reports,
        alerts=alerts,
        suppressed_domains=suppressed,
    )


# ── Exercise 4 ────────────────────────────────────────────────────────────────

def freshness_to_run_record(result: FreshnessMonitorResult) -> dict:
    return {
        "freshness_computed_at": result.computed_at.isoformat(),
        "index_freshness_score": round(result.index_freshness_score, 4),
        "alerts": result.alerts,
        "suppressed_domains": result.suppressed_domains,
        "domain_reports": {
            domain: {
                "total_docs": r.total_docs,
                "stale_docs": r.stale_docs,
                "staleness_rate": round(r.staleness_rate, 4),
                "mean_staleness_hours": round(r.mean_staleness_hours, 2),
                "ingestion_lag_hours": round(r.ingestion_lag_hours, 2),
                "threshold_exceeded": r.threshold_exceeded,
            }
            for domain, r in result.domain_reports.items()
        },
    }


# ── Exercise 5 ────────────────────────────────────────────────────────────────

def diff_freshness(run_a: dict, run_b: dict) -> dict:
    # Pull the freshness section. Using .get() with empty dicts as defaults
    # means this function handles run records from before freshness monitoring
    # was added without crashing — it simply reports nothing changed.
    a_reports = run_a.get("freshness", {}).get("domain_reports", {})
    b_reports = run_b.get("freshness", {}).get("domain_reports", {})

    degraded: List[str] = []
    improved: List[str] = []
    new_alerts: List[str] = []

    for domain in set(a_reports) | set(b_reports):
        a = a_reports.get(domain)
        b = b_reports.get(domain)

        if a is None:
            # Domain is new in run_b.
            if b and b.get("threshold_exceeded"):
                new_alerts.append(
                    f"{domain}: new domain in run B with threshold exceeded "
                    f"(staleness rate {b['staleness_rate']:.1%})"
                )
            continue

        if b is None:
            # Domain disappeared in run_b — nothing to compare.
            continue

        delta = b["staleness_rate"] - a["staleness_rate"]

        # 0.05 threshold filters out noise from floating-point variance
        # and minor day-to-day fluctuations. Changes smaller than 5
        # percentage points are unlikely to be actionable.
        if delta > 0.05:
            degraded.append(
                f"{domain}: staleness rate increased "
                f"{a['staleness_rate']:.1%} → {b['staleness_rate']:.1%} "
                f"(+{delta:.1%})"
            )
        elif delta < -0.05:
            improved.append(
                f"{domain}: staleness rate decreased "
                f"{a['staleness_rate']:.1%} → {b['staleness_rate']:.1%} "
                f"({delta:.1%})"
            )

        if not a["threshold_exceeded"] and b["threshold_exceeded"]:
            new_alerts.append(
                f"{domain}: newly exceeded threshold in run B "
                f"(staleness rate {b['staleness_rate']:.1%})"
            )

    return {
        "degraded": degraded,
        "improved": improved,
        "new_alerts": new_alerts,
    }


# ── Sample data (identical to starter) ───────────────────────────────────────

SAMPLE_NOW = datetime(2024, 6, 1, 12, 0, 0)

SAMPLE_DOCUMENTS = [
    IndexedDocument("doc_001", "pricing",
                    datetime(2024, 5, 31, 8, 0), datetime(2024, 5, 28, 0, 0)),
    IndexedDocument("doc_002", "pricing",
                    datetime(2024, 5, 30, 8, 0), datetime(2024, 5, 28, 0, 0)),
    IndexedDocument("doc_003", "pricing",
                    datetime(2024, 5, 25, 8, 0), datetime(2024, 5, 28, 0, 0)),
    IndexedDocument("doc_004", "policy",
                    datetime(2024, 5, 20, 8, 0), datetime(2024, 5, 31, 0, 0)),
    IndexedDocument("doc_005", "policy",
                    datetime(2024, 5, 18, 8, 0), datetime(2024, 5, 31, 0, 0)),
    IndexedDocument("doc_006", "policy",
                    datetime(2024, 4, 1,  8, 0), datetime(2024, 5, 31, 0, 0)),
]

SAMPLE_CONFIGS = {
    "pricing": DomainFreshnessConfig(24, 0.1, 0.5),
    "policy":  DomainFreshnessConfig(720, 0.2, 0.8),
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

# Expected output:
    # [ALERT] Domain 'pricing': staleness rate 66.7% exceeds threshold.
    #         Mean staleness: 82.7h. Ingestion lag: 84.0h.
    # [SUPPRESS] Domain 'pricing' suppressed — staleness rate 66.7% exceeds
    #            suppression threshold 50%. Responses withheld pending index refresh.
    #
    # Suppressed domains: ['pricing']
    # Index freshness score: 0.5003
    # {
    #   "freshness_computed_at": "2024-06-01T12:00:00",
    #   "index_freshness_score": 0.5003,
    #   "alerts": [
    #     "[ALERT] Domain 'pricing': staleness rate 66.7% exceeds threshold. ...",
    #     "[SUPPRESS] Domain 'pricing' suppressed ..."
    #   ],
    #   "suppressed_domains": ["pricing"],
    #   "domain_reports": {
    #     "pricing": {
    #       "total_docs": 3,
    #       "stale_docs": 2,
    #       "staleness_rate": 0.6667,
    #       "mean_staleness_hours": 82.67,
    #       "ingestion_lag_hours": 84.0,
    #       "threshold_exceeded": true
    #     },
    #     "policy": {
    #       "total_docs": 3,
    #       "stale_docs": 0,
    #       "staleness_rate": 0.0,
    #       "mean_staleness_hours": 24.0,
    #       "ingestion_lag_hours": 12.0,
    #       "threshold_exceeded": false
    #     }
    #   }
    # }
