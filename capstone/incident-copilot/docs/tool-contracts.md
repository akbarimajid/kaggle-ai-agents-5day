# Tool contracts (v0)

Interfaces only — **not implemented** in v0. All tools read from mock files under `data/`.

---

## Shared types (conceptual)

```python
LogMatch = {
    "timestamp": str,       # ISO-8601
    "level": str,           # INFO | WARN | ERROR
    "component": str,       # scheduler | worker | webserver | pgbouncer
    "message": str,
    "source_file": str,     # path under data/logs/
    "line_number": int,
}

AirflowStatus = {
    "incident_id": str,
    "scheduler_healthy": bool,
    "queued_task_count": int,
    "running_task_count": int,
    "failed_task_count": int,
    "affected_dags": list[str],
    "worker_pods_available": int,
    "worker_pods_pending": int,
    "notes": list[str],
}

K8sEvent = {
    "timestamp": str,
    "namespace": str,
    "object_kind": str,
    "object_name": str,
    "reason": str,
    "message": str,
    "type": str,            # Normal | Warning
}

MetricsSnapshot = {
    "incident_id": str,
    "window_start": str,
    "window_end": str,
    "series": list[{
        "name": str,
        "unit": str,
        "values": list[{"ts": str, "value": float}],
    }],
}

RunbookSection = {
    "runbook_id": str,
    "title": str,
    "section": str,
    "content": str,
    "source_file": str,
}

DeploymentEvent = {
    "deployed_at": str,
    "component": str,
    "version": str,
    "environment": str,
    "changed_by": str,
    "summary": str,
}
```

---

## `search_logs(incident_id: str, query: str) -> list[LogMatch]`

| Field | Value |
|-------|-------|
| **Purpose** | Search mock log files for lines matching a keyword or phrase |
| **Inputs** | `incident_id` — maps to `data/logs/{incident_id}.log`; `query` — case-insensitive substring |
| **Outputs** | Ordered list of `LogMatch` |
| **Allowed data source** | `data/logs/INC-*.log` only |
| **Failure behavior** | Return empty list if file missing; never fabricate lines |
| **Guardrails** | Read-only; max 100 matches; no log injection |
| **Used by** | `LogsMetricsInvestigatorAgent` |

---

## `get_airflow_status(incident_id: str) -> AirflowStatus`

| Field | Value |
|-------|-------|
| **Purpose** | Return Airflow scheduler/worker/task snapshot for an incident |
| **Inputs** | `incident_id` |
| **Outputs** | `AirflowStatus` parsed from JSON |
| **Allowed data source** | `data/airflow/{incident_id}-status.json` |
| **Failure behavior** | Raise `ToolError("airflow_status_not_found")` if file missing |
| **Guardrails** | Read-only; no DAG triggers |
| **Used by** | `AirflowInvestigatorAgent` |

---

## `get_k8s_events(incident_id: str) -> list[K8sEvent]`

| Field | Value |
|-------|-------|
| **Purpose** | Return Kubernetes events relevant to the incident |
| **Inputs** | `incident_id` |
| **Outputs** | List of `K8sEvent` |
| **Allowed data source** | `data/k8s/{incident_id}-events.yaml` |
| **Failure behavior** | Return empty list with warning metadata if file missing |
| **Guardrails** | Read-only; no cluster API calls in v0 |
| **Used by** | `KubernetesInvestigatorAgent` |

---

## `get_metrics(incident_id: str) -> MetricsSnapshot`

| Field | Value |
|-------|-------|
| **Purpose** | Return time-series metrics for correlation |
| **Inputs** | `incident_id` |
| **Outputs** | `MetricsSnapshot` |
| **Allowed data source** | `data/metrics/{incident_id}.json` |
| **Failure behavior** | Raise `ToolError("metrics_not_found")` if file missing |
| **Guardrails** | Read-only |
| **Used by** | `LogsMetricsInvestigatorAgent` |

---

## `search_runbooks(query: str) -> list[RunbookSection]`

| Field | Value |
|-------|-------|
| **Purpose** | Find runbook sections matching symptoms or components |
| **Inputs** | `query` — keyword search across `data/runbooks/*.md` |
| **Outputs** | Ranked `RunbookSection` list (title + heading + excerpt) |
| **Allowed data source** | `data/runbooks/*.md` |
| **Failure behavior** | Return empty list if no match |
| **Guardrails** | Read-only; return excerpts only (no arbitrary file read) |
| **Used by** | `RunbookAdvisorAgent` |

---

## `get_deployments(incident_id: str) -> list[DeploymentEvent]`

| Field | Value |
|-------|-------|
| **Purpose** | Return recent deployment events tied to an incident |
| **Inputs** | `incident_id` |
| **Outputs** | List of `DeploymentEvent` from incident metadata |
| **Allowed data source** | `data/incidents/{incident_id}.json` field `deployment_events` |
| **Failure behavior** | Return empty list if none recorded |
| **Guardrails** | Read-only; no deploy/rollback execution |
| **Used by** | `AirflowInvestigatorAgent` |

---

## Cross-cutting tool policies

1. All tools are **synchronous** and **deterministic** on mock data
2. Tools **must not** write to disk or call external networks in v0
3. Tool responses should include `source_file` references for citation
4. Coordinator may call tools only through specialist `AgentTool` wrappers (design intent)
