# Versioned agent prompt templates (v0)

Static prompt templates for the AI Platform Incident Copilot multi-agent topology.
These files turn the ADK agent design into explicit, reviewable context artifacts
before live LLM execution is introduced.

## Versioning

- **Prompt version:** v0
- **Output contract:** see [docs/output-contract.md](../docs/output-contract.md)
- **Quality gate:** deterministic `manual_investigator` baseline and eval harness (54 / 54)

Prompts are plain Markdown files in this directory. Update them deliberately and
re-run tests when changing agent behavior expectations.

## Capstone context

This capstone uses **mock data and deterministic tools only**. Tools read from files
under `data/` (logs, metrics, Kubernetes events, Airflow status, runbooks). No live
Airflow, Kubernetes, or cloud API access is required or permitted in v0.

## Agent prompts

| File | Agent | Pattern role |
| --- | --- | --- |
| [coordinator.md](./coordinator.md) | `IncidentCoordinatorAgent` | LLM orchestrator |
| [airflow-investigator.md](./airflow-investigator.md) | `AirflowInvestigatorAgent` | Specialist |
| [kubernetes-investigator.md](./kubernetes-investigator.md) | `KubernetesInvestigatorAgent` | Specialist |
| [logs-metrics-investigator.md](./logs-metrics-investigator.md) | `LogsMetricsInvestigatorAgent` | Specialist |
| [runbook-advisor.md](./runbook-advisor.md) | `RunbookAdvisorAgent` | Specialist |
| [summary-safety.md](./summary-safety.md) | `SummarySafetyAgent` | Sequential reporting |

## Topology flow

```text
Incident report
  -> IncidentCoordinatorAgent (routes to specialists, collects evidence)
      -> AirflowInvestigatorAgent
      -> KubernetesInvestigatorAgent
      -> LogsMetricsInvestigatorAgent
      -> RunbookAdvisorAgent
  -> SummarySafetyAgent (final contract-valid response)
```

## Related

* [agent-design.md](../docs/agent-design.md)
* [tool-contracts.md](../docs/tool-contracts.md)
* [output-contract.md](../docs/output-contract.md)
* [agentic-engineering-playbook.md](../docs/agentic-engineering-playbook.md)
