"The fuck you mean you want freedom?"
**PathFinder** is an AI agent designed to drill down into your actual goals—not the vague "I want freedom" bullshit—and map it directly to a specific job, major, and finally, a university that actually fits.

### Purpose:
Most counseling is just matching test scores to random schools. PathFinder drills you. 
- Why do you want PM over Dev? (Because you care about impact over writing the code).
- Why do you actually want to study in the US? (Is it the tech scene or just ego?).
It forces you to answer the hard questions, translates that into structured data, and then cross-checks to find the right degree and school.

### Tech Stack?
- **Brain:** OpenAI GPT + LangGraph (Master Orchestrator + 8 Specialist Agents)
- **Backend:** Python + Pydantic (Strict structured data, no yapping from sub-agents)
- **State:** LangGraph MemorySaver (3-Tier Context RAG to keep API costs down)
- **Frontend:** React + Vite + Tailwind (Soon)

### How to Use:
*(Blank for now until the Orchestrator graph is wired)*

### Development History:
We are building this agent from the ground up (Bottom-Up Law) to master multi-agent AI engineering.

- [x] Master topology designed (Orchestrator Ascended pattern)
- [x] State schema locked (4 chronological layers)
- [x] Gitignore shielded
- [x] Tier 1: The Purpose Agent (Drill down) -> 3-node graph compiled and running.
- [ ] Tier 2: The Goals Agent
- [ ] Tier 3: The Job Agent
- [ ] Tier 4: The Major Agent
- [ ] Tier 5: The Uni & Research Agents
- [ ] Wire the Master Orchestrator

### Q&A:
Why?
To prove I can orchestrate complex, multi-agent AI systems, manage API context heavily, and build something that actually helps visual thinkers like me make massive life decisions. This is the FPT SE Scholarship portfolio piece.

TF are you doing?
Applying the SEAM method. Building to the junction, seeing what breaks, and fixing it. I'm forcing the AI to give me only the `???` scaffolds so I have to actually write the logic bodies myself. No copy-pasting answers. 

### Logs:
See [DEV_DIARY.md](DEV_DIARY.md)
- Mapped the massive 8-agent topology. Realized I need to build from the bottom up or it will become a tangled mess.
- Dialed in the Antigravity Engine: Refined the X-Ray doc tools and forced the AI to only give me "official docs" so I don't get robbed of the learning gap.
- Connected LangGraph Studio local server to bypass docker headaches.
- Started building the `purpose.py` agent. Realized Pydantic models need exact `.model_dump()` to not crash the LangGraph state.
- Slowly moving from "Thinker" to "Doer" phase, as always haha.
- Executed massive `/research` protocols on LangGraph Evals and Bootstrapping.
- Complete System Architecture Audit: Redesigned the Orchestrator with internal Chat Manager nodes, defined "Soft Boundaries" for agent handoffs, and injected `ThinkingProfile` into the graph state.
- Purged messy dict states. Built new strict Pydantic models (`PurposeProfile`, `MajorProfile`, etc.) in `models.py` and wired them heavily into `state.py`.
- Currently running `langgraph dev` testing the newly fortified `purpose_graph.py` against the rigid schema.

*Built by Anh Duc*