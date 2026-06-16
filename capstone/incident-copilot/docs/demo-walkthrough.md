# Demo walkthrough

This guide walks through the **AI Platform Incident Copilot** capstone as a local,
deterministic learning demo. No cloud credentials, live LLMs, or production integrations
are required.

## Purpose of the demo

The demo shows how the capstone works end-to-end:

1. Mock incident data and read-only tools supply evidence.
2. The deterministic manual investigator produces contract-shaped predictions.
3. The output contract validator, eval runner, and critic/refiner gate quality.
4. The ADK coordinator layer describes multi-agent topology and can delegate to the same
   deterministic baseline.

Everything runs offline with stdlib Python. The goal is learning and verification, not
production incident response.

## Prerequisites

* Python 3.10+ (stdlib only for the deterministic path)
* Git clone of this repository
* Working directory: `capstone/incident-copilot`

Optional (not required for this walkthrough):

* `pip install -r requirements-adk.txt` for ADK object materialization or live mode
* `GOOGLE_API_KEY` or `GEMINI_API_KEY` only if you explicitly opt into live ADK mode

## Local setup

From the repository root:

```bash
cd capstone/incident-copilot
```

Set `PYTHONPATH=app` for all commands below so Python finds the `incident_copilot`
package.

## Full deterministic demo flow

Run these commands in order. Each step builds on the previous one.

### 1. Unit tests

```bash
PYTHONPATH=app python -m unittest discover -s tests
```

**What it proves:** Tools, investigator logic, contract validator, eval runner, ADK
coordinator boundary, critic/refiner, and prompt templates behave as expected. Tests do
not call live models or require API keys.

**Expected:** `Ran 89 tests` and `OK`.

### 2. Generate predictions for all incidents

```bash
PYTHONPATH=app python -m incident_copilot.manual_investigator \
  --all \
  --output evals/manual-investigator-predictions.json
```

**What it proves:** The deterministic baseline reads mock data under `data/`, calls
read-only tools, and writes one prediction per incident (`INC-001` to `INC-003`) in the
output contract shape.

**Expected:** A JSON file with three incident predictions. No stdout required if
`--output` is set.

### 3. Validate the output contract

```bash
PYTHONPATH=app python -m incident_copilot.contract_validator \
  --predictions evals/manual-investigator-predictions.json
```

**What it proves:** Every prediction has required fields (`root_cause`, `evidence`,
`actions`, `confidence`, and so on) with valid types and shapes.

**Expected:**

```text
OK: predictions match the output contract
```

### 4. Score against golden answers

```bash
PYTHONPATH=app python -m incident_copilot.eval_runner \
  --predictions evals/manual-investigator-predictions.json
```

**What it proves:** Predictions match acceptance criteria in `evals/golden-answers.json`
across nine dimensions per incident (root cause, evidence, action safety, and others).

**Expected:** Summary block similar to:

```json
"summary": {
  "total_score": 54,
  "max_total_score": 54,
  "incident_count": 3
}
```

Each incident should score 18 / 18.

### 5. Run the critic/refiner quality gate

```bash
PYTHONPATH=app python -m incident_copilot.critic_refiner \
  --predictions evals/manual-investigator-predictions.json
```

**What it proves:** A deterministic review pass checks contract validity, evidence
citations, action safety, rollback guidance, confidence consistency, and specialist
coverage. This is an offline quality gate, not live LLM refinement.

**Expected:** Top-level `"approved": true` with three incident results. Some incidents
may include non-blocking warnings (for example summary grounding). Issues would block
approval.

### 6. Inspect ADK topology

```bash
PYTHONPATH=app python -m incident_copilot.adk_coordinator --topology
```

**What it proves:** The multi-agent design is documented as JSON: coordinator, four
specialists, sequential summary/safety stage, state keys, and execution defaults.

**Expected:** JSON with `"execution_default": "deterministic"`, `"adk_installed": false`
(unless you installed `google-adk`), and agent names such as
`IncidentCoordinatorAgent` and `KubernetesInvestigatorAgent`.

### 7. Run ADK coordinator in deterministic mode (with critic)

```bash
PYTHONPATH=app python -m incident_copilot.adk_coordinator \
  --incident-id INC-001 \
  --with-critic
```

**What it proves:** The ADK boundary delegates to `manual_investigator` by default,
validates the contract, and optionally attaches a critic report. No live model is called.

**Expected:** JSON with `"execution_mode": "deterministic"`, `"delegated_to":
"manual_investigator"`, a `prediction` object, and a `critic_report` when
`--with-critic` is set.

## How to run one incident

Investigate a single scenario and print JSON to stdout:

