# Day 1: The New SDLC With Vibe Coding

Concise public-safe learning notes from the Google / Kaggle 5-Day AI Agents course, Day 1 paper.

## Executive summary

* Development is shifting from writing syntax to expressing **intent** that AI systems translate into working software.
* **Vibe coding** suits fast prototypes; **agentic engineering** adds structure, verification, and constraints for production.
* **Context engineering** matters more than clever prompts — structured instructions, knowledge, tools, and examples guide reasoning.
* The **harness** (tools, sandbox, orchestration, guardrails, observability) often matters more than the model alone.
* Reliability combines **deterministic tests** with **evals** that score non-deterministic agent trajectories and outputs.
* Developers act as **conductors** (hands-on IDE direction) or **orchestrators** (delegating async goals to agents).
* Production agents need governed tool access, memory, and deployable infrastructure — not one-off scripts.
* The **factory model** treats the developer as a system designer of pipelines, gates, and loops rather than a manual coder.
* Human value moves toward judgment, architecture, verification, and safety — especially for the hard final 20% of tasks.

## Key concepts

| Concept | Meaning | Why it matters |
|---------|---------|----------------|
| **Agent loop** | Perceive → plan → act → observe (iterate until done) | Enables self-correction beyond one-shot chat |
| **Model** | LLM reasoning engine | Drives decisions at each loop step |
| **Tools** | Callable interfaces to logs, metrics, APIs, scripts | Connects reasoning to real systems |
| **Memory** | Retained state across steps or sessions | Avoids starting from zero each turn |
| **Orchestration** | Logic routing agents, tools, and termination | Assembles context and controls flow |
| **Deployment** | Hosting the agent as a service | Moves prototype to shared production use |
| **Context engineering** | Structured static + dynamic information for the model | Higher leverage than prompt tricks |
| **Harness** | Scaffolding around the model (rules, tools, logs, evals) | Shapes most observable agent behavior |
| **Guardrails** | Hard limits on unsafe actions | Required for autonomous tools in prod |
| **Observability** | Traces of reasoning, tool calls, costs | Makes agent decisions auditable |
| **Tests** | Deterministic input/output checks | Validates parsers, tools, contracts |
| **Evals** | Scoring quality of reasoning and outputs | Measures non-deterministic behavior |
| **Conductor mode** | Real-time IDE collaboration with the agent | Best for exploratory work |
| **Orchestrator mode** | Delegate goals; review results async | Higher leverage for routine workflows |
| **Factory model** | Design the assembly line, not every widget | Reframes dev as pipeline architecture |

## Public source note

These notes are **original summaries** for a public learning portfolio. They reflect concepts from the course paper *Day 1: The New SDLC With Vibe Coding* (Addy Osmani, Shubham Saboo, Sokratis Kartakis). Original course materials remain property of their authors. This file does not reproduce long passages, figures, or transcripts from the source.

**Related repo notes:** [day-1b-agent-architectures.md](./day-1b-agent-architectures.md) · [day-1-learning-log.md](./day-1-learning-log.md)
