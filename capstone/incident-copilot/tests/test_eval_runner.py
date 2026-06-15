"""Additional eval_runner CLI and scoring tests."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from incident_copilot import eval_runner
from incident_copilot.paths import evals_dir


class EvalRunnerCliTests(unittest.TestCase):
    def test_cli_prints_json(self) -> None:
        predictions_path = evals_dir() / "example-predictions.json"
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = eval_runner.main(["--predictions", str(predictions_path)])
        self.assertEqual(code, 0)
        output = json.loads(buffer.getvalue())
        self.assertIn("summary", output)
        self.assertEqual(output["summary"]["incident_count"], 3)
        self.assertEqual(output["summary"]["max_total_score"], 54)

    def test_cli_includes_new_score_fields(self) -> None:
        predictions_path = evals_dir() / "example-predictions.json"
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            eval_runner.main(["--predictions", str(predictions_path)])
        output = json.loads(buffer.getvalue())
        scores = output["incident_results"][0]["scores"]
        for key in (
            "confidence_calibration",
            "clarifying_questions_quality",
            "rollback_recommendation_quality",
            "summary_quality",
        ):
            self.assertIn(key, scores)
        self.assertEqual(scores["max_total"], 18)

    def test_missing_golden_incident_raises(self) -> None:
        with self.assertRaises(ValueError):
            eval_runner.score_predictions(
                [
                    {
                        "incident_id": "INC-999",
                        "root_cause": "",
                        "confidence": 0.5,
                        "evidence": [],
                        "clarifying_questions": [],
                        "actions": [],
                        "rollback_recommendation": "",
                        "incident_summary": "",
                        "specialists_used": [],
                        "uncertainty": "",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
