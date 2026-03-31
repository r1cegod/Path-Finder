# PathFinder — Dev Log

---

### Entry 001 — Day 14: 2026-03-28

**Goal:** Redesign the PATH and GOALS stages and resolve what psychometric tests feed ThinkingProfile.

**Decision:** Collapsed GOALS and PATH from planned separate LangGraph subgraphs into output compiler modes — Case B1 (drill arc, stages 1–5) and Case B2 (path debate arc). Stripped `PathProfile` in `state.py` of all synthesis fields (`track`, `recommended_uni`, `timeline`, `confidence`) and replaced with a debate state tracker: `debate_active`, `locked`, `debate_rounds`. Added `path_debate_ready: bool` to `PathFinderState` as a Python-computed gate — fires when all stages `done=True` + `user_tag` clean + behavioral counters below threshold. For the thinking test stack, confirmed O*NET Interest Profiler API (RIASEC, CC-BY 4.0, free) as Test 2. Test 1 (MI/thinking style) is blocked pending licensing resolution.

**Rejected alternative:** Building `goals_graph.py` and `path_graph.py` as full subgraphs (Scoring → Summarizer → ChatBot pattern). This would've been architecturally consistent but semantically wrong — neither stage collects new data, they synthesize existing data. A subgraph for synthesis creates unnecessary LLM hops and a scoring node with nothing to score. The right frame: does this stage extract new fields from the user? If no → compiler mode, not subgraph.

**What broke:** `ThinkingProfile` fields (`learning_mode`, `env_constraint`, `social_battery`, `personality_type`) are now stale. Original design assumed a simple 4-bucket quiz. Research revealed idrlabs MI questions are copyrighted (ToS: "reproduction prohibited"), VARK is copyrighted AND academically debunked, no free MI API exists, and no GitHub repo has an MIT-licensed MI question bank. ThinkingProfile field redesign is blocked until the MI test source question is resolved.

**What I learned:** The gate for "build a subgraph vs. build a compiler mode" is: does this stage extract new structured data from the user? Synthesis stages that read existing state belong in the output layer, not the agent layer. Mapping this decision early prevents building scaffolding that actively fights the architecture.

**Next:** Resolve MI test legitimacy (write original Gardner-framework questions vs. find a licensed instrument) → update `ThinkingProfile` fields to match final test choice → spec the `/init` endpoint that seeds `ThinkingProfile` from quiz results.

---

### Entry 003 — Day 15: 2026-03-29

**Goal:** Audit and lock the stage agent prompt architecture, with two critical findings that required structural changes across all 6 stage graphs.

**Decision:** Identified that stage agents (thinking, purpose, etc.) were generating student-facing Vietnamese responses into `{stage}_message` queues — responses the output compiler never reads, since `output_compiler` reads `state["messages"]` (global) not per-stage queues. Chose Option B: stage agents now generate ANALYSIS written to `stage_reasoning.{stage}`, which the output compiler reads via `PROFILE_CONTEXT_BLOCK`. Separately, removed `summarizer_node` and `check_node` from all 6 stage graphs — these were per-stage token counting and compression nodes that added an LLM hop for compressing analysis the agent itself now writes each turn. Renamed `ProfileSummary` → `StageReasoning` across all 18 files to align class name with new function. Audited and enriched `INPUT_PARSER_PROMPT` (added `<architecture>` block defining knowledge vs. data agent taxonomy, removed stale `path(6)` from stage sequence), `THINKING_DRILL_PROMPT` (removed MI/RIASEC priors — test results belong in a Python seeding function, not LLM interpretation), and `PURPOSE_DRILL_PROMPT` (added domain knowledge block with 10 Vietnamese cultural compliance patterns and per-field probe angles). Expanded `ThinkingProfile.personality_type` to 5 buckets by adding `"leader"` to cover E (Enterprising) RIASEC and Interpersonal MI gap.

**Rejected alternative:** Option A (chatbot generates draft question → new `stage_draft` state field → output compiler adapts). Option A would've kept the agent as a questioner but required a new state field and a new `STAGE_DRAFT_BLOCK` in `output.py`. Option B achieves the same goal with zero new state fields — the output compiler already reads `stage_reasoning` via `PROFILE_CONTEXT_BLOCK`. The only cost: output compiler gets less structured guidance (prose analysis vs. a draft question), but it already has `fields_needed` and `stage_status` from `_compute_stage_status()` to compensate.

**What broke:** The chatbot nodes in `thinking_graph.py` and `purpose_graph.py` were generating Vietnamese student responses and writing them as strings to `{stage}_message`. These strings accumulated in the per-stage queue but were never read by the output compiler. The output compiler was generating the actual response independently from `compiler_prompt + state["messages"]`. Two LLM calls per turn were running; only one was doing visible work.

**What I learned:** Node output shape determines information flow, not graph topology. A node can return the right type and write to the right state key while being functionally invisible if no downstream node reads that key. The audit question "does this output reach the student?" must be traced through the actual reader chain, not assumed from the graph edge.

**Next:** Build Python seeding function that maps `brain_type` + `riasec_scores` → ThinkingProfile initial field confidences (e.g., kinesthetic → `learning_mode: hands-on, confidence=0.6`). Write `goals.py` prompts — first new knowledge agent prompt with the analyst output pattern.

---

### Entry 002 — Day 15: 2026-03-29

**Goal:** Lock the path-agent removal and spec the knowledge/data agent taxonomy and data retrieval contract.

**Decision:** Fully deleted `PathProfile` from `state.py` and removed `path` + `path_limit` from `PathFinderState`. Path debate is now Case B2 in `build_compiler_prompt()` — a prompt injection block (`PATH_DEBATE_BLOCK`) triggered by a pure Python check: all 6 profiles `done=True`. Separately, formalized the agent split into **knowledge agents** (thinking, purpose, goals — extract from the student's head, no external data) and **data agents** (job, major, uni — match against real-world datasets). Designed agent-exclusive Pydantic query forms (`JobQuery`, `MajorQuery`, `UniQuery`) where each form's fields map directly to that agent's `*Profile` fields. `JobScoringOutput` combines FieldEntries + `JobQuery | None` + `need_data: bool` into one structured output call, avoiding a second LLM hop.

**Rejected alternative:** RAG (vector store + semantic search) for data agent retrieval. The full VN-focused dataset is ~100 entries across three categories — it fits in a few KB of JSON. Semantic search adds embedding costs, a vector store dependency, and nondeterministic results on short enum-like entries ("startup", "engineer"). Deterministic Python filter functions on JSON files (`filter(jobs, role_category="engineer")`) are faster, cheaper, and produce auditable results. RAG solves a scale problem that doesn't exist here.

**What broke:** `PathProfile` class and `path: PathProfile | None` / `path_limit: bool` removed from state. Any node that referenced these fields (none were wired yet) would now fail import. `ProfileSummary.path` slot also removed. `_compute_stage_status()` in `output.py` no longer includes a "path" entry in its `profile_map`.

**What I learned:** The gate question for "subgraph vs. compiler mode" is: does this stage introduce a **new query form exclusive to its domain**? Data agents are distinguished by having a typed retrieval contract (a Pydantic query form) that knowledge agents never need. The taxonomy isn't just a UX distinction — it's a structural one that changes node topology.

**Next:** Define `jobs.json` schema (~50 VN-relevant entries: role_category, company_stage, vn_salary range, required_skills, related_majors). Build `retrieve_node` as a pure Python filter. Spec `JobScoringOutput` as the dual-purpose scoring output (FieldEntries + retrieval query).

---
