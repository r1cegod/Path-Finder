# Backend — LangGraph Rules

## LangGraph TypedDict Rules
1. **`.model_dump()` before returning Pydantic to TypedDict state.** Every node MUST call `.model_dump()`. LangGraph TypedDict cannot hold live Pydantic objects.
2. **Sequential edges only.** `add_edge()` for the counseling chain. Never `add_conditional_edges` with `Send` unless explicitly parallel.
3. **Per-agent message queues.** Each agent reads/writes `{agent}_message`, not global `messages`.
4. **Subgraph flow:** START → scoring_node → summarizer_node → chatbot_node → END
5. **MemorySaver** handles persistence. Nodes return partial state dicts.

## LLM / Python Boundary
- LLM classifies (outputs bools, strings, enums)
- Python counts (manages ints, thresholds, escalation)
- LLM NEVER reads counter values. It outputs booleans, Python manages the count.

## Known Bugs
- `purpose_graph.py`: model names are wrong (`gpt-5.4-mini` should be `gpt-4o-mini`)
- `purpose_graph.py`: `memory = MemorySaver()` defined but never passed to `builder.compile()`
- `orchestrator_graph.py`: model names are wrong (`gpt-5.4` should be `gpt-4o`)
- `state.py` L224: `fit_score: int` vs `DEFAULT_STATE` L274: `"fit_scores": {}` — name + type mismatch
