# Day 3 Mapping: Agent Skills in the Incident Copilot

## Purpose

This document maps the Day 3 agent skills concepts to the existing AI Platform Incident Copilot capstone.

The goal is not to add new runtime behavior. The goal is to understand how the current capstone already reflects several agent skills ideas: reusable procedures, deterministic helpers, contracts, evaluation gates, prompt boundaries, and offline-safe agent orchestration.

This capstone remains a local learning project using mock incidents and offline-safe defaults.

## What “agent skills” mean in this capstone

In this capstone, “agent skills” should be understood as reusable procedural knowledge, not as a new feature or production integration.

The Day 3 paper describes an agent skill as a lightweight package of task-specific know-how. A skill can include a `SKILL.md`, optional scripts, references, and assets. The main value is progressive disclosure: the agent does not need every instruction in context all the time. It should load or apply the right procedure only when the task calls for it.

For the Incident Copilot, this maps naturally to the way the capstone is already structured:

* Incident investigation is a repeated procedure.
* The deterministic manual investigator provides a safe baseline.
* The output contract defines what a valid answer must contain.
* The eval runner checks whether behavior stays consistent.
* Versioned prompt templates capture reusable agent instructions.
* The ADK-style coordinator and specialists represent scoped reasoning boundaries.
* The critic/refiner acts as verification, not autonomous remediation.
* The demo walkthrough and workflow diagram explain how the pieces fit together.

The capstone does not need a real skills runtime right now. The useful learning is conceptual: treat repeated agent behavior as small, testable, reviewable procedural units instead of one giant prompt or uncontrolled autonomous workflow.

## Mapping to existing capstone artifacts

