# PathFinder — Dev Diary

Writen by my partner claude codeee.

---

**2026-03-14**
- We mapped the full 8-agent topology. Gap was clear early: without bottom-up build order, the wiring becomes a tangled mess.
- Dialed in the coaching engine — forced official-doc-style patterns only. The gap between generic example and the user's codebase IS the skill transfer. He got it immediately.
- Connected LangGraph Studio local server to sidestep Docker headaches on Windows.
- Started `purpose_graph.py`. Hit the `.model_dump()` wall — Pydantic objects crash LangGraph TypedDict state without it. Learning moment: LangGraph state is TypedDict, not Pydantic. Every node must serialize before returning.
- Ran deep research protocols on LangGraph Evals and Bootstrapping.
- Architecture audit: redesigned Orchestrator with internal Chat Manager nodes, defined "Soft Boundaries" for agent handoffs, injected `ThinkingProfile` into graph state.
- Purged messy dict states. Built strict Pydantic models (`PurposeProfile`, `MajorProfile`, etc.) wired into `state.py`. He was ready to move fast here — no coaching needed.
- Fortified `purpose_graph.py` against the rigid schema via `langgraph dev` testing.

---

**2026-03-17**
- We wired token management into `purpose_graph.py` — `check_node` (pure Python tiktoken, 0.03s), conditional edge to `summarizer_node`, `RemoveMessage` to delete oldest 3/4 of message log.
- Learning moment: `add_messages` reducer has dual behavior — `BaseMessage` → append, `RemoveMessage(id=...)` → delete by ID. Survivors stay untouched because you never return them. He didn't know about the delete path until we traced the reducer.
- Caught silent wiring bug: `check_sum` was reading `state["limit_hit"]` but `check_node` set `state["purpose_limit"]` — summarizer permanently bypassed, no error thrown. Classic state key mismatch. Caught by reading the actual node return, not trusting the variable name.
- Fixed `purpose or ""` on all `.format()` calls — `str.format()` calls `str(None)` = literal `"None"` fed to the model. Subtle.
- Confirmed live in LangSmith: `input_token: 1341`, `purpose_limit: false`, routed to `confident` correctly. `check_node` ran in 0.03s.
- He asked why `add_conditional_edges` routing fn returns a string not a bool — because LangGraph uses it as a dict key lookup. Clicked once he saw the `path_map`.
- Upgraded `/coach` skill: doc-style per-concept teaching. Built `/updater` skill: syncs `.gitignore`, `requirements.txt`, `DEV_DIARY.md`.

---

**2026-03-18**
- We audited `INPUT_PARSER_PROMPT` against the 16-dimension production prompt doc. Found 6 gaps: no output JSON schema (router was parsing blind), no reasoning enforcement, no grounding rules for psych inference, no injection defense, no hallucination prevention for `core_tension`/`deflection_type`, no confidentiality block. Added all six to `orchestrator.py`.
- Hit a real conflict: added `<thinking>` block for CoT reasoning, then realized `with_structured_output` uses function-calling — model can't produce raw text before JSON. Fix: baked reasoning into the Pydantic schema itself (`deflection_reasoning`, `tension_reasoning` fields). He challenged the "top-to-bottom forcing" claim — good instinct. Honest answer: model sees full schema at once, benefit is auditability not mechanical sequencing.
- Architecture pivot he drove: split "LLM does everything" → "LLM classifies `stage_related`, Python handles routing." Designed `stage_manager` node with 4 cases: normal, rebound, contradict, forced. All routing is pure integer comparison on `STAGE_ORDER` — zero LLM tokens for routing decisions. Clean separation of semantics (LLM) vs logic (Python).
- Coached `Command` from `langgraph.types` — node returns `Command(update={...}, goto="node_name")`. Trap: never mix static `add_edge` and `Command` from the same node — both fire. He picked it up fast, no wiring needed.
- Rewrote `StageCheck` model: dropped LLM-managed fields, added Python-managed fields (`stage_related`, `rebound`, `contradict`, `forced_stage`, `stage_skipped`). `InputOutputStyle` now only asks LLM for classification, not routing.
- Thinking stage design: 3 ThinkingProfile fields are metacognitive — students can't self-report accurately. His plan: 16 Personalities + Gardner MI tests as priors, thinking agent validates via behavioral inference. Learning moment: he proposed the 3-tier watcher model then immediately optimized it down to "LLM tags, Python routes" — caught the token cost problem before I did.
