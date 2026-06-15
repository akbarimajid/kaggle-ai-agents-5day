"""Path helpers for incident-copilot mock data and evals."""

from __future__ import annotations

import json
from pathlib import Path

VALID_INCIDENT_IDS = frozenset({"INC-001", "INC-002", "INC-003"})


def project_root() -> Path:
    """Return capstone/incident-copilot directory (contains data/ and evals/)."""
    start = Path(__file__).resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / "data").is_dir() and (candidate / "evals").is_dir():
            return candidate
    raise RuntimeError("Could not locate incident-copilot project root")


def data_dir() -> Path:
    return project_root() / "data"


def evals_dir() -> Path:
    return project_root() / "evals"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_incident_id(incident_id: str) -> None:
    if incident_id not in VALID_INCIDENT_IDS:
        raise ValueError(f"Unknown incident_id: {incident_id}")


def rel_data_path(path: Path) -> str:
    """Path relative to project root for citations."""
    root = project_root()
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
