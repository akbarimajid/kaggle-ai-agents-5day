# Day 2 Brief: Agent Tools and Interoperability

## Purpose

This document summarizes the key concepts from the Day 2 white paper, Agent Tools and Interoperability, and explains how they should influence our agentic engineering work.

The main idea is simple: agentic systems should not be built as isolated prompt-driven scripts with custom wrappers for every tool, API, UI, or payment flow. They should be designed around standard interoperability layers.

For our work, this means we should treat MCP, Skills, A2A, A2UI, AP2, and UCP as architectural concepts that help us decide where responsibilities belong, what should be standardized, and where we need safety boundaries.

## Core Thesis

Agentic engineering moves developers from writing every line of implementation manually to orchestrating systems that can plan, call tools, collaborate, generate interfaces, and eventually execute commercial actions.

Without standards, every integration becomes a custom one-off connection. That creates fragility, security risk, duplicated work, and long-term maintenance cost.

With standards, agents become easier to connect, govern, debug, and reuse.

## Protocol Selection Rule

Use the right interoperability layer for the right type of responsibility.

### MCP: Tool Access

Use MCP-style thinking when an agent needs to call a bounded tool.

Examples:

* Read a file
* Query a database
* Search documentation
* Call GitHub
* Inspect logs
* Fetch data from a known API

MCP is best for structured, predictable tool calls where the agent sends inputs and receives outputs.

Default rule:

* Prefer official or trusted MCP servers.
* Use read-only access by default.
* Scope access to the minimum project or resource.
* Avoid production data unless explicitly approved.
* Never hardcode credentials in prompts or scripts.

### Skills: Repeatable Playbooks

Use Skills when we have repeatable local workflows that agents should follow consistently.

Examples:

* PR review procedure
* Repository rules
* Testing policy
* Current-docs lookup process
* Security review checklist
* Release verification procedure

Skills are not external services. They are operational instructions and local scripts that make agent behavior more consistent.

### A2A: Agent-to-Agent Collaboration

Use A2A-style thinking when the work is not just a tool call, but a responsibility that another specialist agent should own.

A tool gives a result. A specialist agent takes responsibility.

Use A2A when the delegated task may require:

* Multi-turn clarification
* Independent reasoning
* Follow-up questions
* State management
* Domain-specific judgment
* Negotiation between agents or systems

Example:

* A security specialist agent reviews a risky PR and asks clarifying questions.
* A cloud-cost specialist agent investigates infrastructure spend and proposes savings.
* A compliance specialist agent checks whether a workflow violates policy.

Do not use A2A just because something sounds advanced. If the task is bounded and deterministic, use a tool or Skill instead.

### Agent Card: Agent Identity and Contract

An Agent Card is the machine-readable description of an agent.

It should describe:

* What the agent can do
* What inputs it accepts
* What outputs it returns
* What tools or systems it can access
* What permissions it requires
* What security and compliance boundaries apply
* What it explicitly does not do

For our work, an Agent Card can be a lightweight markdown or JSON document before we implement any formal protocol.

### Agent Registry: Discoverable Agents

An Agent Registry is a catalog where agents can be found and used.

There are two useful mental models:

* Public registry: external marketplace of agents
* Private registry: internal catalog of approved agents

For our repository, we do not need a real registry yet. But we should keep our agent definitions discoverable through docs, issue templates, and clear task ownership.

### A2UI: Agent-to-UI Interoperability

A2UI is about letting agents describe user interfaces safely.

The key point is that agents should not generate arbitrary executable UI code. Instead, they should request trusted UI components from a known catalog.

The renderer owns the actual implementation. The agent only describes intent.

Examples:

* Render a summary card
* Show a chart
* Display a filterable incident timeline
* Show a confirmation form
* Present a dashboard using trusted components

For our work, A2UI is useful as a future direction for incident dashboards and agent-generated reports. For now, prefer structured JSON plus markdown unless interactive UI clearly adds value.

### UCP: Universal Commerce Protocol

UCP is the commerce/catalog/order layer.

It helps an agent interact with commercial systems in a standard way.

Examples:

* Discover available products or services
* Check availability
* Compare options
* Build a cart
* Prepare an order
* Return price, tax, fee, and delivery information

UCP answers the question: what can be bought and under what terms?

### AP2: Agent Payments Protocol

AP2 is the payment and authorization layer.

It allows an agent to pay only within a human-approved mandate.

A mandate defines constraints such as:

* Maximum spend
* Approved merchant
* Approved category
* Time limit
* Quantity limit
* User intent
* Audit requirements

AP2 answers the question: is this payment authorized and provable?

For our work, AP2-style thinking applies to any action with financial impact.

Examples:

* Upgrade a SaaS plan
* Increase cloud quota
* Provision paid infrastructure
* Buy external API credits
* Trigger paid agent calls
* Purchase a marketplace agent

No agent should perform financial actions without explicit approval, clear constraints, audit logs, and rollback or stop conditions.

## Architecture Decision Rules

### Rule 1: Bounded tool call means MCP

If the agent needs a predictable result from a known system, treat it as a tool call.

Example:

* Query logs
* Read a GitHub issue
* Fetch a BigQuery table schema
* Run a local test command

### Rule 2: Repeatable local workflow means Skill

If the agent needs to follow the same process repeatedly, document it as a Skill.

Example:

* How to review a PR
* How to check current API docs
* How to validate repository boundaries
* How to run security checks

