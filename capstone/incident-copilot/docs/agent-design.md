# Agent design (v0)

Conceptual multi-agent design for AI Platform Incident Copilot, based on Day 1b patterns from [notes/day-1b-agent-architectures.md](../../../notes/day-1b-agent-architectures.md).

---

## Design goals

1. **Dynamic investigation** — route to the right evidence sources per incident
2. **Deterministic deliverables** — always produce evidence → diagnosis → remediation → summary
3. **Testable specialists** — each agent has one job and a small tool set
4. **Eval-first** — golden scenarios define success before code

---

## Agent roster

| Agent | Pattern role | Tools (via AgentTool or direct) |
|-------|--------------|----------------------------------|
| `IncidentCoordinatorAgent` | LLM orchestrator | `AgentTool` wrappers for all specialists |
| `AirflowInvestigatorAgent` | Specialist | `get_airflow_status`, `get_deployments` |
| `KubernetesInvestigatorAgent` | Specialist | `get_k8s_events` |
| `LogsMetricsInvestigatorAgent` | Specialist | `search_logs`, `get_metrics` |
| `RunbookAdvisorAgent` | Specialist | `search_runbooks` |
| `IncidentSummaryAgent` | Sequential stage (final) | none — reads state |
| `SafetyCriticAgent` | *(future Loop)* | read-only review |

---

## Phase 1: Investigation (LLM orchestrator)

```text
IncidentCoordinatorAgent
  instruction: |
    You triage platform incidents. Based on user symptoms:
    1. Call the minimum set of specialist agents to gather evidence
    2. Do not diagnose until evidence_bundle is populated
    3. Prefer Kubernetes + metrics when tasks are queued
    4. Prefer deployments + logs when failures follow a release
    5. Prefer metrics + logs + scheduler health when scheduler is unstable
  tools:
    - AgentTool(AirflowInvestigatorAgent)
    - AgentTool(KubernetesInvestigatorAgent)
    - AgentTool(LogsMetricsInvestigatorAgent)
    - AgentTool(RunbookAdvisorAgent)
  output_key: investigation_trace
```

Each specialist writes into shared **`evidence_bundle`** (append-only list of cited findings):

```json
{
  "findings": [
    {
      "specialist": "KubernetesInvestigatorAgent",
      "summary": "Worker pods Pending: insufficient cpu quota",
      "citations": ["data/k8s/INC-001-events.yaml#L12"]
    }
  ]
}
```

Specialists are conceptually wrapped like Day 1b `AgentTool(research_agent)` — the coordinator invokes them as tools rather than embedding all logic in one prompt.

---

## Phase 2: Reporting (Sequential)

After investigation completes, a **`SequentialAgent`** runs fixed sub-stages:

```text
SequentialAgent(name="IncidentReportPipeline")
  sub_agents:
    - EvidenceCollectorAgent      → validates evidence_bundle completeness
    - DiagnosisGeneratorAgent     → output_key: diagnosis_draft
    - SafetyCheckAgent            → output_key: remediation_plan
    - IncidentSummaryAgent        → output_key: incident_summary
```

| Stage | Input state | Output state |
|-------|-------------|--------------|
| Evidence collector | `evidence_bundle` | validated `evidence_bundle` |
| Diagnosis generator | `evidence_bundle` | `diagnosis_draft` |
| Safety check | `diagnosis_draft`, runbook guidance | `remediation_plan` (unsafe actions stripped) |
| Summary | all above | `incident_summary` |

This mirrors Day 1b Outline → Writer → Editor — order is **guaranteed** for the user-facing artifact.

---

## Phase 3: Future Loop (not implemented)

```text
LoopAgent(name="DiagnosisQualityLoop", max_iterations=2)
  sub_agents:
    - SafetyCriticAgent
    - DiagnosisRefinerAgent
```

**SafetyCriticAgent** checks:

* Is root cause supported by at least two independent evidence sources?
* Does `remediation_plan` contain any known unsafe actions?
* Response must include exact token `APPROVED` or specific gaps

**DiagnosisRefinerAgent** either revises `diagnosis_draft` or calls `exit_loop()`.

Placed **after** initial diagnosis, **before** `IncidentSummaryAgent` — or wraps the diagnosis + safety substeps.

---

## State handoff (`output_key` pattern)

| Key | Producer | Consumers |
|-----|----------|-----------|
| `investigation_trace` | Coordinator | Observability / evals |
| `evidence_bundle` | Specialists + collector | Diagnosis, critic |
| `diagnosis_draft` | Diagnosis generator | Safety check, refiner, critic |
| `remediation_plan` | Safety check | Summary agent |
| `incident_summary` | Summary agent | User response |

Instructions reference placeholders: `{evidence_bundle}`, `{diagnosis_draft}`, etc. — same pattern as Day 1b `{research_findings}`.

---

## Why this is easier to test than one do-it-all agent

| Monolithic agent | Multi-agent design |
|------------------|-------------------|
| Single huge prompt | Focused instructions per specialist |
| Unclear which "step" failed | Eval per specialist tool + coordinator routing |
| Hard to mock tools | Each agent has 1–2 tools |
| Non-reproducible routing | Sequential stage locks output shape |
| Weak safety enforcement | Dedicated safety check + future critic |

**Eval strategy:** Test tools against mock files → test each specialist with golden `incident_id` → test coordinator routing → test Sequential output against `golden-answers.json`.

---

## Example coordinator routing (by scenario)

| Incident | Expected specialist calls (minimum) |
|----------|-------------------------------------|
| INC-001 | Airflow, Kubernetes, LogsMetrics, Runbook |
| INC-002 | Airflow, LogsMetrics, Runbook (+ deployments) |
| INC-003 | Airflow, LogsMetrics, Kubernetes, Runbook |

Order may vary in Phase 1; Phase 2 order is fixed.

---

## ADK mapping (future implementation)

```python
# Conceptual — not implemented in v0
from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.tools import AgentTool, FunctionTool

coordinator = Agent(
    name="IncidentCoordinatorAgent",
    tools=[
        AgentTool(airflow_investigator),
        AgentTool(k8s_investigator),
        AgentTool(logs_metrics_investigator),
        AgentTool(runbook_advisor),
    ],
    output_key="investigation_trace",
)

report_pipeline = SequentialAgent(
    name="IncidentReportPipeline",
    sub_agents=[
        evidence_collector,
        diagnosis_generator,
        safety_check,
        incident_summary,
    ],
)
```

Root composition TBD: either nested agents or a thin workflow wrapper that runs coordinator then `report_pipeline`.
