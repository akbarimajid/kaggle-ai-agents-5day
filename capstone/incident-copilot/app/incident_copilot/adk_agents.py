"""ADK specialist agent definitions for Incident Copilot (optional dependency)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from incident_copilot import tools

COORDINATOR_NAME = "IncidentCoordinatorAgent"
SUMMARY_SAFETY_AGENT_NAME = "SummarySafetyAgent"

SPECIALIST_AGENT_NAMES = (
    "AirflowInvestigatorAgent",
    "KubernetesInvestigatorAgent",
    "LogsMetricsInvestigatorAgent",
    "RunbookAdvisorAgent",
)

SEQUENTIAL_STAGE_NAMES = (SUMMARY_SAFETY_AGENT_NAME,)

DEFAULT_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class AgentSpec:
    """Offline-safe agent descriptor used when ADK is not installed."""

    name: str
    description: str
    instruction: str
    tools: tuple[str, ...]
    output_key: str | None = None
    pattern_role: str = "specialist"

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "instruction": self.instruction,
            "tools": list(self.tools),
            "pattern_role": self.pattern_role,
        }
        if self.output_key:
            payload["output_key"] = self.output_key
        return payload


_SPECIALIST_SPECS: dict[str, AgentSpec] = {
    "AirflowInvestigatorAgent": AgentSpec(
        name="AirflowInvestigatorAgent",
        description="Investigates Airflow scheduler health, task queues, and deployment events.",
        instruction=(
            "Gather Airflow status and deployment metadata for the incident. "
            "Cite source files and summarize queue, worker, scheduler, and deploy signals."
        ),
        tools=("get_airflow_status", "get_deployments"),
        output_key="airflow_findings",
    ),
    "KubernetesInvestigatorAgent": AgentSpec(
        name="KubernetesInvestigatorAgent",
        description="Investigates Kubernetes scheduling, pod, and ConfigMap events.",
        instruction=(
            "Inspect Kubernetes events for scheduling failures, pod health, and config changes. "
            "Return cited findings for the evidence bundle."
        ),
        tools=("get_k8s_events",),
        output_key="kubernetes_findings",
    ),
    "LogsMetricsInvestigatorAgent": AgentSpec(
        name="LogsMetricsInvestigatorAgent",
        description="Correlates logs and metrics snapshots for incident symptoms.",
        instruction=(
            "Search logs and read metrics for patterns matching the incident symptom. "
            "Return cited log lines and metric highlights."
        ),
        tools=("search_logs", "get_metrics"),
        output_key="logs_metrics_findings",
    ),
    "RunbookAdvisorAgent": AgentSpec(
        name="RunbookAdvisorAgent",
        description="Finds runbook guidance relevant to the incident symptom.",
        instruction=(
            "Search runbooks for safe remediation patterns and escalation guidance. "
            "Return cited runbook sections only; do not invent procedures."
        ),
        tools=("search_runbooks",),
        output_key="runbook_guidance",
    ),
}

_SUMMARY_SAFETY_SPEC = AgentSpec(
    name=SUMMARY_SAFETY_AGENT_NAME,
    description=(
        "Sequential reporting stage that validates evidence, drafts diagnosis, "
        "checks remediation safety, and produces the incident summary."
    ),
    instruction=(
        "Using the evidence bundle and investigation trace, produce a contract-valid "
        "incident response: root cause, evidence, safe actions, clarifying questions, "
        "rollback recommendation, confidence, uncertainty, and incident summary. "
        "Reject unsafe remediation steps."
    ),
    tools=(),
    output_key="incident_summary",
    pattern_role="sequential_reporting",
)

_COORDINATOR_SPEC = AgentSpec(
    name=COORDINATOR_NAME,
    description="LLM orchestrator that selects specialist investigators based on symptoms.",
    instruction=(
        "Triage the incident using symptom and title. Call the minimum specialist agents "
        "needed to populate evidence_bundle. Do not diagnose until evidence is collected. "
        "Prefer Kubernetes and metrics for queued tasks, deployments and logs for deploy "
        "failures, and scheduler metrics plus logs for scheduler instability."
    ),
    tools=SPECIALIST_AGENT_NAMES,
    output_key="investigation_trace",
    pattern_role="llm_orchestrator",
)

_TOOL_BINDINGS: dict[str, Callable[..., Any]] = {
    "get_airflow_status": tools.get_airflow_status,
    "get_deployments": tools.get_deployments,
    "get_k8s_events": tools.get_k8s_events,
    "search_logs": tools.search_logs,
    "get_metrics": tools.get_metrics,
    "search_runbooks": tools.search_runbooks,
}


def adk_available() -> bool:
    """Return True when google-adk is installed."""
    try:
        import google.adk  # noqa: F401

        return True
    except ImportError:
        return False


def get_specialist_specs() -> tuple[AgentSpec, ...]:
    return tuple(_SPECIALIST_SPECS[name] for name in SPECIALIST_AGENT_NAMES)


def get_summary_safety_spec() -> AgentSpec:
    return _SUMMARY_SAFETY_SPEC


def get_coordinator_spec() -> AgentSpec:
    return _COORDINATOR_SPEC


def _build_adk_agent(spec: AgentSpec, tool_objects: list[Any] | None = None) -> Any:
    from google.adk.agents import Agent

    return Agent(
        name=spec.name,
        model=DEFAULT_MODEL,
        description=spec.description,
        instruction=spec.instruction,
        tools=tool_objects or [],
        output_key=spec.output_key,
    )


def build_specialist_adk_agents() -> dict[str, Any]:
    """Build ADK specialist Agent objects. Requires optional google-adk install."""
    if not adk_available():
        raise ImportError(
            "google-adk is not installed. Install with: "
            "pip install -r requirements-adk.txt"
        )

    from google.adk.tools import FunctionTool

    agents: dict[str, Any] = {}
    for spec in get_specialist_specs():
        function_tools = [
            FunctionTool(_TOOL_BINDINGS[tool_name]) for tool_name in spec.tools
        ]
        agents[spec.name] = _build_adk_agent(spec, function_tools)
    return agents


def build_summary_safety_adk_agent() -> Any:
    if not adk_available():
        raise ImportError(
            "google-adk is not installed. Install with: "
            "pip install -r requirements-adk.txt"
        )
    return _build_adk_agent(get_summary_safety_spec())


def build_specialist_agent_tool_map() -> dict[str, Any]:
    """Build specialist agents wrapped as ADK AgentTool objects for the coordinator."""
    if not adk_available():
        raise ImportError(
            "google-adk is not installed. Install with: "
            "pip install -r requirements-adk.txt"
        )

    from google.adk.tools import AgentTool

    specialists = build_specialist_adk_agents()
    return {name: AgentTool(agent) for name, agent in specialists.items()}


def build_coordinator_adk_agent() -> Any:
    """Build the IncidentCoordinatorAgent ADK object (offline until executed)."""
    if not adk_available():
        raise ImportError(
            "google-adk is not installed. Install with: "
            "pip install -r requirements-adk.txt"
        )

    agent_tools = list(build_specialist_agent_tool_map().values())
    return _build_adk_agent(get_coordinator_spec(), agent_tools)


def build_reporting_pipeline_adk_agent() -> Any:
    """Build the sequential reporting stage with SummarySafetyAgent."""
    if not adk_available():
        raise ImportError(
            "google-adk is not installed. Install with: "
            "pip install -r requirements-adk.txt"
        )

    from google.adk.agents import SequentialAgent

    return SequentialAgent(
        name="IncidentReportPipeline",
        sub_agents=[build_summary_safety_adk_agent()],
    )
