# PathFinder — Dev Log

*Anh Duc — solo build, self-taught. FPT SE Scholarship portfolio.*

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

---

**2026-03-20**
- Caught false-positive rebound: `has_rebound = bool(future)` alone fired on any broad message the LLM tagged multi-stage. Root cause: OR logic where AND was required. Fixed in `orchestrator_graph.py`: `has_rebound = bool(future) and stage.rebound` — index signal + LLM semantic gate must both agree before rebound fires.
- Second false positive: forced backward jumps (`"Let's go back to thinking"`) returned `rebound=True`. Prompt had no forced_stage carveout. Added rule to `orchestrator.py`: forced_stage set (any direction) → rebound=False always.
- Added stage content map to `INPUT_PARSER_PROMPT` — each stage now has a precise field list so LLM stops tagging "purpose" on broad statements like "tôi muốn tự do". Precision rule appended: default to `current_stage` for ambiguous messages.
- User initially resisted adding `<current_stage>` to the orchestrator prompt ("designed to not know current stage"). After LangSmith showed false positives were unfixable without it, reversed: orchestrator needs current stage to anchor the precision rule, not to route.
- `StageCheck` had no field defaults → `ValidationError` on stale checkpoints when `get_stage()` returned `{}`. Fixed in `state.py`: all six fields get defaults in the Pydantic model. Added `DEFAULT_STAGE` dict. Removed `stage_skipped` — no node writes it, dead weight.
- Learning moment: variable shadowing. User reused `stage` for both the `list[str]` slice and the `StageCheck` object in the same scope — the list was silently destroyed. No error, no warning. Named shadowing is silent data loss.

### Entry 002 — Day 15: 2026-03-29

**Goal:** Lock the path-agent removal and spec the knowledge/data agent taxonomy and data retrieval contract.

