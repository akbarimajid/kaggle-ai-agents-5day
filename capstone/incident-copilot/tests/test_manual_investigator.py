"""Tests for deterministic manual investigator."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from incident_copilot import eval_runner, manual_investigator
from incident_copilot.manual_investigator import OUTPUT_CONTRACT_FIELDS


class ManualInvestigatorTests(unittest.TestCase):
    def _assert_contract_fields(self, prediction: dict) -> None:
        for field in OUTPUT_CONTRACT_FIELDS:
            self.assertIn(field, prediction, msg=f"missing field: {field}")

    def test_inc_001_root_cause_mentions_quota_and_pending_workers(self) -> None:
        prediction = manual_investigator.investigate("INC-001")
        root_cause = prediction["root_cause"].casefold()
        self.assertIn("quota", root_cause)
        self.assertTrue(
            "pending" in root_cause or "queued" in root_cause or "worker" in root_cause
        )
        self._assert_contract_fields(prediction)

    def test_inc_002_root_cause_mentions_env_and_deploy_version(self) -> None:
        prediction = manual_investigator.investigate("INC-002")
        root_cause = prediction["root_cause"].casefold()
        self.assertIn("bq_dataset_prod", root_cause)
        self.assertIn("v2.14.0", root_cause)
        self._assert_contract_fields(prediction)

    def test_inc_003_root_cause_mentions_pgbouncer_and_pool_exhaustion(self) -> None:
        prediction = manual_investigator.investigate("INC-003")
        root_cause = prediction["root_cause"].casefold()
        self.assertIn("pgbouncer", root_cause)
        self.assertTrue(
            "pool" in root_cause
            or "connection" in root_cause
            or "exhausted" in root_cause
        )
        self._assert_contract_fields(prediction)

    def test_all_mode_produces_three_predictions(self) -> None:
        predictions = manual_investigator.investigate_all()
        self.assertEqual(len(predictions), 3)
        incident_ids = {item["incident_id"] for item in predictions}
        self.assertEqual(incident_ids, {"INC-001", "INC-002", "INC-003"})
        for prediction in predictions:
            self._assert_contract_fields(prediction)

    def test_cli_single_incident_prints_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = manual_investigator.main(["--incident-id", "INC-001"])
        self.assertEqual(code, 0)
        prediction = json.loads(buffer.getvalue())
        self._assert_contract_fields(prediction)

    def test_cli_all_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "predictions.json"
            code = manual_investigator.main(
                ["--all", "--output", str(output_path)]
            )
            self.assertEqual(code, 0)
            self.assertTrue(output_path.is_file())
            predictions = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(len(predictions), 3)

    def test_predictions_score_at_least_45_of_54(self) -> None:
        predictions = manual_investigator.investigate_all()
        report = eval_runner.score_predictions(predictions)
        total = report["summary"]["total_score"]
        max_total = report["summary"]["max_total_score"]
        self.assertEqual(max_total, 54)
        self.assertGreaterEqual(total, 45, msg=json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
