# Manager Demo: AI Platform Incident Copilot

## Demo goal

This document describes a learning capstone for agentic engineering, not production
incident software. The project simulates production-style incident investigation using
mock logs, metrics, Kubernetes events, Airflow status, deployment metadata, and runbook
snippets. It demonstrates safe AI-agent design patterns: bounded tools, structured
outputs, and verification before autonomy. The capstone prioritizes deterministic
baselines, output contracts, evals, and review gates before any live model execution or
production integration.

## One-minute story

We start with a mock incident bundle that looks like the kind of evidence engineers
inspect during an incident. The copilot reads signals from logs, metrics, Kubernetes
events, Airflow status, deployment metadata, and runbook snippets. It produces a
structured diagnosis with likely root cause, supporting evidence, safe next steps,
rollback recommendation, clarifying questions, and a postmortem-style summary. Then the
output is validated, scored, and reviewed by an offline critic/refiner.

## Text visual: how it works

```
+------------------------------+
| Mock incident bundle          |
| logs, metrics, k8s events,    |
| Airflow status, runbooks      |
+---------------+--------------+
                |
                v
+------------------------------+
| Deterministic investigator    |
| parses evidence and produces  |
| a structured diagnosis        |
+---------------+--------------+
                |
                v
+------------------------------+
| Output contract               |
| checks required fields,       |
| types, confidence, structure  |
+---------------+--------------+
                |
                v
+------------------------------+
| Eval runner                   |
| checks expected evidence and  |
| quality against mock cases    |
+---------------+--------------+
                |
                v
+------------------------------+
| Offline critic/refiner        |
| reviews grounding, safety,    |
| rollback, and next steps      |
+------------------------------+
```

Each stage has a clear responsibility. The investigator turns raw mock evidence into a
structured response. The contract enforces shape and required fields so outputs stay
reviewable. Evals compare predictions against golden scenarios so quality does not drift
silently. The critic/refiner adds a final verification pass for grounding, safety, and
consistency without taking production actions.

## Text visual: current demo vs future adaptation

| Layer | Current capstone | Future real-use adaptation |
| --- | --- | --- |
| Input | Mock incident bundle | Read-only incident evidence from approved sources |
| Investigation | Deterministic local logic | Mix of deterministic checks and approved agent skills |
| Output | Structured diagnosis | Incident summary, triage recommendation, handoff notes |
| Safety | Contract, evals, critic/refiner | Policy gates, approvals, audit trail, human-in-the-loop |
| Actions | No production actions | Start with read-only, then draft-only, then approved actions |

Future adaptation should stay cautious. Real systems would add governance, access
controls, and human approval long before any automated remediation.

## What the demo proves

- AI incident copilots should not start with full autonomy.
- Deterministic baselines make quality measurable.
- Contracts make outputs safer and easier to test.
- Evals prevent silent regressions.
- Critic/refiner loops are useful as verification, not autonomous remediation.
- Agent coordination can be modeled without giving the system production access.
- Live execution should remain explicit and guarded.

## Why this design matters

Incident response is high risk. Wrong or hallucinated remediation can make outages worse.
Agents need boundaries: read-only tools, structured outputs, and explicit quality gates.
Structured outputs are easier to validate than free-form chat. Evals and contracts make
the system reviewable by humans and by automated checks. A safe learning capstone can
still reflect real engineering tradeoffs without claiming production readiness.

## How this could adapt to real use cases later

Future adaptation should happen in stages. The capstone does not claim to be ready for
any of these stages today.

**Stage 1: Read-only assistant**

- Reads approved incident context
- Summarizes evidence
- Suggests hypotheses
- Asks clarifying questions
- Takes no actions

**Stage 2: Draft-only assistant**

- Drafts incident summaries
- Drafts Slack updates or postmortem notes
- Drafts runbook-based next steps
- Requires human review of everything

**Stage 3: Guarded workflow assistant**

- Integrates with approved tools
- Requires explicit approval for risky actions
- Logs all recommendations and decisions
- Uses stronger evals and policy gates

