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
- **State:** 42-field TypedDict — 4 layers: conversation, extracted profiles, behavioral signals, counters
- **Frontend:** React 18 + Vite + Tailwind (wired)

### How to Use:
Start the API: `python main.py`
Send a POST to `/chat` with `{ "session_id": "...", "message": "..." }`.
LangGraph Studio: `langgraph dev`

### Development History:
Building from the ground up — Bottom-Up Law. Each node verified in isolation before wiring.

- [x] Master topology designed (Orchestrator Ascended pattern)
- [x] State schema locked (4 chronological layers, 42 fields, full writer/reader contracts)
- [x] Gitignore shielded
- [x] Input orchestrator complete — classify, rebound detection, contradict detection, 6 decay counters, 10-turn window
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

### Q&A:
**Why?**
To prove I can orchestrate complex, multi-agent AI systems — manage state, handle edge cases, keep context tight — and build something that actually helps students like me make massive life decisions. This is the FPT SE Scholarship portfolio piece.

**How are you building this?**
Applying the SEAM method. Bottom-Up Law — build each node independently, verify in isolation, wire last. Every architectural decision has a rejected alternative documented. See `ARCHITECTURE.md` for the full ADR record.

**What's the hardest part?**
Not the models. State management and edge case routing — troll detection, contradictions, stage skips, rebound detection — all must feel like happy cases, not errors. The LLM classifies; Python counts, routes, and escalates. That boundary is where most of the design work lives.

### Logs:
See `DEV_LOG.md`

*Built by Anh Duc — solo, self-taught.*
