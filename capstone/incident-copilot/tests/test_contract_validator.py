"""Tests for output contract validator."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from incident_copilot import contract_validator, manual_investigator
from incident_copilot.paths import evals_dir


def _valid_prediction() -> dict:
    return dict(manual_investigator.investigate("INC-001"))


class ContractValidatorTests(unittest.TestCase):
    def test_valid_manual_investigator_prediction(self) -> None:
        prediction = _valid_prediction()
        self.assertEqual(contract_validator.validate_prediction(prediction), [])

    def test_valid_example_predictions_file(self) -> None:
        payload = json.loads(
            (evals_dir() / "example-predictions.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract_validator.validate_predictions(payload), [])

    def test_all_manual_investigator_predictions_are_valid(self) -> None:
        predictions = manual_investigator.investigate_all()
        self.assertEqual(contract_validator.validate_predictions(predictions), [])

    def test_missing_required_fields(self) -> None:
        prediction = _valid_prediction()
        del prediction["root_cause"]
        del prediction["confidence"]

        errors = contract_validator.validate_prediction(prediction)
        self.assertIn("root_cause: missing required field", errors)
        self.assertIn("confidence: missing required field", errors)

    def test_wrong_field_types(self) -> None:
        prediction = _valid_prediction()
        prediction["confidence"] = "high"
        prediction["root_cause"] = 42
        prediction["uncertainty"] = ["not", "a", "string"]

        errors = contract_validator.validate_prediction(prediction)
        self.assertIn("confidence: expected number, got str", errors)
        self.assertIn("root_cause: expected string, got int", errors)
        self.assertIn("uncertainty: expected string, got list", errors)

    def test_invalid_nested_list_shape(self) -> None:
        prediction = _valid_prediction()
        prediction["evidence"] = [
            "data/logs/INC-001.log - valid line",
            {"source": "data/metrics/INC-001.json", "detail": "bad shape"},
        ]
        prediction["specialists_used"] = "AirflowInvestigatorAgent"

        errors = contract_validator.validate_prediction(prediction)
        self.assertIn(
            "evidence[1]: expected string, got dict",
            errors,
        )
        self.assertIn(
            "specialists_used: expected list, got str",
            errors,
        )

    def test_confidence_out_of_range(self) -> None:
        prediction = _valid_prediction()
        prediction["confidence"] = 1.5
        errors = contract_validator.validate_prediction(prediction)
        self.assertIn(
            "confidence: must be between 0.0 and 1.0, got 1.5",
            errors,
        )

    def test_unknown_incident_id(self) -> None:
        prediction = _valid_prediction()
        prediction["incident_id"] = "INC-999"
        errors = contract_validator.validate_prediction(prediction)
        self.assertIn("incident_id: unknown incident_id 'INC-999'", errors)

    def test_empty_string_fields(self) -> None:
        prediction = _valid_prediction()
        prediction["incident_summary"] = "   "
        errors = contract_validator.validate_prediction(prediction)
        self.assertIn("incident_summary: must be a non-empty string", errors)

    def test_empty_list_item(self) -> None:
        prediction = _valid_prediction()
        prediction["actions"] = ["valid action", "  "]
        errors = contract_validator.validate_prediction(prediction)
        self.assertIn("actions[1]: must be a non-empty string", errors)

    def test_validate_predictions_reports_indexed_paths(self) -> None:
        valid = _valid_prediction()
        invalid = _valid_prediction()
        invalid["confidence"] = "not-a-number"

        errors = contract_validator.validate_predictions([valid, invalid])
        self.assertEqual(errors, ["[1].confidence: expected number, got str"])

    def test_cli_valid_predictions(self) -> None:
        predictions_path = evals_dir() / "example-predictions.json"
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = contract_validator.main(["--predictions", str(predictions_path)])
        self.assertEqual(code, 0)
        self.assertIn("OK", buffer.getvalue())

    def test_cli_invalid_predictions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                json.dumps([{"incident_id": "INC-001", "confidence": "high"}]),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = contract_validator.main(["--predictions", str(path)])
            self.assertEqual(code, 1)
            self.assertIn("confidence: expected number, got str", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
