"""
Chapter 9 — Section 1: Thompson Sampling for model selection
Reference solution (Exercises 1-3)

Read this only after attempting the exercises yourself.
Every non-trivial decision is explained in an inline comment.

No Anthropic API key required — this exercise uses only NumPy.
All results are simulated for illustration, not measured on a real system.
"""

from dataclasses import dataclass
from typing import Dict, Sequence

import numpy as np


# ── Scenario (matches Section 1 of the chapter) ───────────────────────────────

MODEL_NAMES = "ABCDE"
TRUE_RATES = np.array([0.62, 0.71, 0.58, 0.66, 0.64])  # task completion, Models A-E
DAYS = 14
QUERIES_PER_DAY = 2000
DEFAULT_RUNS = 500


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class PolicyResult:
    cumulative_regret: np.ndarray   # mean cumulative regret after each day
    final_share: np.ndarray         # mean traffic share per model on the last day

    @property
    def total_regret(self) -> float:
        return float(self.cumulative_regret[-1])


# ── Provided simulator ────────────────────────────────────────────────────────

def thompson_choices(a: np.ndarray, b: np.ndarray, n_queries: int,
                     rng: np.random.Generator) -> np.ndarray:
    """Return the model chosen for each query by Thompson Sampling."""
    # One draw per model per query: each query is routed independently, so
    # models with wide posteriors win some draws and keep being explored.
    draws = rng.beta(a, b, size=(n_queries, len(a)))
    return draws.argmax(axis=1)


def run_policy(policy: str, floor: float = 0.0, rates: np.ndarray = TRUE_RATES,
               update_every: int = 1, runs: int = DEFAULT_RUNS,
               seed: int = 42) -> PolicyResult:
    """
    Simulate DAYS days of routing and average over `runs` repetitions.

    policy        "uniform" or "ts" (Thompson Sampling)
    floor         share of daily traffic reserved for a uniform split
                  (Thompson Sampling only)
    rates         true completion rate of each model (hidden from the policy)
    update_every  days between posterior updates (1 = daily, 7 = weekly)
    """
    rng = np.random.default_rng(seed)
    k, best = len(rates), rates.max()
    regret = np.zeros(DAYS)
    last_day_share = np.zeros(k)
    for _ in range(runs):
        a, b = np.ones(k), np.ones(k)               # Beta(1, 1): a flat prior
        pend_s, pend_f = np.zeros(k), np.zeros(k)   # outcomes waiting for an update
        cum = 0.0
        for day in range(DAYS):
            if policy == "uniform":
                n = rng.multinomial(QUERIES_PER_DAY, np.full(k, 1 / k))
            else:
                n = route_with_floor(a, b, QUERIES_PER_DAY, floor, rng)
            s = rng.binomial(n, rates)              # completions per model today
            # Outcomes are buffered and applied only on update days. This is the
            # whole mechanism behind delayed feedback: the policy keeps routing
            # on a posterior that does not yet include the buffered outcomes.
            pend_s += s
            pend_f += n - s
            if (day + 1) % update_every == 0:
                a += pend_s
                b += pend_f
                pend_s[:], pend_f[:] = 0, 0
            cum += (n * (best - rates)).sum()       # completions lost versus the best model
            regret[day] += cum
        last_day_share += n / QUERIES_PER_DAY
    return PolicyResult(regret / runs, last_day_share / runs)


def report(label: str, result: PolicyResult) -> None:
    shares = "  ".join(f"{m}:{s:5.1%}" for m, s in zip(MODEL_NAMES, result.final_share))
    print(f"{label:22s} cumulative regret after {DAYS} days: "
          f"{result.total_regret:8,.0f} completions")
    print(f"{'':22s} day-{DAYS} traffic share  {shares}")


# ── Exercise 1: The price of an exploration floor ─────────────────────────────

def route_with_floor(a: np.ndarray, b: np.ndarray, n_queries: int, floor: float,
                     rng: np.random.Generator) -> np.ndarray:
    k = len(a)
    choices = thompson_choices(a, b, n_queries, rng)
    if floor <= 0:
        return np.bincount(choices, minlength=k)
    # Take the floor share of queries out of the Thompson Sampling allocation and
    # route them uniformly instead. Removing queries at random (rather than the
    # last n_floor) keeps the remaining allocation an unbiased sample of the
    # Thompson Sampling choices.
    n_floor = rng.binomial(n_queries, floor)
    keep = rng.permutation(n_queries)[:n_queries - n_floor]
    return (np.bincount(choices[keep], minlength=k)
            + rng.multinomial(n_floor, np.full(k, 1 / k)))


