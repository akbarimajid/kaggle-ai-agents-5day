# Output contract

Defines the **AI Platform Incident Copilot** response shape for each investigated incident. Aligns with the original capstone promise and the v0 eval harness in `evals/golden-answers.json`.

## Response fields

### Incident restatement

| | |
|---|---|
| **Purpose** | Confirms the agent understood the alert: service, environment, symptom, time window |
| **Why it matters** | Prevents investigating the wrong problem; anchors human review |
| **v0 eval** | *Planned*  -  not yet a separate scored field; implied in summary quality |
| **Prediction key** | `incident_restatement` *(future)* |

### Likely root cause

| | |
|---|---|
| **Purpose** | Primary diagnosis hypothesis backed by evidence |
| **Why it matters** | Directs on-call action; core capstone deliverable |
| **v0 eval** | `root_cause_correct` (0-3)  -  keyword overlap vs golden root cause |
| **Prediction key** | `root_cause` |

### Confidence score

| | |
|---|---|
| **Purpose** | Calibrated trust signal (0.0-1.0) |
| **Why it matters** | Flags when human review is required |
| **v0 eval** | `confidence_calibration` (0-1)  -  must fall in `expected_confidence_range` |
| **Prediction key** | `confidence` |

### Evidence list with source references

| | |
|---|---|
| **Purpose** | Grounded citations from logs, metrics, k8s, airflow, deployments |
| **Why it matters** | Prevents hallucination; supports audit and postmortem |
| **v0 eval** | `evidence_quality` (0-3)  -  layer coverage + required evidence hits |
| **Prediction key** | `evidence` |

### Clarifying questions

| | |
|---|---|
| **Purpose** | Questions that reduce ambiguity before remediation |
| **Why it matters** | Acknowledges incomplete context; invites tribal knowledge |
| **v0 eval** | `clarifying_questions_quality` (0-2)  -  overlap with golden questions |
| **Prediction key** | `clarifying_questions` |

### Safe next actions

| | |
|---|---|
| **Purpose** | Recommended steps that avoid further harm |
| **Why it matters** | Operational guidance under time pressure |
| **v0 eval** | `action_safety` (0-3)  -  acceptable actions present; unsafe actions absent |
| **Prediction key** | `actions` |

### Rollback / no-rollback recommendation

| | |
|---|---|
| **Purpose** | Explicit deploy rollback guidance or confirmation that rollback is not appropriate |
| **Why it matters** | Highest-stakes incident decision for deploy-correlated failures |
| **v0 eval** | `rollback_recommendation_quality` (0-2)  -  alignment with golden recommendation |
| **Prediction key** | `rollback_recommendation` |

### What not to do

| | |
|---|---|
| **Purpose** | Explicit list of unsafe or out-of-scope actions |
| **Why it matters** | Prevents destructive troubleshooting patterns |
| **v0 eval** | Indirect via `action_safety` (0 score if unsafe actions appear in `actions`); golden `unsafe_actions` in `golden-answers.json` |
| **Prediction key** | `unsafe_actions_to_avoid` *(future)* or derived from safety check stage |

### Incident summary / postmortem draft

| | |
|---|---|
| **Purpose** | Human-readable narrative: timeline, impact, cause, remediation, follow-ups |
| **Why it matters** | Automates tedious post-incident documentation |
| **v0 eval** | `summary_quality` (0-1)  -  overlap with `expected_summary_points` |
| **Prediction key** | `incident_summary` |

## Supporting fields (v0 harness)

| Field | Purpose | v0 eval |
|-------|---------|---------|
| `specialists_used` | Which investigator agents were invoked | `specialist_selection` (0-2) |
| `uncertainty` | Free-text confidence / gap statement | `uncertainty_handling` (0-1) |

## Scoring summary

| Dimension | Max points |
|-----------|------------|
| root_cause_correct | 3 |
| evidence_quality | 3 |
| action_safety | 3 |
| specialist_selection | 2 |
| uncertainty_handling | 1 |
| confidence_calibration | 1 |
| clarifying_questions_quality | 2 |
| rollback_recommendation_quality | 2 |
| summary_quality | 1 |
| **Total per incident** | **18** |

Run scorer:

```bash
cd capstone/incident-copilot
PYTHONPATH=app python -m incident_copilot.eval_runner --predictions evals/example-predictions.json
```

## Example prediction shape (v0)

```json
{
  "incident_id": "INC-001",
  "root_cause": "...",
  "confidence": 0.88,
  "evidence": ["..."],
  "clarifying_questions": ["..."],
  "actions": ["..."],
  "rollback_recommendation": "...",
  "incident_summary": "...",
  "specialists_used": ["..."],
  "uncertainty": "..."
}
```

## Future extensions

* `incident_restatement` as scored field
* `unsafe_actions_to_avoid` as explicit output (not only via action safety)
* Loop critic stage before summary (implemented — deterministic `critic_refiner.py`)
* Optional LM-judge layer  -  v0 uses deterministic scoring only

## Related

* [golden-answers.json](../evals/golden-answers.json)
* [example-predictions.json](../evals/example-predictions.json)
* [agentic-engineering-capstone-mapping.md](./agentic-engineering-capstone-mapping.md)
