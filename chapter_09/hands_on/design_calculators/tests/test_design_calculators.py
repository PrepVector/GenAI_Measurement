"""
Tests for Chapter 9 Sections 2-4 — Design calculators.

Run from the exercise folder:
    pytest tests/ -v

Tests are grouped by exercise:
    pytest tests/ -v -k "TestExercise4"
"""

import pytest

from design_calculators_starter import (
    BEST_PER_TYPE,
    GENERAL_TO_B,
    TRAFFIC_MIX,
    decisive_judgments,
    interleaving_query_fraction,
    policy_completion_rate,
)


# ── Exercise 4 ────────────────────────────────────────────────────────────────

class TestExercise4:

    def test_best_per_type_policy_is_75_point_8(self):
        assert policy_completion_rate(TRAFFIC_MIX, BEST_PER_TYPE) == pytest.approx(0.758)

    def test_general_queries_to_model_b(self):
        assert policy_completion_rate(TRAFFIC_MIX, GENERAL_TO_B) == pytest.approx(0.752)

    def test_cost_of_sending_general_queries_to_b(self):
        loss = (policy_completion_rate(TRAFFIC_MIX, BEST_PER_TYPE)
                - policy_completion_rate(TRAFFIC_MIX, GENERAL_TO_B))
        assert loss == pytest.approx(0.006)

    def test_single_type_policy_returns_that_rate(self):
        assert policy_completion_rate([1.0, 0.0], [0.7, 0.9]) == pytest.approx(0.7)

    def test_equal_mix_is_the_plain_average(self):
        assert policy_completion_rate([0.5, 0.5], [0.6, 0.8]) == pytest.approx(0.7)


# ── Exercise 5 ────────────────────────────────────────────────────────────────

class TestExercise5:

    def test_57_percent_needs_about_398(self):
        assert round(decisive_judgments(0.57)) == 398

    @pytest.mark.parametrize("q, expected", [(0.52, 4900), (0.55, 780),
                                             (0.60, 190), (0.65, 85)])
    def test_matches_table_9_8(self, q, expected):
        """Table 9.8 values are rounded, so allow 5%."""
        assert decisive_judgments(q) == pytest.approx(expected, rel=0.05)

    def test_symmetric_around_50_percent(self):
        assert decisive_judgments(0.43) == pytest.approx(decisive_judgments(0.57), rel=0.01)

    def test_larger_preference_needs_fewer_judgments(self):
        assert decisive_judgments(0.65) < decisive_judgments(0.60) < decisive_judgments(0.55)

    def test_higher_power_needs_more_judgments(self):
        assert decisive_judgments(0.57, z_power=1.2816) > decisive_judgments(0.57)


# ── Exercise 6 ────────────────────────────────────────────────────────────────

class TestExercise6:

    def test_ratio_of_four(self):
        per_arm, of_total = interleaving_query_fraction(4.0)
        assert per_arm == pytest.approx(0.20)
        assert of_total == pytest.approx(0.10)

    def test_no_between_query_variance_gives_no_saving_per_arm(self):
        per_arm, of_total = interleaving_query_fraction(0.0)
        assert per_arm == pytest.approx(1.0)
        assert of_total == pytest.approx(0.5)

    def test_total_fraction_is_half_the_per_arm_fraction(self):
        per_arm, of_total = interleaving_query_fraction(2.5)
        assert of_total == pytest.approx(per_arm / 2)

    def test_more_varied_queries_help_interleaving_more(self):
        assert interleaving_query_fraction(9.0)[0] < interleaving_query_fraction(1.0)[0]
