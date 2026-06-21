"""
Chapter 3 — Section 3: Agent evaluation pipeline
Reference solution

Read this only after attempting the exercises yourself.
Every non-trivial decision is explained in an inline comment.
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
    parameter_accuracy: str
    correctness_category: str
    judge_reasoning: str


@dataclass
class TaskEvaluation:
    task_id: str
    goal_completion_score: int
    path_efficiency: float
    step_evaluations: List[StepEvaluation]
    step_accuracy: float
    judge_reasoning: str
    evaluated_at: datetime = field(default_factory=datetime.utcnow)


# ── Exercise 1: Step-level judge ──────────────────────────────────────────────

# The system prompt does three things:
#   1. Defines all four categories with concrete examples so the judge
#      does not have to infer what "partially correct" means.
#   2. Draws an explicit line between exact match and semantic equivalence
#      for parameters — the most common source of false negatives.
#   3. Mandates JSON-only output so parsing is deterministic. Without
#      this constraint the model occasionally adds preamble text that
#      breaks json.loads().
TOOL_CALL_JUDGE_SYSTEM = """You are an expert evaluator of AI agent tool calls.
You assess whether an agent's tool call is correct given the task context
and a reference (expected) tool call.

You must respond with a JSON object only — no preamble, no markdown fences.
Required fields:
  correctness_category: one of "correct", "partially_correct", "wrong_tool", "not_needed"
  tool_selection_correct: boolean
  parameter_accuracy: one of "exact", "semantic", "partial", "incorrect"
  reasoning: a brief explanation of your judgement (1-3 sentences)

Category definitions:
  correct          — the agent selected the right tool AND the parameters are
                     equivalent to the reference (either exact or semantic match).
  partially_correct — the agent selected the right tool BUT one or more parameters
                     are incorrect or meaningfully different from the reference.
  wrong_tool       — the agent selected the wrong tool entirely, regardless of
                     what parameters it used.
  not_needed       — the agent called a tool when the reference expects no tool
                     call at this step.

Parameter accuracy definitions:
  exact    — parameters match the reference character-for-character.
  semantic — parameters differ in wording but are equivalent in intent and would
             produce the same result. Example: "EU remote work policy" and
             "remote work policy EU employees" are semantically equivalent
             retrieval queries if they retrieve the same documents.
  partial  — some parameters are correct but at least one is meaningfully wrong
             (wrong value, wrong field, or substantively different wording that
             would change the result).
  incorrect — parameters are wrong or missing in a way that would produce a
              different result from the reference.

Always evaluate parameters in the context of the task. Small wording differences
that preserve meaning are semantic equivalence, not errors."""


def evaluate_tool_call(
    task_description: str,
    step: TrajectoryStep,
    available_tools: List[Dict],
) -> StepEvaluation:
    # Handle the abstention case first — no API call needed.
    # This is important: making an API call for a trivially correct
    # abstention wastes tokens and introduces unnecessary variance.
    if step.tool_call is None and step.reference_tool_call is None:
        return StepEvaluation(
            step_index=step.step_index,
            tool_selection_correct=True,
            parameter_accuracy="exact",
            correctness_category="correct",
            judge_reasoning=(
                "No tool call required at this step; "
                "agent correctly abstained."
            ),
        )

    # Serialise tool calls to JSON for the prompt. Using json.dumps
    # ensures consistent formatting and handles nested dicts cleanly.
    actual = (
        json.dumps({
            "tool": step.tool_call.tool_name,
            "parameters": step.tool_call.parameters,
        }, indent=2)
        if step.tool_call else "No tool called"
    )
    reference = (
        json.dumps({
            "tool": step.reference_tool_call.tool_name,
            "parameters": step.reference_tool_call.parameters,
        }, indent=2)
        if step.reference_tool_call else "No tool required at this step"
    )

    user_prompt = f"""Task: {task_description}

Agent's reasoning at this step:
{step.agent_reasoning}

Agent's actual tool call:
{actual}

Reference (expected) tool call:
{reference}

Available tools:
{json.dumps(available_tools, indent=2)}

Evaluate the agent's tool call against the reference."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=TOOL_CALL_JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Strip any accidental whitespace before parsing. The system prompt
    # requests JSON-only output but a small safety strip is cheap.
    result = json.loads(response.content[0].text.strip())

    return StepEvaluation(
        step_index=step.step_index,
        tool_selection_correct=result["tool_selection_correct"],
        parameter_accuracy=result["parameter_accuracy"],
        correctness_category=result["correctness_category"],
        judge_reasoning=result["reasoning"],
    )


# ── Exercise 2: Task-level judge ──────────────────────────────────────────────

