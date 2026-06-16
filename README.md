# Kaggle AI Agents 5-Day Course

Public learning repository for the **Google / Kaggle 5-Day AI Agents Intensive Course**.

This repository contains my notes, exercises, small experiments, and reflections while following the course. It is intended as a clean learning log, not a mirror of the original course materials.

Original course content, codelabs, notebooks, and other materials belong to Google, Kaggle, and their respective authors.

## Purpose

The goal of this repository is to document practical learning around AI agents, AI-assisted development workflows, and deployment-oriented experimentation.

This repo focuses on:

* Daily learning notes
* Course exercise summaries
* Small implementation experiments
* Reflections on what worked and what did not
* Reusable patterns and engineering takeaways
* Public-safe documentation of progress

## Topics

The course and related exercises may involve:

* AI agents
* Vibe coding
* Agentic engineering
* Prompting and tool use
* AI-assisted software development
* Google AI tools
* Cloud-based deployment workflows
* Evaluation, constraints, and safety guardrails

## Repository Structure

```text
kaggle-ai-agents-5day/
|-- README.md
|-- capstone/
|   `-- incident-copilot/
|-- day-1/
|   `-- README.md
|-- notes/
|   |-- day-1-learning-log.md
|   |-- day-1-new-sdlc-summary.md
|   |-- day-1-visuals-to-recreate.md
|   `-- day-1b-agent-architectures.md
`-- scratch/
    `-- .gitkeep
```

## Capstone status

This repo uses **vibe coding** as the development workflow: AI-assisted iteration with explicit guardrails, eval gates, and public-safe documentation.

The capstone demonstrates **agentic engineering for AI platform operations**: multi-agent incident investigation over mock Airflow, Kubernetes, logs, metrics, and runbooks.

| PR | Capability | Focus |
|----|------------|-------|
| #1 | Foundation | Mock incident data, deterministic tools, contracts, eval harness |
| #2 | Deterministic baseline | End-to-end manual investigator (54 / 54 eval score) |
| #3 | Agent topology | ADK coordinator and specialist agent topology (offline-safe; no live LLM in tests) |

**Project:** [AI Platform Incident Copilot](capstone/incident-copilot/)

**Demo:** [Walkthrough](capstone/incident-copilot/docs/demo-walkthrough.md) |
[Learning summary](capstone/incident-copilot/docs/learning-summary.md)

**Career alignment:** AI platform engineering, MLOps, DevOps/SRE, and GenAI platform roles.

## Day 1: From Vibe Coding to Agentic Engineering

* [Day 1 SDLC summary](notes/day-1-new-sdlc-summary.md)
* [Day 1 visuals to recreate](notes/day-1-visuals-to-recreate.md)
* [Agentic engineering capstone mapping](capstone/incident-copilot/docs/agentic-engineering-capstone-mapping.md)
* [Incident copilot output contract](capstone/incident-copilot/docs/output-contract.md)

## Daily Progress

| Day   | Focus                  | Status      |
| ----- | ---------------------- | ----------- |
| Day 1 | Introduction and setup | In progress |
| Day 2 | [Tools and interoperability](capstone/incident-copilot/docs/agentic-engineering-day-2-tools-interoperability.md) | Documented |
| Day 3 | TBD                    | Not started |
| Day 4 | TBD                    | Not started |
| Day 5 | TBD                    | Not started |

## Learning Log Format

Each day should capture:

```text
What I built:
-

Tools used:
-

Key concepts:
-

What confused me:
-

What I changed or experimented with:
-

What I can reuse later:
-

Risks and guardrails:
-
```

## Attribution

This repository is my personal learning workspace for the Google / Kaggle 5-Day AI Agents course.

Original course materials are owned by Google, Kaggle, and the relevant course authors. This repository contains only my own notes, experiments, and learning artifacts.