```bash
PYTHONPATH=app python -m incident_copilot.manual_investigator --incident-id INC-001
```

Write one incident to a file:

```bash
PYTHONPATH=app python -m incident_copilot.manual_investigator \
  --incident-id INC-002 \
  --output /tmp/inc-002-prediction.json
```

Available incident IDs: `INC-001`, `INC-002`, `INC-003`. See `docs/scenarios.md` for
what each scenario represents.

Short example (truncated):

```json
{
  "incident_id": "INC-001",
  "root_cause": "Worker pods cannot start because the analytics-batch namespace CPU quota ...",
  "confidence": 0.88,
  "evidence": [
    "data/airflow/INC-001-status.json - 51 queued tasks, 11 pending worker pods ..."
  ],
  "actions": [
    "Confirm quota saturation via metrics and Kubernetes events"
  ]
}
```

## How to run all incidents

Use `--all` with an output path (recommended for eval and critic steps):

```bash
PYTHONPATH=app python -m incident_copilot.manual_investigator \
  --all \
  --output evals/manual-investigator-predictions.json
```

This is the same command as step 2 in the full flow above.

## How to validate output contract

Point the contract validator at any predictions file that follows the batch shape:

```bash
PYTHONPATH=app python -m incident_copilot.contract_validator \
  --predictions evals/manual-investigator-predictions.json
```

Field definitions live in [output-contract.md](output-contract.md).

## How to score evals

```bash
PYTHONPATH=app python -m incident_copilot.eval_runner \
  --predictions evals/manual-investigator-predictions.json
```

Golden answers and rubric dimensions are in `evals/golden-answers.json`. The v0 target
is **54 / 54** across three incidents.

## How to run critic/refiner

On a predictions file:

```bash
PYTHONPATH=app python -m incident_copilot.critic_refiner \
  --predictions evals/manual-investigator-predictions.json
```

Through the ADK coordinator for one incident:

```bash
PYTHONPATH=app python -m incident_copilot.adk_coordinator \
  --incident-id INC-001 \
  --with-critic
```

The critic does not mutate infrastructure or call live LLMs. It reports approval,
warnings, and check results.

## How to inspect ADK topology

```bash
PYTHONPATH=app python -m incident_copilot.adk_coordinator --topology
```

Use this to understand orchestrator vs specialist vs sequential reporting roles before
any live execution experiment.

## How to run ADK coordinator in deterministic mode

Default mode (no flag needed):

```bash
PYTHONPATH=app python -m incident_copilot.adk_coordinator --incident-id INC-001
```

Explicit mode:

```bash
PYTHONPATH=app python -m incident_copilot.adk_coordinator \
  --incident-id INC-001 \
  --execution-mode deterministic
```

Both delegate to the manual investigator and validate the output contract.

## Optional live ADK mode (explicit opt-in)

Live mode is guarded and never silent:

```bash
PYTHONPATH=app python -m incident_copilot.adk_coordinator \
  --incident-id INC-001 \
  --execution-mode live-adk
```

**When ADK or credentials are missing:** the CLI exits with a non-zero status and a
clear error on stderr. It does **not** fall back to deterministic execution.

Example without `google-adk` installed:

```text
error: google-adk is not installed. Install with: pip install -r requirements-adk.txt
```

With ADK installed but no API key, you would see a similar explicit error about missing
credentials. Tests and the default demo path never require this mode.

## System layers (what each part does)

| Layer | Role in v0 |
| --- | --- |
| `data/` | Mock incidents, logs, metrics, K8s events, Airflow status, runbooks |
| `tools.py` | Read-only functions that load mock telemetry |
| `manual_investigator.py` | Deterministic end-to-end investigator (acceptance baseline) |
| `contract_validator.py` | Schema and shape checks for predictions |
| `eval_runner.py` | Scores predictions against golden answers |
| `critic_refiner.py` | Offline quality gate on diagnosis and safety |
| `adk_agents.py` / `adk_coordinator.py` | Multi-agent topology and delegation boundary |
| `prompts/` | Versioned agent instructions for future live execution |

## Cleanup

Generated predictions and Python cache files should not be committed. After validating:

```bash
rm -f evals/manual-investigator-predictions.json
find . -type d -name '__pycache__' -prune -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```

Confirm a clean tree:

```bash
git status --short
```

Only intentional doc or code changes should appear.

## Related reading

* [Learning summary](learning-summary.md) - personal takeaways from building the capstone
* [Agentic engineering playbook](agentic-engineering-playbook.md)
* [Output contract](output-contract.md)
* [README](../README.md) - scope, architecture summary, and capstone progression
