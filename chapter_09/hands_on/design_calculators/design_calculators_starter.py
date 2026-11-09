"""
Chapter 9 — Sections 2-4: Design calculators
Starter file (Exercises 4-6)

Work through the three exercises in the book to implement each
function marked with TODO. Run pytest tests/ to validate your
implementation.

No Anthropic API key required — this exercise uses only the
Python standard library.
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
    """
    Return the completion rate of a routing policy.

    TODO (Exercise 4):
      mix[i] is the share of traffic that is query type i, and rates[i]
      is the completion rate query type i achieves under the model the
      policy picks for it. The policy's completion rate is the
      traffic-weighted average. Then compare BEST_PER_TYPE with
      GENERAL_TO_B: how much does sending general queries to Model B
      instead of Model D cost?
    """
    raise NotImplementedError("Implement policy_completion_rate() — Exercise 4")


# ── Exercise 5: Sizing a preference test ──────────────────────────────────────

def decisive_judgments(win_rate: float, z_alpha: float = 1.96,
                       z_power: float = 0.8416) -> float:
    """
    Return the number of decisive judgments needed to detect a true win
    rate of `win_rate` against 50% with a sign test.

    TODO (Exercise 5):
      Use the formula behind Table 9.8, with q = win_rate:

        n = ((z_alpha * 0.5 + z_power * sqrt(q * (1 - q))) / (q - 0.5)) ** 2

      The defaults are the normal quantiles for alpha = 0.05 (two-sided)
      and 80% power. Check your function against Table 9.8: 52% needs
      about 4,900, 55% about 780, 60% about 190 and 65% about 85.
      Ties do not count: divide by the share of decisive verdicts to
      get the number of judgments to collect.
    """
    raise NotImplementedError("Implement decisive_judgments() — Exercise 5")


# ── Exercise 6: Interleaving versus an A/B test ───────────────────────────────

def interleaving_query_fraction(variance_ratio: float) -> Tuple[float, float]:
    """
    Return (fraction of one A/B arm's queries, fraction of the A/B test's
    total) that interleaving needs for equal precision.

    TODO (Exercise 6):
      variance_ratio is between-query variance divided by within-query
      variance (Section 3.1). Interleaving needs 1 / (1 + variance_ratio)
      of the queries in one A/B arm. The A/B test has two arms, so
      measured against its total the fraction is half of that.
    """
    raise NotImplementedError("Implement interleaving_query_fraction() — Exercise 6")


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
