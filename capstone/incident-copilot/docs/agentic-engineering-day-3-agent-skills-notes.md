# Day 3 Notes: Agent Skills

## Purpose

This note captures my useful learning from Day 3 of the AI Agents Intensive. The focus is agent skills: what they are, why they matter, how they differ from prompts, tools, workflows, and project instructions, and what I should remember before applying the idea to the Incident Copilot capstone.

This is not a full mechanical summary of the white paper. It is my learning note for understanding the concept clearly and avoiding overbuilding.

## Core concepts

### Agent skills are reusable know-how

An agent skill is a small, reusable package of instructions and optional resources that gives a general-purpose agent a specific competence on demand.

A skill is usually a folder with:

* `SKILL.md`: the required file with metadata and instructions.
* `scripts/`: optional deterministic helper code.
* `references/`: optional deeper domain knowledge.
* `assets/`: optional templates, schemas, examples, or output formats.

The important idea is not just the folder structure. The important idea is that the agent can become temporarily specialized without loading all instructions all the time.

Example:

A general agent does not need to always know every detail of cafe preparation. But when a user asks for ingredient quantities and prep sheets, the agent can load a `cafe-preparation` skill that contains the specific procedure, references, and helper scripts.

### Skills are procedural memory

The paper frames skills as a form of procedural memory.

In simple terms:

* Semantic memory means facts the agent knows.
* Episodic memory means things that happened before.
* Procedural memory means knowing how to do a task step by step.

Agent skills are useful because many real tasks are not just about knowing facts. They are about following a repeatable procedure.

Example:

For an incident copilot, knowing what “latency” means is semantic knowledge. Remembering that incident `INC-001` happened is episodic memory. Knowing how to inspect logs, summarize signals, classify severity, and produce an incident summary is procedural memory.

### Progressive disclosure is the key design pattern

Progressive disclosure means the agent does not load everything at once.

The paper describes three levels:

1. Skill metadata is always visible.
2. The `SKILL.md` body is loaded only when the skill triggers.
3. Supporting files are loaded only when needed.

This matters because large context does not automatically mean better reasoning. Too much instruction text can create context rot, where the model has so much information that useful details become harder to use.

The practical lesson is simple: keep the always-loaded context small. Load deeper instructions only when they are relevant.

### The description field is the routing interface

The skill description is not just documentation. It is the routing signal that helps the agent decide whether to load the skill.

A good skill description should say:

* What the skill does.
* When to use it.
* When not to use it.
* Which trigger phrases or task types should activate it.

Example:

Weak:

“Helps with logs.”

Better:

“Analyze incident log excerpts, extract likely failure signals, and draft a read-only incident summary. Use when the user provides service logs, stack traces, or incident snippets. Do not use for changing infrastructure, deploying fixes, or editing runbooks.”

The better version gives the agent stronger routing cues and safer boundaries.

### Skills let one agent behave like many specialists

Before skills, many systems solved specialization by creating many sub-agents. A router agent would decide which specialist agent should handle a task.

The paper argues that many of those cases can be simpler with one general agent plus many skills. The agent stays the same, but it loads specialist knowledge only when needed.

This does not mean multi-agent systems are obsolete. Multi-agent architecture still makes sense when there is real parallelism, different access boundaries, different tools, separate security postures, or genuine hierarchical decomposition.

The useful mental model is:

Use skills when one agent needs many reusable procedures. Use multiple agents when the system really needs separate actors, permissions, or execution paths.

### Skills are owned, versioned, and testable units

A skill should be treated like code, not like a random note.

That means:

* It should have a clear purpose.
* It should have a clear owner.
* It should be reviewed.
* It should be versioned.
* It should have tests or eval cases.
* It should be small enough to understand and maintain.

The paper’s warning is important: a bad skill can make the agent worse. A skill that triggers at the wrong time, injects irrelevant instructions, or overlaps with another skill can degrade behavior instead of improving it.

### Evaluation is part of the skill, not an optional extra

The paper highlights four failure modes:

1. Trigger failure: the right skill does not fire, or the wrong skill fires.
2. Execution failure: the skill fires, but the output or tool calls are wrong.
3. Token budget failure: the skill is too large and harms context quality.
4. Regression: a new skill overlaps with older skills and breaks routing.

A skill is not proven useful just because it works once. It needs to be tested across positive examples, negative examples, expected outputs, and realistic context conditions.

### Evaluate output and trajectory separately

The final answer is not the whole story. The agent may produce a good answer after taking the wrong path.

For read-only tasks, a slightly different path may be acceptable. For action-allowed tasks, the tool trajectory matters much more.

Example:

If an agent summarizes logs, the final summary may be enough to evaluate. But if an agent issues refunds, changes infrastructure, or sends messages, the exact tool sequence matters because wrong actions can create side effects.

The lesson for me: when tools are involved, evaluate both what the agent says and what the agent does.

### Skills and tools compose

Skills and tools are not the same thing.

A tool gives the agent an external capability. For example, reading a file, querying an API, running a script, or fetching logs.

A skill teaches the agent how to approach a type of work. It can tell the agent when and how to use tools.

Example:

A log parser script is a tool or helper. A skill explains when to parse logs, what signals to extract, how to interpret the result, and what output format to produce.

### Skills and MCP compose

The paper distinguishes skills from MCP.

MCP is about reach. It connects the agent to external systems such as APIs, data stores, SaaS tools, or internal services.

Skills are about know-how. They teach the agent how to perform a type of task.

A skill may instruct the agent to use tools exposed by an MCP server, but the skill itself is not the external integration.

### Skills and `AGENTS.md` have different jobs

