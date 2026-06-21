# ── Exercise 5: Offline gate ──────────────────────────────────────────────────

from eval_run_record_starter import (
    GateCondition,
    GateDecision,
    evaluate_gate,
    print_gate_report,
    gate_and_record,
    GATE_SAMPLE_RECORD,
    GATE_SAMPLE_THRESHOLDS,
)


def passing_gate_record() -> dict:
    return {
        "run_id": "run_pass",
        "aggregate_metrics": {
            "goal_metric_score":  4.2,
            "hallucination_rate": 0.03,
            "latency_p95_ms":     3800.0,
            "cost_per_query_usd": 0.004,
        },
    }


class TestExercise5OfflineGate:

    # GateCondition
    def test_min_condition_passes(self):
        c = GateCondition("Q", 4.1, 3.8, "min")
        assert c.passed is True

    def test_min_condition_fails(self):
        c = GateCondition("Q", 3.5, 3.8, "min")
        assert c.passed is False

    def test_min_gap_positive_when_passing(self):
        c = GateCondition("Q", 4.1, 3.8, "min")
        assert abs(c.gap - 0.3) < 0.001

    def test_min_gap_negative_when_failing(self):
        c = GateCondition("Q", 3.5, 3.8, "min")
        assert abs(c.gap - (-0.3)) < 0.001

    def test_max_condition_passes(self):
        c = GateCondition("L", 3800.0, 4000.0, "max")
        assert c.passed is True

    def test_max_condition_fails(self):
        c = GateCondition("L", 4340.0, 4000.0, "max")
        assert c.passed is False

    def test_max_gap_negative_when_failing(self):
        c = GateCondition("L", 4340.0, 4000.0, "max")
        assert abs(c.gap - (-340.0)) < 0.001

    # evaluate_gate
    def test_sample_fails(self):
        d = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert d.passed is False

    def test_sample_latency_fails(self):
        d = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert d.conditions["latency_ceiling"].passed is False

    def test_sample_quality_passes(self):
        d = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert d.conditions["quality_floor"].passed is True

    def test_all_pass_scenario(self):
        d = evaluate_gate(passing_gate_record(), **GATE_SAMPLE_THRESHOLDS)
        assert d.passed is True

    def test_all_pass_annotation(self):
        d = evaluate_gate(passing_gate_record(), **GATE_SAMPLE_THRESHOLDS)
        assert "shadow" in d.annotation.lower()

    def test_single_failure_annotation_names_condition(self):
        d = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert "Latency" in d.annotation

    def test_single_failure_annotation_includes_gap(self):
        d = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert "340" in d.annotation

    def test_four_conditions_returned(self):
        d = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert len(d.conditions) == 4

    def test_missing_metric_defaults_to_failure(self):
        d = evaluate_gate({"aggregate_metrics": {}}, **GATE_SAMPLE_THRESHOLDS)
        assert d.passed is False

    def test_returns_gate_decision_type(self):
        d = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert isinstance(d, GateDecision)

    # print_gate_report
    def test_prints_block(self, capsys):
        d = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        print_gate_report(d)
        assert "BLOCK" in capsys.readouterr().out

    def test_prints_pass(self, capsys):
        d = evaluate_gate(passing_gate_record(), **GATE_SAMPLE_THRESHOLDS)
        print_gate_report(d)
        assert "PASS" in capsys.readouterr().out

    def test_prints_all_condition_names(self, capsys):
        d = evaluate_gate(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        print_gate_report(d)
        out = capsys.readouterr().out
        for name in ["Quality", "Hallucination", "Cost", "Latency"]:
            assert name in out

    # gate_and_record
    def test_gate_decision_key_present(self):
        r = gate_and_record(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert "gate_decision" in r

    def test_original_not_mutated(self):
        original_keys = set(GATE_SAMPLE_RECORD.keys())
        gate_and_record(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert "gate_decision" not in GATE_SAMPLE_RECORD
        assert set(GATE_SAMPLE_RECORD.keys()) == original_keys

    def test_conditions_have_required_keys(self):
        r = gate_and_record(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        for cond in r["gate_decision"]["conditions"].values():
            for f in ["name", "observed", "threshold", "passed", "gap"]:
                assert f in cond

    def test_values_rounded_to_4dp(self):
        r = gate_and_record(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        for cond in r["gate_decision"]["conditions"].values():
            assert cond["observed"]  == round(cond["observed"],  4)
            assert cond["threshold"] == round(cond["threshold"], 4)
            assert cond["gap"]       == round(cond["gap"],       4)

    def test_json_serialisable(self):
        r = gate_and_record(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        json.dumps(r)

    def test_passed_false_for_sample(self):
        r = gate_and_record(GATE_SAMPLE_RECORD, **GATE_SAMPLE_THRESHOLDS)
        assert r["gate_decision"]["passed"] is False

    def test_passed_true_for_passing(self):
        r = gate_and_record(passing_gate_record(), **GATE_SAMPLE_THRESHOLDS)
        assert r["gate_decision"]["passed"] is True