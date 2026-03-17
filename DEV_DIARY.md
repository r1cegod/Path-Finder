# PathFinder — Dev Diary

Raw session logs. No polish.

---

**2026-03-14**
- Mapped the massive 8-agent topology. Realized build from the bottom up or it becomes a tangled mess.
- Dialed in the coaching engine: forced AI to give only official-doc-style patterns, not custom wiring — the gap between generic example and my codebase IS the learning.
- Connected LangGraph Studio local server to bypass docker headaches.
- Started `purpose_graph.py`. Hit the `.model_dump()` wall — Pydantic objects crash LangGraph TypedDict state without it.
- Executed deep research protocols on LangGraph Evals and Bootstrapping.
- System Architecture Audit: redesigned Orchestrator with internal Chat Manager nodes, defined "Soft Boundaries" for agent handoffs, injected `ThinkingProfile` into graph state.
- Purged messy dict states. Built strict Pydantic models (`PurposeProfile`, `MajorProfile`, etc.) wired into `state.py`.
- Running `langgraph dev` testing fortified `purpose_graph.py` against the rigid schema.

---

**2026-03-17**
- Built token management into `purpose_graph.py` — `check_node` (pure Python tiktoken, 0.03s), conditional edge to `summarizer_node`, `RemoveMessage` to delete oldest 3/4 of message log.
- Learned `add_messages` reducer dual behavior: `BaseMessage` → append, `RemoveMessage(id=...)` → delete by ID. Survivors stay untouched because you never return them.
- Caught silent wiring bug: `check_sum` was reading `state["limit_hit"]` but `check_node` set `state["purpose_limit"]` — summarizer permanently bypassed, no error thrown.
- Fixed `purpose or ""` on all `.format()` calls — `str.format()` calls `str(None)` = literal `"None"` fed to the model.
- Confirmed live in LangSmith: `input_token: 1341`, `purpose_limit: false`, routed to `confident` correctly. `check_node` ran in 0.03s.
- Learned `add_conditional_edges` routing fn must return a string matching exact `add_node()` name — returns string not bool because LangGraph uses it as a dict key lookup.
- Upgraded `/coach` skill: doc-style per-concept teaching (what it is → how it works → minimal example), architect-mode profile — explain to core, trust user to wire, no narrate-back.
- Built `/updater` skill: syncs `.gitignore`, `requirements.txt`, and `DEV_DIARY.md` from conversation history + git diff.
