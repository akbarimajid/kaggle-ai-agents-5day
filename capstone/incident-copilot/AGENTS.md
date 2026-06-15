# Agent guidance: AI Platform Incident Copilot

Instructions for coding agents working in this capstone directory.

## Safety and scope

* **Keep the public repo safe** — no PII, real cloud project IDs, billing details, or production credentials
* **Use mock data only** under `data/` — never wire real Airflow, Kubernetes, or log backends in v0
* **No real company or personal account data** in commits
* **Do not deploy anything** unless the user explicitly requests a later phase
* **Do not add real Airflow/Kubernetes client dependencies** until mock tools and evals pass

## Engineering discipline

* **Keep v0 small** — prefer docs, contracts, and mock-backed tools over feature sprawl
* **Prefer evidence-based diagnosis** over confident guessing; cite file paths and log lines
* **Add or update evals before full implementation** — `evals/golden-answers.json` is the acceptance source of truth
* **Test specialists in isolation** before composing the full orchestrator

## Architecture (do not drift)

1. **Primary:** `IncidentCoordinatorAgent` as LLM orchestrator — dynamic investigation path
2. **Supporting:** Sequential final stage — evidence → diagnosis → safe remediation → summary
3. **Future only:** Loop with `SafetyCriticAgent` + refiner — document but do not implement without explicit approval

## File boundaries

* Work inside `capstone/incident-copilot/` unless updating root `README.md` capstone link
* Tool implementations belong in `app/` when added; contracts live in `docs/tool-contracts.md`
* Scenario truth lives in `docs/scenarios.md` and `data/incidents/` — keep them aligned

## When implementing tools

* Read only from `data/` paths declared in tool contracts
* Return structured errors on missing files; do not fabricate production telemetry
* Enforce guardrails: read-only, no shell execution, no cluster mutations

## When implementing agents

* One specialist = one focused instruction + scoped tools
* Pass state via named keys: `evidence_bundle`, `diagnosis_draft`, `remediation_plan`, `incident_summary`
* Final user-facing output must list evidence citations and flag uncertainty

## Out of scope for agents unless asked

* Cloud Run / GCP deployment
* Live incident paging integrations
* Auto-remediation or write operations against infrastructure
