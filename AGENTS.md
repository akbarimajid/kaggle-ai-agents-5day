# Agent Instructions

This repository is a public learning portfolio for the Google/Kaggle 5-Day AI Agents
course.

The main capstone is:

`capstone/incident-copilot/`

## Operating model

Use vibe coding as the development workflow, but treat the capstone as an agentic
engineering project.

The goal is not to generate code quickly. The goal is to build a testable, reviewable,
public-safe AI Platform Incident Copilot.

Read before making capstone changes:

* `capstone/incident-copilot/README.md`
* `capstone/incident-copilot/docs/agentic-engineering-playbook.md`
* `capstone/incident-copilot/docs/output-contract.md`

## Capstone roadmap

Current sequence:

1. Foundation: mock data, deterministic tools, output contract, eval harness
2. Deterministic manual investigator
3. ADK coordinator and specialist agent topology
4. Agentic engineering playbook
5. Output contract validator
6. Versioned agent prompt templates
7. Optional live ADK execution behind a flag
8. Critic/refiner loop

Do not skip quality gates to jump to live LLM behavior.

## Engineering rules

* Keep the deterministic baseline working.
* Do not reduce the current eval score without an explicit reason.
* Preserve the output contract unless the contract is deliberately versioned.
* Tests must not require live API keys.
* Live ADK or LLM execution must stay optional until explicitly scoped.
* Keep generated predictions untracked.
* Do not commit runtime artifacts such as `__pycache__/` or `*.pyc`.
* Do not commit secrets, credentials, billing info, project IDs, or private operational
  details.
* Keep changes small and PR-scoped.
* Prefer stdlib-only code unless a dependency is explicitly approved.

## Review expectations

Every capstone PR should explain:

* what changed
* why it matters
* which contract or quality gate it preserves
* commands run
* test result
* eval score, when applicable
* public-safety and hygiene confirmation

## Portfolio goal

This repo should show disciplined AI-assisted engineering for:

* AI platform engineering
* MLOps
* DevOps/SRE
* GenAI platform roles

The strongest story is: AI accelerates implementation, but human judgment defines
architecture, constraints, verification, and merge decisions.
