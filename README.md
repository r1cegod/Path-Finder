"The fuck you mean you want freedom?"
**PathFinder** is an AI agent designed to drill down into your actual goals—not the vague "I want freedom" bullshit—and map it directly to a specific job, major, and finally, a university that actually fits.

### Purpose:
Most counseling is just matching test scores to random schools. PathFinder drills you.
- Why do you want PM over Dev? (Because you care about impact over writing the code).
- Why do you actually want to study in the US? (Is it the tech scene or just ego?).
It forces you to answer the hard questions, translates that into structured data, and then cross-checks to find the right degree and school.

Built for Vietnamese students. Conducted in Vietnamese.

### Tech Stack:
- **Brain:** OpenAI GPT + LangGraph (Master Orchestrator + 6 Stage Agents)
- **Backend:** Python + Pydantic v2 (strict structured output, `extra="forbid"` on all models)
- **State:** Shit tons of field, go see for your self
- **Frontend:** React 18 + Vite + Tailwind (wired), live with railway and vercel.

### How to Use:
Start the API: `python main.py`
Send a POST to `/chat` with `{ "session_id": "...", "message": "..." }`.
LangGraph Studio: `langgraph dev`
Live in vercel: https://path-finder-rosy.vercel.app

### Documentation:
Live documentation now lives in the PathFinder vault workspace:
https://github.com/r1cegod/ADUC-obsidian-vault

The repo `docs/` folder is legacy archive material and should not be treated as canonical.
The canonical Python-function-check workflow now lives in the PathFinder vault evaluation docs, not in this repo tree.

### Learning history:
- Raw python bot
- Langraph integration
- First project: https://github.com/r1cegod/FunctionPartner-Amber
- And now this damn project
- And also a master obsidian vault: https://github.com/r1cegod/ADUC-obsidian-vault

### Development History:
Building from the ground up — Bottom-Up Law. Each node verified in isolation before wiring.

- [x] Master topology designed (Orchestrator Ascended pattern)
- [x] State schema locked (4 chronological layers, 42 fields, full writer/reader contracts)
- [x] Gitignore shielded
- [x] Input orchestrator complete — classify, contradict detection, anchor-stage requests, 6 decay counters, 10-turn window
- [x] Stage agent architecture locked — analyst pattern (writes to `stage_reasoning`; output compiler is sole response generator)
- [x] Tier 0: Thinking Agent (MI + RIASEC seeding → behavioral inference)
- [x] Tier 1: Purpose Agent (Socratic drilling, compliance detection)
- [x] Tier 2: Goals Agent
- [x] Tier 3: Job Agent
- [x] Tier 4: Major Agent
- [x] Tier 5: University Agent
- [x] Master Orchestrator wired — full pipeline: input → 6 stage agents → output compiler
- [x] Output compiler Case B — B1 (stage drill) and B2 (path debate placeholder) prompt injection
- [x] Persistent domain memory — Python tagger writes raw messages to `{stage}_message` queues, isolated from global summarizer compression
- [x] Contradict tagger — `stage_manager` re-tags past stage queues when `contradict_target` is set
- [x] Data agent retrieve contracts — `JobQuery` / `MajorQuery` / `UniQuery` + `retrieve_node` (Python filter on JSON)
- [x] Output compiler B2 fully implemented — path debate synthesis logic
- [x] fully working frontend
- [x] some evaluation, mvp shipped
- [x] Goals agent runtime bug fixed — missing prompt format args (is_current_stage, purpose, message_tag) in goals_graph.py
- [x] Eval pipeline documented — delegation doc at docs/delegated/eval_run_eval.md (2-floor flow, all Python patterns explained)
- [x] Delegation protocol locked — HOW_TO_USE + 2-floor flow standard for all delegated code (docs/workflows/delegated_feature_how_to.md)
- [x] CLAUDE.md upgraded — inline auto-update rules table replacing end-of-session batch rule
- [x] RIASEC/MI quiz seeding fixed — `/test` now writes brain_type/riasec_top to LangGraph checkpointer via `aupdate_state`; thinking_graph sees quiz results
- [x] `serialize_state` coverage fixed — university now included in completedStages; escalationPending surfaced to frontend
- [x] Post-escalation backend lock — `main.py chat_stream` gates all graph runs on `escalation_pending`; streams hardcoded VN response with zero graph traversal
- [x] `vague_turns` counter completed — direct escalation cap at >= 4, documented in state_architecture.md
- [x] Master vault initialized

### Q&A:
**Why?**
To prove I can orchestrate complex, multi-agent AI systems — manage state, handle edge cases, keep context tight — and build something that actually helps students like me make massive life decisions. This is the FPT SE Scholarship portfolio piece.

**It is just "vibe coded" app?**
Hell naw, define "vibe code"? Vibe coded mark only apply for products created with pure "fun and vibes" no fucking understanding whatsoever. I learned shit my self starting with python llm bot call and moving on, did delegated the frontend and some python feature still i got the understanding.

**How are you building this?**
Applying the SEAM method. Bottom-Up Law — build each node independently, verify in isolation, wire last. Every architectural decision has a rejected alternative documented. See `ARCHITECTURE.md` for the full ADR record.

**What's the hardest part?**
Not the models. State management and edge case routing — troll detection, contradictions, stage skips, and anchor-stage detours — all must feel like happy cases, not errors. The LLM classifies; Python counts, routes, and escalates. That boundary is where most of the design work lives.

**Drop the settup**'
The four horse men of development "ME"-Learning and Architecting (literally), "Claude code"-Reasoning (fucking useless with this kind of limit), "Codex"-Execution (code write, review, prompt audit) and "Gemini-Antigravity-Google AI studio"- One hit wonder (gives the cool ide and frontend build)

### Logs:
See https://github.com/r1cegod/ADUC-obsidian-vault

### NOTE:
PLEASE don't go crazy on pathfinder or share it to other people, I only have 250k token on gpt 5.4 and 2.5M on gpt 5.4 mini DAILY. It can NOT handle over 100 message a day, over the limit and my wallet vaporizes.

*Built by Anh Duc — solo, self-taught, powered with claude, codex and gemini*
