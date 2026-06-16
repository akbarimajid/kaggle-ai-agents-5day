"""Tests for ADK coordinator boundary (no live LLM or API key required)."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from incident_copilot import adk_agents, adk_coordinator, adk_live, contract_validator, eval_runner, manual_investigator
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

    def test_topology_reports_live_adk_configuration_state(self) -> None:
        topology = adk_coordinator.describe_agent_topology()
        self.assertIn("live_adk_configured", topology)
        self.assertIn("live_adk", topology["live_execution_modes"])
        self.assertFalse(topology["live_adk_configured"])

    def test_is_live_adk_configured_false_without_optional_dependency(self) -> None:
        self.assertFalse(adk_live.is_live_adk_configured())
        self.assertIsNotNone(adk_live.get_live_adk_unavailability_reason())

    def test_live_mode_is_opt_in(self) -> None:
        with mock.patch(
            "incident_copilot.adk_coordinator.adk_live.run_live_adk_incident_analysis"
        ) as live_mock:
            adk_coordinator.run_adk_incident_analysis("INC-001")
            live_mock.assert_not_called()

    def test_explicit_live_mode_invokes_live_path(self) -> None:
        with mock.patch(
            "incident_copilot.adk_coordinator.adk_live.run_live_adk_incident_analysis"
        ) as live_mock:
            live_mock.side_effect = adk_live.LiveAdkUnavailableError("test unavailable")
            with self.assertRaises(adk_live.LiveAdkUnavailableError):
                adk_coordinator.run_adk_incident_analysis(
                    "INC-001",
                    execution_mode="live_adk",
                )
            live_mock.assert_called_once_with("INC-001")

    def test_live_mode_unavailable_raises_controlled_error(self) -> None:
        with self.assertRaises(adk_live.LiveAdkUnavailableError) as ctx:
            adk_live.run_live_adk_incident_analysis("INC-001")
        message = str(ctx.exception).casefold()
        self.assertTrue(
            "google-adk" in message or "credentials" in message,
            msg=str(ctx.exception),
        )

    def test_cli_default_incident_analysis_is_deterministic(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = adk_coordinator.main(["--incident-id", "INC-001"])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["execution_mode"], "deterministic")
        self.assertEqual(payload["delegated_to"], "manual_investigator")

    def test_cli_explicit_deterministic_mode_works(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = adk_coordinator.main(
                ["--incident-id", "INC-001", "--execution-mode", "deterministic"]
            )
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["execution_mode"], "deterministic")

    def test_cli_live_adk_unavailable_exits_nonzero(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = adk_coordinator.main(
                ["--incident-id", "INC-001", "--execution-mode", "live-adk"]
            )
        self.assertEqual(code, 1)
        message = stderr.getvalue().casefold()
        self.assertIn("error:", message)
        self.assertTrue("google-adk" in message or "credentials" in message)

    def test_deterministic_prediction_passes_contract_validator(self) -> None:
        result = adk_coordinator.run_adk_incident_analysis("INC-002")
        prediction = result["prediction"]
        self.assertEqual(
            contract_validator.validate_prediction(prediction),
            [],
        )


if __name__ == "__main__":
    unittest.main()
