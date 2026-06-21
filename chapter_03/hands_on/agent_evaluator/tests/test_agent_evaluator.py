"""
Tests for Chapter 3 Section 3 — Agent evaluation pipeline.

Run from the exercise folder:
    pytest tests/ -v

All tests use the TEST_TRAJECTORY and AVAILABLE_TOOLS defined in
agent_evaluator_starter.py (or agent_evaluator_solution.py).

Tests are grouped by exercise so you can run one group at a time:
    pytest tests/ -v -k "exercise_1"
"""

import pytest
from agent_evaluator_starter import (
    evaluate_tool_call,
    evaluate_task_completion,
    evaluate_agent_trajectory,
    to_run_record,
    summarise_run,
    TEST_TRAJECTORY,
    AVAILABLE_TOOLS,
    ToolCall,
    TrajectoryStep,
    AgentTrajectory,
    StepEvaluation,
    TaskEvaluation,
)

EXPECTED_STEPS = 2


# ── Exercise 1: Step-level judge ──────────────────────────────────────────────

class TestExercise1:

    def test_abstention_returns_correct_without_api_call(self):
        """When both tool_call and reference are None, return correct immediately."""
        step = TrajectoryStep(
            step_index=2,
            agent_reasoning="I have enough information to answer.",
            tool_call=None,
            tool_output=None,
            reference_tool_call=None,
        )
        result = evaluate_tool_call("any task", step, AVAILABLE_TOOLS)
        assert result.correctness_category == "correct"
        assert result.tool_selection_correct is True

    def test_semantic_equivalence_rated_correct(self):
        """Semantically equivalent but differently worded queries are correct."""
        step = TEST_TRAJECTORY.steps[0]
        result = evaluate_tool_call(
            TEST_TRAJECTORY.task_description, step, AVAILABLE_TOOLS
        )
        assert result.correctness_category == "correct"
        assert result.parameter_accuracy == "semantic"
        assert result.tool_selection_correct is True

    def test_minor_param_difference_rated_partially_correct(self):
        """Right tool and doc_id but different focus wording = partially correct."""
        step = TEST_TRAJECTORY.steps[1]
        result = evaluate_tool_call(
            TEST_TRAJECTORY.task_description, step, AVAILABLE_TOOLS
        )
        assert result.correctness_category == "partially_correct"
        assert result.tool_selection_correct is True

    def test_wrong_tool_detected(self):
        """Agent uses query_database when retrieve_documents was expected."""
        step = TrajectoryStep(
            step_index=0,
            agent_reasoning="I will query the database for the policy.",
            tool_call=ToolCall(
                "query_database",
                {"table": "policies", "filter": {"region": "EU"}}
            ),
            tool_output="[]",
            reference_tool_call=ToolCall(
                "retrieve_documents",
                {"query": "EU remote work policy", "top_k": 3}
            ),
        )
        result = evaluate_tool_call(
            TEST_TRAJECTORY.task_description, step, AVAILABLE_TOOLS
        )
        assert result.correctness_category == "wrong_tool"
        assert result.tool_selection_correct is False

    def test_unnecessary_tool_call_rated_not_needed(self):
        """Tool called when reference expects no tool = not_needed."""
        step = TrajectoryStep(
            step_index=2,
            agent_reasoning="Let me summarise the document again.",
            tool_call=ToolCall(
                "summarise_document",
                {"doc_id": "42", "focus": "allowance"}
            ),
            tool_output="EU employees may work remotely up to 3 days/week.",
            reference_tool_call=None,
        )
        result = evaluate_tool_call(
            TEST_TRAJECTORY.task_description, step, AVAILABLE_TOOLS
        )
        assert result.correctness_category == "not_needed"

    def test_returns_step_evaluation_type(self):
        """evaluate_tool_call always returns a StepEvaluation."""
        result = evaluate_tool_call(
            TEST_TRAJECTORY.task_description,
            TEST_TRAJECTORY.steps[0],
            AVAILABLE_TOOLS,
        )
        assert isinstance(result, StepEvaluation)
        assert result.reasoning  # non-empty reasoning string


# ── Exercise 2: Task-level judge ──────────────────────────────────────────────

class TestExercise2:

    def test_task_score_is_integer_in_range(self):
        """Goal completion score is an integer between 1 and 5."""
        result = evaluate_task_completion(TEST_TRAJECTORY)
        assert isinstance(result["goal_completion_score"], int)
        assert 1 <= result["goal_completion_score"] <= 5

    def test_correct_trajectory_scores_high(self):
        """The test trajectory satisfies all criteria — should score 4 or 5."""
        result = evaluate_task_completion(TEST_TRAJECTORY)
        assert result["goal_completion_score"] >= 4

    def test_result_contains_reasoning(self):
        """Response includes a non-empty reasoning string."""
        result = evaluate_task_completion(TEST_TRAJECTORY)
        assert "reasoning" in result
        assert len(result["reasoning"]) > 20


