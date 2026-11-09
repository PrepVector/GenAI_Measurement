# Chapter 9: Multi-Armed Bandits and Advanced Experiment Designs

This chapter covers experiment designs for questions a standard A/B test
handles poorly: choosing among many candidates (bandits), matching options
to queries (contextual bandits and off-policy evaluation), comparing rankers
(interleaving), comparing answers (preference testing) and finding out
whether components interact (factorial designs).

## Hands-on exercises

### Section 1 — Thompson Sampling for model selection (Exercises 1–3)
Folder: `hands_on/bandit_model_selection/`

Simulate the five-model routing scenario from Section 1 and compare a
uniform split, Thompson Sampling, and Thompson Sampling with an exploration
floor. Explore the price of the floor, what happens when the leading models
tie, and how delayed feedback raises regret.

### Sections 2–4 — Design calculators (Exercises 4–6)
Folder: `hands_on/design_calculators/`

Three short calculations that put numbers on the designs: the completion
rate of a routing policy (Section 2), the sample size of a preference test
(Section 4) and the saving from interleaving (Section 3).

## Prerequisites

- Familiarity with the Beta-Binomial update from Section 1.3
- Python 3.9+
- NumPy (`pip install -r requirements.txt` from the repo root)
- No Anthropic API key required
