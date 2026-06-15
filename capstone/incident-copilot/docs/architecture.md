# Architecture (v0)

AI Platform Incident Copilot — evidence-based multi-agent incident investigation using Day 1b patterns.

## End-to-end flow

```text
User incident report
        │
        ▼
IncidentCoordinatorAgent          ← LLM orchestrator (primary)
        │
        ├── AirflowInvestigatorAgent      ─┐
        ├── KubernetesInvestigatorAgent   ─┤ dynamic investigation
        ├── LogsMetricsInvestigatorAgent  ─┤ (order depends on symptoms)
        └── RunbookAdvisorAgent           ─┘
        │
        ▼
Sequential reporting stage        ← fixed pipeline (supporting)
        │
        ├── evidence collector
        ├── diagnosis generator
        ├── safety check
        └── IncidentSummaryAgent
        │
        ▼
Structured incident response
(citations, root cause, safe actions, summary)
```

### Future stretch (not in v0)

```text
LoopAgent (max_iterations = N)
    ├── SafetyCriticAgent    — reviews evidence sufficiency & unsafe recommendations
    └── RefinerAgent         — improves diagnosis or calls exit when approved
```

Nested after investigation, before final summary — see [agent-design.md](./agent-design.md).

---

## Specialist agents

| Agent | Responsibility | Typical tools |
|-------|----------------|---------------|
| `IncidentCoordinatorAgent` | Triage symptoms; invoke specialists; avoid premature conclusion | `AgentTool` wrappers for all specialists |
| `AirflowInvestigatorAgent` | DAG runs, task states, scheduler/worker health | `get_airflow_status`, `get_deployments` |
| `KubernetesInvestigatorAgent` | Pod events, scheduling failures, restarts | `get_k8s_events` |
| `LogsMetricsInvestigatorAgent` | Correlate log lines and metric anomalies | `search_logs`, `get_metrics` |
| `RunbookAdvisorAgent` | Map symptoms to documented procedures | `search_runbooks` |
| `IncidentSummaryAgent` | Produce final human-readable report with citations | reads state keys only |
| `SafetyCriticAgent` | *(future)* Challenge weak evidence or unsafe actions | read-only review of `diagnosis_draft` |

---

## Tool contracts (summary)

Full definitions: [tool-contracts.md](./tool-contracts.md).

| Tool | Purpose |
|------|---------|
| `search_logs(incident_id, query)` | Return matching log lines from mock log files |
| `get_airflow_status(incident_id)` | Return DAG/task/scheduler snapshot |
| `get_k8s_events(incident_id)` | Return Kubernetes events for the incident window |
| `get_metrics(incident_id)` | Return metrics snapshot JSON |
| `search_runbooks(query)` | Return relevant runbook sections |
| `get_deployments(incident_id)` | Return recent deployment events |

All v0 tools read **mock files under `data/`** only.

---

## Pattern rationale

### Why LLM orchestrator is primary

Incidents are **symptom-driven** and **path-dependent**:

* Queued tasks may need Kubernetes quota evidence before Airflow conclusions
* Post-deploy failures need deployment metadata before log deep-dives
* Scheduler instability may require metrics + logs before runbook steps

A fixed pipeline cannot know investigation order in advance. `IncidentCoordinatorAgent` mirrors Day 1b's `ResearchCoordinator` pattern: the model decides **which specialist to call next** based on observed evidence.

**Trade-off accepted:** Non-deterministic ordering during investigation; mitigated by evals and Sequential final stage.

### Where Sequential is used

After investigation, the **user-facing response** must always follow:

1. **Evidence collection** — consolidate specialist outputs into `evidence_bundle`
2. **Diagnosis** — `diagnosis_draft` with cited evidence
3. **Safe remediation** — `remediation_plan` filtered against unsafe action list
4. **Incident summary** — `IncidentSummaryAgent` produces final narrative

This matches Day 1b `SequentialAgent` — deterministic order for deliverables even when investigation was dynamic.

### Where Loop could be added later

Before final summary, a `LoopAgent` could run:

* `SafetyCriticAgent` — "Is root cause supported by cited evidence? Any unsafe remediation?"
* `RefinerAgent` — revise diagnosis or exit when critic returns `APPROVED`

Analogous to Day 1b story critic/refiner loop with `max_iterations` guardrail.

---

## Responsibility split

| Concern | Owner | Notes |
|---------|-------|-------|
| **Model** | Each `Agent` uses an LLM for reasoning within its scope | Coordinator model routes; specialists reason narrowly |
| **Tools** | Mock read-only functions | No cluster mutations; data from `data/` |
| **Memory / state** | Session keys (ADK `output_key` pattern) | `evidence_bundle`, `diagnosis_draft`, `remediation_plan`, `incident_summary` |
| **Orchestration** | Coordinator (dynamic) + Sequential stage (fixed) | Parallel optional later for independent specialists |
| **Deployment** | Out of scope v0 | Future: ADK runner, optional Cloud Run |

---

## Guardrails

| Guardrail | Implementation intent |
|-----------|-------------------------|
| Read-only tools | No `kubectl apply`, no DAG triggers, no infra writes |
| Evidence required | Diagnosis must cite `linked_data_files` paths or log line refs |
| Unsafe action blocklist | Per-incident `expected_unsafe_actions` in golden evals |
| Uncertainty | State when evidence is insufficient; do not invent telemetry |
| Loop cap | `max_iterations` when Loop is added |
| Public safety | Fake service names, environments, reporters |

---

## Observability and eval signals

| Signal | Use |
|--------|-----|
| Specialist invocation trace | Did coordinator call expected agents for scenario? |
| Tool call log | Which files were read; query terms used |
| State snapshots | Contents of `evidence_bundle` at each stage |
| Citation coverage | % of `required_evidence` items cited |
| Rubric scores | `evals/golden-answers.json` per incident |
| Unsafe action detection | Any recommended action in `unsafe_actions` list |
| Latency / token usage | Future operational metrics |

---

## Agent loop mapping

| Stage | Incident copilot |
|-------|------------------|
| Perceive | User report + tool outputs |
| Plan | Coordinator or Sequential stage decides next step |
| Act | Tool call or specialist invocation |
| Observe | Parse tool result into state |
| Iterate | Future Loop critic/refiner; v0 relies on coordinator re-querying specialists |

---

## Context and harness engineering (v0)

| Lever | Application |
|-------|-------------|
| Instructions | Focused per-specialist system prompts |
| Knowledge | Runbooks + mock telemetry files |
| Memory | Named state keys between stages |
| Examples | Golden answers in evals |
| Tools | Scoped per specialist |
| Sandbox | Mock `data/` directory only |
| Orchestration | Coordinator + Sequential |
| Observability | Eval rubric + future run traces |
