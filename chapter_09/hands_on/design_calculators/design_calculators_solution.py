"""
Chapter 9 — Sections 2-4: Design calculators
Reference solution (Exercises 4-6)

Read this only after attempting the exercises yourself.
Every non-trivial decision is explained in an inline comment.

No Anthropic API key required — this exercise uses only the Python
standard library.
"""

import math
from typing import Sequence, Tuple


# ── Table 9.4 inputs (simulated) ──────────────────────────────────────────────

QUERY_TYPES = ("simple lookup", "multi-hop", "code", "general")
TRAFFIC_MIX = (0.40, 0.30, 0.15, 0.15)

# Completion rate on each query type under two routing policies:
# the best model per type (Models A, B, C, D) and the same policy except
# that general queries go to Model B (68%) instead of Model D (72%).
BEST_PER_TYPE = (0.74, 0.80, 0.76, 0.72)
GENERAL_TO_B = (0.74, 0.80, 0.76, 0.68)


# ── Exercise 4: Routing arithmetic ────────────────────────────────────────────

def policy_completion_rate(mix: Sequence[float], rates: Sequence[float]) -> float:
    # A routing policy's completion rate is the traffic-weighted average of
    # the rate each query type achieves under the model the policy picks for it.
    return sum(m * r for m, r in zip(mix, rates))


# ── Exercise 5: Sizing a preference test ──────────────────────────────────────

def decisive_judgments(win_rate: float, z_alpha: float = 1.96,
                       z_power: float = 0.8416) -> float:
    # Sign test against 50%. The defaults are the normal quantiles for
    # alpha = 0.05 (two-sided) and 80% power. Under the null the standard
    # deviation of a decisive verdict is 0.5; under the alternative it is
    # sqrt(q(1 - q)), which is why the two terms differ.
    q = win_rate
    return ((z_alpha * 0.5 + z_power * math.sqrt(q * (1 - q))) / (q - 0.5)) ** 2


# ── Exercise 6: Interleaving versus an A/B test ───────────────────────────────

def interleaving_query_fraction(variance_ratio: float) -> Tuple[float, float]:
    # variance_ratio = between-query variance / within-query variance.
    # Interleaving needs 1 / (1 + ratio) of the queries in ONE A/B arm. The A/B
    # test has two arms, so measured against its total the fraction is halved.
    # This is the ideal case with no ties; Section 3.4's simulation gains less.
    per_arm = 1 / (1 + variance_ratio)
    return per_arm, per_arm / 2


if __name__ == "__main__":
    print("=== Exercise 4: routing arithmetic from Table 9.4 ===")
    oracle = policy_completion_rate(TRAFFIC_MIX, BEST_PER_TYPE)
    general_to_b = policy_completion_rate(TRAFFIC_MIX, GENERAL_TO_B)
    print(f"oracle routing:           {oracle:.1%}")
    print(f"general queries -> B:     {general_to_b:.1%}  "
          f"({(oracle - general_to_b) * 100:.1f} points lower)")

    print("\n=== Exercise 5: decisive judgments for a 57% win rate ===")
    print(f"decisive judgments needed: {decisive_judgments(0.57):,.0f}")

    print("\n=== Exercise 6: interleaving sample size from the variance ratio ===")
    per_arm, of_total = interleaving_query_fraction(4.0)
    print(f"fraction of one A/B arm's queries: {per_arm:.2f}")
    print(f"fraction of the A/B test's total:  {of_total:.2f}")


# Expected output:
#
# === Exercise 4: routing arithmetic from Table 9.4 ===
# oracle routing:           75.8%
# general queries -> B:     75.2%  (0.6 points lower)
#
# === Exercise 5: decisive judgments for a 57% win rate ===
# decisive judgments needed: 398
#
# === Exercise 6: interleaving sample size from the variance ratio ===
# fraction of one A/B arm's queries: 0.20
# fraction of the A/B test's total:  0.10