**Decision:** Fully deleted `PathProfile` from `state.py` and removed `path` + `path_limit` from `PathFinderState`. Path debate is now Case B2 in `build_compiler_prompt()` — a prompt injection block (`PATH_DEBATE_BLOCK`) triggered by a pure Python check: all 6 profiles `done=True`. Separately, formalized the agent split into **knowledge agents** (thinking, purpose, goals — extract from the student's head, no external data) and **data agents** (job, major, uni — match against real-world datasets). Designed agent-exclusive Pydantic query forms (`JobQuery`, `MajorQuery`, `UniQuery`) where each form's fields map directly to that agent's `*Profile` fields. `JobScoringOutput` combines FieldEntries + `JobQuery | None` + `need_data: bool` into one structured output call, avoiding a second LLM hop.

**Rejected alternative:** RAG (vector store + semantic search) for data agent retrieval. The full VN-focused dataset is ~100 entries across three categories — it fits in a few KB of JSON. Semantic search adds embedding costs, a vector store dependency, and nondeterministic results on short enum-like entries ("startup", "engineer"). Deterministic Python filter functions on JSON files (`filter(jobs, role_category="engineer")`) are faster, cheaper, and produce auditable results. RAG solves a scale problem that doesn't exist here.

**What broke:** `PathProfile` class and `path: PathProfile | None` / `path_limit: bool` removed from state. Any node that referenced these fields (none were wired yet) would now fail import. `ProfileSummary.path` slot also removed. `_compute_stage_status()` in `output.py` no longer includes a "path" entry in its `profile_map`.

**What I learned:** The gate question for "subgraph vs. compiler mode" is: does this stage introduce a **new query form exclusive to its domain**? Data agents are distinguished by having a typed retrieval contract (a Pydantic query form) that knowledge agents never need. The taxonomy isn't just a UX distinction — it's a structural one that changes node topology.

**Next:** Define `jobs.json` schema (~50 VN-relevant entries: role_category, company_stage, vn_salary range, required_skills, related_majors). Build `retrieve_node` as a pure Python filter. Spec `JobScoringOutput` as the dual-purpose scoring output (FieldEntries + retrieval query).

---

### Entry 003 — Day 15: 2026-03-29

**Goal:** Eliminate redundant LLM calls in stage subgraphs without losing response quality.

**Decision:** Removed `chatbot_node` and `summarizer_node` from all 6 stage subgraphs. Replaced with a single **analyst node** that writes a prose analysis to `stage_reasoning.{stage}`. The output compiler reads `stage_reasoning` via `PROFILE_CONTEXT_BLOCK` and generates the student-facing response itself — it is the sole response generator across all stages.

**Rejected alternative:** Keep the chatbot node, add a `stage_draft` state field, have the output compiler adapt the draft. Rejected because it adds a new top-level state field and a new `STAGE_DRAFT_BLOCK` in `output.py` for zero net gain — the output compiler already has `fields_needed` and `stage_status` from `_compute_stage_status()`.

**What broke:** Nothing at runtime — and that was the sign something was wrong. The chatbot nodes had been silently writing to `{stage}_message` queues while the output compiler reads from `messages` (global). Two LLM calls per turn, only one doing visible work. No error, no warning.

**What I learned:** Trace information flow, not just code flow. The bug wasn't in the node logic — it was in the channel. `{stage}_message` is a routing queue for stage agents to read context; it is not a response channel. The output compiler reads `messages` (global). These are two different channels.

**Next:** Build remaining stage agents using the 2-node pattern (scoring + analyst). Wire all into the master orchestrator.

---

### Entry 004 — Day 16: 2026-03-30

**Goal:** Guarantee stage agents retain full domain memory even after the global summarizer compresses the conversation.

**Decision:** Split memory into two permanent layers. (1) The global `SUMMARIZER_PROMPT` is narrowed to track only macro psychology, compliance, and routing events — not stage content. (2) A deterministic **Python Tagger** is added to `input_parser`: it reads `response.stage_related` from the LLM and instantly copies the raw `HumanMessage` to every matching `{stage}_message` queue. Result: `job_message` is an untruncated vault of every message the student sent that touched the job domain. Separately, wired **contradict tagger** into `stage_manager`: when `contradict_target` is set, the current message is additionally tagged to all past-stage queues, and `context_compiler` assembles prompts from `list(dict.fromkeys(stage_related + contradict_target))` (union, order-preserved).

**Rejected alternative:** Let stage agents read global `messages`. Rejected because the summarizer runs at 2000 tokens — within 30 minutes of a real session, stage agents would lose the student's exact early answers. Let the summarizer track stage data — rejected because it requires the summarizer to understand domain-specific fields without hallucinating them.

**What broke:** Nothing at code level. The `context_stages` union exposes that `contradict_target ⊆ stage_related` is currently always true — but that's an assumption that could break if `stage_related` filtering logic changes. Making the union explicit is forward-proof.

**What I learned:** The summarizer compresses exactly what stage agents need most. Routing memory (behavioral patterns) degrades gracefully. Domain memory (what the student actually said) cannot degrade. Two channels, two decay profiles, two memory strategies.

**Next:** Wire all 6 stage subgraphs into the master orchestrator.

---

### Entry 005 — Day 17: 2026-03-31

**Goal:** Full end-to-end pipeline wired. One graph from student input to response.

**Decision:** Compiled all 6 stage subgraphs as nodes in the master `StateGraph`. Node names match `current_stage` string values exactly (`"thinking"`, `"purpose"`, `"goals"`, `"job"`, `"major"`, `"university"`) — `route_stage()` returns `current_stage` directly as the routing key, eliminating a mapping step. Stage subgraphs compile without `checkpointer=` — parent `input_orchestrator` holds the `MemorySaver`, LangGraph propagates it down. `route_stage()` short-circuits to `context_compiler` on `escalation_pending` or `bypass_stage`. Edge: every stage node → `context_compiler` → `output_compiler` → `END`.

**What broke:** Three pre-existing silent bugs discovered in `job_graph.py`, `major_graph.py`, `uni_graph.py`:
- `stage.get("current")` → always `None` (key is `"current_stage"`). `is_current_stage` was permanently `False` — scoring nodes never knew they were the active stage.
- `stage_reasoning.university` → `AttributeError` at runtime. Field is `stage_reasoning.uni`. Would have been invisible until the uni stage was reached.
- Unused `MemorySaver` import in `uni_graph.py`.

Import tests caught syntax errors. They did not catch wrong dict keys. Those only surface by reading the state schema.

**What I learned:** Silent `False` is worse than an exception. `is_current_stage = False` means the scoring node runs in a degraded mode with no error — it processes the message but without current-stage context. The bug would have produced subtly wrong outputs across every session, never throwing.

**Next:** Live end-to-end test run. Then: `retrieve_node` + `jobs.json` for data agent contracts.