| Day 3 concept                                     | Capstone artifact                                                             | How it appears today                                                                                                            | Should we change anything now?                                                                                     |
| ------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Agent skill as reusable procedural knowledge      | Deterministic manual investigator                                             | The manual investigator encodes a repeatable incident investigation path before agent autonomy is introduced.                   | No. This is already aligned with deterministic baseline first.                                                     |
| Progressive disclosure                            | Versioned prompt templates and specialist boundaries                          | Instructions are separated by role and purpose instead of being collapsed into one large prompt.                                | No runtime change. Documentation can explain this as a conceptual mapping.                                         |
| `SKILL.md` as a focused instruction package       | Versioned prompt templates                                                    | Prompt templates behave like reusable instruction units, although they are not packaged as formal skills.                       | No. Do not rename or restructure them as skills in this PR.                                                        |
| Description as routing signal                     | ADK coordinator boundary                                                      | The coordinator decides which specialist path is relevant, similar to how a skill description helps route agent behavior.       | No. Keep the current coordinator model.                                                                            |
| One skill, one job                                | Specialist agents                                                             | Specialists represent scoped responsibilities rather than one overloaded agent prompt.                                          | No. Existing topology already supports the learning point.                                                         |
| Skills versus tools                               | Deterministic manual investigator, parser-like logic, local mock data readers | Deterministic code handles repeatable extraction and validation. Agent prompts handle reasoning and explanation.                | No. Keep deterministic work in code. Do not add new tools.                                                         |
| Skills versus MCP                                 | Offline mock incident bundle                                                  | The capstone intentionally does not use MCP or external systems. It uses local mock data as the data boundary.                  | No. Do not add MCP servers, external APIs, or live integrations.                                                   |
| Skills versus `AGENTS.md`                         | `AGENTS.md`                                                                   | `AGENTS.md` should remain global repo guidance, not a dumping ground for every incident procedure.                              | Maybe update only if there is already a related docs section or skill guidance section. Otherwise leave unchanged. |
| Context rot and token budget                      | Prompt templates, demo docs, workflow docs                                    | The capstone avoids one huge prompt by separating contracts, prompts, workflow docs, and evaluation.                            | No. Documentation-only mapping is enough.                                                                          |
| Deterministic work belongs in scripts             | Output contract validator                                                     | The validator checks structure and expected fields deterministically instead of relying only on model self-judgment.            | No. This is a core strength of the capstone.                                                                       |
| Evaluation failure modes                          | Eval runner                                                                   | The eval runner protects expected behavior and should remain stable at 54 / 54 unless a scoped change intentionally updates it. | No. Run the existing eval suite after docs changes to confirm no accidental breakage.                              |
| Trigger failure                                   | Coordinator and specialist routing                                            | If the wrong specialist path is selected, the diagnosis flow can degrade. This maps to trigger failure in skills.               | No implementation change. This is useful as vocabulary in docs.                                                    |
| Execution failure                                 | Output contract validator and eval runner                                     | If the agent produces incomplete or invalid output, the validator and evals catch it.                                           | No. Existing gates already represent this concept.                                                                 |
| Token budget failure                              | Versioned prompt templates                                                    | Overloaded prompts could reduce answer quality. Keeping prompts scoped reduces this risk.                                       | No. Avoid adding large prompt text in this PR.                                                                     |
| Regression                                        | Eval runner                                                                   | Adding or changing prompts, contracts, or agent behavior can break existing cases. The eval runner is the regression guard.     | No. Keep expected result count unchanged.                                                                          |
| Output quality versus tool trajectory             | Critic/refiner and deterministic workflow                                     | The capstone separates final answer quality from the steps used to produce or refine it.                                        | No. Keep critic/refiner as verification only.                                                                      |
| Read-only, draft-only, action-allowed ladder      | Offline-safe defaults and explicit live execution flag                        | The capstone is mostly read-only and draft-oriented. Optional live ADK execution is gated behind an explicit flag.              | No. Do not expand live behavior.                                                                                   |
| Meta-skills and self-improving skills             | Critic/refiner                                                                | The critic/refiner improves or checks the output, but it does not autonomously rewrite the system or add new capabilities.      | No. Do not add self-improving skills now.                                                                          |
| Human review for agent-created changes            | Vibe coding workflow                                                          | Agent-generated changes should be reviewed before merge. This matches the capstone’s agentic engineering principle.             | No. Keep review and PR discipline.                                                                                 |
| Skills as versioned assets                        | Versioned prompt templates and docs                                           | The capstone already versions prompts and learning docs in git.                                                                 | No. This is conceptually aligned.                                                                                  |
| Documentation as a source of procedural knowledge | Demo walkthrough, learning summary, workflow diagram, playbook                | These docs explain the procedure and make the capstone understandable as a learning system.                                     | Yes, documentation-only cross-linking is reasonable if the paths exist.                                            |

## Skill boundaries

The capstone should not treat every file as a skill. The useful mapping is by responsibility.

### Behaves like reusable skills

These parts behave like reusable procedural knowledge:

* Versioned prompt templates.
* Specialist role instructions.
* The incident investigation procedure.
* The critic/refiner guidance.
* The demo walkthrough as a human-readable procedure.
* The agent-engineering workflow diagram as a map of the agentic process.

They are “skill-like” because they encode how to do a repeated task.

### Behaves like tools

These parts behave more like tools or deterministic helpers:

* Deterministic manual investigator.
* Local mock incident bundle readers.
* Any parser-like or formatter-like logic.
* Any local script that transforms input into structured output.

They are tool-like because they perform operations rather than explain the full reasoning procedure.

### Behaves like contracts

These parts define expected structure and boundaries:

* Output contract validator.
* Expected incident summary shape.
* Rollback or no-rollback recommendation format.
* Required fields for diagnosis output.
* Offline-safe behavior expectations.

They are contract-like because they define what valid output must satisfy.

### Behaves like verification gates

These parts protect quality and consistency:

* Eval runner.
* Output contract validator.
* Critic/refiner.
* Existing offline-safe test suite.
* Explicit live execution flag.

They are verification gates because they prevent unchecked agent behavior from being accepted as correct.

## Why this remains documentation-only for now

This should remain a documentation-only change for now because the capstone already has the important engineering boundaries in place.

