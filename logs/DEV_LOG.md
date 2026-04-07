# PathFinder - Dev Log

*Anh Duc - solo build, self-taught. FPT SE Scholarship portfolio.*

> Early March entries were reconstructed from daily session bullets. They keep the same facts, but the opening section is now normalized for faster scanning.

---

### 2026-03-14 | Topology, state contract, and `purpose_graph.py`

**Focus:** Establish the first workable graph shape and get `purpose_graph.py` operating against a real typed state contract.

**Key outcomes:**
- mapped the full 8-agent topology and locked the need for bottom-up build order
- connected LangGraph Studio locally on Windows to avoid Docker friction
- redesigned the orchestrator around internal chat-manager behavior and soft handoff boundaries
- introduced strict Pydantic profile models in `state.py` instead of loose dict state
- fixed the `.model_dump()` boundary in `purpose_graph.py` so Pydantic objects could safely cross TypedDict state
- hardened the early `purpose_graph.py` loop against the real schema with `langgraph dev`

**What I learned:**
- LangGraph state is TypedDict-first, not Pydantic-first; every node has to serialize before returning
- official-doc-style teaching transferred better because the gap between the generic example and the repo stayed visible

**Next:** Keep reinforcing `purpose_graph.py` against the strict schema and preserve the bottom-up build sequence.

---

### 2026-03-17 | Token management and reducer semantics

**Focus:** Add message-budget control to `purpose_graph.py` without losing deterministic state behavior.

**Key outcomes:**
- wired token management into `purpose_graph.py` with `check_node`, a conditional route, and a `summarizer_node`
- used `RemoveMessage` to delete the oldest 3/4 of the message log when the limit was hit
- found and fixed a silent state-key mismatch: `check_sum` read `limit_hit` while `check_node` wrote `purpose_limit`
- fixed `purpose or ""` formatting so `None` no longer leaked into prompts as the literal string `"None"`
- confirmed the path live in LangSmith with `input_token: 1341`, `purpose_limit: false`, and correct routing to `confident`

**What I learned:**
- the `add_messages` reducer has two different behaviors: `BaseMessage` appends, while `RemoveMessage(id=...)` deletes by ID
- conditional routers return lookup keys, not booleans; the `path_map` is the real mental model

**Next:** Keep the stage graph lean and carry the same discipline into the later stage graphs.

---

### 2026-03-18 | Orchestrator classification boundary

**Focus:** Audit the input parser and separate LLM classification from Python routing.

**Key outcomes:**
- audited `INPUT_PARSER_PROMPT` against the 16-dimension production prompt doc and patched 6 gaps in `orchestrator.py`
- moved reasoning into the structured schema (`deflection_reasoning`, `tension_reasoning`) after realizing `with_structured_output` cannot emit free text before JSON
- redesigned the stage manager around 4 Python-owned routing cases: normal, rebound, contradict, and forced
- rewrote `StageCheck` so the LLM only classifies and Python owns the route decision
- clarified the Thinking-stage strategy: use quiz priors, then let the agent verify behaviorally rather than trusting self-report

**What I learned:**
- auditability is the real gain from structured reasoning fields; schema order does not force model cognition
- the clean boundary is `LLM tags, Python routes`; pushing both into the model spends tokens and hides bugs

**Next:** Keep hardening the orchestrator prompts while preserving the Python-owned control surface.

---

### 2026-03-20 | Rebound false positives and StageCheck defaults

**Focus:** Remove silent routing regressions in the orchestrator before they spread across more sessions.

**Key outcomes:**
- fixed false-positive rebound routing by changing `has_rebound` from an OR-like rule to `bool(future) and stage.rebound`
- added the forced-stage carveout so explicit backward jumps no longer count as rebounds
- added a precise stage-content map to `INPUT_PARSER_PROMPT` so broad messages stop spraying tags across stages
- added defaults to every `StageCheck` field in `state.py` and introduced `DEFAULT_STAGE` for stale checkpoints
- removed dead `stage_skipped` state and caught a variable-shadowing bug that silently destroyed a list slice

**What I learned:**
- silent `False` states are worse than exceptions because they degrade behavior without announcing the failure
- prompt precision still depends on having the right local context; the orchestrator needed `current_stage` as an anchor even if Python still owned routing

**Next:** Run the master graph end to end and keep watching for state-shape bugs that import tests will not catch.

### Entry 002 Ã¢â‚¬â€ Day 15: 2026-03-29

**Goal:** Lock the path-agent removal and spec the knowledge/data agent taxonomy and data retrieval contract.

