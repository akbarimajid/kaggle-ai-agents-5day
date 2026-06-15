# Day 1b: Agent Architectures

Summary of architecture patterns from the **Day 1b — Multi-Agent Systems & Workflow Patterns** notebook.

**Sources inspected:**

* Kaggle: https://www.kaggle.com/code/kaggle5daysofai/day-1b-agent-architectures
* Public mirror: https://github.com/sdivyanshu90/5-Day-AI-Agents-Intensive-Course-with-Google/blob/main/Day%201/notebooks/day-1b-agent-architectures.ipynb

Stack: **Google ADK** (`google-adk`), **Gemini** models, `InMemoryRunner`.

---

## Why multi-agent?

| Problem (single "do-it-all" agent) | Solution (team of specialists) |
|-----------------------------------|--------------------------------|
| Long, confusing instruction prompt | One clear job per agent |
| Hard to debug which step failed | Isolate failures to a specialist |
| Unreliable on complex workflows | Compose simple agents that collaborate |

---

## Core patterns (from notebook)

### 1. LLM orchestrator (dynamic manager)

**When:** Steps are related but order or branching should be decided at runtime.

**How:** A root `Agent` treats other agents as tools via `AgentTool`.

**Example:** `ResearchCoordinator` calls `ResearchAgent` (search) then `SummarizerAgent`.

| Piece | Role |
|-------|------|
| Sub-agents | Specialists with focused `instruction` and tools |
| Root agent | Coordinator; instructions describe *how* to use sub-agents |
| `AgentTool` | Wraps an agent so the root can invoke it like a tool |

**Trade-off:** Flexible, but order is not guaranteed — depends on the LLM following instructions.

---

### 2. Sequential workflow (`SequentialAgent`)

**When:** Fixed pipeline; each step depends on the previous output.

**How:** Sub-agents run in listed order; output flows forward automatically.

**Example:** Blog pipeline — Outline → Writer → Editor.

| Use | Avoid |
|-----|-------|
| Order must be deterministic | Independent tasks that could run concurrently |
| Each step builds on prior state | Dynamic branching |

**Maps to agent loop:** plan → act → observe, repeated in a **fixed** sequence.

---

### 3. Parallel workflow (`ParallelAgent`)

**When:** Independent tasks; latency matters.

**How:** Sub-agents run concurrently; results are combined by a downstream aggregator (often inside a parent `SequentialAgent`).

**Example:** Daily briefing — Tech / Health / Finance researchers in parallel → Aggregator → final report.

| Use | Avoid |
|-----|-------|
| Topics or subtasks do not depend on each other | Step B needs output from step A |
| Speedup over sequential execution | Strict ordering requirements |

---

### 4. Loop workflow (`LoopAgent`)

**When:** Iterative refinement until quality criteria or max iterations.

**How:** Sub-agents repeat until exit condition or `max_iterations`.

**Example:** Story refinement — Initial Writer → loop(Critic → Refiner) until `APPROVED` or cap reached.

| Component | Purpose |
|-----------|---------|
| `CriticAgent` | Evaluates output; returns feedback or exact token `APPROVED` |
| `RefinerAgent` | Rewrites from critique, or calls `exit_loop` when approved |
| `exit_loop` + `FunctionTool` | Explicit termination signal for the loop |
| `max_iterations` | Guardrail against infinite loops |

**Often nested:** `SequentialAgent([initial_writer, LoopAgent([critic, refiner])])`.

**Maps to agent loop:** perceive → plan → act → **observe → iterate** until constraint met.

---

## Pattern selection (decision tree)

```
Need orchestration?
├── Fixed order (A → B → C)     → SequentialAgent
├── Independent concurrent work → ParallelAgent (+ optional aggregator)
├── Refine until good enough    → LoopAgent (+ exit condition + max_iterations)
└── LLM decides what to call    → Root Agent + AgentTool(sub-agents)
```

| Pattern | When to use | Key feature |
|---------|-------------|-------------|
| LLM orchestrator | Dynamic decisions | Model chooses which agent/tool to invoke |
| Sequential | Linear pipeline | Deterministic order |
| Parallel | Independent tasks | Concurrent execution |
| Loop | Quality refinement | Repeated critic/refine cycles |

---

## Shared state: `output_key`

Sub-agents write results into session state under a named key. Downstream agents reference placeholders in instructions, e.g. `{research_findings}`.

This is the notebook's mechanism for **memory / context passing** between agents in a workflow.

---

## ADK building blocks (notebook)

| Import | Purpose |
|--------|---------|
| `Agent` | LLM agent with instruction, tools, optional `output_key` |
| `SequentialAgent` | Ordered sub-agent pipeline |
| `ParallelAgent` | Concurrent sub-agents |
| `LoopAgent` | Iterative sub-agent cycle |
| `AgentTool` | Expose an agent as a callable tool |
| `FunctionTool` | Expose Python functions (e.g. `exit_loop`) |
| `InMemoryRunner` | Run and debug agents in-notebook |
| `google_search` | Example built-in tool on research agent |

---

## Mapped to Day 1 paper concepts

### Agent loop: perceive, plan, act, observe, iterate

| Loop stage | Notebook manifestation |
|------------|------------------------|
| Perceive | User prompt; prior `output_key` state; tool results |
| Plan | Agent instruction + model decides next step |
| Act | Tool call, sub-agent invocation, or content generation |
| Observe | Tool/sub-agent return value stored in state |
| Iterate | Explicit in `LoopAgent`; implicit in multi-step flows |

### Agent components

| Component | Notebook |
|-----------|----------|
| Model | `Gemini(...)` with retry options |
| Tools | `google_search`, `FunctionTool`, `AgentTool` |
| Memory | Session state via `output_key` |
| Orchestration | Root agent, Sequential, Parallel, Loop |
| Deployment | Out of scope in 1b (Kaggle notebook / ADK local runner) |

### Context engineering

| Lever | Notebook example |
|-------|------------------|
| Instructions | Per-agent focused system prompts |
| Knowledge | Search tool results in state |
| Memory | `{research_findings}`, `{current_story}`, `{critique}` |
| Examples | Structured output requests (bulleted summary) |
| Tools | Search, agent-as-tool, exit function |
| Guardrails | `max_iterations`, explicit `APPROVED` token, retry config |

### Harness engineering

| Lever | Notebook example |
|-------|------------------|
| Instructions / rules | Coordinator workflow steps; critic approval phrase |
| Tools | Scoped per specialist agent |
| Sandbox | Kaggle notebook environment |
| Orchestration | Workflow agent types + nesting |
| Guardrails | Loop caps, 429 / rate-limit guidance (run cells one-by-one) |
| Observability | `run_debug` for tracing runs |

### Tests and evals before full implementation

Notebook emphasizes **small specialists** and **deterministic workflows** where order matters — easier to test each agent in isolation before composing.

Loop pattern is explicitly an **eval/refine** harness: Critic acts as judge; Refiner acts on feedback until approval.

---

## Practical guardrails (from notebook)

* Run cells **one at a time** — "Run all" can hit Gemini API rate limits (429).
* Set `max_iterations` on loops.
* Use explicit exit signals (`exit_loop`) rather than hoping the loop agent infers stop conditions.
* Prefer Sequential/Parallel/Loop when order or concurrency must be **reliable**; use LLM orchestrator when flexibility is worth non-determinism.

---

## What to try locally (later)

* Reproduce one pattern with ADK outside Kaggle (`pip install google-adk`).
* Add eval cases before expanding agent count (golden inputs → expected structure).
* Compare LLM orchestrator vs `SequentialAgent` on the same research+summarize task.
