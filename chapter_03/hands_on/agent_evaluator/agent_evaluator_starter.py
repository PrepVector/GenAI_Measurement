"""
Chapter 3 — Section 3: Agent evaluation pipeline
Starter file

Work through the five exercises in the book to implement
each function marked with TODO. Run pytest tests/ to validate
your implementation.

Prerequisites:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic

client = Anthropic()


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ToolCall:
    tool_name: str
    parameters: Dict[str, Any]


@dataclass
class TrajectoryStep:
    step_index: int
    agent_reasoning: str
    tool_call: Optional[ToolCall]
    tool_output: Optional[str]
    reference_tool_call: Optional[ToolCall] = None


@dataclass
class AgentTrajectory:
    task_id: str
    task_description: str
    steps: List[TrajectoryStep]
    final_response: str
    success_criteria: str


@dataclass
class StepEvaluation:
    step_index: int
    tool_selection_correct: bool
    parameter_accuracy: str   # "exact" | "semantic" | "partial" | "incorrect"
    correctness_category: str # "correct" | "partially_correct" | "wrong_tool" | "not_needed"
    judge_reasoning: str


@dataclass
class TaskEvaluation:
    task_id: str
    goal_completion_score: int   # 1–5
    path_efficiency: float
    step_evaluations: List[StepEvaluation]
    step_accuracy: float
    judge_reasoning: str
    evaluated_at: datetime = field(default_factory=datetime.utcnow)


# ── Exercise 1: Step-level judge ──────────────────────────────────────────────

# TODO (Exercise 1): Write a system prompt for the step-level judge.
#
# Your prompt must:
#   1. Define all four correctness categories precisely:
#        correct          — right tool, params equivalent to reference
#        partially_correct — right tool, one or more params wrong
#        wrong_tool       — incorrect tool selected
#        not_needed       — tool called when none was required
#   2. Distinguish exact match from semantic equivalence for parameters.
#      Two retrieval queries with different wording but equivalent intent
#      should be rated "correct" with parameter_accuracy "semantic".
#   3. Instruct the model to return JSON only — no preamble, no fences.
#      Required fields: correctness_category, tool_selection_correct,
#                       parameter_accuracy, reasoning
#
TOOL_CALL_JUDGE_SYSTEM = """
TODO: Write your step-level judge system prompt here.
"""


def evaluate_tool_call(
    task_description: str,
    step: TrajectoryStep,
    available_tools: List[Dict],
) -> StepEvaluation:
    """
    Use an LLM judge to evaluate a single tool call.

    TODO (Exercise 1):
      1. Handle the case where both tool_call and reference_tool_call
         are None — return a "correct" StepEvaluation immediately
         without making an API call.
      2. Build a user prompt that provides:
           - The overall task description
           - The agent's reasoning at this step
           - The agent's actual tool call (serialised as JSON),
             or "No tool called" if tool_call is None
           - The reference tool call (serialised as JSON),
             or "No tool required" if reference_tool_call is None
           - The list of available tools with their schemas
      3. Call client.messages.create() with TOOL_CALL_JUDGE_SYSTEM
         and your user prompt. Use model="claude-sonnet-4-6",
         max_tokens=1000.
      4. Parse the JSON response and return a StepEvaluation.
    """
    raise NotImplementedError("Implement evaluate_tool_call() — Exercise 1")


# ── Exercise 2: Task-level judge ──────────────────────────────────────────────

# TODO (Exercise 2): Write a system prompt for the task-level judge.
#
# Your prompt must:
#   1. Define a precise 1–5 rubric:
#        5 = all success criteria explicitly satisfied
#        4 = mostly satisfied, minor gaps
#        3 = partially satisfied, significant gaps
#        2 = attempted but largely failed
#        1 = does not address the task
#   2. Instruct the judge to evaluate the final response against the
#      success criteria — NOT the process the agent used to get there.
#   3. Return JSON only with fields: goal_completion_score, reasoning
#
TASK_JUDGE_SYSTEM = """
TODO: Write your task-level judge system prompt here.
"""


def evaluate_task_completion(trajectory: AgentTrajectory) -> Dict:
    """
    Use an LLM judge to evaluate overall task completion.

    TODO (Exercise 2):
      1. Build a trajectory summary — a short record of each step:
           "Step N: <first 100 chars of reasoning> → Tool: <tool_name or 'none'>"
      2. Build a user prompt providing:
           - Task description
           - Success criteria
           - Trajectory summary
           - Final response
      3. Call client.messages.create() with TASK_JUDGE_SYSTEM.
         Use model="claude-sonnet-4-6", max_tokens=1000.
      4. Parse and return the JSON response as a dict.
    """
    raise NotImplementedError("Implement evaluate_task_completion() — Exercise 2")


# ── Exercise 3: Full pipeline ─────────────────────────────────────────────────

def evaluate_agent_trajectory(
    trajectory: AgentTrajectory,
    available_tools: List[Dict],
    expected_steps: int,
) -> TaskEvaluation:
    """
    Run the full evaluation pipeline on a single agent trajectory.

    TODO (Exercise 3):
      1. Call evaluate_tool_call() for every step in trajectory.steps
      2. Compute step_accuracy:
           correct_steps / total_steps
         where correct_steps = steps with correctness_category == "correct"
      3. Call evaluate_task_completion() for the full trajectory
      4. Compute path_efficiency:
           min(expected_steps / len(trajectory.steps), 1.0)
      5. Return a TaskEvaluation with all of the above.
    """
    raise NotImplementedError("Implement evaluate_agent_trajectory() — Exercise 3")


# ── Exercise 5: Serialisation ─────────────────────────────────────────────────

def to_run_record(evaluation: TaskEvaluation) -> dict:
    """
    Serialise a TaskEvaluation for inclusion in the Chapter 2
    eval run record format.

    TODO (Exercise 5):
      Return a dict with two top-level keys:
        "task_level": {
            "goal_completion_score": ...,
            "path_efficiency": ...,
            "judge_reasoning": ...
        }
        "step_level": {
            "step_accuracy": ...,
            "steps": [
                {
                    "step_index": ...,
                    "correctness_category": ...,
                    "tool_selection_correct": ...,
                    "parameter_accuracy": ...,
                    "reasoning": ...
                },
                ...
            ]
        }
    """
    raise NotImplementedError("Implement to_run_record() — Exercise 5")


def summarise_run(evaluations: List[TaskEvaluation]) -> dict:
    """
    Aggregate metrics across a full evaluation run.

    TODO (Exercise 5):
      Return a dict with:
        "mean_step_accuracy": float
        "mean_task_score": float
        "mean_path_efficiency": float
        "correctness_breakdown": {
            "correct": float,          # fraction of all steps
            "partially_correct": float,
            "wrong_tool": float,
            "not_needed": float,
        }
    """
    raise NotImplementedError("Implement summarise_run() — Exercise 5")


# ── Test trajectory (used in exercises and tests) ─────────────────────────────

AVAILABLE_TOOLS = [
    {
        "name": "retrieve_documents",
        "description": "Retrieve relevant documents from the knowledge base",
        "parameters": {"query": "string", "top_k": "integer"},
    },
    {
        "name": "summarise_document",
        "description": "Summarise a retrieved document",
        "parameters": {"doc_id": "string", "focus": "string"},
    },
    {
        "name": "query_database",
        "description": "Query the structured product database",
        "parameters": {"table": "string", "filter": "dict"},
    },
]

TEST_TRAJECTORY = AgentTrajectory(
    task_id="task_001",
    task_description=(
        "What is our current remote work policy for employees in the EU?"
    ),
    success_criteria=(
        "Response must cite the correct policy document, "
        "state the specific EU remote work allowance, "
        "and note any recent amendments."
    ),
    steps=[
        TrajectoryStep(
            step_index=0,
            agent_reasoning="I need to retrieve the remote work policy document.",
            tool_call=ToolCall(
                "retrieve_documents",
                {"query": "remote work policy EU employees", "top_k": 3}
            ),
            tool_output="[Doc 42: EU Remote Work Policy v2.1, Doc 17: General HR Policy]",
            reference_tool_call=ToolCall(
                "retrieve_documents",
                {"query": "EU remote work policy", "top_k": 3}
            ),
        ),
        TrajectoryStep(
            step_index=1,
            agent_reasoning="I should summarise the EU policy document.",
            tool_call=ToolCall(
                "summarise_document",
                {"doc_id": "42", "focus": "EU remote work allowance and amendments"}
            ),
            tool_output="EU employees may work remotely up to 3 days/week. Amended Jan 2024.",
            reference_tool_call=ToolCall(
                "summarise_document",
                {"doc_id": "42", "focus": "remote work allowance EU"}
            ),
        ),
        TrajectoryStep(
            step_index=2,
            agent_reasoning="I have enough information to answer.",
            tool_call=None,
            tool_output=None,
            reference_tool_call=None,
        ),
    ],
    final_response=(
        "According to the EU Remote Work Policy v2.1 (amended January 2024), "
        "EU employees may work remotely for up to 3 days per week. "
        "The January 2024 amendment extended this from the previous 2-day allowance."
    ),
)


if __name__ == "__main__":
    evaluation = evaluate_agent_trajectory(
        TEST_TRAJECTORY, AVAILABLE_TOOLS, expected_steps=2
    )
    print(f"Task:            {evaluation.task_id}")
    print(f"Task score:      {evaluation.goal_completion_score}/5")
    print(f"Step accuracy:   {evaluation.step_accuracy:.0%}")
    print(f"Path efficiency: {evaluation.path_efficiency:.0%}")
    print(f"\nStep breakdown:")
    for e in evaluation.step_evaluations:
        print(
            f"  Step {e.step_index}: {e.correctness_category} "
            f"(tool: {'✓' if e.tool_selection_correct else '✗'}, "
            f"params: {e.parameter_accuracy})"
        )
    print(f"\nRun record:")
    print(json.dumps(to_run_record(evaluation), indent=2))