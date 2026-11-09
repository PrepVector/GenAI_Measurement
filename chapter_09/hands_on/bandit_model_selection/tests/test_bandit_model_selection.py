"""
Tests for Chapter 9 Section 1 — Thompson Sampling for model selection.

Run from the exercise folder:
    pytest tests/ -v

Tests are grouped by exercise:
    pytest tests/ -v -k "TestExercise1"

The simulations use a small number of repetitions (runs=100) so the tests
run quickly, and the assertions check ordering and rough size, not exact
values, so they do not depend on how you consume the random number stream.
"""

import numpy as np
import pytest

from bandit_model_selection_starter import (
    TRUE_RATES,
    PolicyResult,
    floor_sweep,
    route_with_floor,
    run_policy,
    tied_leaders_experiment,
    top_two_share,
    update_cadence_experiment,
)

RUNS = 100


# ── Exercise 1 ────────────────────────────────────────────────────────────────

class TestExercise1:

    def test_route_with_floor_sums_to_n_queries(self):
        """Every query is routed to exactly one model."""
        rng = np.random.default_rng(0)
        n = route_with_floor(np.ones(5), np.ones(5), 2000, 0.1, rng)
        assert n.sum() == 2000
        assert len(n) == 5

    def test_route_without_floor_sums_to_n_queries(self):
        rng = np.random.default_rng(0)
        n = route_with_floor(np.ones(5), np.ones(5), 2000, 0.0, rng)
        assert n.sum() == 2000

    def test_floor_keeps_every_model_alive(self):
        """With a posterior that strongly favors Model B, a 20% floor still
        sends each model roughly floor / 5 = 4% of traffic."""
        rng = np.random.default_rng(1)
        a = np.array([1.0, 700.0, 1.0, 1.0, 1.0])
        b = np.array([400.0, 300.0, 400.0, 400.0, 400.0])
        shares = np.mean([route_with_floor(a, b, 5000, 0.2, rng) / 5000
                          for _ in range(20)], axis=0)
        assert (shares[[0, 2, 3, 4]] > 0.03).all()
        assert shares[1] > 0.75

    def test_no_floor_concentrates_on_the_leader(self):
        rng = np.random.default_rng(2)
        a = np.array([1.0, 700.0, 1.0, 1.0, 1.0])
        b = np.array([400.0, 300.0, 400.0, 400.0, 400.0])
        n = route_with_floor(a, b, 5000, 0.0, rng)
        assert n[1] / 5000 > 0.99

    def test_floor_sweep_returns_one_result_per_floor(self):
        results = floor_sweep((0.05, 0.20), runs=RUNS)
        assert set(results) == {0.05, 0.20}
        assert all(isinstance(r, PolicyResult) for r in results.values())

    def test_regret_rises_with_the_floor(self):
        results = floor_sweep((0.05, 0.10, 0.20), runs=RUNS)
        regrets = [results[f].total_regret for f in (0.05, 0.10, 0.20)]
        assert regrets[0] < regrets[1] < regrets[2]

    def test_best_model_share_falls_with_the_floor(self):
        results = floor_sweep((0.05, 0.20), runs=RUNS)
        assert results[0.05].final_share[1] > results[0.20].final_share[1]

    def test_every_floor_beats_a_uniform_split(self):
        uniform = run_policy("uniform", runs=RUNS).total_regret
        for res in floor_sweep((0.05, 0.10, 0.20), runs=RUNS).values():
            assert res.total_regret < 0.5 * uniform


# ── Exercise 2 ────────────────────────────────────────────────────────────────

class TestExercise2:

    def test_returns_both_policies(self):
        results = tied_leaders_experiment(runs=RUNS)
        assert set(results) == {"uniform", "ts"}

    def test_uniform_regret_matches_the_formula(self):
        """Uniform regret = 14 days x 2,000 queries x (0.66 - mean rate)."""
        close = TRUE_RATES.copy()
        close[1] = 0.66
        expected = 14 * 2000 * (0.66 - close.mean())
        got = tied_leaders_experiment(runs=RUNS)["uniform"].total_regret
        assert abs(got - expected) / expected < 0.05

    def test_thompson_sampling_still_beats_uniform(self):
        results = tied_leaders_experiment(runs=RUNS)
        assert results["ts"].total_regret < 0.4 * results["uniform"].total_regret

    def test_traffic_is_split_between_the_tied_leaders(self):
        results = tied_leaders_experiment(runs=RUNS)
        share = results["ts"].final_share
        assert share[1] > 0.3 and share[3] > 0.3   # Models B and D

    def test_top_two_share_adds_the_two_best_models(self):
        close = TRUE_RATES.copy()
        close[1] = 0.66
        result = PolicyResult(np.zeros(14), np.array([0.1, 0.4, 0.0, 0.45, 0.05]))
        assert top_two_share(result, close) == pytest.approx(0.85)

    def test_top_two_share_is_high_for_the_experiment(self):
        close = TRUE_RATES.copy()
        close[1] = 0.66
        res = tied_leaders_experiment(runs=RUNS)["ts"]
        assert top_two_share(res, close) > 0.85


# ── Exercise 3 ────────────────────────────────────────────────────────────────

class TestExercise3:

    def test_returns_one_result_per_interval(self):
        results = update_cadence_experiment((1, 7), runs=RUNS)
        assert set(results) == {1, 7}

    def test_weekly_updates_cost_much_more_regret(self):
        results = update_cadence_experiment((1, 7), runs=RUNS)
        assert results[7].total_regret > 3 * results[1].total_regret

    def test_first_week_is_effectively_uniform(self):
        """No update has happened by day 7, so the first week loses roughly
        7 x 2,000 x (0.71 - mean rate) = about 950 completions."""
        weekly = update_cadence_experiment((7,), runs=RUNS)[7]
        expected = 7 * 2000 * (TRUE_RATES.max() - TRUE_RATES.mean())
        assert abs(weekly.cumulative_regret[6] - expected) / expected < 0.05

    def test_one_update_at_the_end_is_the_uniform_split(self):
        """An update interval of 14 days means no learning at all."""
        results = update_cadence_experiment((14,), runs=RUNS)
        uniform = run_policy("uniform", runs=RUNS).total_regret
        assert abs(results[14].total_regret - uniform) / uniform < 0.05

    def test_both_cadences_end_on_the_best_model(self):
        results = update_cadence_experiment((1, 7), runs=RUNS)
        for res in results.values():
            assert res.final_share[1] > 0.9
