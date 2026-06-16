"""Tests for deterministic critic/refiner quality gate."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from incident_copilot import contract_validator, critic_refiner, manual_investigator
from incident_copilot.paths import evals_dir


def _valid_prediction() -> dict:
    return dict(manual_investigator.investigate("INC-001"))


class CriticRefinerTests(unittest.TestCase):
    def test_valid_manual_investigator_prediction_is_approved(self) -> None:
        prediction = _valid_prediction()
        critique = critic_refiner.critique_prediction(prediction)
        self.assertTrue(critique["approved"])
        self.assertEqual(critique["issues"], [])
        self.assertTrue(critique["checks"]["contract_valid"])
        self.assertTrue(critique["checks"]["evidence_present"])
        self.assertTrue(critique["checks"]["safe_actions"])
        self.assertTrue(critique["checks"]["rollback_present"])

    def test_all_manual_investigator_predictions_are_approved(self) -> None:
        for prediction in manual_investigator.investigate_all():
            critique = critic_refiner.critique_prediction(prediction)
            self.assertTrue(
                critique["approved"],
                msg=f"{prediction['incident_id']}: {critique['issues']}",
            )

    def test_missing_output_contract_field_is_rejected(self) -> None:
        prediction = _valid_prediction()
        del prediction["root_cause"]
        critique = critic_refiner.critique_prediction(prediction)
        self.assertFalse(critique["approved"])
        self.assertFalse(critique["checks"]["contract_valid"])
        self.assertTrue(
            any("root_cause: missing required field" in issue for issue in critique["issues"])
        )

    def test_unsupported_root_cause_is_rejected(self) -> None:
        prediction = _valid_prediction()
        prediction["root_cause"] = (
            "Unrelated network partition in a different region caused the outage."
        )
        critique = critic_refiner.critique_prediction(prediction)
        self.assertFalse(critique["approved"])
        self.assertFalse(critique["checks"]["root_cause_supported"])
        self.assertIn(
            "root_cause is not supported by cited evidence keywords",
            critique["issues"],
        )

    def test_unsafe_destructive_action_is_rejected(self) -> None:
        prediction = _valid_prediction()
        prediction["actions"] = [
            "Restart all scheduler pods immediately to clear errors",
            "Review scheduler logs for connection errors",
        ]
        critique = critic_refiner.critique_prediction(prediction)
        self.assertFalse(critique["approved"])
        self.assertFalse(critique["checks"]["safe_actions"])
        self.assertTrue(
            any("unsafe or destructive" in issue for issue in critique["issues"])
        )

    def test_missing_rollback_recommendation_is_rejected(self) -> None:
        prediction = _valid_prediction()
        prediction["rollback_recommendation"] = "   "
        critique = critic_refiner.critique_prediction(prediction)
        self.assertFalse(critique["approved"])
        self.assertFalse(critique["checks"]["rollback_present"])
        self.assertIn(
            "rollback_recommendation is missing or empty",
            critique["issues"],
        )

    def test_low_confidence_without_clarifying_questions_is_rejected(self) -> None:
        prediction = _valid_prediction()
        prediction["confidence"] = 0.55
        prediction["uncertainty"] = "Low confidence; several signals are missing."
        prediction["clarifying_questions"] = []
        critique = critic_refiner.critique_prediction(prediction)
        self.assertFalse(critique["approved"])
        self.assertFalse(critique["checks"]["clarifying_questions_present"])
        self.assertIn(
            "clarifying_questions are missing despite low confidence or uncertainty language",
            critique["issues"],
        )

    def test_ambiguous_uncertainty_without_questions_warns(self) -> None:
        prediction = _valid_prediction()
        prediction["uncertainty"] = "Partial evidence; may need further DB review."
        prediction["clarifying_questions"] = []
        critique = critic_refiner.critique_prediction(prediction)
        self.assertTrue(
            any("clarifying_questions" in warning for warning in critique["warnings"])
        )

    def test_bounded_loop_stops_at_max_iterations(self) -> None:
        prediction = _valid_prediction()
        prediction["root_cause"] = (
            "Unrelated network partition in a different region caused the outage."
        )

        with mock.patch(
            "incident_copilot.critic_refiner.refine_prediction",
            wraps=critic_refiner.refine_prediction,
        ) as refine_mock:
            result = critic_refiner.run_critic_refiner(prediction, max_iterations=2)
            self.assertEqual(result["iterations"], 2)
            self.assertEqual(refine_mock.call_count, 2)

        self.assertFalse(result["approved"])

        approved = critic_refiner.run_critic_refiner(_valid_prediction(), max_iterations=0)
        self.assertEqual(approved["iterations"], 0)
        self.assertTrue(approved["approved"])

    def test_refine_prediction_makes_conservative_safe_changes(self) -> None:
        prediction = _valid_prediction()
        prediction["actions"] = [
            "Restart all scheduler pods immediately to clear errors",
            "Review scheduler logs for connection errors",
        ]
        prediction["clarifying_questions"] = []
        prediction["confidence"] = 0.55
        prediction["uncertainty"] = "Low confidence; several signals are missing."

        critique = critic_refiner.critique_prediction(prediction)
        refined = critic_refiner.refine_prediction(prediction, critique)
        self.assertNotIn(
            "Restart all scheduler pods immediately to clear errors",
            refined["actions"],
        )
        self.assertEqual(len(refined["clarifying_questions"]), 1)
        self.assertIn("_critic_refiner_notes", refined)

    def test_no_live_adk_or_llm_execution_is_required(self) -> None:
        with mock.patch(
            "incident_copilot.critic_refiner.contract_validator.validate_prediction",
            wraps=contract_validator.validate_prediction,
        ) as validator_mock:
            critique = critic_refiner.critique_prediction(_valid_prediction())
            self.assertTrue(critique["approved"])
            validator_mock.assert_called()

    def test_contract_validator_remains_used(self) -> None:
        prediction = _valid_prediction()
        del prediction["confidence"]
        critique = critic_refiner.critique_prediction(prediction)
        self.assertFalse(critique["checks"]["contract_valid"])
        self.assertIn("confidence: missing required field", critique["issues"])

    def test_empty_specialists_used_is_rejected(self) -> None:
        prediction = _valid_prediction()
        prediction["specialists_used"] = []
        critique = critic_refiner.critique_prediction(prediction)
        self.assertFalse(critique["approved"])
        self.assertFalse(critique["checks"]["specialists_used"])

    def test_cli_valid_predictions_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.json"
            path.write_text(
                json.dumps(manual_investigator.investigate_all()),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = critic_refiner.main(["--predictions", str(path)])
            self.assertEqual(code, 0)
            report = json.loads(buffer.getvalue())
            self.assertTrue(report["approved"])
            self.assertEqual(report["count"], 3)

    def test_cli_invalid_predictions_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            bad = _valid_prediction()
            bad["rollback_recommendation"] = ""
            path.write_text(json.dumps([bad]), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = critic_refiner.main(["--predictions", str(path)])
            self.assertEqual(code, 1)
            report = json.loads(buffer.getvalue())
            self.assertFalse(report["approved"])

    def test_example_predictions_inc003_is_not_approved_by_critic(self) -> None:
        payload = json.loads(
            (evals_dir() / "example-predictions.json").read_text(encoding="utf-8")
        )
        inc003 = next(
            item for item in payload["predictions"] if item["incident_id"] == "INC-003"
        )
        critique = critic_refiner.critique_prediction(inc003)
        self.assertFalse(critique["approved"])


if __name__ == "__main__":
    unittest.main()