def floor_sweep(floors: Sequence[float] = (0.05, 0.10, 0.20),
                runs: int = DEFAULT_RUNS) -> Dict[float, PolicyResult]:
    return {f: run_policy("ts", floor=f, runs=runs) for f in floors}


# ── Exercise 2: When the leaders tie ──────────────────────────────────────────

def tied_leaders_experiment(runs: int = DEFAULT_RUNS) -> Dict[str, PolicyResult]:
    close = TRUE_RATES.copy()
    close[1] = 0.66                      # Model B drops from 71% to 66%, tying with D
    return {"uniform": run_policy("uniform", rates=close, runs=runs),
            "ts": run_policy("ts", rates=close, runs=runs)}


def top_two_share(result: PolicyResult, rates: np.ndarray) -> float:
    # The two best models by true rate; with a tie, Thompson Sampling splits
    # traffic between them, so their combined share is the number to look at.
    top_two = np.argsort(rates)[-2:]
    return float(result.final_share[top_two].sum())


# ── Exercise 3: Delayed feedback ──────────────────────────────────────────────

def update_cadence_experiment(intervals: Sequence[int] = (1, 7),
                              runs: int = DEFAULT_RUNS) -> Dict[int, PolicyResult]:
    return {n: run_policy("ts", update_every=n, runs=runs) for n in intervals}


if __name__ == "__main__":
    print("=== Baseline: the three policies of Section 1.6 ===")
    report("Uniform", run_policy("uniform"))
    report("Thompson Sampling", run_policy("ts"))
    report("Thompson + 10% floor", run_policy("ts", floor=0.10))

    print("\n=== Exercise 1: change the floor ===")
    for floor, res in floor_sweep().items():
        report(f"Thompson + {floor:.0%} floor", res)

    print("\n=== Exercise 2: narrow the gap (Model B 71% -> 66%) ===")
    tied = tied_leaders_experiment()
    report("Uniform", tied["uniform"])
    report("Thompson Sampling", tied["ts"])

    print("\n=== Exercise 3: weekly instead of daily updates ===")
    for every, res in update_cadence_experiment().items():
        report(f"Update every {every} day(s)", res)


# Expected output:
#
# === Baseline: the three policies of Section 1.6 ===
# Uniform                cumulative regret after 14 days:    1,904 completions
#                        day-14 traffic share  A:20.0%  B:20.0%  C:20.0%  D:20.0%  E:20.0%
# Thompson Sampling      cumulative regret after 14 days:      174 completions
#                        day-14 traffic share  A: 0.0%  B:99.7%  C: 0.0%  D: 0.2%  E: 0.1%
# Thompson + 10% floor   cumulative regret after 14 days:      345 completions
#                        day-14 traffic share  A: 2.0%  B:91.9%  C: 2.0%  D: 2.1%  E: 2.0%
#
# === Exercise 1: change the floor ===
# Thompson + 5% floor    cumulative regret after 14 days:      257 completions
#                        day-14 traffic share  A: 1.0%  B:95.9%  C: 1.0%  D: 1.1%  E: 1.0%
# Thompson + 10% floor   cumulative regret after 14 days:      345 completions
#                        day-14 traffic share  A: 2.0%  B:91.9%  C: 2.0%  D: 2.1%  E: 2.0%
# Thompson + 20% floor   cumulative regret after 14 days:      515 completions
#                        day-14 traffic share  A: 4.0%  B:83.9%  C: 4.0%  D: 4.0%  E: 4.0%
#
# === Exercise 2: narrow the gap (Model B 71% -> 66%) ===
# Uniform                cumulative regret after 14 days:      784 completions
#                        day-14 traffic share  A:20.0%  B:19.9%  C:20.0%  D:20.0%  E:20.1%
# Thompson Sampling      cumulative regret after 14 days:      113 completions
#                        day-14 traffic share  A: 0.7%  B:47.4%  C: 0.1%  D:48.8%  E: 2.9%
#
# === Exercise 3: weekly instead of daily updates ===
# Update every 1 day(s)  cumulative regret after 14 days:      174 completions
#                        day-14 traffic share  A: 0.0%  B:99.7%  C: 0.0%  D: 0.2%  E: 0.1%
# Update every 7 day(s)  cumulative regret after 14 days:      954 completions
#                        day-14 traffic share  A: 0.0%  B:99.8%  C: 0.0%  D: 0.2%  E: 0.0%
