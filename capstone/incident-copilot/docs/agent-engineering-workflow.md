# Agent engineering workflow

This diagram shows how the **AI Platform Incident Copilot** capstone is structured:
mock incident data feeds a deterministic investigation path, quality gates score and verify
output, and an optional ADK coordinator boundary sits beside the baseline without replacing
it. Versioned engineering artifacts support every stage.

## Workflow diagram

```mermaid
flowchart TB
  subgraph bundle["Mock incident bundle"]
    direction TB
    B1[Incident JSON]
    B2[Logs and metrics]
    B3[Kubernetes events]
    B4[Deployment metadata]
    B5[Runbook snippets]
  end

  subgraph pipeline["Deterministic quality pipeline"]
    direction LR
    MI["Manual Investigator<br/>Load incident<br/>Call mock tools<br/>Collect evidence<br/>Prediction JSON"]
    OCV["Contract Validator<br/>Required fields<br/>Types and structure<br/>Valid output"]
    ER["Eval Runner<br/>Golden answers<br/>Score predictions<br/>Baseline 54 / 54"]
    CR["Critic / Refiner<br/>Evidence support<br/>Safe actions<br/>Rollback reasoning<br/>Bounded loop"]
    FRP["Final Reviewed Prediction<br/>Root cause, confidence<br/>Evidence, actions<br/>Rollback, summary"]
    MI --> OCV --> ER --> CR --> FRP
  end

  subgraph adk["ADK coordinator boundary (optional)"]
    direction TB
    COORD[Coordinator]
    A1[Airflow Investigator]
    A2[Kubernetes Investigator]
    A3["Logs / Metrics Investigator"]
    A4[Runbook Advisor]
    A5["Summary / Safety Agent"]
    LIVE["Live ADK: explicit flag,<br/>optional install, credentials"]
    COORD --> A1
    COORD --> A2
    COORD --> A3
    COORD --> A4
    A1 --> A5
    A2 --> A5
    A3 --> A5
    A4 --> A5
    A5 -.-> LIVE
    DELEG["Default: deterministic delegate"]
    DELEG -.-> COORD
  end

  subgraph artifacts["Versioned engineering artifacts"]
    direction LR
    AR1[Output contract]
    AR2[Prompt templates]
    AR3[Engineering playbook]
    AR4[Tests]
    AR5[Mock tools]
    AR6[Eval harness]
  end

  B1 --> MI
  B2 --> MI
  B3 --> MI
  B4 --> MI
  B5 --> MI
  MI -.-> COORD
  ER -.-> COORD
  artifacts -.-> pipeline

  footer["Local learning project: mock incidents and offline-safe defaults"]
  FRP --> footer
```

## How to read it

**Solid arrows (default path)** follow the deterministic pipeline: mock data enters the
manual investigator, then passes through contract validation, eval scoring, and critic
review before producing a final prediction. This is the acceptance baseline and the path
documented in the demo walkthrough.

**Dashed arrows (guarded optional path)** connect to the ADK coordinator boundary. By
default the coordinator delegates to the same deterministic investigator. Live ADK
execution requires an explicit flag, optional `google-adk` install, and credentials. It
does not silently replace the offline path.

**Validation and evals are quality gates.** The output contract validator checks shape
and required fields. The eval runner scores predictions against golden answers (54 / 54
baseline). Both must pass before critic review is meaningful.

**Critic/refiner is a verification layer, not autonomous remediation.** It performs
deterministic checks on evidence support, action safety, rollback reasoning, and
uncertainty handling. It does not mutate infrastructure, call live LLMs, or execute
remediation actions.

**Versioned engineering artifacts** (contract, prompts, playbook, tests, mock tools, eval
harness) sit alongside the pipeline and define how each stage is built and verified.

## Related docs

* [Demo walkthrough](demo-walkthrough.md)
* [Learning summary](learning-summary.md)
* [Output contract](output-contract.md)
* [Agentic engineering playbook](agentic-engineering-playbook.md)
* [Prompt templates](../prompts/README.md)
