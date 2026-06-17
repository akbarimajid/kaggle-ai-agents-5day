# Learning summary

Personal notes from building the **AI Platform Incident Copilot** capstone during the
Google / Kaggle 5-Day AI Agents course. This is a learning project with mock data and
local deterministic tools, not production incident software.

## What this capstone is

A small multi-agent *design* for investigating platform incidents: correlate mock
Airflow, Kubernetes, logs, metrics, and runbook signals, then produce an evidence-backed
diagnosis with safe next steps and an auditable summary.

v0 proves the harness (data, tools, contract, evals, deterministic baseline) before
trusting any live model.

## What I built

* Three mock incident scenarios (`INC-001` to `INC-003`) with golden answers
* Read-only mock tools over files in `data/`
* A deterministic manual investigator that scores **54 / 54** on the eval harness
* Output contract validator and eval runner
* Versioned prompt templates for coordinator, specialists, and summary/safety agents
* ADK coordinator boundary describing orchestrator + specialist + sequential topology
* Optional live ADK execution behind an explicit flag (not used in tests)
* Deterministic critic/refiner quality gate (offline, no live LLM)

The runnable demo path is documented in [demo-walkthrough.md](demo-walkthrough.md).
See also the [agent engineering workflow](agent-engineering-workflow.md) diagram.

## How the system works

```text
Alert / incident JSON
    -> read-only tools (logs, metrics, k8s, airflow, runbooks)
    -> investigation (manual_investigator or ADK delegate)
    -> output contract (root_cause, evidence, actions, ...)
    -> contract validator + eval runner + critic/refiner
    -> optional ADK topology / live mode (explicit opt-in)
```

The manual investigator is the acceptance baseline. The ADK layer describes how a future
LLM orchestrator would route work to specialists, but default execution still delegates
to the deterministic path.

## Lessons from Day 1

Day 1 contrasted **vibe coding** (fast AI-assisted iteration) with **agentic
engineering** (contracts, tests, evals, and review discipline).

What stuck with me:

* Generation is cheap; judgment about scope, architecture, and verification is not.
* "Looks good" is not a quality gate. Unit tests and eval scores are.
* Small, reviewable PRs preserve a working baseline better than big jumps toward live
  agents.
* Public-safe mock data lets me iterate without credentials, billing, or production risk.

I used vibe coding to draft code and docs, but I treated merge decisions and architecture
as mine. The playbook in `docs/agentic-engineering-playbook.md` captures that operating
model for this repo.

## Lessons from Day 2

Day 2 emphasized **tools and interoperability** as architecture guidance: bounded tool
access, clear agent responsibilities, and safety boundaries instead of ad-hoc wrappers
for every integration.

For this capstone that translated to:

* Mock tools with explicit contracts in `docs/tool-contracts.md`
* Read-only, file-backed implementations (no cluster mutations in v0)
* Specialist agents scoped to one signal domain each
* Thinking about MCP-style tool boundaries even though v0 does not implement MCP servers

The point was not to wire every protocol. It was to design the system so external tools
and agents could plug in later without rewriting the core harness.

## Why deterministic first

I built the deterministic manual investigator and eval harness before leaning on live
LLMs because:

1. **Evidence before opinions** - The capstone promise requires cited telemetry. Tools
   had to return reproducible data first.
2. **Eval-first** - Golden scenarios define "done" before model behavior drifts the
   goalposts.
3. **Debuggability** - When something fails, I can separate bad mock data, bad routing,
   and bad reasoning.
4. **Offline learning** - Anyone can clone the repo and get 54 / 54 without API keys.

The ADK topology sits *beside* this baseline; it does not replace it.

## Why contracts and evals matter

The output contract (`docs/output-contract.md`) forces every response to include root
cause, confidence, evidence citations, safe actions, rollback guidance, clarifying
questions, and a summary. That shape is what makes output reviewable and machine-checkable.

Evals in `evals/golden-answers.json` turn qualitative incident work into nine scored
dimensions per scenario. They caught regressions when I added validators, prompts, and
the critic layer.

Without contract + evals, I would have no objective way to know whether a change helped.

## Why prompt templates are versioned

Agent instructions live under `prompts/` as versioned markdown files, not hidden strings
in code. That matches how I want to evolve coordinator and specialist behavior: diffable
prompts, explicit roles, and alignment with the topology in `adk_agents.py`.

Templates are ready for optional live ADK runs; they are not required for the
deterministic demo.

## Why live execution is guarded

Live ADK mode requires:

* Explicit `--execution-mode live-adk`
* Optional `google-adk` install
* Credentials such as `GOOGLE_API_KEY` or `GEMINI_API_KEY`

If ADK or credentials are missing, the CLI fails with a clear error and does **not**
silently fall back to deterministic mode. Tests never call live models.

That guardrail keeps the public repo honest: the default path is reproducible; live
experiments are intentional.

## Why critic/refiner is offline first

The critic/refiner is a deterministic quality gate, not an autonomous remediation loop.
It checks contract validity, evidence support, unsafe action phrases, rollback guidance,
confidence consistency, and specialist usage.

I wanted a review stage I could run in CI and locally without API cost or nondeterminism.
Live LLM critique might come later; the offline gate already adds useful signal (and
currently approves the manual investigator predictions with occasional summary warnings).

## Current limits

Intentionally mock-only or deferred in v0:

* No live Airflow, Kubernetes, or cloud APIs
* No production UI, auth, or paging integrations
* No automated remediation or write operations against infrastructure
* No deployment or cloud billing setup in this repo
* Live LLM execution is optional and not part of test or eval gates
* Three incidents only; not a general incident platform

The capstone demonstrates agentic *engineering discipline* on a small surface, not
on-call production readiness.

## Possible next explorations

Bounded ideas I might try later, not commitments:

* Add more mock incident scenarios and extend golden answers
* Tighten critic rules (for example summary grounding warnings on INC-001 and INC-002)
* Try live ADK manually with a throwaway local API key and compare outputs to the
  deterministic baseline
* Add a small architecture diagram to the docs
* Fold in Day 3 course concepts after reviewing that material

Each exploration should preserve the current eval gate unless the contract is deliberately
versioned.

## Related docs

* [Incident Copilot demo](incident-copilot-demo.md) - conceptual demo narrative (no commands)
* [Demo walkthrough](demo-walkthrough.md)
* [Agentic engineering playbook](agentic-engineering-playbook.md)
* [Day 2 tools brief](agentic-engineering-day-2-tools-interoperability.md)
* [Day 3 agent skills notes](agentic-engineering-day-3-agent-skills-notes.md)
* [Capstone README](../README.md)
