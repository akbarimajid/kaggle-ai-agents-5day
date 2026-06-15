# AI Platform Incident Copilot

**One-line pitch:** A multi-agent copilot that investigates platform incidents, cites evidence from mock telemetry, and recommends safe next steps with an auditable incident summary.

## Problem statement

Platform engineers investigating Airflow, Kubernetes, and data-pipeline incidents must correlate signals across logs, metrics, deployment history, and runbooks under time pressure. Manual triage is slow, error-prone, and often skips evidence citation. This capstone explores whether a **specialist multi-agent system** can produce **evidence-backed diagnoses** and **safe remediation guidance** without connecting to real production systems in v0.

## Target user

Platform engineer / SRE / MLOps engineer on-call for data orchestration and batch workloads.

## v0 scope

* Architecture and agent design documentation
* Mock incident scenarios (`INC-001` to `INC-003`)
* Fake logs, metrics, Kubernetes events, Airflow status, runbooks, deployment metadata
* Deterministic mock tools, eval harness, and golden answers
* Deterministic manual investigator baseline (PR #2)
* ADK coordinator and specialist topology boundary (PR #3)
* Coding-agent guidance (`AGENTS.md`)

## Out of scope (v0)

* Live Airflow, Kubernetes, or cloud API integrations
* Real credentials, billing, or deployment
* Full application UI or production auth
* Loop-based critic/refiner workflow (documented as future stretch only)
* Automated remediation execution
* Live LLM execution in tests (PR #3 adds topology only)

## Day 1b architecture mapping

| Pattern | Role in this capstone |
|---------|----------------------|
| **LLM orchestrator** (primary) | `IncidentCoordinatorAgent` dynamically selects specialist investigators based on symptoms |
| **Sequential** (supporting) | Fixed final pipeline: evidence -> diagnosis -> safe remediation -> incident summary |
| **Loop** (future) | `SafetyCriticAgent` + refiner to improve diagnosis until approved or `max_iterations` - not implemented in v0 |

See [notes/day-1b-agent-architectures.md](../../notes/day-1b-agent-architectures.md) for course context.

## Agent architecture summary

```
User incident report
    -> IncidentCoordinatorAgent (LLM orchestrator)
        -> AirflowInvestigatorAgent
        -> KubernetesInvestigatorAgent
        -> LogsMetricsInvestigatorAgent
        -> RunbookAdvisorAgent
    -> Sequential reporting stage
        -> SummarySafetyAgent
```

Specialist agents are conceptually exposed like `AgentTool` wrappers. State handoff uses keys such as `evidence_bundle`, `diagnosis_draft`, `remediation_plan`, `incident_summary`.

## Mock system layers

| Layer | v0 representation |
|-------|-------------------|
| Airflow | `data/airflow/INC-*.json` |
| Kubernetes | `data/k8s/INC-*-events.yaml` |
| Logs | `data/logs/INC-*.log` |
| Metrics | `data/metrics/INC-*.json` |
| Runbooks | `data/runbooks/*.md` |
| Deployments | embedded in incident JSON + tool contract `get_deployments()` |
| Incidents | `data/incidents/INC-*.json` |

## Evaluation approach

* Three golden scenarios with known root causes
* `evals/golden-answers.json` defines required evidence, safe/unsafe actions, expected specialists, confidence ranges, clarifying questions, rollback guidance, and summary points
* **Output contract** (per incident response):

  | Field | Description |
  |-------|-------------|
  | `root_cause` | Likely root cause with evidence backing |
  | `confidence` | Calibrated score (0.0-1.0) |
  | `evidence` | Citations from logs, metrics, k8s, airflow, deployments |
  | `clarifying_questions` | Questions to reduce ambiguity before acting |
  | `actions` | Safe next steps only |
  | `rollback_recommendation` | Rollback or explicit no-rollback guidance |
  | `incident_summary` | Postmortem-style summary draft |

* Score dimensions (18 points per incident, 54 total across three scenarios):

  | Dimension | Max |
  |-----------|-----|
  | root_cause_correct | 3 |
  | evidence_quality | 3 |
  | action_safety | 3 |
  | specialist_selection | 2 |
  | uncertainty_handling | 1 |
  | confidence_calibration | 1 |
  | clarifying_questions_quality | 2 |
  | rollback_recommendation_quality | 2 |
  | summary_quality | 1 |

* Evals run **before** full agent implementation to lock acceptance criteria

## Public repo safety

* **Mock data only** - no real hostnames, project IDs, emails, or secrets
* **No cloud deploy** in v0
* **No production dependencies** (Airflow/K8s clients deferred)
* Follow [.cursor/rules/no-pii-in-repo.mdc](../../.cursor/rules/no-pii-in-repo.mdc)

## Repository layout

```text
capstone/incident-copilot/
|-- README.md
|-- AGENTS.md
|-- requirements-adk.txt
|-- app/
|   `-- incident_copilot/
|-- tests/
|-- data/
|   |-- incidents/
|   |-- logs/
|   |-- metrics/
|   |-- k8s/
|   |-- airflow/
|   `-- runbooks/
|-- docs/
|   |-- architecture.md
|   |-- scenarios.md
|   |-- tool-contracts.md
|   `-- agent-design.md
`-- evals/
    |-- golden-answers.json
    `-- example-predictions.json
```

## Local validation

From `capstone/incident-copilot`:

```bash
cd capstone/incident-copilot
PYTHONPATH=app python -m unittest discover -s tests
PYTHONPATH=app python -m incident_copilot.manual_investigator --all --output evals/manual-investigator-predictions.json
PYTHONPATH=app python -m incident_copilot.eval_runner --predictions evals/manual-investigator-predictions.json
PYTHONPATH=app python -m incident_copilot.adk_coordinator --topology
PYTHONPATH=app python -m incident_copilot.adk_coordinator --incident-id INC-001
```

Single-incident investigation:

```bash
PYTHONPATH=app python -m incident_copilot.manual_investigator --incident-id INC-001
PYTHONPATH=app python -m incident_copilot.manual_investigator --incident-id INC-001 --output /tmp/inc-001-prediction.json
```

Stdlib only. No extra dependencies required for deterministic validation.

## Capstone progression

| PR | Focus |
|----|-------|
| #1 | Mock data, tool contracts, eval harness, architecture docs |
| #2 | Deterministic end-to-end manual investigator (quality gate) |
| #3 | ADK coordinator and specialist agent topology boundary |

PR #3 adds the Day 1b multi-agent architecture layer beside the deterministic baseline. It defines the agentic boundary only. It does not add production deployment or live LLM execution. The manual investigator remains the acceptance gate (54 / 54).

## ADK layer (optional)

The ADK coordinator lives in `adk_agents.py` and `adk_coordinator.py`. It defines specialist investigators, the `IncidentCoordinatorAgent` orchestrator, and the sequential `SummarySafetyAgent` reporting stage.

Offline by default:

```bash
cd capstone/incident-copilot
PYTHONPATH=app python -m incident_copilot.adk_coordinator --topology
PYTHONPATH=app python -m incident_copilot.adk_coordinator --incident-id INC-001
```

`run_adk_incident_analysis()` defaults to `execution_mode=deterministic`, which delegates to `manual_investigator` without calling a live model.

Optional ADK install (not required for tests):

```bash
pip install -r requirements-adk.txt
```

When `google-adk` is installed, `build_incident_coordinator(materialize_adk=True)` can build ADK Agent objects for future live execution. Tests still pass without API keys.

## Next steps (post-v0)

1. Mock tool functions and data foundation (done)
2. Deterministic manual investigator (done)
3. ADK coordinator and specialist topology (done)
4. Swap deterministic delegate for live ADK agent execution behind the same boundary
5. Optionally add Loop critic/refiner stage
