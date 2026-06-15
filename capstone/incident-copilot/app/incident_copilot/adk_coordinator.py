"""ADK coordinator boundary for Incident Copilot (offline-safe by default)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Literal

from incident_copilot import adk_agents, manual_investigator
from incident_copilot.manual_investigator import OUTPUT_CONTRACT_FIELDS

ExecutionMode = Literal["deterministic", "topology_only", "adk_config"]

DEFAULT_EXECUTION_MODE: ExecutionMode = "deterministic"


def describe_agent_topology() -> dict[str, Any]:
    """Return a stable, serializable description of the multi-agent topology."""
    coordinator = adk_agents.get_coordinator_spec().as_dict()
    specialists = [spec.as_dict() for spec in adk_agents.get_specialist_specs()]
    sequential_stage = adk_agents.get_summary_safety_spec().as_dict()

    return {
        "version": "v0",
        "patterns": {
            "primary": "llm_orchestrator",
            "supporting": "sequential_reporting",
            "future_stretch": "critic_refiner_loop",
        },
        "coordinator": coordinator,
        "specialists": specialists,
        "sequential_stage": [sequential_stage],
        "state_keys": [
            "investigation_trace",
            "evidence_bundle",
            "diagnosis_draft",
            "remediation_plan",
            "incident_summary",
        ],
        "execution_default": DEFAULT_EXECUTION_MODE,
        "adk_installed": adk_agents.adk_available(),
        "live_llm_required_for_tests": False,
    }


def build_incident_coordinator(*, materialize_adk: bool = False) -> dict[str, Any] | Any:
    """
    Build the incident coordinator boundary.

    Default: offline AgentSpec descriptors (no API key, no live model).
    When materialize_adk=True and google-adk is installed, returns ADK Agent objects.
    """
    topology = describe_agent_topology()
    if not materialize_adk:
        return topology

    coordinator_agent = adk_agents.build_coordinator_adk_agent()
    reporting_pipeline = adk_agents.build_reporting_pipeline_adk_agent()
    return {
        "topology": topology,
        "coordinator_agent": coordinator_agent,
        "reporting_pipeline": reporting_pipeline,
        "specialist_agents": adk_agents.build_specialist_adk_agents(),
    }


def run_adk_incident_analysis(
    incident_id: str,
    *,
    execution_mode: ExecutionMode = DEFAULT_EXECUTION_MODE,
) -> dict[str, Any]:
    """
    Run incident analysis through the ADK coordinator boundary.

    Safe defaults:
    - deterministic: delegate to manual_investigator (no live LLM)
    - topology_only: return topology/config only
    - adk_config: build ADK objects but do not execute a live model
    """
    topology = describe_agent_topology()
    result: dict[str, Any] = {
        "incident_id": incident_id,
        "execution_mode": execution_mode,
        "topology": topology,
    }

    if execution_mode == "topology_only":
        return result

    if execution_mode == "deterministic":
        prediction = manual_investigator.investigate(incident_id)
        _validate_prediction_contract(prediction)
        result["prediction"] = prediction
        result["delegated_to"] = "manual_investigator"
        return result

    if execution_mode == "adk_config":
        if not adk_agents.adk_available():
            raise ImportError(
                "execution_mode=adk_config requires google-adk. "
                "Install with: pip install -r requirements-adk.txt"
            )
        result["adk_config"] = build_incident_coordinator(materialize_adk=True)
        result["live_model_executed"] = False
        return result

    raise ValueError(f"Unsupported execution_mode: {execution_mode}")


def _validate_prediction_contract(prediction: dict[str, Any]) -> None:
    missing = [field for field in OUTPUT_CONTRACT_FIELDS if field not in prediction]
    if missing:
        raise ValueError(f"Prediction missing output contract fields: {missing}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Incident Copilot ADK coordinator boundary (offline-safe)"
    )
    parser.add_argument(
        "--topology",
        action="store_true",
        help="Print the ADK agent topology as JSON",
    )
    parser.add_argument(
        "--incident-id",
        help="Run offline incident analysis for one incident (deterministic delegate)",
    )
    parser.add_argument(
        "--execution-mode",
        choices=["deterministic", "topology_only", "adk_config"],
        default=DEFAULT_EXECUTION_MODE,
        help="Analysis mode (default: deterministic, no live LLM)",
    )
    args = parser.parse_args(argv)

    if args.topology:
        json.dump(describe_agent_topology(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if args.incident_id:
        payload = run_adk_incident_analysis(
            args.incident_id,
            execution_mode=args.execution_mode,
        )
        json.dump(payload, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0

    parser.error("Provide --topology or --incident-id")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
