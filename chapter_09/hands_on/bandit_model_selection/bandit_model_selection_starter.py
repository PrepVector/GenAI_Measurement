"""
Chapter 9 — Section 1: Thompson Sampling for model selection
Starter file (Exercises 1-3)

Work through the three exercises in the book to implement each
function marked with TODO. Run pytest tests/ to validate your
implementation.

The simulator (thompson_choices, run_policy, report) is provided so
you can focus on the experiments. All results are simulated for
illustration, not measured on a real system.

No Anthropic API key required — this exercise uses only NumPy.
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
    """
    Route n_queries and return the number of queries sent to each model.

    TODO (Exercise 1):
      1. Draw each query's Thompson Sampling choice with thompson_choices().
      2. If floor <= 0, return the count of choices per model
         (np.bincount with minlength=len(a)).
      3. Otherwise reserve a share of traffic for uniform exploration:
           - n_floor = rng.binomial(n_queries, floor)
           - keep a random subset of n_queries - n_floor of the Thompson
             Sampling choices (rng.permutation gives a random order)
           - send the n_floor reserved queries uniformly across the models
             (rng.multinomial)
         and return the two counts added together.
      The result must always sum to n_queries.
    """
    raise NotImplementedError("Implement route_with_floor() — Exercise 1")


def floor_sweep(floors: Sequence[float] = (0.05, 0.10, 0.20),
                runs: int = DEFAULT_RUNS) -> Dict[float, PolicyResult]:
    """
    TODO (Exercise 1):
      Run Thompson Sampling ("ts") once per floor value and return a
      dict mapping each floor to its PolicyResult. Use run_policy().
      Which floor would you choose? Compare regret with the share of
      traffic Model B reaches on day 14.
    """
    raise NotImplementedError("Implement floor_sweep() — Exercise 1")


# ── Exercise 2: When the leaders tie ──────────────────────────────────────────

def tied_leaders_experiment(runs: int = DEFAULT_RUNS) -> Dict[str, PolicyResult]:
    """
    TODO (Exercise 2):
      Copy TRUE_RATES and set Model B (index 1) to 0.66, so it ties with
      Model D. Run the uniform and Thompson Sampling policies on the new
      rates (pass them as rates=) and return
        {"uniform": <PolicyResult>, "ts": <PolicyResult>}
    """
    raise NotImplementedError("Implement tied_leaders_experiment() — Exercise 2")


def top_two_share(result: PolicyResult, rates: np.ndarray) -> float:
    """
    TODO (Exercise 2):
      Return the combined day-14 traffic share of the two models with
      the highest true rate (np.argsort(rates) sorts ascending).
      When the leaders tie, how is traffic divided between them?
    """
    raise NotImplementedError("Implement top_two_share() — Exercise 2")


# ── Exercise 3: Delayed feedback ──────────────────────────────────────────────

def update_cadence_experiment(intervals: Sequence[int] = (1, 7),
                              runs: int = DEFAULT_RUNS) -> Dict[int, PolicyResult]:
    """
    TODO (Exercise 3):
      Run Thompson Sampling once per update interval (in days) and return
      a dict mapping each interval to its PolicyResult. Pass the interval
      as update_every= to run_policy().
      Why does a weekly update cost so much more regret than a daily one?
    """
    raise NotImplementedError("Implement update_cadence_experiment() — Exercise 3")


if __name__ == "__main__":
    print("=== Exercise 1: change the floor ===")
    for floor, res in floor_sweep().items():
        report(f"Thompson + {floor:.0%} floor", res)

    print("\n=== Exercise 2: narrow the gap (Model B 71% -> 66%) ===")
    tied = tied_leaders_experiment()
    report("Uniform", tied["uniform"])
    report("Thompson Sampling", tied["ts"])

    print("\n=== Exercise 3: weekly instead of daily updates ===")
    for every, res in update_cadence_experiment().items():
        report(f"Update every {every} day(s)", res)
