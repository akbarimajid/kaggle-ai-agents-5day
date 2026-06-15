"""Tests for ADK coordinator boundary (no live LLM or API key required)."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from incident_copilot import adk_agents, adk_coordinator, eval_runner, manual_investigator
from incident_copilot.manual_investigator import OUTPUT_CONTRACT_FIELDS


class AdkCoordinatorTests(unittest.TestCase):
    def test_coordinator_exists(self) -> None:
        topology = adk_coordinator.describe_agent_topology()
        self.assertEqual(
            topology["coordinator"]["name"],
            adk_agents.COORDINATOR_NAME,
        )
        self.assertEqual(topology["coordinator"]["pattern_role"], "llm_orchestrator")

    def test_all_expected_specialist_names_exist(self) -> None:
        topology = adk_coordinator.describe_agent_topology()
        specialist_names = [item["name"] for item in topology["specialists"]]
        self.assertEqual(specialist_names, list(adk_agents.SPECIALIST_AGENT_NAMES))
        self.assertIn(
            adk_agents.SUMMARY_SAFETY_AGENT_NAME,
            [item["name"] for item in topology["sequential_stage"]],
        )

    def test_topology_order_is_stable(self) -> None:
        first = adk_coordinator.describe_agent_topology()
        second = adk_coordinator.describe_agent_topology()
        self.assertEqual(first, second)
        self.assertEqual(first["patterns"]["primary"], "llm_orchestrator")
        self.assertEqual(first["patterns"]["supporting"], "sequential_reporting")
        self.assertFalse(first["live_llm_required_for_tests"])

    def test_build_incident_coordinator_offline_by_default(self) -> None:
        coordinator = adk_coordinator.build_incident_coordinator()
        self.assertIsInstance(coordinator, dict)
        self.assertIn("coordinator", coordinator)
        self.assertIn("specialists", coordinator)
        self.assertEqual(len(coordinator["specialists"]), 4)

    def test_run_adk_incident_analysis_deterministic_delegate(self) -> None:
        result = adk_coordinator.run_adk_incident_analysis(
            "INC-001",
            execution_mode="deterministic",
        )
        self.assertEqual(result["execution_mode"], "deterministic")
        self.assertEqual(result["delegated_to"], "manual_investigator")
        prediction = result["prediction"]
        for field in OUTPUT_CONTRACT_FIELDS:
            self.assertIn(field, prediction)

    def test_run_adk_incident_analysis_topology_only(self) -> None:
        result = adk_coordinator.run_adk_incident_analysis(
            "INC-002",
            execution_mode="topology_only",
        )
        self.assertNotIn("prediction", result)
        self.assertIn("topology", result)

    def test_default_execution_is_offline_safe_without_api_key(self) -> None:
        result = adk_coordinator.run_adk_incident_analysis("INC-003")
        self.assertEqual(result["execution_mode"], "deterministic")
        self.assertEqual(result["topology"]["live_llm_required_for_tests"], False)
        self.assertEqual(result["topology"]["execution_default"], "deterministic")
        self.assertEqual(result["delegated_to"], "manual_investigator")
        self.assertNotIn("live_model_executed", result)
        prediction = result["prediction"]
        for field in OUTPUT_CONTRACT_FIELDS:
            self.assertIn(field, prediction)

    def test_manual_investigator_still_scores_54_of_54(self) -> None:
        predictions = manual_investigator.investigate_all()
        report = eval_runner.score_predictions(predictions)
        self.assertEqual(report["summary"]["total_score"], 54)
        self.assertEqual(report["summary"]["max_total_score"], 54)

    def test_cli_topology_prints_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = adk_coordinator.main(["--topology"])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["coordinator"]["name"], adk_agents.COORDINATOR_NAME)


if __name__ == "__main__":
    unittest.main()