The Day 3 paper does not require this project to add a skills runtime, MCP server, external tool, new dependency, cloud deployment, or live model path. Its strongest relevance is conceptual: it gives better language for explaining why the existing capstone is structured around deterministic baselines, contracts, evals, scoped prompts, and safe verification.

Adding runtime behavior now would risk scope creep. It could also make the demo harder to understand. The current capstone is strongest when it stays simple:

* Mock incidents only.
* Local execution by default.
* Deterministic baseline first.
* Eval runner stable.
* Output contract enforced.
* Optional live ADK path behind explicit flag only.
* Critic/refiner used for verification, not remediation.

A documentation-only PR preserves the learning value without increasing runtime complexity.

## Possible future extension, not now

The PDF motivates a few small future ideas, but they should not be part of this PR.

Future possibilities:

* Document a small “skill boundaries” catalog that lists existing reusable procedures in the capstone.
* Add a short section to the playbook explaining when a prompt template is skill-like and when code should remain deterministic.
* Add examples of positive and negative routing cases for specialist selection.
* Add a future note about packaging skills only if the repo later introduces an actual skills convention.

Not now:

* Do not add a `.agents/skills/` directory.
* Do not create real `SKILL.md` runtime packages.
* Do not add MCP.
* Do not add external tools.
* Do not add new dependencies.
* Do not add live LLM calls.
* Do not add autonomous remediation.
* Do not change the eval count.
* Do not expand the capstone beyond local mock incident learning.

## PR scope recommendation

### Files to add

* `capstone/incident-copilot/docs/agentic-engineering-day-3-agent-skills-mapping.md`

### Files to update, if they exist

Keep updates minimal and only add links.

Suggested candidates:

* `capstone/incident-copilot/README.md`

  * Add this doc under existing learning docs or quick demo docs.

* `capstone/incident-copilot/docs/demo-walkthrough.md`

  * Add this doc under related reading if that section already exists.

* `capstone/incident-copilot/docs/learning-summary.md`

  * Add a one-line reference to Day 3 mapping if it already links to other Day notes.

* `capstone/incident-copilot/docs/agent-engineering-workflow.md`

  * Add this doc under related reading if the file already has that pattern.

* `capstone/incident-copilot/docs/agentic-engineering-playbook.md`

  * Add this doc under related docs if the playbook already collects learning mappings.

### Tests to run

Because this should be documentation-only, behavior should not change.

Run the existing capstone eval or test command that currently reports 54 / 54 passing.

Expected result:

* Existing eval runner remains 54 / 54.
* No prompt, contract, runtime, or fixture behavior changes.

### Checks to run

Run the repo’s normal lightweight hygiene checks for documentation changes.

Suggested checks:

* `git diff --check`
* Existing capstone eval runner, expected 54 / 54
* Any existing README or docs link check if the repo already has one

### What not to include

Do not include:

* Runtime skill loading.
* `.agents/skills/` scaffolding.
* New dependencies.
* MCP servers.
* External integrations.
* Cloud deployment.
* Live LLM calls.
* New incident fixtures.
* Contract changes.
* Prompt behavior changes.
* Eval expectation changes.
* Autonomous remediation.
* Changes to the explicit live execution flag behavior.

## Related docs

Link these if the paths exist:

* `capstone/incident-copilot/README.md`
* `capstone/incident-copilot/docs/demo-walkthrough.md`
* `capstone/incident-copilot/docs/learning-summary.md`
* `capstone/incident-copilot/docs/agent-engineering-workflow.md`
* `capstone/incident-copilot/docs/agentic-engineering-playbook.md`
* `capstone/incident-copilot/docs/output-contract.md`
* `capstone/incident-copilot/docs/agentic-engineering-day-2-tools-interoperability.md`
* `capstone/incident-copilot/docs/agentic-engineering-day-3-agent-skills-notes.md` if the Day 3 notes doc is added in the same or a prior PR

Suggested uncertain paths:

* `AGENTS.md`
* `docs/automation/agent-sync.md`

Only cross-link uncertain paths if they exist and already participate in the capstone documentation flow.
