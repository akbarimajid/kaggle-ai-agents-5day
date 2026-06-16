"""Optional live ADK execution helpers (explicit opt-in only)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from incident_copilot import adk_agents, contract_validator, manual_investigator
from incident_copilot.paths import project_root, read_text, validate_incident_id

APP_NAME = "incident_copilot"

LIVE_ADK_API_KEY_ENV_VARS = (
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
)

AGENT_PROMPT_FILES: dict[str, str] = {
    adk_agents.COORDINATOR_NAME: "coordinator.md",
    "AirflowInvestigatorAgent": "airflow-investigator.md",
    "KubernetesInvestigatorAgent": "kubernetes-investigator.md",
    "LogsMetricsInvestigatorAgent": "logs-metrics-investigator.md",
    "RunbookAdvisorAgent": "runbook-advisor.md",
    adk_agents.SUMMARY_SAFETY_AGENT_NAME: "summary-safety.md",
}


class LiveAdkUnavailableError(RuntimeError):
    """Raised when live ADK execution was requested but prerequisites are missing."""


def _has_live_api_key() -> bool:
    return any(os.environ.get(name, "").strip() for name in LIVE_ADK_API_KEY_ENV_VARS)


def _has_vertex_credentials() -> bool:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    return bool(project and credentials)


def _has_live_credentials() -> bool:
    return _has_live_api_key() or _has_vertex_credentials()


def get_live_adk_unavailability_reason() -> str | None:
    if not adk_agents.adk_available():
        return (
            "google-adk is not installed. "
            "Install with: pip install -r requirements-adk.txt"
        )
    if not _has_live_credentials():
        return (
            "Live ADK credentials are not configured. "
            "Set GOOGLE_API_KEY or GEMINI_API_KEY, or configure Vertex AI with "
            "GOOGLE_CLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALS."
        )
    return None


def is_live_adk_configured() -> bool:
    """Return True when optional ADK and live credentials are both available."""
    return get_live_adk_unavailability_reason() is None


def load_agent_prompt(agent_name: str) -> str:
    filename = AGENT_PROMPT_FILES[agent_name]
    path = project_root() / "prompts" / filename
    if not path.is_file():
        raise FileNotFoundError(f"Prompt template not found for {agent_name}: {path}")
    return read_text(path)


def _format_incident_request(incident: dict[str, Any]) -> str:
    return (
        "Investigate this platform incident and produce a contract-valid JSON prediction.\n"
        f"incident_id: {incident['incident_id']}\n"
        f"title: {incident.get('title', '')}\n"
        f"symptom: {incident.get('symptom', '')}\n"
        f"severity: {incident.get('severity', '')}\n"
        f"environment: {incident.get('environment', '')}\n"
        "Use mock tools only. Cite evidence from tool outputs. "
        "Return the final prediction as a single JSON object matching the v0 output contract."
    )


def _build_prompted_specialist_agents() -> dict[str, Any]:
    from google.adk.tools import FunctionTool

    from incident_copilot import tools

    tool_bindings: dict[str, Any] = {
        "get_airflow_status": tools.get_airflow_status,
        "get_deployments": tools.get_deployments,
        "get_k8s_events": tools.get_k8s_events,
        "search_logs": tools.search_logs,
        "get_metrics": tools.get_metrics,
        "search_runbooks": tools.search_runbooks,
    }

    agents: dict[str, Any] = {}
    for spec in adk_agents.get_specialist_specs():
        function_tools = [
            FunctionTool(tool_bindings[tool_name]) for tool_name in spec.tools
        ]
        instruction = load_agent_prompt(spec.name)
        agents[spec.name] = _build_adk_agent_with_instruction(
            spec, function_tools, instruction
        )
    return agents


def _build_adk_agent_with_instruction(
    spec: adk_agents.AgentSpec,
    tool_objects: list[Any],
    instruction: str,
) -> Any:
    from google.adk.agents import Agent

    return Agent(
        name=spec.name,
        model=adk_agents.DEFAULT_MODEL,
        description=spec.description,
        instruction=instruction,
        tools=tool_objects,
        output_key=spec.output_key,
    )


def _build_live_root_agent() -> Any:
    from google.adk.agents import SequentialAgent
    from google.adk.tools import AgentTool

    specialists = _build_prompted_specialist_agents()
    coordinator_spec = adk_agents.get_coordinator_spec()
    coordinator_tools = [AgentTool(agent) for agent in specialists.values()]
    coordinator = _build_adk_agent_with_instruction(
        coordinator_spec,
        coordinator_tools,
        load_agent_prompt(coordinator_spec.name),
    )

    summary_spec = adk_agents.get_summary_safety_spec()
    summary_agent = _build_adk_agent_with_instruction(
        summary_spec,
        [],
        load_agent_prompt(summary_spec.name),
    )

    return SequentialAgent(
        name="IncidentCopilotLivePipeline",
        sub_agents=[coordinator, summary_agent],
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Live ADK response was empty")

    try:
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if match:
        payload = json.loads(match.group(0))
        if isinstance(payload, dict):
            return payload

    raise ValueError("Live ADK response did not contain a JSON prediction object")


def _collect_final_response_text(events: Any) -> str:
    final_text = ""
    for event in events:
        content = getattr(event, "content", None)
        if not content or not getattr(content, "parts", None):
            continue
        for part in content.parts:
            text = getattr(part, "text", None)
            if text:
                final_text = text
    return final_text


def _execute_live_adk_pipeline(incident_id: str, user_message: str) -> dict[str, Any]:
    import asyncio

    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    session_service = InMemorySessionService()
    user_id = "incident_copilot_user"

    async def _create_session() -> Any:
        return await session_service.create_session(
            state={"incident_id": incident_id},
            app_name=APP_NAME,
            user_id=user_id,
        )

    session = asyncio.run(_create_session())
    runner = Runner(
        app_name=APP_NAME,
        agent=_build_live_root_agent(),
        session_service=session_service,
    )
    content = types.Content(role="user", parts=[types.Part(text=user_message)])

    if hasattr(runner, "run"):
        events = runner.run(
            user_id=user_id,
            session_id=session.id,
            new_message=content,
        )
        response_text = _collect_final_response_text(events)
    else:

        async def _run() -> str:
            final_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=content,
            ):
                content_obj = getattr(event, "content", None)
                if not content_obj or not getattr(content_obj, "parts", None):
                    continue
                for part in content_obj.parts:
                    text = getattr(part, "text", None)
                    if text:
                        final_text = text
            return final_text

        response_text = asyncio.run(_run())

    prediction = _extract_json_object(response_text)
    if prediction.get("incident_id") != incident_id:
        prediction["incident_id"] = incident_id
    return prediction


def _validate_live_prediction(prediction: dict[str, Any]) -> None:
    errors = contract_validator.validate_prediction(prediction)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Live ADK output failed contract validation: {joined}")


def run_live_adk_incident_analysis(incident_id: str) -> dict[str, Any]:
    """
    Run live ADK incident analysis.

    Requires optional google-adk install and configured credentials.
    Raises LiveAdkUnavailableError when prerequisites are missing.
    """
    validate_incident_id(incident_id)
    reason = get_live_adk_unavailability_reason()
    if reason:
        raise LiveAdkUnavailableError(reason)

    incident = manual_investigator.load_incident(incident_id)
    user_message = _format_incident_request(incident)
    prediction = _execute_live_adk_pipeline(incident_id, user_message)
    _validate_live_prediction(prediction)

    return {
        "incident_id": incident_id,
        "execution_mode": "live_adk",
        "live_model_executed": True,
        "prompt_templates": list(AGENT_PROMPT_FILES.values()),
        "prediction": prediction,
    }