# The task-level rubric is deliberately outcome-focused, not process-focused.
# We do not penalise the agent for taking an unexpected path if the final
# response satisfies the success criteria. This is intentional — task-level
# evaluation is about destination, not route. Step-level evaluation handles
# the route assessment.
TASK_JUDGE_SYSTEM = """You are an expert evaluator of AI agent task completion.
You assess whether an agent's final response successfully completed the user's task.

You must respond with a JSON object only — no preamble, no markdown fences.
Required fields:
  goal_completion_score: integer from 1 to 5
  reasoning: explanation of your score (2-4 sentences)

Score rubric — evaluate the FINAL RESPONSE against the SUCCESS CRITERIA only.
Do not penalise the agent for the path it took to get there:
  5 = All success criteria are explicitly and correctly satisfied.
      The response is accurate, complete, and directly addresses the task.
  4 = Most success criteria are satisfied. Minor gaps or imprecision
      that do not affect the core correctness of the response.
  3 = Some success criteria are satisfied but significant gaps remain.
      The response partially addresses the task but a user would need
      to seek additional information.
  2 = The response attempts the task but largely fails to satisfy the
      success criteria. Some relevant information is present but the
      overall answer is incorrect or substantially incomplete.
  1 = The response does not address the task or directly contradicts
      the success criteria."""


def evaluate_task_completion(trajectory: AgentTrajectory) -> Dict:
    # Build a condensed trajectory summary. We truncate reasoning to
    # 100 characters to keep the prompt compact — the judge does not
    # need the full reasoning text, just enough context to understand
    # what the agent attempted at each step.
    trajectory_summary = "\n".join([
        f"Step {s.step_index}: {s.agent_reasoning[:100]}... "
        f"→ Tool: {s.tool_call.tool_name if s.tool_call else 'none'}"
        for s in trajectory.steps
    ])

    user_prompt = f"""Task description: {trajectory.task_description}

Success criteria: {trajectory.success_criteria}

Agent trajectory summary:
{trajectory_summary}

Agent's final response:
{trajectory.final_response}

Evaluate whether the agent successfully completed the task."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=TASK_JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return json.loads(response.content[0].text.strip())


# ── Exercise 3: Full pipeline ─────────────────────────────────────────────────

def evaluate_agent_trajectory(
    trajectory: AgentTrajectory,
    available_tools: List[Dict],
    expected_steps: int,
) -> TaskEvaluation:
    # Step 1: evaluate each step independently.
    step_evals = [
        evaluate_tool_call(trajectory.task_description, step, available_tools)
        for step in trajectory.steps
    ]

    # Step 2: compute step accuracy.
    # We count only "correct" steps, not "partially_correct".
    # Partial credit at the step level is captured in the
    # parameter_accuracy field — step_accuracy is a binary signal.
    correct_steps = sum(
        1 for e in step_evals
        if e.correctness_category == "correct"
    )
    step_accuracy = correct_steps / len(step_evals) if step_evals else 0.0

    # Step 3: evaluate overall task completion.
    task_result = evaluate_task_completion(trajectory)

    # Step 4: compute path efficiency.
    # Capping at 1.0 means "met or beat the expected step count" — we
    # do not reward agents for completing tasks in fewer steps than
    # expected, because a suspiciously short path may indicate the
    # agent skipped required steps rather than being genuinely efficient.
    path_efficiency = min(
        expected_steps / len(trajectory.steps),
        1.0
    ) if trajectory.steps else 0.0

    return TaskEvaluation(
        task_id=trajectory.task_id,
        goal_completion_score=task_result["goal_completion_score"],
        path_efficiency=path_efficiency,
        step_evaluations=step_evals,
        step_accuracy=step_accuracy,
        judge_reasoning=task_result["reasoning"],
    )


# ── Exercise 5: Serialisation ─────────────────────────────────────────────────

def to_run_record(evaluation: TaskEvaluation) -> dict:
    return {
        "task_id": evaluation.task_id,
        "evaluated_at": evaluation.evaluated_at.isoformat(),
        "task_level": {
            "goal_completion_score": evaluation.goal_completion_score,
            "path_efficiency": round(evaluation.path_efficiency, 4),
            "judge_reasoning": evaluation.judge_reasoning,
        },
        "step_level": {
            "step_accuracy": round(evaluation.step_accuracy, 4),
            "steps": [
                {
                    "step_index": e.step_index,
                    "correctness_category": e.correctness_category,
                    "tool_selection_correct": e.tool_selection_correct,
                    "parameter_accuracy": e.parameter_accuracy,
                    "reasoning": e.judge_reasoning,
                }
                for e in evaluation.step_evaluations
            ],
        },
    }


def summarise_run(evaluations: List[TaskEvaluation]) -> dict:
    if not evaluations:
        return {}

    # Collect all step evaluations across the full run.
    all_steps = [
        e for ev in evaluations
        for e in ev.step_evaluations
    ]
    total_steps = len(all_steps)

    # Count each correctness category.
    categories = ["correct", "partially_correct", "wrong_tool", "not_needed"]
    breakdown = {
        cat: sum(1 for s in all_steps if s.correctness_category == cat) / total_steps
        for cat in categories
    } if total_steps else {cat: 0.0 for cat in categories}

    return {
        "mean_step_accuracy": round(
            sum(ev.step_accuracy for ev in evaluations) / len(evaluations), 4
        ),
        "mean_task_score": round(
            sum(ev.goal_completion_score for ev in evaluations) / len(evaluations), 4
        ),
        "mean_path_efficiency": round(
            sum(ev.path_efficiency for ev in evaluations) / len(evaluations), 4
        ),
        "correctness_breakdown": {
            cat: round(v, 4) for cat, v in breakdown.items()
        },
    }


# ── Test trajectory ───────────────────────────────────────────────────────────

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