**Decision:** Fully deleted `PathProfile` from `state.py` and removed `path` + `path_limit` from `PathFinderState`. Path debate is now Case B2 in `build_compiler_prompt()` Ã¢â‚¬â€ a prompt injection block (`PATH_DEBATE_BLOCK`) triggered by a pure Python check: all 6 profiles `done=True`. Separately, formalized the agent split into **knowledge agents** (thinking, purpose, goals Ã¢â‚¬â€ extract from the student's head, no external data) and **data agents** (job, major, uni Ã¢â‚¬â€ match against real-world datasets). Designed agent-exclusive Pydantic query forms (`JobQuery`, `MajorQuery`, `UniQuery`) where each form's fields map directly to that agent's `*Profile` fields. `JobScoringOutput` combines FieldEntries + `JobQuery | None` + `need_data: bool` into one structured output call, avoiding a second LLM hop.

**Rejected alternative:** RAG (vector store + semantic search) for data agent retrieval. The full VN-focused dataset is ~100 entries across three categories Ã¢â‚¬â€ it fits in a few KB of JSON. Semantic search adds embedding costs, a vector store dependency, and nondeterministic results on short enum-like entries ("startup", "engineer"). Deterministic Python filter functions on JSON files (`filter(jobs, role_category="engineer")`) are faster, cheaper, and produce auditable results. RAG solves a scale problem that doesn't exist here.

**What broke:** `PathProfile` class and `path: PathProfile | None` / `path_limit: bool` removed from state. Any node that referenced these fields (none were wired yet) would now fail import. `ProfileSummary.path` slot also removed. `_compute_stage_status()` in `output.py` no longer includes a "path" entry in its `profile_map`.

**What I learned:** The gate question for "subgraph vs. compiler mode" is: does this stage introduce a **new query form exclusive to its domain**? Data agents are distinguished by having a typed retrieval contract (a Pydantic query form) that knowledge agents never need. The taxonomy isn't just a UX distinction Ã¢â‚¬â€ it's a structural one that changes node topology.

**Next:** Define `jobs.json` schema (~50 VN-relevant entries: role_category, company_stage, vn_salary range, required_skills, related_majors). Build `retrieve_node` as a pure Python filter. Spec `JobScoringOutput` as the dual-purpose scoring output (FieldEntries + retrieval query).

---

### Entry 003 Ã¢â‚¬â€ Day 15: 2026-03-29

**Goal:** Eliminate redundant LLM calls in stage subgraphs without losing response quality.

**Decision:** Removed `chatbot_node` and `summarizer_node` from all 6 stage subgraphs. Replaced with a single **analyst node** that writes a prose analysis to `stage_reasoning.{stage}`. The output compiler reads `stage_reasoning` via `PROFILE_CONTEXT_BLOCK` and generates the student-facing response itself Ã¢â‚¬â€ it is the sole response generator across all stages.

**Rejected alternative:** Keep the chatbot node, add a `stage_draft` state field, have the output compiler adapt the draft. Rejected because it adds a new top-level state field and a new `STAGE_DRAFT_BLOCK` in `output.py` for zero net gain Ã¢â‚¬â€ the output compiler already has `fields_needed` and `stage_status` from `_compute_stage_status()`.

**What broke:** Nothing at runtime Ã¢â‚¬â€ and that was the sign something was wrong. The chatbot nodes had been silently writing to `{stage}_message` queues while the output compiler reads from `messages` (global). Two LLM calls per turn, only one doing visible work. No error, no warning.

**What I learned:** Trace information flow, not just code flow. The bug wasn't in the node logic Ã¢â‚¬â€ it was in the channel. `{stage}_message` is a routing queue for stage agents to read context; it is not a response channel. The output compiler reads `messages` (global). These are two different channels.

**Next:** Build remaining stage agents using the 2-node pattern (scoring + analyst). Wire all into the master orchestrator.

---

### Entry 004 Ã¢â‚¬â€ Day 16: 2026-03-30

**Goal:** Guarantee stage agents retain full domain memory even after the global summarizer compresses the conversation.

**Decision:** Split memory into two permanent layers. (1) The global `SUMMARIZER_PROMPT` is narrowed to track only macro psychology, compliance, and routing events Ã¢â‚¬â€ not stage content. (2) A deterministic **Python Tagger** is added to `input_parser`: it reads `response.stage_related` from the LLM and instantly copies the raw `HumanMessage` to every matching `{stage}_message` queue. Result: `job_message` is an untruncated vault of every message the student sent that touched the job domain. Separately, wired **contradict tagger** into `stage_manager`: when `contradict_target` is set, the current message is additionally tagged to all past-stage queues, and `context_compiler` assembles prompts from `list(dict.fromkeys(stage_related + contradict_target))` (union, order-preserved).

**Rejected alternative:** Let stage agents read global `messages`. Rejected because the summarizer runs at 2000 tokens Ã¢â‚¬â€ within 30 minutes of a real session, stage agents would lose the student's exact early answers. Let the summarizer track stage data Ã¢â‚¬â€ rejected because it requires the summarizer to understand domain-specific fields without hallucinating them.

**What broke:** Nothing at code level. The `context_stages` union exposes that `contradict_target Ã¢Å â€  stage_related` is currently always true Ã¢â‚¬â€ but that's an assumption that could break if `stage_related` filtering logic changes. Making the union explicit is forward-proof.

**What I learned:** The summarizer compresses exactly what stage agents need most. Routing memory (behavioral patterns) degrades gracefully. Domain memory (what the student actually said) cannot degrade. Two channels, two decay profiles, two memory strategies.

**Next:** Wire all 6 stage subgraphs into the master orchestrator.

---

### Entry 005 Ã¢â‚¬â€ Day 17: 2026-03-31

**Goal:** Full end-to-end pipeline wired. One graph from student input to response.

**Decision:** Compiled all 6 stage subgraphs as nodes in the master `StateGraph`. Node names match `current_stage` string values exactly (`"thinking"`, `"purpose"`, `"goals"`, `"job"`, `"major"`, `"university"`) Ã¢â‚¬â€ `route_stage()` returns `current_stage` directly as the routing key, eliminating a mapping step. Stage subgraphs compile without `checkpointer=` Ã¢â‚¬â€ parent `input_orchestrator` holds the `MemorySaver`, LangGraph propagates it down. `route_stage()` short-circuits to `context_compiler` on `escalation_pending` or `bypass_stage`. Edge: every stage node Ã¢â€ â€™ `context_compiler` Ã¢â€ â€™ `output_compiler` Ã¢â€ â€™ `END`.

**What broke:** Three pre-existing silent bugs discovered in `job_graph.py`, `major_graph.py`, `uni_graph.py`:
- `stage.get("current")` Ã¢â€ â€™ always `None` (key is `"current_stage"`). `is_current_stage` was permanently `False` Ã¢â‚¬â€ scoring nodes never knew they were the active stage.
- `stage_reasoning.university` Ã¢â€ â€™ `AttributeError` at runtime. Field is `stage_reasoning.uni`. Would have been invisible until the uni stage was reached.
- Unused `MemorySaver` import in `uni_graph.py`.

Import tests caught syntax errors. They did not catch wrong dict keys. Those only surface by reading the state schema.

**What I learned:** Silent `False` is worse than an exception. `is_current_stage = False` means the scoring node runs in a degraded mode with no error Ã¢â‚¬â€ it processes the message but without current-stage context. The bug would have produced subtly wrong outputs across every session, never throwing.

**Next:** Live end-to-end test run. Then: `retrieve_node` + `jobs.json` for data agent contracts.

---

### Entry 006 - 2026-04-02

**Goal:** Make repo instructions point to the actual docs context system and require agents to keep it updated.

**Decision:** Updated `AGENTS.md` so the first stop for repo context is `docs/context/docs/PROJECT_CONTEXT.md`, then `docs/context/docs/CURRENT_CONTEXT.md`, with `docs/context/how to/context_maintenance.md` as the maintenance workflow. Added an explicit "Critical Development Rules" section and made context updates part of done, not optional follow-up.

**What changed:** `AGENTS.md` now points to the canonical docs tree, defines auto-update rules for `CURRENT_CONTEXT.md`, `PROJECT_CONTEXT.md`, and `docs/DEV_LOG.md`, and calls out guardrails like Python-owned control flow, Path as Output Compiler Case B2, and the state contract update rule. `PROJECT_CONTEXT.md` now also links to the context maintenance guide.

**Why it matters:** The repo already had the right context files, but the top-level agent instructions did not force agents to read or maintain them. That gap makes context drift likely after session compaction or multi-step doc changes.

---

### Entry 007 - 2026-04-02

**Goal:** Tighten the live `PathFinderState` contract and stop the output compiler from misreading nested profiles.

**Decision:** Removed dead state fields that no live node reads or writes (`terminate`, per-stage `*_limit`, `input_token`) from `backend/data/state.py` and the canonical architecture docs. Rewrote `_compute_stage_status()` in `backend/data/prompts/output.py` to recurse through nested models and dicts instead of assuming every top-level field is a direct `FieldEntry`. Added `test_output_prompt_contract.py` to lock the helper behavior for `GoalsProfile`, scalar leaves like `UniProfile.is_domestic`, and the dead-field cleanup.

**What broke:** `GoalsProfile` was a wrapper profile (`long` + `short`), but the helper treated those wrappers as leaf fields, so fully-populated goals still showed `not started`. `UniProfile.is_domestic` is a required boolean, but the helper treated every non-`FieldEntry` leaf as missing, so university progress was also undercounted.

**What I learned:** State helpers are part of the contract surface, not convenience glue. A stale helper can poison prompt assembly just as badly as a bad router because the compiler is the only student-facing response node.

---

### Entry 008 - 2026-04-02

**Goal:** Extract the repeated stage-name and state-key mappings into one reusable contract.

**Decision:** Added `backend/data/contracts/stages.py` as the single source of truth for `STAGE_ORDER`, `STAGE_INDEX`, `STAGE_TO_PROFILE_KEY`, `STAGE_TO_REASONING_KEY`, and `STAGE_TO_QUEUE_KEY`. Wired the contract into `backend/orchestrator_graph.py` for queue tagging, stage-order checks, and route validation, and into `backend/data/prompts/output.py` for profile lookup and reasoning synthesis. Added `test_stage_contract.py` to lock completeness and uniqueness of the mapping.

**What broke before:** The same stage knowledge existed in multiple places with slightly different shapes. That made bugs like `university` vs `uni` or `thinking` vs `thinking_style_message` too easy to create because every file was free to invent its own mapping.

**What I learned:** A contract module is not abstraction for its own sake. It is a pressure valve for string drift. When a concept is reused across routing, state access, and prompt assembly, the cheapest safe move is to name it once and import it everywhere.

**Follow-through:** Migrated all six stage graphs to the contract pattern as well, not just the orchestrator and output helper layer. `thinking_graph.py` served as the manual learning pass, then the same `STAGE / PROFILE_KEY / QUEUE_KEY / REASONING_KEY` pattern was applied to `purpose`, `goals`, `job`, `major`, and `uni`. Validation passed via unit tests, graph imports, and a grep sweep for leftover hardcoded graph key lookups.

**Second follow-through:** Removed redundant `MemorySaver` ownership from all stage subgraphs and from `output_graph.py`; only the root orchestrator keeps the checkpointer now. Also fixed a real output tagging bug: `output_compiler` was appending a new AI response to `messages` but tagging `state["messages"][-1]`, which still pointed at the previous turn's human message. The node now tags the newly created `AIMessage` into the union of `stage_related + contradict_target`, and `test_output_graph_contract.py` locks that behavior.

---

### Entry 009 - 2026-04-03

**Goal:** Define a stable evaluation method for the web-enabled data agents (`job`, `major`, `uni`).

**Decision:** Formalized data-agent evaluation as a **retrieval-plus-reasoning** problem, not a normal stage-agent prompt audit. Added `docs/evaluation/data_agent_evaluation.md` as the canonical guide. The evaluation seam now includes six checks: search-trigger correctness, query quality, evidence grounding, consensus-crash quality, confidence calibration, and tool discipline. Also locked the recommended test stack into three layers: deterministic replay suite as primary, adversarial retrieval suite for noisy/frozen evidence, and live-search smoke runs only for drift detection.

**Why this matters:** The current stage audit pattern was built for knowledge agents. Data agents can fail before reasoning quality even matters: they may skip a required search, formulate the wrong VN query, or ignore the returned evidence while still writing plausible prose. Treating them like normal stage agents hides the real failure mode.

**Constraint surfaced:** `eval/run_eval.py` already replays input state and writes traces, but it does not yet inject mocked tool responses. That means the repo can run live-search attack datasets today, but a fully deterministic replay harness still requires a mockable search seam.

**Next:** Use the new guide to build the first dedicated audit doc and attack dataset for one retrieval stage, preferably `job`, then decide whether to extend the eval runner with frozen tool fixtures.

---

### Entry 010 - 2026-04-05

**Goal:** Evaluate and harden the Stage 2 `goals` agent against the existing attack dataset.

**Decision:** Tightened the `goals` extractor and analyst contracts, then re-ran `eval/goals_attack.jsonl` until all three attacks passed. The extractor now has explicit rules for `TITLE IS NOT DEFENSE`, `NUMBERS OR IT IS UNCLEAR`, `GENERIC SOFT-SKILL BAN`, and `HORIZON GAP PENALTY`. The analyst now explicitly treats `gov stability` vs `freelance/founder` as a structural crash and must embed that contradiction directly into the final `PROBE:` anchor.

**What changed:** Added a clean prompt module at `backend/data/prompts/goals_v2.py` and rewired `backend/goals_graph.py` to import it. Recorded the passing trace results in `docs/evaluation/goals_evaluation.md`. The verified eval command was `venv\Scripts\python eval/run_eval.py --mode multi --file eval/goals_attack.jsonl --graph goals`.

**What broke before:** The old Stage 2 prompt let self-reported `founder`, `freelance`, `full autonomy`, and `soft skills` claims climb far above the intended verification ceiling. It also let the analyst note prior crashes in prose without always weaponizing them in the final `PROBE:` string.

**What I learned:** For the goals stage, horizon mismatch is a calibration signal, not just analyst commentary. If the student names a bold 5-year identity with no 1-year artifact, that missing bridge must suppress extractor confidence and sharpen the analyst handoff at the same time.

**Follow-up:** Consolidated the clean prompt back into `backend/data/prompts/goals.py` and deleted `goals_v2.py`. The next real gap is coverage, not path layout: the current Stage 2 suite still needs more Vietnamese-student edge cases before it can be called production-grade.

**Second follow-up:** Expanded `eval/goals_attack.jsonl` to 8 attacks and re-ran the suite. New cases covered Vietnamese-student-specific realities: Da Lat lifestyle fantasy, parent-pleasing civil-service compliance, debt-driven salary pressure, founder-to-solo contradiction, and safe-path drift. The goals agent passed all 8. This is enough to call Stage 2 strongly hardened at the stage-agent level, but still not enough to call the full production path hardened without orchestrator/output end-to-end evals.

**Third follow-up:** Closed the last Stage 2 contract gap in `backend/goals_graph.py`. The analyst no longer returns a single free-text blob. It now returns `goals_summary`, `probe_field`, and `probe_instruction`, and Python composes the final `PROBE:` line with a deterministic fallback if the model under-specifies it. Re-ran the previously failing last attack in isolation plus a 3-run stability replay; all runs now preserved a trailing `PROBE:` anchor in `stage_reasoning.goals`.

---

### Entry 011 Ã¢â‚¬â€ Day 23: 2026-04-05

**Goal:** Audit and close the remaining demo-critical gaps before the scholarship submission: RIASEC/MI seeding, completedStages coverage, post-escalation behavior, and vague counter parity.

**Decision:** Moved the post-escalation lock entirely to `main.py`'s `chat_stream`. Before calling `astream_events`, the endpoint calls `aget_state(config)` and checks `escalation_pending`. If True, it streams the hardcoded Vietnamese response directly as a token event and returns Ã¢â‚¬â€ zero graph nodes run, zero LLM calls. The `/test/{session_id}` endpoint was fixed to call `aupdate_state(config, {"thinking": merged})` against the LangGraph checkpointer instead of only yielding a client-side SSE event. `vague_turns` gained a direct consecutive escalation cap at >= 4 in `counter_manager`, matching the disengagement and avoidance pattern.

**Rejected alternative:** Two alternatives were tried and discarded. First: a `locked_response_node` inside `orchestrator_graph`. That node returns a direct `AIMessage` without touching `output_compiler`, so no `on_chat_model_stream` events fire Ã¢â‚¬â€ the frontend would show the user's message with no reply. Second: a frontend guard in `App.jsx handleSend` that short-circuits before the API call. That guard works for UX but duplicates the lock logic on the client, creating two sources of truth for what constitutes a locked session.

**What broke:** `/test/{session_id}` had `# noqa: ARG001` on its `session_id` parameter Ã¢â‚¬â€ the tell that it was intentionally unused. The endpoint was streaming a synthetic `{"type": "state"}` SSE event to React `useState` only. The LangGraph `MemorySaver` checkpointer had never received `brain_type` or `riasec_top`, so `thinking_graph`'s scoring node was reading `None` for both fields on every session.

**What I learned:** The token-stream boundary is a coupling point between the graph and the UI. Any response path that bypasses the LLM output node (`output_compiler`) produces no `on_chat_model_stream` events Ã¢â‚¬â€ only `on_chain_end` state updates, which don't populate the chat window. The lock must be placed upstream of `astream_events()`, not inside the graph, to guarantee both zero cost and a visible response.

**Next:** Knowledge gap drilling Ã¢â‚¬â€ five architectural decisions that must be defensible verbally before the scholarship interview: counter decay, reasoning lock, stage queue tagger, 10-turn window vs. direct escalation, and B2 gate conditions.

---

### Entry 012 - 2026-04-05

**Goal:** Reevaluate the Stage 0 `thinking` agent against the newer S4 stage-prompt rules instead of trusting the earlier S3 audit label.

**Decision:** Hardened `backend/data/prompts/thinking.py` with three explicit extractor rules: `PRIOR AGREEMENT IS NOT DEFENSE`, `DETAIL IS NOT DEFENSE`, and the required `Student Claim -> Agent Squeeze -> Student Defense` verification sequence before any conversational field can exceed `0.7`. Also added explicit analyst-side `TENSION EMBEDDING` language so the final `PROBE:` anchor starts with the actual prior-vs-claim conflict instead of a generic "test it" handoff.

**What broke before:** The replay of `eval/thinking_attack_v2.jsonl` exposed a real cap violation. In the "Abstract Intellectual" case, Nova promoted `learning_mode="theoretical"` to `0.74` from a polished self-report that merely matched the quiz priors. That is exactly the failure the S4 verification loop is supposed to block.

**What I learned:** Prior alignment is calibration context, not proof. If a student says something that sounds smart and it happens to match the test, the model gets seduced into calling it "verified" unless the prompt says, in plain language, that alignment is still just a self-report until the student survives a forced trade-off.

**Verification:** Re-ran both Stage 0 attack suites after the patch:
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/thinking_attack_v2.jsonl --graph thinking`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/thinking_attack.jsonl --graph thinking`

**Next:** Either add a longer multi-turn contradiction dataset for Thinking, or move up one layer and test whether the orchestrator/output path preserves the stronger Stage 0 `PROBE:` tension end-to-end.

---

### Entry 014 - 2026-04-05

**Goal:** Reevaluate the Stage 1 `purpose` agent against the same S4 prompt-audit standard now used for Thinking and Goals.

**Decision:** Hardened Stage 1 at both the prompt and graph layer. `backend/purpose_graph.py` no longer trusts the analyst to emit the final probe line consistently. The analyst now returns structured fields (`purpose_summary`, `probe_field`, `probe_tension`, `probe_instruction`), and Python composes the final trailing `PROBE:` line with deterministic fallbacks. The analyst prompt now receives `user_tag` explicitly, and the extractor prompt gained hard rules for stepping-stone destination blocking, calling-vs-FIRE contradiction drops, contradiction priority, and a digital-nomad location-fantasy cap.

**What broke before:** The fresh replay of `eval/purpose_attack.jsonl` exposed two real regressions. First, multiple traces omitted the required `PROBE:` anchor entirely even though the stage_prompt contract requires it every turn. Second, the FIRE case let `work_relationship="calling"` survive the explicit "retire completely at 35" contradiction, which is exactly the deadlock the Stage 1 rules are supposed to crush.

**What I learned:** For Stage 1, a pure prompt-only contract was not enough. The analyst can still reason correctly and then forget the output anchor, so the handoff itself needs a Python safety rail. Also, contradiction text must be first-class structured data (`probe_tension`) rather than something we hope survives inside a free-text summary.

**Verification:** Re-ran `venv\Scripts\python eval/run_eval.py --mode multi --file eval/purpose_attack.jsonl --graph purpose` until all 7 attacks held the intended caps and every trace ended with a contradiction-rich `PROBE:` line. Also re-verified import health with `venv\Scripts\python -c "from backend.purpose_graph import purpose_graph; print('OK')"`.

**Next:** The remaining question is no longer Stage 1 prompt integrity. It is whether the orchestrator/output path preserves the stronger Stage 1 handoff end-to-end in student-facing Vietnamese responses.

---

### Entry 013 - 2026-04-05

**Goal:** Run the first dedicated retrieval-agent audit on Stage 3 `job` using the data-agent evaluation workflow.

**Decision:** Built `eval/job_attack.jsonl` and `docs/evaluation/job_evaluation.md` as the first `job`-specific audit pair, then hardened `backend/data/prompts/job.py` around the failures exposed by the live traces. The extractor no longer asks for a nonexistent `key_quote`, and now enforces `SINGLE-TURN SELF-REPORT CAP`, stronger `DAY-TO-DAY FIRST`, `AUTONOMY DEPENDS ON GRIND`, and `CONTRADICTION DROP` rules. The analyst now has explicit tool-discipline, Vietnam-query, and tension-embedding rules.

**What broke:** The prompt layer improved, but the audit exposed a deeper graph seam: after tool use, `job_agent` still intermittently leaves `stage_reasoning.job` blank. In the latest live suite, search triggers and confidence ceilings mostly behaved, but only 1 of 4 attacks reliably handed a usable `PROBE:` to the output compiler. This is not a prompt-quality failure anymore; it is a post-tool synthesis reliability problem in the current data-agent graph shape.

**What I learned:** Retrieval agents need a more explicit synthesis seam than normal stage agents. Search-trigger logic and extractor caps can be correct while the actual analyst handoff still collapses. For `job`, the next fix should target graph architecture or deterministic fallback behavior after the tool loop, not more prompt wording alone.

**Next:** Add a reliable post-tool synthesis step for `job`, then decide whether the same seam should be generalized across `major` and `uni` before calling any retrieval stage production-ready.

---

### Entry 014 - 2026-04-05

**Goal:** Clean up the retrieval-stage source layer before adding a dedicated research seam.

**Decision:** Repaired the mojibake in `docs/prompt/docs/stage_prompt.md`, added `backend/data/contracts/research_sources.py` as the first reusable domain/source seed contract, and documented source priorities plus Reddit options in `docs/evaluation/research_sources.md`. Also tightened `backend/tools.py` guidance so retrieval queries stay narrow and contradiction-focused rather than collapsing into one giant request.

**What broke before:** The repo had two separate issues mixed together. First, `stage_prompt.md` had real mojibake in source, not just terminal display noise. Second, Serper behaved badly when asked a broad Ã¢â‚¬Å“research requestÃ¢â‚¬Â query that mixed salary, remote, stakeholder load, and company stage into one search. The result quality improved only when the query was decomposed into narrow factual slices and, in some cases, site filters.

**What I learned:** Source strategy is part of the architecture. A future research node should not start from a blank search box. It needs a curated domain list, query decomposition rules, and explicit treatment of Reddit as supplementary evidence. Reddit's current Data API wiki says OAuth is required and warns that some legacy API documentation is out of date, so the safe short-term move is Serper discovery via `site:reddit.com`, not treating Reddit snippets as primary evidence.

**Next:** Use the new source contract in a dedicated `job` research planner / synthesis path, then decide whether the same source-selection logic should be shared across `major` and `uni`.

## Entry 032 - 2026-04-05
**Goal:** Replace the brittle Stage 3 direct search loop with a working research draft and replay the `job` attack suite.

**Decision:** Stage 3 `job` now uses a dedicated planner/researcher/synthesizer seam backed by OpenAI web search. The graph writes a structured `job_research` packet into shared state, then the synthesizer writes the final `stage_reasoning.job` from that packet instead of trying to synthesize inside the same node that calls tools.

**What changed:**
- Added `JobResearch` and `job_research` to shared state.
- Rewrote `backend/job_graph.py` around `confident_node -> job_research_planner -> job_researcher -> job_synthesizer`.
- Rewrote `backend/data/prompts/job.py` so planning, retrieval, and synthesis are separate prompt responsibilities.
- Replayed `venv\Scripts\python eval/run_eval.py --mode multi --file eval/job_attack.jsonl --graph job`.

**Result:** The draft works materially better than the old Serper-style loop. All 4 attacks completed, each produced a populated research packet, and each preserved a non-empty `stage_reasoning.job` with a trailing `PROBE:`. The main remaining weakness is evidence noise, not handoff collapse.

**Residual issues:** OpenAI web search still returns some irrelevant or weak URLs in `cited_sources`, and eval traces emit Pydantic serializer warnings around structured outputs. Those do not block the draft, but they should be cleaned up before copying the pattern into more stages.

**Next:** Add lightweight source pruning or evidence compression, then decide whether to generalize the same planner/researcher/synthesizer architecture into `major` or `uni`.

## Entry 033 - 2026-04-06
**Goal:** Collapse the evaluation workflow into one official pipeline document before more audit work lands.

**Decision:** `eval/HOW_TO_USE.md` is now the single source of truth for the evaluation pipeline. It owns the production-first workflow, the runner usage, the required context docs, the trace-audit loop, and the new rule that meaningful behavior changes must be surfaced to the user for opinion before they are treated as final production direction.

**What changed:**
- Rewrote `eval/HOW_TO_USE.md` from a runner-only note into the full evaluation workflow.
- Removed duplicated workflow steps from `docs/prompt/docs/stage_prompt.md` and replaced them with a pointer.
- Updated `docs/evaluation/stage_evaluation.md` and `docs/evaluation/data_agent_evaluation.md` to treat `eval/HOW_TO_USE.md` as the official process doc.
- Updated `docs/context/docs/PROJECT_CONTEXT.md` and `docs/context/docs/CURRENT_CONTEXT.md` so the new source-of-truth location is discoverable at the start of work.

**Why this matters:** The repo previously split the process across two files: `stage_prompt.md` described the workflow while `eval/HOW_TO_USE.md` only described the CLI. That made it too easy to skip production planning and too easy for future docs to drift.

**New workflow rules locked:**
- evaluation work must start by planning for production behavior before writing datasets
- evaluation logs are created or updated before JSONL authoring
- meaningful student-facing behavior changes must be discussed with the user and their opinion requested before the behavior is treated as final production direction

**Next:** Use the new pipeline on the next real stage audit and tighten it only if a practical gap shows up in execution.

## Entry 034 - 2026-04-06
**Goal:** Tighten the newly centralized evaluation workflow so production signoff happens in explicit rounds instead of an open-ended hardening loop.

**Decision:** The official evaluation pipeline now uses a hard **3-round gate** before a stage can be called production-ready.

**Rules locked:**
- every evaluation plan is capped at 3 rounds total
- each evaluation run may finish exactly 1 stage only
- after each run, the updated evaluation log must be handed to the user
- after each run, a user conversation must happen before the next round starts
- production-ready status requires all 3 rounds to be completed for that stage

**Why this matters:** Without a round cap and a forced handoff point, evaluation work tends to drift into large bundled passes that hide behavior shifts and skip user review between hardening steps.

**What changed:** Updated `eval/HOW_TO_USE.md` to encode the 3-round gate in the workflow, planning rules, close-the-loop step, and completion criteria. Refreshed `docs/context/docs/CURRENT_CONTEXT.md` to reflect the new cadence.

**Next:** Apply the 3-round gate on the next real stage evaluation and keep it unless execution reveals a concrete failure mode in the process itself.

---

### Entry 014 - 2026-04-05

**Goal:** Eliminate the Stage 3 `job` graph failure where analyst reasoning disappeared after tool use, and align its probe handoff with the newer Purpose/Goals pattern before orchestrator/output evaluation.

**Decision:** Split the old single `job_agent` seam into two roles inside `backend/job_graph.py`: a tool-planning node that only decides search calls, and a non-tool `job_synthesizer` node that always produces structured analyst output (`job_summary`, `probe_field`, `probe_tension`, `probe_instruction`). Python now deterministically composes the final `PROBE:` line from those fields, exactly like the newer Stage 1 and Stage 2 flows.

**What broke before:** The retrieval logic and extraction quality were often acceptable, but after tool use the stage could still end with blank `stage_reasoning.job`. That meant the output compiler would receive no actual Socratic handoff even when the search found useful market contradictions.

**What I learned:** Retrieval stages need a harder seam than prompt-only obedience. A tool planner and a synthesis writer are different jobs. When one node tries to do both, the search loop can succeed while the final reasoning silently collapses. The fix was architectural, not rhetorical.

**Verification:** 
- `venv\Scripts\python -c "from backend.job_graph import job_graph; print('OK')"`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/job_attack.jsonl --graph job`

**Result:** all 4 Job attacks now preserve non-empty `stage_reasoning.job` with a trailing `PROBE:` line after tool use.

**Next:** Decide whether to run orchestrator/output end-to-end evaluation now that Stages 0-3 have stronger handoff contracts, or continue stage-local hardening on the remaining later stages first.

---

### Entry 015 - 2026-04-05

**Goal:** Close the last Stage 0 calibration leak before orchestrator/output wiring tests.

**Decision:** Kept the new structured analyst handoff in `backend/thinking_graph.py`, but added a deterministic Python verification clamp inside the Thinking scoring node. If `thinking_style_message` contains fewer than 2 human turns, no conversational Thinking field (`learning_mode`, `env_constraint`, `social_battery`, `personality_type`) may exceed `0.6`, and `done` is recomputed after the clamp. Also tightened the extractor prompt with `FORCED-CHOICE CONFESSION IS STILL SELF-REPORT` and `SCENE DETAIL IS NOT ENV CONSTRAINT`.

**What broke before:** The prompt-only hardening was not enough. In the legacy "dark room" replay, a single forced-choice answer still produced absurdly strong extractor outputs like `social_battery="solo" 0.96` and `env_constraint="home" 0.92`, even though the conversation had not yet completed the required claim -> squeeze -> defense loop.

**What I learned:** For Stage 0, the verification threshold is structural, not rhetorical. If high confidence depends on turn count, Python must own that rule inside the scoring node. Prompt wording can guide the model, but it should not be the sole gate for a hard confidence ceiling.

**Verification:**
- `venv\Scripts\python -c "from backend.thinking_graph import thinking_graph; print('OK')"`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/thinking_attack_v2.jsonl --graph thinking`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/thinking_attack.jsonl --graph thinking`

**Result:** both Thinking suites still pass, every trace still ends with a trailing `PROBE:`, and the old single-turn overconfidence leak is gone in the fresh replay.

**Next:** Use the strongest Stage 0-3 attacks for orchestrator/output end-to-end evaluation and inspect whether the student-facing Vietnamese output preserves the stronger stage-local handoffs.

---

### Entry 016 - 2026-04-06

**Goal:** Retire the repo `docs/` folder as the live documentation source and make the PathFinder vault the official documentation home.

**Decision:** The canonical PathFinder docs now live in the Obsidian vault under `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\sources\docs\`. The repo copy at `D:\ANHDUC\Path_finder\docs\` is archive-only. Repo instruction files now point to the vault first, while the project README and hub layer route agents into the correct canonical files.

**What changed:** Updated repo `AGENTS.md`, `CLAUDE.md`, `README.md`, and `eval/HOW_TO_USE.md` to treat the vault as canonical. Added archive notices to the main repo context files and created `docs/ARCHIVE_NOTICE.md`. Updated the vault copies of `PROJECT_CONTEXT.md`, `CURRENT_CONTEXT.md`, `context_maintenance.md`, and the PathFinder README so the canonical side agrees with the new contract.

**What I learned:** A routing layer naturally becomes the documentation home once it accumulates the canonical raw files, strong hubs, and the maintenance habit. At that point keeping repo `docs/` "also canonical" is not redundancy, it is drift risk.

**Next:** Validate the vault-first read path during the next real coding task and only add more synchronization or freezing machinery if the archive still causes confusion.

---

### Entry 016 - 2026-04-06

**Goal:** Align the repo's agent instructions with the new mirrored Obsidian PathFinder workspace so future sessions can use the vault as a low-token routing layer without confusing it for the source of truth.

**Decision:** Updated `AGENTS.md` and the context docs to acknowledge the vault mirror at `D:\ANHDUC\ADUC_vault\ADUC\projects\pathfinder\`, but locked a strict boundary: the vault is for routing and synthesis, while the repo `docs/` tree remains canonical for operational contracts. The reading pattern is now: repo context docs first, optional vault README/domain hub for faster navigation, then back to repo docs for exact contract checks.

**What changed:** Added a dedicated `Vault Routing Layer` section to `AGENTS.md`, added the vault mirror and navigation pattern to `docs/context/docs/PROJECT_CONTEXT.md`, and refreshed `docs/context/docs/CURRENT_CONTEXT.md` so the active workstream and handoff reflect the new repo-vs-vault convention.

**What I learned:** A strong external knowledge layer becomes risky the moment it stops being clearly subordinate to the repo's canonical docs. The useful pattern is not "replace repo docs with vault notes"; it is "use the vault to route faster, then verify against the repo where exact wording matters."

**Next:** Validate the repo-plus-vault read path on the next real coding task and only add more synchronization machinery if router-level maintenance proves insufficient.

---

### Entry 017 - 2026-04-06

**Goal:** Remove duplicated navigation logic from the repo bootstrap files after the docs-to-vault transition.

**Decision:** Simplified repo `AGENTS.md` and `CLAUDE.md` into thin bootstrap files. They now only state that repo `docs/` is archived, point to the vault as canonical, and direct readers into the vault entry docs instead of recreating the vault routing tree inside the repo.

**What changed:** Rewrote both repo bootstrap files so they no longer duplicate the project routing pattern already defined in the vault. Kept only a minimal repo-local note block plus the hard rule that live documentation belongs in the vault.

**What I learned:** Once a canonical navigation system exists, duplicating that routing tree in a secondary bootstrap file recreates the same drift surface under a different name. The clean bootstrap is a redirect, not a second router.

**Next:** Watch whether `README.md` should also be thinned later, or whether it still serves a distinct project-facing purpose.

---

### Entry 018 - 2026-04-07

**Goal:** Lock the `DEV_LOG.md` synchronization rule after moving canonical docs into the vault.

**Decision:** `projects/pathfinder/sources/docs/DEV_LOG.md` remains the canonical dev log, but `D:\ANHDUC\Path_finder\docs (archived)\DEV_LOG.md` is a required mirror. Every new durable decision entry must be appended to both files in the same change.

**What changed:** Updated the canonical project context docs and maintenance rules to name the mirror exception explicitly, corrected stale repo archive paths to `docs (archived)\`, and updated the repo entry files so future sessions see the rule before touching docs.

**What I learned:** "Archive-only" is too broad when one file is still intentionally mirrored. If the exception is not written down, drift is not an accident; it is the default outcome.

**Next:** Keep both dev-log copies aligned on every future durable documentation or architecture decision.

---

### Entry 019 - 2026-04-07

**Goal:** Move the repo dev-log mirror out of the archived docs tree and make the opening of the log easier to scan.

**Decision:** The repo mirror now lives at `D:\ANHDUC\Path_finder\logs\DEV_LOG.md` instead of inside `docs (archived)/`. The canonical copy remains `projects/pathfinder/sources/docs/DEV_LOG.md`. The first four March entries were rewritten into structured date snapshots so the file starts with readable context instead of raw bullets.

**What changed:** Updated repo and vault contracts to point at `logs/DEV_LOG.md`, added a dedicated repo `logs/` folder, and normalized the 2026-03-14 / 2026-03-17 / 2026-03-18 / 2026-03-20 sections into `Focus`, `Key outcomes`, `What I learned`, and `Next`.

**What I learned:** A mirrored operational file should not live inside an archive tree. It makes the exception invisible and encourages drift. The log itself also needed a readable opening so the earliest architecture decisions were not buried in diary-style bullets.

**Next:** If more cleanup is worth the time later, standardize the remaining duplicate entry numbering without changing the historical substance.

---

### Entry 020 - 2026-04-07

**Goal:** Replace the split search paths with one shared free-first retrieval layer that can serve both current PathFinder data agents and future agents.

**Decision:** Added `backend/retrieval/` as the shared Python retrieval subsystem. It now owns general search, news search, Reddit search hooks, quota tracking, and URL extraction. `job_graph.py` uses it directly for researcher mode, while `major_graph.py` and `uni_graph.py` stay on their existing ToolNode shape through a thin adapter in `backend/tools.py`.

**What changed:**
- Added normalized retrieval models and provider routing under `backend/retrieval/`.
- Kept Serper as primary general-search provider while local quota remains, with DDG fallback and 3-5 second jitter.
- Added Reddit support scaffolding through PRAW when credentials exist, plus DDG/RSS/json fallbacks for future work.
- Added Jina Reader first-pass extraction and optional Crawl4AI fallback.
- Replaced the direct OpenAI web search call in `backend/job_graph.py`.
- Added `test_retrieval_service_contract.py`.

**Verification:**
- `venv\Scripts\python -m unittest test_retrieval_service_contract.py`
- `venv\Scripts\python -c "from backend.job_graph import job_graph; from backend.major_graph import major_graph; from backend.uni_graph import uni_graph; print('graphs-ok')"`
- `venv\Scripts\python -c "from backend.retrieval import SearchRequest, search_web; import json; r=search_web(SearchRequest(query='data scientist fresher vietnam salary', domains_allowlist=['itviec.com','topcv.vn'], max_results=3)); print(json.dumps(r.model_dump(), ensure_ascii=True, indent=2))"`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/job_attack.jsonl --graph job`

**Result:** the shared service imports cleanly, legacy stage graphs still import, Serper is again the active primary provider after fixing the wrapper call, and the `job` replay still passes all 4 attacks on top of the new service layer.

**What I learned:** Provider logic belongs in one place. The graph should own reasoning seams; the retrieval layer should own provider order, fallback behavior, quota tracking, and extraction. The earlier split between OpenAI web search in one graph and Serper-only LangChain tools elsewhere was architectural drift, not a feature.

**Next:** when `major` or `uni` are refactored next, move them from ToolNode onto the same planner / researcher / synthesizer pattern instead of adding more provider logic to prompt-bound tool loops.

---

### Entry 021 - 2026-04-07

**Goal:** Lock the archive boundary after accidentally writing a new delegated doc into the repo archive tree.

**Decision:** `D:\ANHDUC\Path_finder\docs (archived)\` is read-only reference material. Do not create or update delegated/workflow docs there. New operational docs belong either in the vault canonical docs or in live repo locations that are not archive-marked.

**What changed:** Removed the new archived delegated doc created during the retrieval-stack pass and tightened the live project context so the no-write rule is explicit.

**What I learned:** "Archived" is not just a routing hint. It has to be treated as a hard write boundary or new docs will drift back into the dead tree by convenience.

**Next:** Keep delegated implementation notes out of the archive tree and only mirror durable decisions through the approved log paths.

---

### Entry 022 - 2026-04-07

**Goal:** Close the last cheap-but-meaningful evaluation gap before calling the knowledge agents production-ready at their visible response seam.

**Decision:** Add a new `backend/evaluation_graph.py` wrapper module for replay evaluation. Each wrapper graph will run `evaluation_prep -> {stage_graph} -> context_compiler -> output_compiler`, skipping the orchestrator entirely. The wrapper owns the seam-specific normalization: if the dataset only provides the target stage queue, `evaluation_prep` copies that queue into `messages`, and if `stage.stage_related` is missing it seeds the current stage so `PROFILE_CONTEXT_BLOCK` reaches the compiler prompt. This proves stage + compiler behavior, not full orchestrator behavior.

**What changed:** Wrote the implementation spec in `projects/pathfinder/sources/docs/delegated/evaluation_graph.md`, updated the live current-context note to move the workstream onto the new seam, and refreshed the Stage 0-2 evaluation logs plus the umbrella stage-evaluation note so the next replay target is stage-to-output compiler wiring instead of immediate orchestrator replay.

**What I learned:** The missing production proof was never "one more stage-local dataset." The real gap is whether a stronger internal `PROBE:` survives prompt assembly and becomes a stronger Vietnamese student-facing reply. The expensive part to skip is the orchestrator's routing/classification layer, not the compiler itself.

**Next:** Implement `backend/evaluation_graph.py`, register the new eval graph names in `eval/run_eval.py`, add one normalization contract test, and replay `thinking_eval`, `purpose_eval`, and `goals_eval`.

---

### Entry 023 - 2026-04-07

**Goal:** Make the first visible-response production gate explicit for the knowledge agents instead of leaving compiler audit as an implied next step.

**Decision:** Stage 4 of knowledge-agent evaluation is `output_compiler` output audit. A stage does not earn a production-grade claim at the visible-response seam until the same attack set is replayed through `<stage>_eval` (`stage_graph -> context_compiler -> output_compiler`) and the final Vietnamese reply is audited for contradiction preservation, `PROBE:` preservation, and attack sharpness.

**What changed:** Updated `projects/pathfinder/sources/docs/evaluation/stage_evaluation.md` to define Stage 4 explicitly, updated `projects/pathfinder/sources/docs/evaluation/thinking_evaluation.md` so Thinking is the first Stage 4 target, and refreshed the live context docs plus note-layer summaries to reflect that the next run starts with `thinking_eval`.

**What I learned:** Passing stage-local attacks proves the internal handoff, not the student-facing response. The production claim must stay open until the compiler preserves the attack instead of softening it into generic counseling.

**Next:** Implement and run `thinking_eval`, inspect both `compiler_prompt` and the final `AIMessage`, then decide whether any failure belongs to the Thinking stage, compiler prompt assembly, or `output_compiler` phrasing.

---

### Entry 024 - 2026-04-07

**Goal:** Run the first real Stage 4 replay on the Thinking agent and prove the new wrapper graph works on production-like attacks.

**Decision:** `backend/evaluation_graph.py` is now the live Stage 4 seam. Thinking passes the current stage + compiler audit on both `eval/thinking_attack_v2.jsonl` and `eval/thinking_attack.jsonl`: the wrapper graph runs cleanly, `compiler_prompt` preserves the trailing `PROBE:`, and the final Vietnamese reply preserves the attack as a forced-choice squeeze instead of generic coaching.

**What changed:** Added `backend/evaluation_graph.py`, registered `thinking_eval` / `purpose_eval` / `goals_eval` / `job_eval` / `major_eval` / `uni_eval` in `eval/run_eval.py`, added `test_evaluation_graph_contract.py`, then ran the two Thinking Stage 4 datasets successfully.

**Verification:**
- `venv\Scripts\python -c "from backend.evaluation_graph import thinking_eval_graph, purpose_eval_graph, goals_eval_graph; print('OK')"`
- `venv\Scripts\python -m unittest test_evaluation_graph_contract.py`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/thinking_attack_v2.jsonl --graph thinking_eval`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/thinking_attack.jsonl --graph thinking_eval`

**What I learned:** The wrapper graph is worth having only if the final response stays sharp. On Thinking, the compiler did not blunt the attack: contradiction framing and forced-choice pressure survived the jump from analyst reasoning into Vietnamese student-facing output.

**Next:** Run the same Stage 4 seam on Purpose and Goals, then compare whether their final replies preserve contradiction and `PROBE:` sharpness as cleanly as Thinking.

---

### Entry 025 - 2026-04-07

**Goal:** Certify the Purpose agent at the current Stage 4 visible-response seam instead of leaving `purpose_eval` as a planned follow-up.

**Decision:** Purpose passes the current `purpose_eval` seam on `eval/purpose_attack.jsonl`. All 7 attacks completed cleanly through `purpose_graph -> context_compiler -> output_compiler`; every `compiler_prompt` preserved the trailing `PROBE:`; and the final Vietnamese replies preserved the same forced trade-off without softening into generic coaching. This is still a stage + compiler claim only, not full orchestrator readiness.

**What changed:** Ran `purpose_eval`, audited the 7 fresh traces under `eval/threads/`, updated the canonical Purpose evaluation log with the Stage 4 replay results, and refreshed the live current-context handoff so Goals is now the next knowledge-agent target.

**Verification:**
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/purpose_attack.jsonl --graph purpose_eval`

**What I learned:** A Stage 4 pass does not require the literal `PROBE:` token to appear in the student-facing reply. The real bar is whether the contradiction survives prompt assembly and shows up as the same sharp Vietnamese trade-off question. Purpose now clears that bar.

**Next:** Run `goals_eval`, then compare whether Goals preserves contradiction and `PROBE:` sharpness as cleanly as Thinking and Purpose.

---

### Entry 026 - 2026-04-07

**Goal:** Start the Goals Stage 4 replay, then fix any visible-response seam failures between `goals_graph` and the final Vietnamese reply.

**Decision:** Goals now passes the current Stage 4 stage + compiler seam on `eval/goals_attack.jsonl`. The right fix was not in `backend/goals_graph.py`; it was in the output compiler contract. `backend/data/prompts/output.py` now forbids generic "rất cụ thể" praise on vague/compliance answers, injects the exact `PROBE:` as a dedicated directive block, and `backend/output_graph.py` now runs deterministically with a reply sanitizer so mixed-script leakage cannot survive the final student-facing message.

**What changed:** Updated the canonical Goals evaluation log with a Round 1 Stage 4 plan, ran `goals_eval`, audited the traces, patched the compiler prompt and output node, then re-ran `goals_eval` until all 8 attacks preserved the intended contradiction/compliance pressure in the final Vietnamese reply. Refreshed the live current-context docs so the knowledge-agent Stage 4 seam is now closed across Thinking, Purpose, and Goals.

**Verification:**
- `venv\Scripts\python -m unittest test_evaluation_graph_contract.py`
- `venv\Scripts\python -c "from backend.output_graph import output_graph; from backend.evaluation_graph import goals_eval_graph; print('OK')"`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/goals_attack.jsonl --graph goals_eval`

**What I learned:** Stage-local `PROBE:` preservation is not enough. The compiler can still blunt the attack with friendly filler or language noise unless the final prompt is explicitly taught to match evidence quality and operationalize the exact trade-off.

**Next:** Choose the next post-Goals hardening target instead of spending another round on the already-clean Goals Stage 4 seam.

---

### Entry 027 - 2026-04-07

**Goal:** Start the Job Stage 4 replay and decide whether the retrieval-stage contradiction still survives through `context_compiler` and `output_compiler`.

**Decision:** Job now passes the current `job_eval` stage + compiler seam on `eval/job_attack.jsonl`. All 4 attacks completed cleanly through `job_graph -> context_compiler -> output_compiler`; every trace kept a populated `job_research` packet and preserved the trailing `PROBE:` in both `stage_reasoning.job` and `compiler_prompt`; and the final Vietnamese replies preserved the intended contradiction instead of softening into generic coaching. This is still a stage + compiler claim only, not full orchestrator readiness.

**What changed:** Verified `job_eval_graph` import and the evaluation-wrapper contract test, ran `job_eval`, audited the 4 fresh traces under `eval/threads/`, updated the canonical Job evaluation log with the Stage 4 replay result, and refreshed the live current-context docs so the next follow-up can be chosen from `major_eval`, `uni_eval`, or serializer-warning cleanup.

**Verification:**
- `venv\Scripts\python -c "from backend.evaluation_graph import job_eval_graph; print('job-eval-ok')"`
- `venv\Scripts\python -m unittest test_evaluation_graph_contract.py`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/job_attack.jsonl --graph job_eval`

**What I learned:** The current wrapper seam also holds for a retrieval stage, not just the knowledge-agent trio. The remaining risk is not contradiction loss; it is trace-time serializer noise around structured outputs, which should be cleaned before treating the same seam as settled for the remaining retrieval stages.

**Next:** Decide whether the higher-leverage next move is `major_eval`, `uni_eval`, or fixing the structured-output serializer warnings before running the next retrieval-stage replay.

---

### Entry 028 - 2026-04-07

**Goal:** Start the Major evaluation cycle by moving `major_graph.py` off the legacy ToolNode path and proving the new retrieval seam at both the stage-local and Stage 4 wrapper layers.

**Decision:** `major` now mirrors `job`'s architecture: `confident -> major_research_planner -> major_researcher -> major_synthesizer`, with a dedicated `major_research` packet in state. The first replay exposed one real trigger bug: a Dreamer case skipped search on a new `field` claim. The planner prompt now hard-requires research on new major-field claims, including Dreamer paths where the search target is the execution barrier rather than whether to search at all. With that fix in place, both `major` and `major_eval` pass `eval/major_attack.jsonl`.

**What changed:** Added `MajorResearch` to `backend/data/state.py`; rewrote `backend/major_graph.py` onto the planner / researcher / synthesizer seam; replaced the old monolithic major analyst prompt with `MAJOR_RESEARCH_PLAN_PROMPT` plus `MAJOR_SYNTHESIS_PROMPT`; added `eval/major_attack.jsonl`; created the canonical `projects/pathfinder/sources/docs/evaluation/major_evaluation.md` log plus the note summary; refreshed live context docs so the current Stage 4 seam is now closed across all six stages.

**Verification:**
- `venv\Scripts\python -c "from backend.data.state import MajorResearch; print('state-ok')"`
- `venv\Scripts\python -c "from backend.major_graph import major_graph; print('major-graph-ok')"`
- `venv\Scripts\python -m unittest test_stage_contract.py test_evaluation_graph_contract.py`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/major_attack.jsonl --graph major`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/major_attack.jsonl --graph major_eval`

**What I learned:** The failure mode was not weak prose. It was trigger ambiguity. Dreamer logic is dangerous if it is allowed to bypass retrieval instead of redirecting retrieval toward the barrier. Once the trigger became deterministic, the stage-local and compiler seams both held.

**Next:** Decide whether to clean the structured-output serializer warnings next or open a broader orchestrator / full-path replay layer now that all six stage wrappers pass.

---

### Entry 028 - 2026-04-07

**Goal:** Start the Uni Stage 4 replay and remove the last legacy ToolNode retrieval loop before evaluating the final school-choice seam.

**Decision:** `uni_graph.py` now uses the same planner -> researcher -> synthesizer retrieval seam as `job_graph.py`. Added `uni_research` to state, split `backend/data/prompts/uni.py` into extractor / planner / synthesizer contracts, and ran `uni_eval` on `eval/uni_attack.jsonl`. All 4 attacks now pass cleanly through `uni_graph -> context_compiler -> output_compiler`, with populated `uni_research`, a trailing `PROBE:` in both `stage_reasoning.uni` and `compiler_prompt`, and a sharp final Vietnamese contradiction in the reply.

**What changed:** Replaced the old ToolNode loop in `backend/uni_graph.py`, added `UniResearch` plus `uni_research` to `backend/data/state.py`, created `eval/uni_attack.jsonl`, added `test_uni_graph_contract.py`, and recorded the new Round 1 results in `projects/pathfinder/sources/docs/evaluation/uni_evaluation.md` plus its note-layer summary.

**Verification:**
- `venv\Scripts\python -c "from backend.uni_graph import uni_graph; print('uni-graph-ok')"`
- `venv\Scripts\python test_uni_graph_contract.py`
- `venv\Scripts\python -m unittest test_evaluation_graph_contract.py test_retrieval_service_contract.py`
- `venv\Scripts\python eval/run_eval.py --mode multi --file eval/uni_attack.jsonl --graph uni_eval`

**What broke:** The first replay exposed a contract leak: the synthesizer could emit invalid `probe_field` names like `tuition` or `college`, which are not real `UniProfile` fields. Fixed by adding a Python-side normalization guard in `_compose_probe_line()` so any invalid value falls back to a real field before composing the final `PROBE:` line, then re-ran the same dataset successfully.

**What I learned:** Retrieval-stage success depends on more than getting search results back. The stage contract also needs deterministic normalization around the final handoff fields, or the run can "pass" while still leaking structurally invalid metadata into the compiler seam.

**Next:** Decide whether to run `major_eval` immediately or clean the shared structured-output serializer warnings first.

---

### Entry 029 - 2026-04-07

**Goal:** Clear the pre-commit regressions found in the review before the current PathFinder delta is committed.

**Decision:** Fixed all three reported blockers instead of trying to argue around them. `serialize_state()` now normalizes backend `university` into frontend `uni`; the frontend no longer appends its own synthetic escalation close-out on the same turn the backend already emits Case C; and the output compiler now prefers the active stage's `PROBE:` while skipping passive `PROBE: NONE (passive analysis only)` lines during fallback extraction. Also fixed the university stage card so it renders the real `UniProfile` fields instead of a dead `uni.value` placeholder.

**What changed:** Updated `main.py`, `frontend/src/App.jsx`, `backend/data/prompts/output.py`, and `frontend/src/components/tabs/StageTab.jsx`. Added regression coverage in `test_output_prompt_contract.py` and `test_main_contract.py`.

**Verification:**
- `python -m py_compile backend\data\prompts\output.py main.py`
- `python test_output_prompt_contract.py`
- `python test_main_contract.py`
- `python test_evaluation_graph_contract.py`
- `python test_retrieval_service_contract.py`
- `python test_uni_graph_contract.py`

**Constraint:** `fastapi` is not installed in the active Python, so `test_main_contract.py` loads `serialize_state()` from source instead of importing the full app module.

**What I learned:** The `PROBE` bug was not in stage generation. It was in the compiler seam: once multi-stage reasoning got merged, a simple reverse scan could grab the wrong passive directive and silently neuter the active-stage question. The stage-name bug was the same class of problem on a different surface: backend and frontend were both internally consistent, but inconsistent with each other.

---

### Entry 030 - 2026-04-07

**Goal:** Make the repo mirror dev log intentionally tracked in git without opening the whole `logs/` folder to noisy files.

**Decision:** Narrowed `.gitignore` to ignore `logs/*` by default and explicitly unignore `logs/DEV_LOG.md`. That keeps the mirrored dev log commit-visible while leaving `logs/README.md` and any future local-only log artifacts outside the repo unless we choose otherwise.

**What changed:** Updated `.gitignore` with:
- `logs/*`
- `!logs/DEV_LOG.md`

**Verification:**
- `git status --short -- .gitignore logs/DEV_LOG.md logs/README.md`
- `git check-ignore -v logs/README.md logs/DEV_LOG.md`

**What I learned:** The repo was not actually "tracking the dev log"; it was just leaving the entire directory ungoverned. Making the exception explicit is cleaner than relying on accidental untracked state.
