# The GenAI Measurement Playbook
### Practical Causal Inference and Experimentation Methods from Prototype to Production

This repository contains the hands-on code exercises for the book
*The GenAI Measurement Playbook* by Minha Hwang and Manisha Arora,
published by Packt Publishing.

## How this repo is organised

Each chapter that contains a hands-on exercise has its own folder.
Inside each chapter folder you will find:

- `README.md` — overview of the chapter's exercises and prerequisites
- `hands_on/` — one subfolder per exercise, each containing:
  - `*_starter.py` — the file you work from (functions stubbed with TODOs)
  - `*_solution.py` — the reference solution (consult after attempting)
  - `tests/` — pytest tests to validate your implementation

## Getting started

1. Clone the repo:
```bash
   git clone https://github.com/GenAIMeasurementPlaybook/playbook.git
   cd playbook
```

2. Create and activate a virtual environment:
```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
   pip install -r requirements.txt
```

4. Set your Anthropic API key:
```bash
   cp .env.example .env
   # Edit .env and add your key
   export ANTHROPIC_API_KEY=your_key_here
```

5. Navigate to the exercise you want to work on and run the tests:
```bash
   cd chapter_03/hands_on/section_3_agent_evaluator
   pytest tests/ -v
```

## Chapter index

| Chapter | Topic | Exercise |
|---------|-------|----------|
| Chapter 2 | Offline metric design | Freshness monitor, eval run record |
| Chapter 3 | Offline experiments | Agent evaluation pipeline |

## A note on solutions

The solution files are in this repo, but we encourage you to attempt
each exercise before opening them. The process of writing and
calibrating the judge prompts — and debugging them when they
produce unexpected results — is itself a core skill the book teaches.

## Requirements

- Python 3.9 or above
- An Anthropic API key (sign up at console.anthropic.com)