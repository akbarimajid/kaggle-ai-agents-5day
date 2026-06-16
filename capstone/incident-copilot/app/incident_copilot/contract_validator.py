"""Output contract validator for Incident Copilot predictions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from incident_copilot.manual_investigator import OUTPUT_CONTRACT_FIELDS
from incident_copilot.paths import VALID_INCIDENT_IDS, evals_dir, load_json

_REQUIRED_STRING_FIELDS = (
    "incident_id",
    "root_cause",
    "rollback_recommendation",
    "incident_summary",
    "uncertainty",
)

_LIST_STRING_FIELDS = (
    "evidence",
    "clarifying_questions",
    "actions",
    "specialists_used",
)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_prediction(prediction: Any, *, path: str = "") -> list[str]:
    """Return human-readable validation errors for one prediction object."""
    prefix = f"{path}." if path else ""
    errors: list[str] = []

    if not isinstance(prediction, dict):
        return [
            f"{prefix}prediction: expected object, got {type(prediction).__name__}"
        ]

    for field in OUTPUT_CONTRACT_FIELDS:
        if field not in prediction:
            errors.append(f"{prefix}{field}: missing required field")

    for field in _REQUIRED_STRING_FIELDS:
        if field not in prediction:
            continue
        value = prediction[field]
        if not isinstance(value, str):
            errors.append(
                f"{prefix}{field}: expected string, got {type(value).__name__}"
            )
        elif not value.strip():
            errors.append(f"{prefix}{field}: must be a non-empty string")

    incident_id = prediction.get("incident_id")
    if isinstance(incident_id, str) and incident_id.strip():
        if incident_id not in VALID_INCIDENT_IDS:
            errors.append(
                f"{prefix}incident_id: unknown incident_id {incident_id!r}"
            )

    confidence = prediction.get("confidence")
    if confidence is not None:
        if not _is_number(confidence):
            errors.append(
                f"{prefix}confidence: expected number, got {type(confidence).__name__}"
            )
        elif not 0.0 <= float(confidence) <= 1.0:
            errors.append(
                f"{prefix}confidence: must be between 0.0 and 1.0, got {confidence}"
            )

    for field in _LIST_STRING_FIELDS:
        if field not in prediction:
            continue
        value = prediction[field]
        if not isinstance(value, list):
            errors.append(
                f"{prefix}{field}: expected list, got {type(value).__name__}"
            )
            continue
        for index, item in enumerate(value):
            item_path = f"{prefix}{field}[{index}]"
            if not isinstance(item, str):
                errors.append(
                    f"{item_path}: expected string, got {type(item).__name__}"
                )
            elif not item.strip():
                errors.append(f"{item_path}: must be a non-empty string")

    return errors


def validate_predictions(payload: Any) -> list[str]:
    """Validate a predictions list or a JSON object with a predictions key."""
    if isinstance(payload, dict) and "predictions" in payload:
        predictions = payload["predictions"]
        base_path = "predictions"
    elif isinstance(payload, list):
        predictions = payload
        base_path = ""
    else:
        return [
            "payload: expected list or object with 'predictions' key, "
            f"got {type(payload).__name__}"
        ]

    if not isinstance(predictions, list):
        return [
            f"{base_path or 'payload'}: expected list, got {type(predictions).__name__}"
        ]

    errors: list[str] = []
    for index, prediction in enumerate(predictions):
        if base_path:
            path = f"{base_path}[{index}]"
        else:
            path = f"[{index}]"
        errors.extend(validate_prediction(prediction, path=path))
    return errors


def is_valid_prediction(prediction: dict) -> bool:
    return not validate_prediction(prediction)


def is_valid_predictions(payload: Any) -> bool:
    return not validate_predictions(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Incident Copilot prediction JSON against the output contract"
    )
    parser.add_argument(
        "--predictions",
        required=True,
        help="Path to predictions JSON file (list or {\"predictions\": [...]})",
    )
    args = parser.parse_args(argv)

    predictions_path = Path(args.predictions)
    if not predictions_path.is_file():
        predictions_path = evals_dir() / args.predictions

    payload = load_json(predictions_path)
    errors = validate_predictions(payload)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("OK: predictions match the output contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