### Rule 3: Ambiguous responsibility means A2A

If the task needs judgment, follow-up, state, or ownership, treat it as agent collaboration.

Example:

* “Investigate this incident and coordinate next steps”
* “Review this architecture and challenge the assumptions”
* “Act as a cost-optimization specialist”

### Rule 4: Human-facing interactive output means A2UI

If visual or interactive output adds value, consider A2UI-style output.

Example:

* Incident timeline
* Cost dashboard
* Risk matrix
* Debugging workflow UI

### Rule 5: Financial action means AP2/UCP-level guardrails

If the agent can spend money or create financial obligation, require human approval and strict constraints.

Example:

* Buying services
* Upgrading plans
* Provisioning expensive resources
* Calling paid external agents

## Security and Governance Principles

Agents must be treated as powerful automation clients, not harmless chatbots.

Required guardrails:

* Use least privilege.
* Use read-only access by default.
* Avoid production credentials unless explicitly approved.
* Never paste secrets into prompts.
* Prefer official and trusted servers.
* Audit public MCP servers before use.
* Log external tool usage.
* Show high-risk tool inputs to the user before execution.
* Require human approval for write actions when risk is material.
* Require explicit mandates for financial actions.
* Keep agent context focused. Do not overload one agent with every tool and instruction.

## Build vs Consume Principle

Do not build custom wrappers or agents when a trusted standard implementation already exists.

Preferred order:

1. Use an official provider integration.
2. Use a trusted internal tool or Skill.
3. Use a reviewed open-source implementation.
4. Build a custom wrapper only when no safe reusable option exists.

This reduces integration debt and avoids maintaining fragile one-off connections.

## Practical Application to This Repository

For this repository, we should treat Day 2 as architecture guidance, not as a requirement to implement every protocol immediately.

Near-term actions:

* Keep AGENTS.md and Skills focused, strict, and reusable.
* Add protocol-selection guidance to the agentic engineering playbook.
* Document any specialist agent with a lightweight Agent Card.
* Keep tool access scoped and auditable.
* Prefer structured outputs over free-form outputs where possible.
* Do not implement agent payments or autonomous commerce unless the product scope explicitly requires it.

Future-facing actions:

* Explore MCP for safe tool integrations.
* Explore A2A if we split responsibilities across specialist agents.
* Explore A2UI if we need interactive incident or cost dashboards.
* Explore AP2/UCP only if agents need to buy services, trigger paid resources, or interact with commerce systems.

## Glossary

### Agent

A system that combines a model, instructions, tools, memory or context, and an execution harness to pursue a goal.

### Harness

The runtime environment around the model. It manages tools, context, execution, permissions, and interaction with external systems.

### MCP

Model Context Protocol. A standard way for agents and models to connect to tools, filesystems, databases, APIs, and other external capabilities.

### MCP Server

A server that exposes tools or resources through the MCP protocol.

### MCP Client

The client inside an agent host that connects to MCP servers and makes their tools available to the agent.

### Tool

A bounded callable capability. It usually accepts structured input and returns structured output.

### Skill

A repeatable playbook, instruction set, or script that teaches an agent how to perform a workflow consistently.

### A2A

Agent-to-Agent protocol. A standard communication layer that allows agents to discover, communicate, delegate, and collaborate with other agents.

### Specialist Agent

An agent focused on a specific domain or responsibility, such as security, billing, compliance, cloud cost, or incident response.

### Orchestrator

The central agent or system that understands the user goal, coordinates workflow, and delegates work to tools or specialist agents.

### Agent Card

A machine-readable profile for an agent. It describes the agent’s capabilities, inputs, outputs, permissions, policies, and interaction schema.

### Agent Registry

A catalog where agents can be discovered, evaluated, and connected.

### A2UI

Agent-to-UI interoperability. A standard approach where agents describe user interface intent using trusted components instead of generating arbitrary executable UI code.

### Generative UI

A UI generated dynamically based on user intent and context.

### Component Catalog

The trusted set of UI components an agent is allowed to request. The client renders these components safely.

### Canvas

A persistent interactive workspace where the user and agent can both update content over time.

### UCP

Universal Commerce Protocol. A protocol for product discovery, catalog access, cart creation, order preparation, and commerce workflows.

### AP2

Agent Payments Protocol. A protocol for secure, authorized, auditable agent payments.

### Mandate

A human-approved payment or action constraint. It defines what an agent is allowed to do, how much it can spend, where it can spend, and under what conditions.

### Human-in-the-Loop

A safety pattern where a human must review or approve sensitive actions before execution.

### Least Privilege

The principle that an agent or tool should receive only the minimum access required to complete the task.

### Read-Only by Default

A safety principle where agents can inspect data but cannot modify systems unless write access is explicitly approved.

### Integration Debt

The long-term cost created by custom one-off integrations, brittle wrappers, hardcoded payloads, and bespoke API handling.

### Build vs Consume

The decision of whether to build a custom capability or consume an existing trusted protocol, tool, Skill, or specialist agent.

## Final Takeaway

Day 2 is not telling us to add every new agent protocol immediately.

The useful lesson is architectural discipline:

* Tools should be standardized.
* Agent responsibilities should be explicit.
* Specialist agents should have contracts.
* UI generation should be safe and component-based.
* Financial actions should require mandates.
* Security and auditability must be built into the harness from the beginning.

For our work, this means we should keep building a small, disciplined agentic engineering system that is protocol-shaped, auditable, and easy to evolve.
