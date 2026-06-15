"""Read-only deterministic mock tools for incident investigation."""

from __future__ import annotations

import re
from pathlib import Path

from incident_copilot.paths import (
    data_dir,
    load_json,
    read_text,
    rel_data_path,
    validate_incident_id,
)

_LOG_LINE_RE = re.compile(
    r"^(?P<timestamp>\S+)\s+(?P<level>\S+)\s+(?P<component>\S+)\s+(?P<message>.+)$"
)


def search_logs(incident_id: str, query: str) -> list[dict]:
    validate_incident_id(incident_id)
    log_path = data_dir() / "logs" / f"{incident_id}.log"
    if not log_path.is_file():
        return []

    needle = query.casefold()
    matches: list[dict] = []
    for line_number, line in enumerate(read_text(log_path).splitlines(), start=1):
        if not line.strip():
            continue
        parsed = _LOG_LINE_RE.match(line)
        if parsed:
            timestamp = parsed.group("timestamp")
            level = parsed.group("level")
            component = parsed.group("component")
            message = parsed.group("message")
        else:
            timestamp = ""
            level = ""
            component = ""
            message = line

        if needle and needle not in message.casefold() and needle not in line.casefold():
            continue

        matched_text = message if needle in message.casefold() else line
        matches.append(
            {
                "timestamp": timestamp,
                "level": level,
                "component": component,
                "message": message,
                "source_file": rel_data_path(log_path),
                "line_number": line_number,
                "matched_text": matched_text,
            }
        )
    return matches


def get_airflow_status(incident_id: str) -> dict:
    validate_incident_id(incident_id)
    status_path = data_dir() / "airflow" / f"{incident_id}-status.json"
    if not status_path.is_file():
        raise ValueError(f"airflow_status_not_found: {incident_id}")
    status = load_json(status_path)
    status["source_file"] = rel_data_path(status_path)
    return status


def _parse_k8s_events_yaml(text: str, source_file: str) -> list[dict]:
    """Minimal parser for the fixed mock K8s List/Event fixture shape."""
    blocks = re.split(r"\n  - apiVersion:", text)
    events: list[dict] = []
    for block in blocks[1:]:
        block = "apiVersion:" + block

        def _field(pattern: str, default: str = "") -> str:
            match = re.search(pattern, block, re.MULTILINE)
            return match.group(1).strip().strip('"') if match else default

        namespace = _field(r"^\s+namespace:\s+(\S+)")
        involved = re.search(
            r"involvedObject:\s*\n\s+kind:\s+(\S+)\s*\n\s+name:\s+(\S+)",
            block,
        )
        if involved:
            object_kind, object_name = involved.group(1), involved.group(2)
        else:
            object_kind = _field(r"^\s+kind:\s+(\S+)")
            object_name = _field(r"^\s+name:\s+(\S+)")
        reason = _field(r"^\s+reason:\s+(\S+)")
        message = _field(r'^\s+message:\s+"(.*)"') or _field(r"^\s+message:\s+(\S+)")
        event_type = _field(r"^\s+type:\s+(\S+)")
        timestamp = _field(r'^\s+firstTimestamp:\s+"([^"]+)"') or _field(
            r'^\s+lastTimestamp:\s+"([^"]+)"'
        )

        events.append(
            {
                "timestamp": timestamp,
                "namespace": namespace,
                "object_kind": object_kind,
                "object_name": object_name,
                "reason": reason,
                "event_reason": reason,
                "message": message,
                "type": event_type,
                "source_file": source_file,
            }
        )
    return events


def get_k8s_events(incident_id: str) -> list[dict]:
    validate_incident_id(incident_id)
    events_path = data_dir() / "k8s" / f"{incident_id}-events.yaml"
    if not events_path.is_file():
        return []
    return _parse_k8s_events_yaml(read_text(events_path), rel_data_path(events_path))


def get_metrics(incident_id: str) -> dict:
    validate_incident_id(incident_id)
    metrics_path = data_dir() / "metrics" / f"{incident_id}.json"
    if not metrics_path.is_file():
        raise ValueError(f"metrics_not_found: {incident_id}")
    snapshot = load_json(metrics_path)
    snapshot["source_file"] = rel_data_path(metrics_path)
    return snapshot


def _split_runbook_sections(text: str, source_file: str) -> list[dict]:
    title = ""
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    sections: list[dict] = []
    current_heading = "Introduction"
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append(
                    {
                        "runbook_id": Path(source_file).stem,
                        "title": title,
                        "section": current_heading,
                        "content": "\n".join(current_lines).strip(),
                        "source_file": source_file,
                    }
                )
            current_heading = line[3:].strip()
            current_lines = []
        elif not line.startswith("# "):
            current_lines.append(line)

    if current_lines:
        sections.append(
            {
                "runbook_id": Path(source_file).stem,
                "title": title,
                "section": current_heading,
                "content": "\n".join(current_lines).strip(),
                "source_file": source_file,
            }
        )
    return sections


def search_runbooks(query: str) -> list[dict]:
    runbooks_path = data_dir() / "runbooks"
    if not runbooks_path.is_dir():
        return []

    needle = query.casefold()
    results: list[dict] = []
    for md_file in sorted(runbooks_path.glob("*.md")):
        source_file = rel_data_path(md_file)
        text = read_text(md_file)
        for section in _split_runbook_sections(text, source_file):
            haystack = " ".join(
                [section["title"], section["section"], section["content"]]
            ).casefold()
            if not needle or needle in haystack:
                results.append(section)
    return results


def get_deployments(incident_id: str) -> list[dict]:
    validate_incident_id(incident_id)
    incident_path = data_dir() / "incidents" / f"{incident_id}.json"
    if not incident_path.is_file():
        return []
    incident = load_json(incident_path)
    deployments = incident.get("deployment_events", [])
    source_file = rel_data_path(incident_path)
    return [{**event, "source_file": source_file} for event in deployments]
