# Path_finder (Local Project State)

## 1. Macro Architecture
PathFinder is an intelligent career/university counseling system built on a multi-stage LangGraph topological architecture.

### 1.1 The System Topology (Final — from Miro v2)
The system is split into two frames: **Orchestrator (Input)** which routes and tags, and **Orchestrator (Output)** which compiles and verifies.

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ORCHESTRATOR (INPUT FRAME)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Orchestrator] ─► [Input] ──messages──► [Global Message Log]
      │                                         │
      │                                  Token limit hit?
      │                                         │
      ▼                                         ▼
 [Processing]                            [Summarizer]
   │                                      │               │
   │  Outputs:                     message_summary  profile_summary
   │  • stage_check                      ▼               ▼
   │  • message_tag                [Orchestrator]  [Stage Agents]
   │  • user_tag
   │  • agent_tag
   │
   ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 STAGE FRAME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                      [Stage Manager]
                 (receives stage_check, message_tag,
                  user_tag, agent_tag)
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
    ─── SEQUENTIAL AGENT CHAIN ───    {type}_data
                                         ▼
  [thinking_agent]                  [data_manager]
       ↓ thinking                        ↕
  [purpose_agent] ──purpose──►      [Database]
  [goal_agent]    ──goal────►           ↕
  [job_agent]     ──job─────►      [researcher]
  [major_agent]   ──major───►
  [uni_agent]     ──uni─────►
  [path_agent]    (terminal: final path synthesis)

  (Each agent: Scoring → Summarizer(conditional) → ChatBot)
  (Each agent system prompt contains the confidence_score mandate)

  ← {agent}_response to output_compiler ─────────────────────►

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ORCHESTRATOR (OUTPUT FRAME)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  {agent}_response + edge_cases
         │
         ▼
  [output_compiler] ──response──► [output_check] ──output──► User
  (GPT-5.2)                       (Verdict/Safety check)
```

### 1.2 The Specialist Subgraph Topology (State-Driven Prompting)
Inside every specialist subgraph (e.g., Purpose), execution strictly follows this order to eliminate Chatbot hallucination:

1. **Scoring Node:** Reads the message queue, hard-extracts `confidence_scores`, and updates the Pydantic State (e.g., `core_desire = "wealth"`).
2. **Summarizer Node (Conditional):** If the Orchestrator flags high token count, this node compresses the agent's specific message history.
3. **ChatBot Node:** Reads the extracted State (NOT just raw messages) to generate the next Socratic question.

---

## 2. Core Operational Protocols

### 2.1 Dual-Model Token & Output Strategy
To operate within the 250k (HIGH) / 2.5M (LOW) daily daily limits, the system enforces a strict division of labor and output shaping:
- **HIGH Model (GPT-5.2):** Used ONLY by the Orchestrator for Semantic Tagging, and by the Compiler Node for final response synthesis.
- **LOW Model (GPT-5-mini):** Used by all 8 Specialist Agents for Scoring and Chatting.

### 2.2 Fluid "Human Flow" Routing
The system does not enforce rigid, static UI stages. It relies on a fluid interface driven by Orchestrator Tags. 
- If a user in the "Purpose" phase suddenly asks about a "Job", the Orchestrator tags both `["purpose", "job"]`.
- Both subgraphs execute and draft responses.
- The Compiler fluidly merges them: *"Understood about the salary requirement (Job). But returning to your core motivation, why is that number important? (Purpose)"*

### 2.3 The Verdict Check Protocol
Before the Output Agent writes the final recommendation, the Orchestrator forces a validation round across ALL agents:
- Orchestrator asks each agent: *"Given this final university, from YOUR domain perspective, does this make sense?"*
- Agents must reply strictly with `APPROVE` or `REJECT` + reason.
- If any agent rejects (e.g., Job Agent outputs: *"REJECT - this uni doesn't produce the role user wants"*), the flow routes back to resolve the contradiction.

---

## 3. State Schema (`backend/data/state.py`)
`PathFinderState` (`TypedDict`) maps with LangGraph `MemorySaver`. All Pydantic models are defined at the top of `state.py` — no separate models file.

### Core Wrapper
- `FieldEntry(BaseModel)`: `{content: str, confidence: float}` — uniform interface for all extractable fields.

### Routing + Output Modifiers
- `StageCheck` — `current_stage`, `completed_stages`, `skipped_stages`, `rebound_pending`, `rebound_target`
- `MessageTag` — per-turn: `message_type` (true/vague/troll), `drill_required`, `response_tone`
- `UserTag` — persistent: `parental_pressure`, `burnout_risk`, `urgency`, `autonomy_conflict`

### Stage Profiles (Layer 2)
| Field in State | Model | Stage |
|---|---|---|
| `thinking` | `ThinkingProfile` | 0 |
| `purpose` | `PurposeProfile` | 1 |
| `goals` | `GoalsProfile` | 2 — wraps `GoalsLongProfile` + `GoalsShortProfile` |
| `job` | `JobProfile` | 3 |
| `major` | `MajorProfile` | 4 |
| `university` | `dict \| None` | 5 — placeholder (UniProfile scrapped for now) |
| `path` | `PathProfile` | 6 — terminal synthesis by `path_agent` |

### Scores (Layer 3)
- `confidence_scores: dict` — per-stage aggregate `{"purpose": 0.8, ...}`
- `fit_scores: dict` — per-university fit

### System Meta (Layer 4)
- `message_tag`, `user_tag`, `active_tags`, `current_agent`
- `escalation_flags`, `troll_warnings`, `uni_data`, `verdict`

---

## 4. Current Implementation State
**Status: `state.py` FINALIZED.** All Pydantic models defined and import-verified.

**Active Focus:** `purpose_graph.py` — align `ConfidentDict` Pydantic output to new `PurposeProfile` model so `confident_node` writes `.model_dump()` back to `purpose` field correctly.

## 5. Known Bugs / Friction Points
- **Pydantic mapping:** Direct assignment of Pydantic Structured Outputs into `TypedDict` states can crash LangGraph type checkers. Ensure each agent explicitly executes `.model_dump()` before state return.
- **Sequential vs Parallel:** The agent chain is sequential (purpose → goal → job → major → uni). Ensure LangGraph edges are `add_edge` (sequential), NOT `add_conditional_edges` with Send (parallel) for the counseling chain.
- **`path_agent`:** This is a NEW terminal agent that synthesizes the final path recommendation. It is NOT the same as the Output Compiler. The Compiler just merges output text. `path_agent` synthesizes the structured PATH object.
