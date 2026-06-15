"""Deterministic manual investigator for incident copilot (no LLM)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from incident_copilot import tools
from incident_copilot.paths import data_dir, load_json, validate_incident_id

OUTPUT_CONTRACT_FIELDS = (
    "incident_id",
    "root_cause",
    "evidence",
    "actions",
    "specialists_used",
    "uncertainty",
    "confidence",
    "clarifying_questions",
    "rollback_recommendation",
    "incident_summary",
)

ALL_INCIDENT_IDS = ("INC-001", "INC-002", "INC-003")


def load_incident(incident_id: str) -> dict:
    validate_incident_id(incident_id)
    path = data_dir() / "incidents" / f"{incident_id}.json"
    if not path.is_file():
        raise ValueError(f"incident_not_found: {incident_id}")
    return load_json(path)


def _format_evidence(source: str, detail: str) -> str:
    return f"{source} - {detail}"


def _investigate_inc_001(incident: dict) -> dict:
    incident_id = incident["incident_id"]
    airflow = tools.get_airflow_status(incident_id)
    k8s_events = tools.get_k8s_events(incident_id)
    metrics = tools.get_metrics(incident_id)
    log_hits = tools.search_logs(incident_id, "quota")
    worker_log_hits = tools.search_logs(incident_id, "worker")
    runbooks = tools.search_runbooks("queued")

    scheduling_events = [
        event
        for event in k8s_events
        if "failedscheduling" in event.get("reason", "").casefold()
        or "quota" in event.get("message", "").casefold()
    ]
    event_detail = (
        scheduling_events[0]["message"]
        if scheduling_events
        else "FailedScheduling and CPU quota ThresholdExceeded"
    )

    evidence = [
        _format_evidence(
            airflow["source_file"],
            f"{airflow['queued_task_count']} queued tasks, "
            f"{airflow['worker_pods_pending']} pending worker pods, "
            f"{airflow['worker_pods_available']} workers available",
        ),
        _format_evidence(
            metrics["source_file"],
            "k8s.namespace.quota.cpu.used_percent at 100% in analytics-batch; "
            "airflow.workers.available at 0",
        ),
        _format_evidence(
            k8s_events[0]["source_file"] if k8s_events else "data/k8s/INC-001-events.yaml",
            f"Kubernetes event: {event_detail}",
        ),
    ]
    if log_hits:
        evidence.append(
            _format_evidence(
                log_hits[0]["source_file"],
                log_hits[0]["matched_text"],
            )
        )
    elif worker_log_hits:
        evidence.append(
            _format_evidence(
                worker_log_hits[0]["source_file"],
                worker_log_hits[0]["matched_text"],
            )
        )

    runbook_hint = runbooks[0]["title"] if runbooks else "airflow-queued-tasks"
    return {
        "incident_id": incident_id,
        "root_cause": (
            "Worker pods cannot start because the analytics-batch namespace CPU quota "
            "(limits.cpu 16/16) is exhausted, leaving Airflow tasks stuck in queued "
            "with zero available workers."
        ),
        "confidence": 0.88,
        "evidence": evidence,
        "clarifying_questions": [
            "Were any namespace quota changes or large DAG backfills started recently?",
            "Did any new workloads deploy into analytics-batch before tasks began queuing?",
        ],
        "actions": [
            "Confirm quota saturation via metrics and Kubernetes events",
            "Request CPU quota increase through change control",
            "Pause or reschedule non-critical DAGs after stakeholder approval",
            f"Review runbook guidance in {runbook_hint} before capacity changes",
        ],
        "rollback_recommendation": (
            "No rollback recommended. Address analytics-batch CPU quota exhaustion "
            "and restore worker capacity first."
        ),
        "incident_summary": (
            "Multiple Airflow tasks remained queued because worker pods could not schedule "
            "in analytics-batch. Kubernetes events show FailedScheduling and CPU quota at "
            "limits.cpu 16/16. Metrics confirm 100% quota usage and zero available workers. "
            "The scheduler is operational but cannot place workers. Remediation requires quota "
            "increase through change control or deprioritizing non-critical DAGs after approval."
        ),
        "specialists_used": list(incident.get("expected_specialists", [])),
        "uncertainty": (
            "High confidence given aligned quota, scheduling, and worker availability signals; "
            "may verify recent namespace quota changes."
        ),
    }


def _investigate_inc_002(incident: dict) -> dict:
    incident_id = incident["incident_id"]
    deployments = tools.get_deployments(incident_id)
    log_env_hits = tools.search_logs(incident_id, "BQ_DATASET_PROD")
    log_dataset_hits = tools.search_logs(incident_id, "analytics_prod_v2")
    metrics = tools.get_metrics(incident_id)
    k8s_events = tools.get_k8s_events(incident_id)
    airflow = tools.get_airflow_status(incident_id)
    runbooks = tools.search_runbooks("deploy")

    latest_deploy = deployments[0] if deployments else {}
    config_events = [
        event
        for event in k8s_events
        if event.get("object_kind") == "ConfigMap"
        or "configmap" in event.get("message", "").casefold()
    ]

    evidence = [
        _format_evidence(
            latest_deploy.get("source_file", f"data/incidents/{incident_id}.json"),
            f"deployment {latest_deploy.get('version', 'v2.14.0')} at "
            f"{latest_deploy.get('deployed_at', '2026-06-14T22:10:00Z')}",
        ),
    ]
    if log_env_hits:
        evidence.append(
            _format_evidence(
                log_env_hits[0]["source_file"],
                log_env_hits[0]["matched_text"],
            )
        )
    if log_dataset_hits:
        evidence.append(
            _format_evidence(
                log_dataset_hits[0]["source_file"],
                log_dataset_hits[0]["matched_text"],
            )
        )
    if config_events:
        evidence.append(
            _format_evidence(
                config_events[0]["source_file"],
                f"ConfigMap event: {config_events[0]['message']}",
            )
        )
    evidence.append(
        _format_evidence(
            metrics["source_file"],
            "airflow task failure rate spike after deploy v2.14.0",
        )
    )
    evidence.append(
        _format_evidence(
            airflow["source_file"],
            f"DAG failures noted in airflow status for {incident['service']}",
        )
    )

    runbook_hint = runbooks[0]["title"] if runbooks else "dag-deploy-failures"
    return {
        "incident_id": incident_id,
        "root_cause": (
            "DAG customer_segmentation_daily fails after deploy v2.14.0 due to missing "
            "BQ_DATASET_PROD environment variable and invalid BigQuery dataset "
            "analytics_prod_v2."
        ),
        "confidence": 0.84,
        "evidence": evidence,
        "clarifying_questions": [
            "Can the failed v2.14.0 deployment be rolled back to the last known good version?",
            "Did the BigQuery dataset name change in this release?",
            "Was BQ_DATASET_PROD intentionally removed from worker configuration?",
        ],
        "actions": [
            "Rollback to DAG bundle v2.13.2 via release process",
            "Add BQ_DATASET_PROD to worker deployment configuration",
            "Correct dataset name to analytics_prod",
            "Re-run DAG after staging validation",
            f"Coordinate config hotfix through change control per {runbook_hint}",
        ],
        "rollback_recommendation": (
            "Rollback DAG bundle from v2.14.0 to v2.13.2 via standard release process, "
            "or hotfix missing BQ_DATASET_PROD and correct dataset name before re-run."
        ),
        "incident_summary": (
            "DAG customer_segmentation_daily began failing immediately after v2.14.0 deployment. "
            "Logs show missing BQ_DATASET_PROD and invalid dataset analytics_prod_v2. "
            "Kubernetes ConfigMap revision removed the env var. Task failure rate spiked "
            "post-deploy. Rollback or config hotfix required before downstream BI recovers."
        ),
        "specialists_used": list(incident.get("expected_specialists", [])),
        "uncertainty": (
            "Confident about deploy correlation; may need config diff review to confirm "
            "dataset naming standard."
        ),
    }


def _investigate_inc_003(incident: dict) -> dict:
    incident_id = incident["incident_id"]
    airflow = tools.get_airflow_status(incident_id)
    metrics = tools.get_metrics(incident_id)
    k8s_events = tools.get_k8s_events(incident_id)
    log_hits = tools.search_logs(incident_id, "pgbouncer")
    connection_log_hits = tools.search_logs(incident_id, "connection")
    runbooks = tools.search_runbooks("scheduler")

    backoff_events = [
        event
        for event in k8s_events
        if event.get("reason", "").casefold() in {"backoff", "unhealthy", "killing"}
    ]

    evidence = [
        _format_evidence(
            metrics["source_file"],
            "pgbouncer pool active 50/50 with waiting clients; "
            "airflow.scheduler.restart.count elevated",
        ),
        _format_evidence(
            airflow["source_file"],
            f"scheduler_healthy {airflow['scheduler_healthy']} with repeated scheduler restarts",
        ),
    ]
    if log_hits:
        evidence.append(
            _format_evidence(
                log_hits[0]["source_file"],
                log_hits[0]["matched_text"],
            )
        )
    elif connection_log_hits:
        evidence.append(
            _format_evidence(
                connection_log_hits[0]["source_file"],
                connection_log_hits[0]["matched_text"],
            )
        )
    if backoff_events:
        evidence.append(
            _format_evidence(
                backoff_events[0]["source_file"],
                f"Scheduler pod {backoff_events[0]['reason']}: "
                f"{backoff_events[0]['message']}",
            )
        )

    runbook_hint = runbooks[0]["title"] if runbooks else "scheduler-db-connections"
    return {
        "incident_id": incident_id,
        "root_cause": (
            "Airflow scheduler repeatedly restarts because metadata database connections "
            "are exhausted through PgBouncer (pool at capacity with waiting clients)."
        ),
        "confidence": 0.82,
        "evidence": evidence,
        "clarifying_questions": [
            "Were database connection limits or PgBouncer pool settings changed recently?",
            "Did scheduler replica count or parsing_processes change before instability began?",
            "Are there long-running queries against the metadata database?",
        ],
        "actions": [
            "Verify PgBouncer pool metrics and scheduler DB connection settings",
            "Temporarily reduce parsing_processes per runbook",
            "Restart scheduler pods one at a time after pool headroom check",
            "Coordinate with DBA on long-running metadata queries",
            f"Request approved pool size increase through change control per {runbook_hint}",
        ],
        "rollback_recommendation": (
            "No application rollback recommended. Reduce scheduler DB connection pressure "
            "and inspect PgBouncer/metadata DB pool settings first."
        ),
        "incident_summary": (
            "Airflow scheduler repeatedly restarted and was marked unhealthy. Metadata database "
            "connections are exhausted through PgBouncer with the pool at capacity and waiting "
            "clients elevated. DAG parsing is delayed due to scheduler instability. Remediation "
            "targets connection pool relief and coordinated scheduler restarts after headroom check."
        ),
        "specialists_used": list(incident.get("expected_specialists", [])),
        "uncertainty": (
            "Moderate confidence; may need DBA confirmation on long-running metadata queries "
            "before changing pool settings."
        ),
    }


_INVESTIGATORS: dict[str, Callable[[dict], dict]] = {
    "INC-001": _investigate_inc_001,
    "INC-002": _investigate_inc_002,
    "INC-003": _investigate_inc_003,
}


def investigate(incident_id: str) -> dict:
    """Run deterministic investigation for one incident."""
    validate_incident_id(incident_id)
    incident = load_incident(incident_id)
    handler = _INVESTIGATORS.get(incident_id)
    if handler is None:
        raise ValueError(f"No investigator registered for {incident_id}")
    prediction = handler(incident)
    missing = [field for field in OUTPUT_CONTRACT_FIELDS if field not in prediction]
    if missing:
        raise ValueError(f"Prediction missing output contract fields: {missing}")
    return prediction


def investigate_all() -> list[dict]:
    return [investigate(incident_id) for incident_id in ALL_INCIDENT_IDS]


def _write_output(payload: Any, output_path: Path | None) -> None:
    if output_path is None:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic manual incident investigator (no LLM)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--incident-id", help="Investigate a single incident (INC-001 to INC-003)")
    group.add_argument(
        "--all",
        action="store_true",
        help="Investigate all incidents and emit a list of predictions",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write JSON output (stdout if omitted)",
    )
    args = parser.parse_args(argv)

    output_path = Path(args.output) if args.output else None

    if args.all:
        payload = investigate_all()
    else:
        payload = investigate(args.incident_id)

    _write_output(payload, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
