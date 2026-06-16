# Day 1 visuals to recreate

Useful diagrams from the Day 1 paper to **recreate yourself** (Excalidraw, Mermaid, etc.). Do not copy original figures.

| Page | Visual / topic | What it explains | Why useful | Recreation idea | Suggested filename |
|------|----------------|------------------|------------|-----------------|-------------------|
| 10 | Agent loop | Perceive → plan → act → observe cycle | Shows agents iterate, not one-shot chat | Four-node cycle with return arrow from observe to plan | `agent-reasoning-loop.png` |
| 14 | Vibe → engineering spectrum | More structure and verification → higher reliability | Helps choose prototype vs production rigor | Horizontal gradient: vibe coding (left) → agentic engineering (right) | `development-reliability-spectrum.png` |
| 17 | Static vs dynamic context | Always-loaded vs on-demand context | Token efficiency and signal-to-noise | Two boxes: static (rules, persona) and dynamic (RAG, incident data) | `context-engineering-strategy.png` |
| 25 | Factory model | Human defines specs/guardrails; agent executes pipeline | Reframes developer as pipeline architect | Two layers: human oversight above, automated loop below | `developer-factory-architecture.png` |
| 27 | Harness anatomy | Model is the engine; harness is the scaffolding | Explains why tooling/evals matter more than model swaps | Concentric rings: LLM core → orchestration → tools → observability | `agent-harness-layers.png` |

## Capstone-specific diagrams (optional)

Original Mermaid adaptations for [AI Platform Incident Copilot](../capstone/incident-copilot/) live in:

* [agentic-engineering-capstone-mapping.md](../capstone/incident-copilot/docs/agentic-engineering-capstone-mapping.md) - theory to design
* [architecture.md](../capstone/incident-copilot/docs/architecture.md) - agent flow

## Public repo note

Recreate visuals in your own words and layout. Do not commit screenshots or copies of copyrighted course figures.