`AGENTS.md` is always-loaded project context. It should stay tight and describe global project conventions, stack, commands, and rules.

Skills load on demand. They should hold narrower, task-specific procedures.

A clean setup can use both:

* `AGENTS.md`: project rules and global guidance.
* Skills: reusable task procedures.
* Tools or MCP: external reach and execution.
* References: deeper context loaded only when needed.

### Deterministic work should move out of instructions

The paper recommends moving deterministic behavior into scripts instead of trying to force the model to follow many runtime rules.

This is the “write software, not rules” lesson.

Example:

Do not write a long instruction that says:

“Always count incidents by severity exactly and never miss duplicate IDs.”

Better:

Use a script that counts incidents deterministically, then let the agent explain or format the result.

The agent should reason and coordinate. Deterministic code should do deterministic work.

### Meta-skills are powerful but risky

Meta-skills are skills that create, evaluate, or improve other skills.

The paper describes examples such as:

* Authoring a draft skill from a workflow description.
* Harvesting a skill from a successful agent trace.
* Improving a skill based on failing eval cases.
* Growing a skill library over time.

The warning is clear: do not start there. Meta-skills only work when the evaluation suite is already strong. Otherwise, the agent may optimize for the wrong metric and make the library worse while reporting improvement.

The safe pattern is:

Humans create or review the first versions. Agent-generated skills stay in draft until they pass the same review and eval process as human-written skills.

## Important distinctions

### Agent skills vs prompts

A prompt is usually one-time instruction or always-loaded context. It can solve the current task, but it is not always reusable or testable.

A skill is reusable procedural knowledge. It is packaged, named, versioned, and loaded only when relevant.

Prompt:

“Analyze these logs and tell me what happened.”

Skill:

A reusable incident-log-analysis procedure that explains when to use it, what evidence to extract, how to structure the output, and what not to do.

### Skills vs tools

A tool performs an operation. A skill explains a procedure.

Tool examples:

* Read a file.
* Run a Python script.
* Query logs.
* Call an API.

Skill examples:

* Analyze incident evidence.
* Draft a structured incident summary.
* Convert a repeated workflow into a reusable procedure.

The model can decide what to do, while scripts and tools handle precise execution.

### Skills vs workflows

A workflow is a sequence of steps. A skill can encode a reusable workflow, but not every workflow should become one large skill.

The paper also warns that real workflows may require composition. If the workflow is too broad, it may need smaller skills, structured handoffs, or deterministic orchestration.

Learning point:

A good skill should have one job. If it has multiple unrelated jobs, it should be split.

### Reusable instructions vs one-off context

One-off context belongs in the conversation or task input.

Reusable instructions belong in a skill only when they apply to a repeated task type.

Example:

A specific incident log excerpt is one-off context. The procedure for analyzing incident logs is reusable instruction.

### Deterministic behavior vs autonomous behavior

Deterministic behavior should be encoded in scripts, schemas, tests, or validation logic.

Autonomous behavior is where the model decides how to interpret the user request, select a relevant skill, call tools, and explain results.

The practical boundary:

Do not ask the model to behave like a calculator, parser, or validator if normal code can do it more reliably.

### Skills vs multi-agent systems

Skills help a single general-purpose agent become specialized on demand.

Multi-agent systems are still useful when there are separate roles, permissions, execution contexts, or parallel work.

The paper’s useful distinction is not “skills replace agents.” It is “do not use multiple agents by default when a skill library would be simpler.”

## Practical takeaways

* Start from repeated real workflows, not imaginary future workflows.
* Keep each skill focused on one job.
* Spend serious attention on the description field because it controls routing.
* Include both when-to-use and when-not-to-use guidance.
* Keep `SKILL.md` short enough that it does not become another giant prompt.
* Move detailed references into `references/`.
* Move deterministic logic into `scripts/`.
* Treat skills like code: review, version, test, and keep them small.
* Test whether the skill triggers when it should.
* Test whether the skill stays quiet when it should not trigger.
* Evaluate final output and tool trajectory separately.
* Do not trust a single successful run.
* Watch for regression when adding a new skill to a library.
* Think of active context as a budget, not a container to fill.
* Use `AGENTS.md` for global project guidance.
* Use skills for task-specific reusable procedures.
* Use tools and MCP for external access and execution.
* Keep human review in the loop for agent-generated skills.
* Do not start by generating a large skill library automatically.
* Avoid action-allowed behavior until the evaluation and review model is mature.

## Relevance to the Incident Copilot capstone

The Incident Copilot capstone is a good conceptual fit for the agent skills model because incident work contains repeated procedures.

Conceptually, the capstone already has several ingredients that map well to the paper’s ideas:

* Incident logs are task input.
* The output contract is a structured expectation for what the copilot should produce.
* The demo walkthrough describes a repeatable path through the system.
* The learning summary and playbook describe how the project should be understood.
* The workflow documentation can help separate user intent, evidence extraction, reasoning, and final response structure.

The main conceptual lesson is that incident analysis should not become one giant prompt. A better mental model is to keep procedural knowledge small, reusable, and testable.

For example, the capstone can be understood as containing different kinds of know-how:

* How to read incident evidence.
* How to extract symptoms and likely causes.
* How to distinguish observed facts from hypotheses.
* How to format an incident summary.
* How to stay read-only and avoid pretending to perform remediation.

This does not mean adding implementation now. It only means the Day 3 skill model gives me a cleaner vocabulary for thinking about the capstone.

The paper also reinforces a useful safety boundary for the capstone: read-only and draft-only behavior are easier to reason about than action-allowed behavior. Since the capstone is a public learning project, it should stay careful, explain