# ── Exercise 3: Full pipeline ─────────────────────────────────────────────────

class TestExercise3:

    @pytest.fixture(scope="class")
    def evaluation(self):
        return evaluate_agent_trajectory(
            TEST_TRAJECTORY, AVAILABLE_TOOLS, expected_steps=EXPECTED_STEPS
        )

    def test_returns_task_evaluation(self, evaluation):
        assert isinstance(evaluation, TaskEvaluation)

    def test_correct_number_of_step_evaluations(self, evaluation):
        assert len(evaluation.step_evaluations) == len(TEST_TRAJECTORY.steps)

    def test_step_accuracy(self, evaluation):
        """2 of 3 steps correct → step accuracy ≈ 0.67."""
        assert abs(evaluation.step_accuracy - 2/3) < 0.01

    def test_path_efficiency(self, evaluation):
        """2 expected steps, 3 actual → efficiency ≈ 0.67."""
        assert abs(evaluation.path_efficiency - 2/3) < 0.01

    def test_path_efficiency_capped_at_one(self):
        """Path efficiency never exceeds 1.0."""
        result = evaluate_agent_trajectory(
            TEST_TRAJECTORY, AVAILABLE_TOOLS, expected_steps=10
        )
        assert result.path_efficiency <= 1.0

    def test_task_score_is_high(self, evaluation):
        """Task score should be 4 or 5 for the test trajectory."""
        assert evaluation.goal_completion_score >= 4


# ── Exercise 4: Stress tests ──────────────────────────────────────────────────

class TestExercise4:

    def test_wrong_document_lowers_task_score(self):
        """Retrieving the wrong document should lower the task-level score."""
        bad_trajectory = AgentTrajectory(
            task_id="task_002",
            task_description=TEST_TRAJECTORY.task_description,
            success_criteria=TEST_TRAJECTORY.success_criteria,
            steps=[
                TrajectoryStep(
                    step_index=0,
                    agent_reasoning="Retrieving policy document.",
                    tool_call=ToolCall(
                        "retrieve_documents",
                        {"query": "EU remote work policy", "top_k": 3}
                    ),
                    tool_output="[Doc 17: General HR Policy]",
                    reference_tool_call=ToolCall(
                        "retrieve_documents",
                        {"query": "EU remote work policy", "top_k": 3}
                    ),
                ),
                TrajectoryStep(
                    step_index=1,
                    agent_reasoning="Summarising the document.",
                    tool_call=ToolCall(
                        "summarise_document",
                        {"doc_id": "17", "focus": "EU work policies"}
                    ),
                    tool_output="General HR policies for all employees.",
                    reference_tool_call=ToolCall(
                        "summarise_document",
                        {"doc_id": "42", "focus": "EU remote work"}
                    ),
                ),
            ],
            final_response="Employees are subject to general HR policies.",
        )
        result = evaluate_task_completion(bad_trajectory)
        assert result["goal_completion_score"] <= 3

    def test_unnecessary_tool_call_detected(self):
        """Extra tool call rated as not_needed."""
        extra_step = TrajectoryStep(
            step_index=2,
            agent_reasoning="Let me summarise the document again.",
            tool_call=ToolCall(
                "summarise_document",
                {"doc_id": "42", "focus": "allowance"}
            ),
            tool_output="EU employees: 3 days remote/week.",
            reference_tool_call=None,
        )
        result = evaluate_tool_call(
            TEST_TRAJECTORY.task_description, extra_step, AVAILABLE_TOOLS
        )
        assert result.correctness_category == "not_needed"


# ── Exercise 5: Serialisation ─────────────────────────────────────────────────

class TestExercise5:

    @pytest.fixture(scope="class")
    def evaluation(self):
        return evaluate_agent_trajectory(
            TEST_TRAJECTORY, AVAILABLE_TOOLS, expected_steps=EXPECTED_STEPS
        )

    def test_run_record_has_required_keys(self, evaluation):
        record = to_run_record(evaluation)
        assert "task_level" in record
        assert "step_level" in record

    def test_run_record_task_level_fields(self, evaluation):
        record = to_run_record(evaluation)
        tl = record["task_level"]
        assert "goal_completion_score" in tl
        assert "path_efficiency" in tl
        assert "judge_reasoning" in tl

    def test_run_record_step_level_fields(self, evaluation):
        record = to_run_record(evaluation)
        sl = record["step_level"]
        assert "step_accuracy" in sl
        assert "steps" in sl
        assert len(sl["steps"]) == len(TEST_TRAJECTORY.steps)

    def test_summarise_run_keys(self, evaluation):
        summary = summarise_run([evaluation, evaluation])
        assert "mean_step_accuracy" in summary
        assert "mean_task_score" in summary
        assert "mean_path_efficiency" in summary
        assert "correctness_breakdown" in summary

    def test_correctness_breakdown_sums_to_one(self, evaluation):
        summary = summarise_run([evaluation])
        total = sum(summary["correctness_breakdown"].values())
        assert abs(total - 1.0) < 0.01