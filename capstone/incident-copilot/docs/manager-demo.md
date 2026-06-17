# Manager Demo: AI Platform Incident Copilot

## Demo goal

This is a local learning capstone for agentic engineering. It is not production incident
software. The project simulates production-style investigation using mock logs, metrics,
Kubernetes events, Airflow status, deployment metadata, and runbook snippets. It shows
how to design an AI incident copilot with bounded tools, structured outputs, and
verification before autonomy. Deterministic baselines, output contracts, evals, and
review gates come first. Live model execution and production integration stay optional and
explicit.

## One-minute story

We start with a mock incident bundle that looks like the kind of evidence engineers
inspect during an incident. The copilot reads signals from logs, metrics, Kubernetes
events, Airflow status, deployment metadata, and runbook snippets. It produces a
structured diagnosis with likely root cause, supporting evidence, safe next steps,
rollback recommendation, clarifying questions, and a postmortem-style summary. Then the
output is validated, scored, and reviewed by an offline critic/refiner.

## Text visual: how it works

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

The investigator turns mock evidence into a structured response. The contract keeps outputs
reviewable. Evals compare results to golden scenarios so quality does not drift silently.
The critic/refiner adds a final verification pass without taking production actions.

## Text visual: current capstone vs future adaptation

| Layer | Current capstone | Future real-use adaptation |
| --- | --- | --- |
| Input | Mock incident bundle | Read-only incident evidence from approved sources |
| Investigation | Deterministic local logic | Mix of deterministic checks and approved agent skills |
| Output | Structured diagnosis | Incident summary, triage recommendation, handoff notes |
| Safety | Contract, evals, critic/refiner | Policy gates, approvals, audit trail, human-in-the-loop |
| Actions | No production actions | Start with read-only, then draft-only, then approved actions |

Future adaptation should stay cautious. Real systems need governance, access controls, and
human approval long before any automated remediation.

## What the demo proves

- AI incident copilots should not start with full autonomy.
- Deterministic baselines make quality measurable.
- Contracts make outputs safer and easier to test.
- Evals prevent silent regressions.
- Critic/refiner loops are useful as verification, not autonomous remediation.
- Agent coordination can be modeled without giving the system production access.
- Live execution should remain explicit and guarded.

## Why this design matters

Incident response is high risk. Hallucinated remediation can make outages worse. Agents
need boundaries: read-only tools, structured outputs, and explicit quality gates.
Structured outputs are easier to validate than free-form chat. Evals and contracts make
the system reviewable. A local learning capstone can still reflect real engineering
tradeoffs without claiming production readiness.

## How this could adapt to real use cases later

Adaptation should happen in stages. This capstone does not claim to be ready for any stage
in a real environment today.

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

**Stage 4: Limited approved actions with human approval and audit trail**

- Only low-risk actions
- Only after human approval
- Only with a full audit trail
- Only after strong testing and operational review

Today the capstone stays before Stage 1 in a real environment. Locally it simulates
read-only assistance with mock data only.

## What to walk through in a demo

Present the capstone as a concept, not as a runbook.

1. **Incident evidence.** Describe the mock bundle: metadata, logs, metrics, Kubernetes
   events, Airflow status, deployment history, and runbook snippets. Stress that all
   data is mock and public-safe.

2. **Structured diagnosis.** Explain the output fields: root cause, confidence, evidence
   citations, clarifying questions, safe next steps, rollback recommendation, and incident
   summary.

3. **Validation.** Explain how the output contract checks required fields, types, and
   structure before a response counts as acceptable.

4. **Scoring.** Explain how results are compared to golden scenarios on root cause,
   evidence quality, and action safety.

5. **Review gate.** Explain the offline critic/refiner pass for grounding, safety,
   rollback guidance, and consistency. No live models and no infrastructure changes.

6. **Agent topology (optional).** Note that a coordinator can route work to domain
   specialists, but the default acceptance path stays deterministic.

7. **Boundaries.** State clearly what is not automated: production remediation, live
   cluster access, and silent autonomous action.

## Optional agentic boundary

The project models a coordinator and specialist topology, but the default quality gate
remains deterministic.

Default path:

    mock incident -> deterministic investigator -> contract -> eval -> critic/refiner

Optional boundary:

    coordinator -> specialists -> summary/safety review
                  |
                  v
           deterministic quality gate remains central

The coordinator shows how a future orchestrator could route investigation work.
Specialists stay scoped to one signal domain each. Any optional live model path still
defers to the deterministic baseline and eval score for acceptance.

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

No. It is a local learning capstone with mock data, deterministic baselines, and offline
verification. It demonstrates engineering discipline, not on-call readiness.

**What would be needed before using this with real incidents?**

Approved read-only data sources, access controls, policy gates, human-in-the-loop review,
stronger evals on real incident shapes, operational ownership, and a staged rollout
starting with read-only assistance only.

**Why not connect it directly to logs and Kubernetes?**

Direct production access adds risk before investigation and safety layers are proven. The
capstone matures contracts, evals, and verification first, then integration later.

**Why deterministic first?**

Deterministic logic is reproducible, debuggable, and scoreable. It sets a baseline so
later model or agent changes can be compared objectively.

**Where would an LLM add value?**

In routing ambiguity, synthesizing summaries, proposing clarifying questions, and drafting
handoff notes, always within contract-shaped outputs and under human review. Live models
are optional here, not the default gate.

**How do we prevent unsafe recommendations?**

Structured outputs, evals that penalize unsafe actions, a critic/refiner verification
stage, read-only tools, no default production actions, and explicit human approval for
anything beyond drafts.

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
