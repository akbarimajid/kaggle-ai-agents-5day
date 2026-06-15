"""Tests for incident_copilot mock tools and eval runner."""

from __future__ import annotations

import unittest

from incident_copilot import eval_runner, tools
from incident_copilot.paths import validate_incident_id


class ToolTests(unittest.TestCase):
    def test_search_logs_inc001_quota_evidence(self) -> None:
        matches = tools.search_logs("INC-001", "insufficient cpu")
        self.assertTrue(matches)
        self.assertTrue(any("insufficient cpu" in m["matched_text"].casefold() for m in matches))
        self.assertEqual(matches[0]["source_file"], "data/logs/INC-001.log")

    def test_search_logs_inc002_env_var(self) -> None:
        matches = tools.search_logs("INC-002", "BQ_DATASET_PROD")
        self.assertTrue(matches)
        self.assertIn("KeyError", matches[0]["message"])

    def test_search_logs_inc003_connections(self) -> None:
        matches = tools.search_logs("INC-003", "too many connections")
        self.assertTrue(matches)

    def test_search_logs_no_match_returns_empty(self) -> None:
        self.assertEqual(tools.search_logs("INC-001", "nonexistent-phrase-xyz"), [])

    def test_get_airflow_status_fields(self) -> None:
        status = tools.get_airflow_status("INC-001")
        self.assertEqual(status["incident_id"], "INC-001")
        self.assertEqual(status["queued_task_count"], 51)
        self.assertEqual(status["worker_pods_available"], 0)
        self.assertIn("source_file", status)

    def test_get_airflow_status_inc003_unhealthy(self) -> None:
        status = tools.get_airflow_status("INC-003")
        self.assertFalse(status["scheduler_healthy"])

    def test_get_k8s_events_inc001(self) -> None:
        events = tools.get_k8s_events("INC-001")
        self.assertGreaterEqual(len(events), 3)
        reasons = {e["event_reason"] for e in events}
        self.assertIn("FailedScheduling", reasons)
        self.assertTrue(any("quota" in e["message"].casefold() for e in events))

    def test_get_k8s_events_inc002(self) -> None:
        events = tools.get_k8s_events("INC-002")
        self.assertTrue(any("BQ_DATASET_PROD" in e["message"] for e in events))

    def test_get_metrics_inc001(self) -> None:
        metrics = tools.get_metrics("INC-001")
        names = {s["name"] for s in metrics["series"]}
        self.assertIn("k8s.namespace.quota.cpu.used_percent", names)
        self.assertIn("airflow.workers.available", names)

    def test_get_metrics_inc003_pgbouncer(self) -> None:
        metrics = tools.get_metrics("INC-003")
        names = {s["name"] for s in metrics["series"]}
        self.assertIn("pgbouncer.pool.waiting_clients", names)

    def test_search_runbooks_queued(self) -> None:
        sections = tools.search_runbooks("queued")
        self.assertTrue(any("queued" in s["title"].casefold() for s in sections))

    def test_search_runbooks_deploy(self) -> None:
        sections = tools.search_runbooks("deployment")
        self.assertTrue(sections)
        self.assertTrue(
            any("deploy" in s["source_file"].casefold() or "deploy" in s["title"].casefold() for s in sections)
        )

    def test_get_deployments_inc002(self) -> None:
        deployments = tools.get_deployments("INC-002")
        self.assertEqual(len(deployments), 2)
        self.assertEqual(deployments[0]["version"], "v2.14.0")

    def test_get_deployments_inc001_empty(self) -> None:
        self.assertEqual(tools.get_deployments("INC-001"), [])

    def test_unknown_incident_raises(self) -> None:
        with self.assertRaises(ValueError):
            validate_incident_id("INC-999")
        with self.assertRaises(ValueError):
            tools.get_metrics("INC-999")


class EvalRunnerTests(unittest.TestCase):
    def test_scores_example_predictions(self) -> None:
        from incident_copilot.paths import evals_dir, load_json

        predictions = load_json(evals_dir() / "example-predictions.json")["predictions"]
        report = eval_runner.score_predictions(predictions)
        self.assertEqual(report["summary"]["incident_count"], 3)
        self.assertEqual(report["summary"]["max_total_score"], 54)
        self.assertGreater(report["summary"]["total_score"], 0)
        self.assertLess(report["summary"]["total_score"], report["summary"]["max_total_score"])

    def test_per_incident_shape(self) -> None:
        from incident_copilot.paths import evals_dir, load_json

        predictions = load_json(evals_dir() / "example-predictions.json")["predictions"]
        report = eval_runner.score_predictions(predictions)
        for result in report["incident_results"]:
            scores = result["scores"]
            self.assertEqual(scores["max_total"], 18)
            for key in eval_runner.SCORE_KEYS:
                self.assertIn(key, scores)

    def test_inc003_lower_than_inc001(self) -> None:
        from incident_copilot.paths import evals_dir, load_json

        predictions = load_json(evals_dir() / "example-predictions.json")["predictions"]
        report = eval_runner.score_predictions(predictions)
        by_id = {r["incident_id"]: r["scores"]["total"] for r in report["incident_results"]}
        self.assertGreater(by_id["INC-001"], by_id["INC-003"])

    def test_inc003_has_imperfect_new_fields(self) -> None:
        from incident_copilot.paths import evals_dir, load_json

        predictions = load_json(evals_dir() / "example-predictions.json")["predictions"]
        report = eval_runner.score_predictions(predictions)
        by_id = {r["incident_id"]: r["scores"] for r in report["incident_results"]}
        inc003 = by_id["INC-003"]
        self.assertEqual(inc003["confidence_calibration"], 0)
        self.assertEqual(inc003["clarifying_questions_quality"], 0)
        self.assertEqual(inc003["rollback_recommendation_quality"], 0)


if __name__ == "__main__":
    unittest.main()
