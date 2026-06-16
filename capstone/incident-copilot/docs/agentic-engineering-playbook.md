# Agentic Engineering Playbook for the Incident Copilot

Status: Active
Scope: AI Platform Incident Copilot capstone
Source: Day 1 learning, The New SDLC With Vibe Coding, and capstone implementation
experience

## Purpose

This document defines how the AI Platform Incident Copilot applies the Day 1 lessons
from vibe coding, structured AI-assisted coding, and agentic engineering.

The capstone uses vibe coding as the development workflow, but the system itself is an
agentic engineering project.

That means the goal is not only to generate code quickly. The goal is to build a
reliable, testable, reviewable, and extensible agent system for AI platform operations.

## Core lesson

Generation is no longer the scarce skill.

The scarce skills are:

* intent specification
* architecture judgment
* context design
* guardrail design
* verification
* review discipline
* safe iteration

For this capstone, every agentic feature must be designed around contracts, tests,
evals, and human review before it is treated as reliable.

## Vibe coding vs agentic engineering in this project

| Dimension | Vibe coding behavior | Agentic engineering behavior |
| --- | --- | --- |
| Intent | Casual prompt to generate code | Explicit task prompt with scope and review gates |
| Verification | "Looks good" manual check | Unit tests, eval score, contract validation |
| Code ownership | AI writes, developer skims | Developer owns architecture and merge decision |
| Context | Chat history only | Versioned docs, contracts, mock data, README notes |
| Error handling | Paste error back to AI | Diagnose root cause, constrain fix, re-run tests |
| Scope | Fast prototype | Production-style learning artifact with public quality |
| Risk | Hidden breakage accepted | Generated files, secrets, Unicode, and drift blocked |

## Capstone operating principle

Structure scales. Vibes do not.

The Incident Copilot should evolve through small, reviewable layers:

1. Data, tools, contracts, and evals
2. Deterministic end-to-end investigator
3. ADK coordinator and specialist topology
4. Live agent execution behind the same contract
5. Critic/refiner loop
6. Reporting, observability, and portfolio polish

Each layer must preserve the quality gate from the previous layer.

## Current architecture interpretation

The Incident Copilot maps directly to the Day 1 agentic engineering models.

### 1. Context engineering

The system separates static and dynamic context.

Static context:

* output contract
* incident schema
* mock tool contracts
* architecture docs
* agent role definitions
* guardrails
* eval criteria

Dynamic context:

* selected incident bundle
* logs
* metrics
* Kubernetes events
* deployment metadata
* runbook snippets
* tool outputs

Design rule:

Static context should live in versioned repo files. Dynamic context should be loaded at
runtime from mock incident data and tools.

### 2. Factory model

The developer does not only produce code. The developer designs the factory that
produces code.

In this project:

* ChatGPT defines product and engineering direction.
* Cursor or another coding agent implements scoped tasks.
* Tests and evals verify output.
* Human review approves or rejects PRs.
* Repo docs preserve decisions and constraints.

Design rule:

Every agent task must include scope boundaries, validation commands, expected outputs,
and public-safety checks.

### 3. Conductor and orchestrator modes

The project uses both modes.

Conductor mode:

* small code edits
* README cleanup
* test fixes
* output contract adjustments
* quick deterministic implementation changes

Orchestrator mode:

* full PR tasks
* multi-file changes
* agent topology work
* eval harness improvements
* structured implementation plans

Design rule:

Use conductor mode for narrow fixes. Use orchestrator mode for PR-level work with
explicit acceptance criteria.

### 4. Harness anatomy

The model is not the product. The harness is the product.

For this capstone, the harness includes:

* incident input bundles
* deterministic tools
* output contract
* eval runner
* specialist agent definitions
* coordinator boundary
* tests
* README commands
* safety and hygiene checks

Design rule:

Do not treat the LLM as reliable by default. Reliability comes from the harness around
it.

## Non-negotiable engineering guardrails

The capstone must preserve these rules:

