"""Deterministic critic/refiner quality gate for incident predictions (offline-safe)."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from incident_copilot import contract_validator
from incident_copilot.paths import evals_dir, load_json

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{2,}", re.IGNORECASE)

_LOW_CONFIDENCE_THRESHOLD = 0.75
_HIGH_CONFIDENCE_THRESHOLD = 0.85

_UNCERTAINTY_AMBIGUITY_MARKERS = (
    "uncertain",
    "partial",
    "need further",
    "may need",
    "might",
    "gap",
    "limited evidence",
    "incomplete",
)

_UNCERTAINTY_HIGH_CONFIDENCE_MARKERS = (
    "high confidence",
    "confident",
    "aligned signals",
    "moderate confidence",
)

_UNSAFE_ACTION_PHRASES = (
    "delete production",
    "purge metadata",
    "force-run tasks on scheduler",
    "patch worker code directly",
    "drop metadata",
    "disable pgbouncer",
    "post db credentials",
    "disable resource quotas",
    "embed service account keys",
    "restart all scheduler pods immediately",
    "wipe",
    "truncate production",
)

_SOURCE_CITATION_MARKERS = ("data/", "incidents/", "logs/", "metrics/", "k8s/", "airflow/")

_ROLLBACK_REASONING_MARKERS = (
    "rollback",
    "no rollback",
    "no application rollback",
    "not recommend rollback",
    "hotfix",
    "release process",
)

_OVERCLAIM_MARKERS = (
    "definitely",
    "proven beyond doubt",
    "confirmed root cause without",
    "100% certain",
)

_DEFAULT_CLARIFYING_QUESTION = (
    "What additional telemetry or recent changes should be verified before remediation?"
)


def _normalize(text: str) -> str:
    return text.casefold().replace("_", " ")


def _tokens(text: str) -> set[str]:
    return {token.casefold() for token in _TOKEN_RE.findall(text)}


def _significant_tokens(text: str) -> set[str]:
    return {token for token in _tokens(text) if len(token) > 4}


def _evidence_blob(evidence: list[str]) -> str:
    return _normalize(" ".join(evidence))


def _has_source_citation(evidence_item: str) -> bool:
    normalized = _normalize(evidence_item)
    return any(marker in normalized for marker in _SOURCE_CITATION_MARKERS)


def _actions_blob(actions: list[str]) -> str:
    return _normalize(" ".join(actions))


def _check_contract_valid(prediction: dict) -> tuple[bool, list[str]]:
    errors = contract_validator.validate_prediction(prediction)
    return not errors, errors


def _check_evidence_present(prediction: dict) -> tuple[bool, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    evidence = prediction.get("evidence", [])
    if not isinstance(evidence, list) or not evidence:
        issues.append("evidence list is empty")
        return False, issues, warnings

    for index, item in enumerate(evidence):
        if not isinstance(item, str) or not item.strip():
            issues.append(f"evidence[{index}] is empty or not a string")
            continue
        if not _has_source_citation(item):
            warnings.append(f"evidence[{index}] lacks an explicit data/ source citation")

    if issues:
        return False, issues, warnings
    if warnings:
        return True, issues, warnings
    return True, issues, warnings


def _check_root_cause_supported(prediction: dict) -> tuple[bool, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    root_cause = prediction.get("root_cause", "")
    evidence = prediction.get("evidence", [])
    if not isinstance(root_cause, str) or not root_cause.strip():
        issues.append("root_cause is empty")
        return False, issues, warnings

    cause_tokens = _significant_tokens(root_cause)
    if not cause_tokens:
        warnings.append("root_cause has no significant diagnostic tokens")
        return True, issues, warnings

    blob = _evidence_blob(evidence if isinstance(evidence, list) else [])
    hits = sum(1 for token in cause_tokens if token in blob)
    required = min(2, len(cause_tokens))
    if hits < required:
        issues.append("root_cause is not supported by cited evidence keywords")
        return False, issues, warnings
    return True, issues, warnings


def _check_safe_actions(prediction: dict) -> tuple[bool, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    actions = prediction.get("actions", [])
    if not isinstance(actions, list) or not actions:
        warnings.append("actions list is empty")
        return True, issues, warnings

    blob = _actions_blob(actions)
    for phrase in _UNSAFE_ACTION_PHRASES:
        if phrase in blob:
            issues.append(f"actions contain unsafe or destructive step: {phrase}")
    if issues:
        return False, issues, warnings
    return True, issues, warnings


def _check_rollback_present(prediction: dict) -> tuple[bool, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    rollback = prediction.get("rollback_recommendation", "")
    if not isinstance(rollback, str) or not rollback.strip():
        issues.append("rollback_recommendation is missing or empty")
        return False, issues, warnings

    normalized = _normalize(rollback)
    if not any(marker in normalized for marker in _ROLLBACK_REASONING_MARKERS):
        warnings.append(
            "rollback_recommendation should explicitly state rollback or no-rollback reasoning"
        )
    return True, issues, warnings


def _check_clarifying_questions(prediction: dict) -> tuple[bool, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    questions = prediction.get("clarifying_questions", [])
    uncertainty = _normalize(str(prediction.get("uncertainty", "")))
    confidence = prediction.get("confidence")

    low_confidence = isinstance(confidence, (int, float)) and float(confidence) < _LOW_CONFIDENCE_THRESHOLD
    ambiguous = any(marker in uncertainty for marker in _UNCERTAINTY_AMBIGUITY_MARKERS)
    needs_questions = low_confidence or ambiguous

    if not needs_questions:
        return True, issues, warnings

    if not isinstance(questions, list) or not questions:
        message = (
            "clarifying_questions are missing despite low confidence or uncertainty language"
        )
        if low_confidence:
            issues.append(message)
            return False, issues, warnings
        warnings.append(message)
    return True, issues, warnings


def _check_confidence_consistency(prediction: dict) -> tuple[bool, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    confidence = prediction.get("confidence")
    uncertainty = _normalize(str(prediction.get("uncertainty", "")))
    if not isinstance(confidence, (int, float)):
        return True, issues, warnings

    value = float(confidence)
    if value >= _HIGH_CONFIDENCE_THRESHOLD and any(
        marker in uncertainty for marker in _UNCERTAINTY_AMBIGUITY_MARKERS
    ):
        if not any(marker in uncertainty for marker in _UNCERTAINTY_HIGH_CONFIDENCE_MARKERS):
            warnings.append(
                "confidence is high but uncertainty language suggests ambiguity"
            )

    if value < _LOW_CONFIDENCE_THRESHOLD and any(
        marker in uncertainty for marker in _UNCERTAINTY_HIGH_CONFIDENCE_MARKERS
    ):
        warnings.append("confidence is low but uncertainty language suggests high confidence")

    return True, issues, warnings


def _check_summary_not_overclaiming(prediction: dict) -> tuple[bool, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    summary = _normalize(str(prediction.get("incident_summary", "")))
    if not summary.strip():
        return True, issues, warnings

    if any(marker in summary for marker in _OVERCLAIM_MARKERS):
        warnings.append("incident_summary may overclaim beyond available evidence")

    grounding = _normalize(
        " ".join(
            [
                str(prediction.get("root_cause", "")),
                _evidence_blob(prediction.get("evidence", [])),
                str(prediction.get("uncertainty", "")),
            ]
        )
    )
    summary_tokens = _significant_tokens(summary)
    if not summary_tokens:
        return True, issues, warnings

    unsupported = [token for token in summary_tokens if token not in grounding]
    if len(unsupported) >= max(3, len(summary_tokens) // 2):
        warnings.append("incident_summary contains claims not grounded in evidence or root cause")

    return True, issues, warnings


def _check_specialists_used(prediction: dict) -> tuple[bool, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    specialists = prediction.get("specialists_used", [])
    if not isinstance(specialists, list) or not specialists:
        issues.append("specialists_used is empty")
        return False, issues, warnings
    return True, issues, warnings


def critique_prediction(prediction: dict) -> dict[str, Any]:
    """Return a deterministic quality critique for one prediction."""
    issues: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}

    contract_valid, contract_errors = _check_contract_valid(prediction)
    checks["contract_valid"] = contract_valid
    if not contract_valid:
        issues.extend(contract_errors)

    evidence_ok, evidence_issues, evidence_warnings = _check_evidence_present(prediction)
    checks["evidence_present"] = evidence_ok
    issues.extend(evidence_issues)
    warnings.extend(evidence_warnings)

    root_ok, root_issues, root_warnings = _check_root_cause_supported(prediction)
    checks["root_cause_supported"] = root_ok
    issues.extend(root_issues)
    warnings.extend(root_warnings)

    safe_ok, safe_issues, safe_warnings = _check_safe_actions(prediction)
    checks["safe_actions"] = safe_ok
    issues.extend(safe_issues)
    warnings.extend(safe_warnings)

    rollback_ok, rollback_issues, rollback_warnings = _check_rollback_present(prediction)
    checks["rollback_present"] = rollback_ok
    issues.extend(rollback_issues)
    warnings.extend(rollback_warnings)

    questions_ok, question_issues, question_warnings = _check_clarifying_questions(prediction)
    checks["clarifying_questions_present"] = questions_ok
    issues.extend(question_issues)
    warnings.extend(question_warnings)

    _confidence_ok, confidence_issues, confidence_warnings = _check_confidence_consistency(
        prediction
    )
    checks["confidence_consistent"] = not confidence_warnings
    warnings.extend(confidence_warnings)
    issues.extend(confidence_issues)

    _summary_ok, summary_issues, summary_warnings = _check_summary_not_overclaiming(prediction)
    checks["summary_grounded"] = not summary_warnings
    warnings.extend(summary_warnings)
    issues.extend(summary_issues)

    specialists_ok, specialist_issues, specialist_warnings = _check_specialists_used(prediction)
    checks["specialists_used"] = specialists_ok
    issues.extend(specialist_issues)
    warnings.extend(specialist_warnings)

    approved = not issues
    return {
        "approved": approved,
        "issues": issues,
        "warnings": warnings,
        "checks": checks,
    }


def _remove_unsafe_actions(actions: list[str]) -> tuple[list[str], list[str]]:
    kept: list[str] = []
    removed: list[str] = []
    for action in actions:
        normalized = _normalize(action)
        if any(phrase in normalized for phrase in _UNSAFE_ACTION_PHRASES):
            removed.append(action)
            continue
        kept.append(action)
    return kept, removed


def refine_prediction(prediction: dict, critique: dict) -> dict:
    """
    Apply conservative, deterministic refinements based on critique findings.

    Does not invent new evidence or rewrite root cause creatively.
    """
    refined = copy.deepcopy(prediction)
    notes: list[str] = list(refined.get("_critic_refiner_notes", []))

    if not critique.get("checks", {}).get("safe_actions", True):
        actions = refined.get("actions", [])
        if isinstance(actions, list):
            kept, removed = _remove_unsafe_actions(actions)
            if removed:
                refined["actions"] = kept
                notes.append(
                    "Removed unsafe actions flagged by critic: "
                    + "; ".join(removed)
                )

    if not critique.get("checks", {}).get("clarifying_questions_present", True):
        questions = refined.get("clarifying_questions", [])
        if not isinstance(questions, list) or not questions:
            refined["clarifying_questions"] = [_DEFAULT_CLARIFYING_QUESTION]
            notes.append("Added default clarifying question for uncertainty gap")

    if critique.get("warnings"):
        for warning in critique["warnings"]:
            if warning not in notes:
                notes.append(f"warning: {warning}")

    if notes:
        refined["_critic_refiner_notes"] = notes
    return refined


def run_critic_refiner(prediction: dict, max_iterations: int = 1) -> dict[str, Any]:
    """
    Run a bounded critic/refiner loop.

    The loop terminates after at most ``max_iterations`` refine passes.
    No live LLM or network calls are made.
    """
    if max_iterations < 0:
        raise ValueError("max_iterations must be >= 0")

    current = copy.deepcopy(prediction)
    iterations = 0
    critique = critique_prediction(current)

    while not critique["approved"] and iterations < max_iterations:
        current = refine_prediction(current, critique)
        iterations += 1
        critique = critique_prediction(current)

    return {
        "prediction": current,
        "critique": critique,
        "iterations": iterations,
        "approved": critique["approved"],
    }


def critique_predictions(payload: Any) -> dict[str, Any]:
    """Critique a predictions list or {\"predictions\": [...]} payload."""
    if isinstance(payload, dict) and "predictions" in payload:
        predictions = payload["predictions"]
    elif isinstance(payload, list):
        predictions = payload
    else:
        raise ValueError("payload must be a list or object with 'predictions' key")

    results = []
    all_approved = True
    for prediction in predictions:
        critique = critique_prediction(prediction)
        if not critique["approved"]:
            all_approved = False
        results.append(
            {
                "incident_id": prediction.get("incident_id"),
                "approved": critique["approved"],
                "issues": critique["issues"],
                "warnings": critique["warnings"],
                "checks": critique["checks"],
            }
        )

    return {
        "approved": all_approved,
        "count": len(results),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic critic/refiner quality gate for predictions"
    )
    parser.add_argument(
        "--predictions",
        required=True,
        help="Path to predictions JSON (list or {\"predictions\": [...]})",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=1,
        help="Maximum refine iterations per prediction (default: 1)",
    )
    args = parser.parse_args(argv)

    predictions_path = Path(args.predictions)
    if not predictions_path.is_file():
        predictions_path = evals_dir() / args.predictions

    payload = load_json(predictions_path)
    if isinstance(payload, dict) and "predictions" in payload:
        predictions = payload["predictions"]
    elif isinstance(payload, list):
        predictions = payload
    else:
        print(
            "error: expected list or object with 'predictions' key",
            file=sys.stderr,
        )
        return 1

    report_items = []
    all_approved = True
    for prediction in predictions:
        result = run_critic_refiner(prediction, max_iterations=args.max_iterations)
        if not result["approved"]:
            all_approved = False
        report_items.append(
            {
                "incident_id": prediction.get("incident_id"),
                "approved": result["approved"],
                "iterations": result["iterations"],
                "issues": result["critique"]["issues"],
                "warnings": result["critique"]["warnings"],
                "checks": result["critique"]["checks"],
            }
        )

    report = {
        "approved": all_approved,
        "count": len(report_items),
        "max_iterations": args.max_iterations,
        "results": report_items,
    }
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if all_approved else 1


if __name__ == "__main__":
    raise SystemExit(main())
