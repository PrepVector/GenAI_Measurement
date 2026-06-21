# Chapter 3: Designing and Running Offline Experiments

This chapter covers evaluation for the two most common GenAI
architectures in production: RAG pipelines and agentic systems.

## Hands-on exercises

### Section 2 — Reference-free evaluation and freshness monitoring
Folder: `hands_on/section_2_freshness_pipeline/`

Build a freshness monitoring pipeline that tracks staleness rates
per domain, raises alerts when thresholds are breached, and
serialises results into the eval run record.

### Section 3 — Evaluating agents
Folder: `hands_on/section_3_agent_evaluator/`

Build an end-to-end agent evaluation pipeline that scores
individual tool calls (step-level) and overall task completion
(task-level), and produces a structured eval run record.

## Prerequisites

- Completed Chapter 2 hands-on exercises, or familiarity with the
  eval run record format from Chapter 2 Section 5
- Python 3.9+
- Anthropic API key