1. The deterministic baseline must stay working.
2. Existing eval score must not regress without an explicit reason.
3. Tests must not require live API keys.
4. Generated predictions must not be committed.
5. Runtime artifacts must not be committed.
6. No secrets, credentials, billing data, project IDs, or private operational details.
7. ADK and LLM execution must be optional until the offline harness is stable.
8. Public repo readability matters.
9. Every PR must explain scope, validation, eval score, and safety checks.
10. Future agent work must keep the same output contract unless deliberately versioned.

## How this applies to the next implementation stages

### Stage 1: Foundation

Status: Done

Implemented:

* mock incident data
* deterministic mock tools
* output contract
* eval harness
* public-safe README updates

Engineering lesson:

Before building agents, define what correct output looks like.

### Stage 2: Deterministic investigator

Status: Done

Implemented:

* manual investigator
* CLI commands
* contract-valid predictions
* eval score 54 / 54
* unit tests

Engineering lesson:

Before trusting an LLM, prove that the workflow can be solved deterministically.

### Stage 3: ADK coordinator and specialist topology

Status: Done

Goal:

Add agentic structure without introducing live-model risk.

Expected result:

* IncidentCoordinatorAgent
* AirflowInvestigatorAgent
* KubernetesInvestigatorAgent
* LogsMetricsInvestigatorAgent
* RunbookAdvisorAgent
* SummarySafetyAgent
* offline-safe tests
* deterministic delegate preserved

Engineering lesson:

Architecture comes before autonomy.

### Stage 4: Live ADK execution

Status: Future

Goal:

Allow the coordinator and specialists to perform live LLM-backed reasoning behind the
same output contract.

Required before implementation:

* stable offline topology
* prompt templates
* model configuration guardrails
* no live credentials in tests
* deterministic fallback
* golden incident evals

Engineering lesson:

Live LLM behavior must be introduced behind a tested boundary, not mixed directly into
the baseline.

### Stage 5: Critic/refiner loop

Status: Done (deterministic, offline-safe)

Goal:

Add a review agent that checks diagnosis quality before final output.

The critic should check:

* evidence coverage
* root cause consistency
* rollback safety
* missing clarifying questions
* whether recommended actions are safe
* whether confidence is justified

Implementation:

* `critic_refiner.py` — deterministic `critique_prediction`, `refine_prediction`,
  and bounded `run_critic_refiner(max_iterations=1)` (no live LLM)
* Optional `--with-critic` on `adk_coordinator` attaches a quality report without
  changing the default prediction
* Manual investigator (54 / 54) remains the acceptance gate

Engineering lesson:

Agentic systems need verification agents, not just generation agents.

## Review checklist for every future PR

A PR is not merge-ready until it answers:

1. What capability did this add?
2. Which contract does it preserve or change?
3. Which tests prove it works?
4. What is the eval score?
5. Does it require live credentials?
6. Did it add new dependencies?
7. Are generated files excluded?
8. Are runtime artifacts excluded?
9. Is the scope limited to the stated task?
10. Does this improve the portfolio story for AI platform, MLOps, DevOps/SRE, or GenAI
    roles?

## Career positioning

This capstone should be described as:

An AI-assisted engineering project that builds an AI Platform Incident Copilot using
agentic engineering practices.

The project demonstrates:

* AI platform incident reasoning
* tool-using agent design
* multi-agent coordination
* output contracts
* deterministic baselines
* eval-driven development
* public-safe engineering discipline
* MLOps and SRE-oriented workflows
* readiness for GenAI platform engineering roles

The key message:

I used vibe coding techniques to accelerate development, but I applied agentic
engineering discipline to make the result testable, reviewable, and portfolio-grade.

## Related docs

* [agentic-engineering-capstone-mapping.md](./agentic-engineering-capstone-mapping.md) - Day 1 and Day 2 theory to capstone mapping
* [agentic-engineering-day-2-tools-interoperability.md](./agentic-engineering-day-2-tools-interoperability.md) - Day 2 concepts and glossary
* [output-contract.md](./output-contract.md) - response fields and eval mapping
* [architecture.md](./architecture.md) - multi-agent design
* [notes/day-1-new-sdlc-summary.md](../../notes/day-1-new-sdlc-summary.md) - Day 1 concepts
* [notes/day-1b-agent-architectures.md](../../notes/day-1b-agent-architectures.md) - ADK workflow patterns