**Stage 4: Limited approved actions**

- Only low-risk actions
- Only after human approval
- Only with audit trail
- Only after strong testing and operational review

This capstone currently stays before Stage 1 in a real environment, or at a local
simulated Stage 1 with mock data only.

## What I would show in a live demo

1. **Mock incident bundle.** Show what evidence looks like: incident metadata, log
   excerpts, metrics, Kubernetes events, Airflow status, deployment history, and runbook
   snippets. Emphasize that all data is mock and public-safe.

2. **Structured output shape.** Walk through the diagnosis fields: root cause, confidence,
   evidence citations, clarifying questions, safe next steps, rollback recommendation,
   and incident summary.

3. **Validation layer.** Show how the output contract checks required fields, types, and
   structure before anything is treated as acceptable.

4. **Eval result.** Show how predictions are scored against golden scenarios across
   dimensions such as root cause accuracy, evidence quality, and action safety.

5. **Critic/refiner review.** Show the offline quality gate that reviews grounding,
   safety, rollback guidance, and consistency without calling live models or mutating
   infrastructure.

6. **Optional coordinator and specialist boundary.** Explain that the project models a
   coordinator routing work to domain specialists (Airflow, Kubernetes, logs/metrics,
   runbooks), but the default acceptance path remains deterministic.

7. **What is intentionally not automated.** Call out that there is no production
   remediation, no live cluster access, and no silent fallback to autonomous action.

## Optional agentic boundary

The project includes an ADK-style coordinator and specialist topology, but the default
quality gate remains deterministic.

Default path:

```
mock incident -> deterministic investigator -> contract -> eval -> critic/refiner
```

Optional boundary:

```
coordinator -> specialists -> summary/safety review
              |
              v
       deterministic quality gate remains central
```

The coordinator describes how a future LLM orchestrator could route investigation work.
Specialists are scoped to one signal domain each. Even when live execution is enabled
behind an explicit flag, the deterministic baseline and eval score remain the acceptance
reference.

## What is intentionally out of scope

- No production remediation
- No cloud credentials
- No private operational data
- No automatic rollback
- No live tool execution by default
- No unsupported production-readiness claims
- No dependency or deployment expansion for this demo

## Expected manager questions

**Is this production-ready?**

No. It is a local learning capstone with mock data, deterministic baselines, and
offline verification. It demonstrates engineering discipline, not on-call readiness.

**What would be needed before using this with real incidents?**

Approved read-only data sources, access controls, policy gates, human-in-the-loop review,
stronger evals on real incident shapes, operational ownership, and a staged rollout
starting with read-only assistance only.

**Why not connect it directly to logs and Kubernetes?**

Direct production access increases risk before the investigation and safety layers are
proven. The capstone separates architecture design from integration so contracts, evals,
and verification can mature first.

**Why deterministic first?**

Deterministic logic is reproducible, debuggable, and scoreable. It establishes a baseline
so later model or agent changes can be compared objectively instead of judged by
impression alone.

**Where would an LLM add value?**

Likely in routing ambiguity, synthesizing narrative summaries, proposing clarifying
questions, and drafting handoff notes, always within contract-shaped outputs and under
human review. The capstone models that boundary without making live models the default
gate.

**How do we prevent unsafe recommendations?**

Through structured outputs, evals that penalize unsafe actions, a critic/refiner
verification stage, read-only tools, no default production actions, and explicit human
approval for anything beyond drafts.

**What is the smallest useful real-world version?**

A read-only assistant that ingests approved incident context, cites evidence, suggests
hypotheses, asks clarifying questions, and drafts a summary for human review. No
automated remediation and no write access to infrastructure.

## Related docs

- [Demo walkthrough](./demo-walkthrough.md)
- [Learning summary](./learning-summary.md)
- [Agent engineering workflow](./agent-engineering-workflow.md)
- [Agentic engineering capstone mapping](./agentic-engineering-capstone-mapping.md)
- [Agentic engineering playbook](./agentic-engineering-playbook.md)
- [Output contract](./output-contract.md)
