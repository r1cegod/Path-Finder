"""
PathFinder shared state — the single source of truth.

Every agent reads from and writes back to this state.
Orchestrator holds the full state. Agents get compressed handoffs.

─────────────────────────────────────────────────────────────
 MODEL HIERARCHY
─────────────────────────────────────────────────────────────
 FieldEntry
  └─► all profile fields              ← uniform {content, confidence} shape
 StageCheck                           ← routing + anchor-stage meta
 MessageTag                           ← per-message output modifier
 UserTag                              ← persistent user constraint modifier
 StageReasoning                       ← per-stage running context summaries
 ThinkingProfile                      ← how user learns / operates
 PurposeProfile                       ← WHY they want anything
 GoalsLongProfile  ─┐
 GoalsShortProfile  ├─► GoalsProfile  ← WHAT they want (both horizons unified)
 JobProfile                           ← WHERE they land
 MajorProfile                         ← HOW they get qualified
─────────────────────────────────────────────────────────────
"""

from typing import TypedDict, Annotated
from langgraph.graph import add_messages
from pydantic import BaseModel, ConfigDict


# ═══════════════════════════════════════════════════════════
#  BASE WRAPPER
# ═══════════════════════════════════════════════════════════

class FieldEntry(BaseModel):
    content: str      # ← extracted text value from conversation
    confidence: float # ← 0.0–1.0; written ONLY by the Scoring Node
    # Rule: Scoring Node reads purpose_message → writes FieldEntry(s) back to state
    # Downstream agents and the output compiler read these values.
    # Never mutate confidence outside the Scoring Node.


# ═══════════════════════════════════════════════════════════
#  ROUTING + OUTPUT MODIFIERS
# ═══════════════════════════════════════════════════════════

class MessageTag(BaseModel):
    # ─ Per-message output modifier ─────────────────────────
    # Set by Orchestrator each turn. Does NOT persist across turns.
    model_config = ConfigDict(extra="forbid")
    message_type: str = "true"
    # "true"          → genuine, on-topic answer
    # "vague"         → long but empty, surface-level content
    # "troll"         → not engaging, adversarial
    # "genuine_update"→ student explicitly revised a past answer (celebrate, do NOT probe)
    # "disengaged"    → short + meaningless, student checked out
    # "avoidance"     → engages but dodges a specific field
    # "compliance"    → answers immediately but answer is social/generic script
    response_tone: str = "socratic"
    # "socratic" → Socratic question drill
    # "firm"     → troll boundary enforcement
    # "redirect" → pull user back to stage topic


class UserTag(BaseModel):
    # ─ Persistent user modifier ────────────────────────────
    # High-level orchestrator parser writes the bool signal fields.
    # Sub-orchestrator maintenance refreshes the reasoning/text fields selectively.
    # bool = True  → concern detected, reasoning string injected into output block
    # bool = False → reasoning ignored, block not injected
    model_config = ConfigDict(extra="forbid")

    # ─── PSYCHOLOGICAL FLAGS (bool + reasoning) ────────────
    parental_pressure: bool = False
    parental_pressure_reasoning: str = ""
    # e.g. "Mother insists on medical school, father defers to mother"

    burnout_risk: bool = False
    burnout_risk_reasoning: str = ""
    # e.g. "Student mentions 4hr sleep, multiple extracurriculars, voice fatigue"

    urgency: bool = False
    urgency_reasoning: str = ""
    # e.g. "GAOKAO in 2 months, application deadline driving all decisions"

    core_tension: bool = False
    core_tension_reasoning: str = ""
    # e.g. "High-achiever identity vs. desire for non-traditional creative path"

    # ─── SELF-AUTHORSHIP (str only, spectrum) ──────────────
    self_authorship: str = ""
    # Empty = no block injected.
    # Non-empty = reasoning injected into SELF_AUTHORSHIP_BLOCK.
    # e.g. "Student exclusively uses 'bố mẹ muốn' framing, no personal voice detected"

    # ─── BEHAVIORAL REASONING (str only, no bool) ──────────
    # Detection lives in MessageTag.message_type. Reasoning persists here.
    reality_gap: bool = False
    # Set by orchestrator. True when ambition vs. evidence diverges.
    # Only clears when orchestrator explicitly sets False.
    reality_gap_reasoning: str = ""
    # Orchestrator UPDATES (appends/refines) when reality_gap=True. Persists until explicitly cleared.
    # Output compiler reads: if reality_gap=True → inject REALITY_GAP_BLOCK with this reasoning.
    compliance_reasoning:       str = ""
    disengagement_reasoning:    str = ""
    avoidance_reasoning:        str = ""
    vague_reasoning:            str = ""


class StageReasoning(BaseModel):
    # ─ Per-stage running context summaries ─────────────────
    # Each stage agent writes its OWN slot. Orchestrator reads ALL slots.
    # Agents receive their own slot instead of the full message history.
    # On first turn, all slots are empty string "".
    thinking: str  = ""   # ThinkingProfile agent's summary of what it extracted
    purpose: str  = ""   # PurposeProfile agent's summary
    goals: str  = ""   # GoalsProfile agent's summary
    job: str  = ""   # JobProfile agent's summary
    major: str  = ""   # MajorProfile agent's summary
    uni: str = ""


# ═══════════════════════════════════════════════════════════
#  STAGE PROFILES
# ═══════════════════════════════════════════════════════════

class ThinkingProfile(BaseModel):
    # ─ Stage 0: How does this human operate? ───────────────
    # Required by Major Agent + Uni Agent for curriculum/campus fit.
    done: bool
    learning_mode: FieldEntry    # "visual" | "hands-on" | "theoretical"
    env_constraint: FieldEntry   # "home" | "campus" | "flexible"
    social_battery: FieldEntry   # "solo" | "small-team" | "collaborative"
    personality_type: FieldEntry # "analytical" | "creative" | "social" | "builder" | "leader"
    brain_type: list[str] = []   # MI types scoring 80+, set by frontend quiz (e.g., logical, kinesthetic)
    riasec_top: list[str] = []   # Top 2 RIASEC codes, set by frontend quiz (e.g., ["I", "R"])
    # Values: R | I | A | S | E | C  — no mapping, raw codes passed to thinking agent
    riasec_scores: list[str] = [] # Top 2-3 Holland Codes from frontend quiz (e.g., ["Realistic", "Investigative"])


class PurposeProfile(BaseModel):
    # ─ Stage 1: WHY do they want anything at all? ──────────
    # Core motivation layer. Goal/Job/Major agents read this to calibrate fit.
    done: bool
    core_desire: FieldEntry       # wealth | impact | creative control | freedom from X
    work_relationship: FieldEntry # "calling" | "stepping stone" | "necessary evil"
    ai_stance: FieldEntry         # "fear" | "leverage" | "indifferent"
    location_vision: FieldEntry   # "remote" | "relocate abroad" | "tied to hometown"
    risk_philosophy: FieldEntry   # "startup risk" | "corporate ladder" | "gov stability"
    key_quote: FieldEntry         # verbatim quote capturing their core essence


class GoalsLongProfile(BaseModel):
    # ─ Stage 2a: Long-term horizon (5–10 year) ─────────────
    done: bool
    income_target: FieldEntry     # concrete number + timeframe ("$5k/mo by 28")
    autonomy_level: FieldEntry    # "full" | "partial" | "employee"
    ownership_model: FieldEntry   # "founder" | "partner" | "freelance" | "employee"
    team_size: FieldEntry         # "solo" | "small (<10)" | "large"


class GoalsShortProfile(BaseModel):
    # ─ Stage 2b: Short-term horizon (next 1–2 years) ───────
    done: bool
    skill_targets: FieldEntry     # specific skills to acquire now
    portfolio_goal: FieldEntry    # what they want to show in 1 year
    credential_needed: FieldEntry # "degree" | "cert" | "portfolio-only"


class GoalsProfile(BaseModel):
    # ─ Stage 2: WRAPPER — both horizons under one state key ─
    # State holds: goals: GoalsProfile | None
    # Goal Agent writes long/short independently; wrapper keeps them atomic.
    done: bool
    long: GoalsLongProfile | None   # None until Scoring Node extracts it
    short: GoalsShortProfile | None # None until Scoring Node extracts it


class JobProfile(BaseModel):
    # ─ Stage 3: WHERE do they land after school? ───────────
    done: bool
    role_category: FieldEntry   # "engineer" | "founder" | "researcher" | "creative"
    company_stage: FieldEntry   # "startup" | "scaleup" | "corp" | "self"
    day_to_day: FieldEntry      # what the actual daily work looks like
    autonomy_level: FieldEntry  # "full" | "managed" | "directed"


class JobResearch(BaseModel):
    need_research: bool = False
    query_focus: str = ""
    contradiction_to_test: str = ""
    search_query: str = ""
    domain_bucket: str = ""
    evidence_summary: str = ""
    cited_sources: list[str] = []
    market_verdict: str = ""
    research_complete: bool = False


class MajorResearch(BaseModel):
    need_research: bool = False
    query_focus: str = ""
    contradiction_to_test: str = ""
    search_query: str = ""
    domain_bucket: str = ""
    evidence_summary: str = ""
    cited_sources: list[str] = []
    market_verdict: str = ""
    research_complete: bool = False


class MajorProfile(BaseModel):
    # ─ Stage 4: HOW do they get qualified? ─────────────────
    done: bool
    field: FieldEntry                    # "CS" | "Business" | "Design" | ...
    curriculum_style: FieldEntry         # "theory-heavy" | "project-based" | "mixed"
    required_skills_coverage: FieldEntry # does this major cover what JobProfile needs?


class UniProfile(BaseModel):
    # ─ Stage 5: WHERE do they study? ───────────────────────
    done: bool
    prestige_requirement: FieldEntry  # e.g., "top-tier" | "mid-tier" | "irrelevant"
    target_school: FieldEntry         # Specific school name
    campus_format: FieldEntry         # e.g., "domestic" | "international"
    is_domestic: bool                 # True if Vietnamese school. Output Compiler strictly warns if False.


class UniResearch(BaseModel):
    need_research: bool = False
    query_focus: str = ""
    contradiction_to_test: str = ""
    search_query: str = ""
    domain_bucket: str = ""
    evidence_summary: str = ""
    cited_sources: list[str] = []
    market_verdict: str = ""
    research_complete: bool = False


class StageCheck(BaseModel):
    # ─ Routing metadata (LLM classifies, Python reads) ───
    stage_related: list[str] = []
    current_stage: str = "thinking"
    anchor_stage: str = "thinking"
    anchor_mode: str = "normal"
    requested_anchor_stage: str = ""
    contradict: bool = False
    contradict_target: list[str] = []
    # contradict_count → moved to top-level state (Python-only)

# ═══════════════════════════════════════════════════════════
#  LANGGRAPH STATE
# ═══════════════════════════════════════════════════════════

class PathFinderState(TypedDict):
    # ─── LAYER 1: CONVERSATION ─────────────────────────────
    messages: Annotated[list, add_messages]
    # Auto-appends via LangGraph's add_messages reducer.
    # Returning {"messages": [new_msg]} APPENDS — it does NOT overwrite.

    stage_reasoning: StageReasoning
    # Per-stage running summaries. Each agent writes its own slot.
    # Agents read THEIR OWN slot here — not the raw global message history.

    summary: str
    # Legacy conversation summary lane. No longer maintained by orchestrator.
    # Keep until other graph consumers are migrated.

    routing_memory: Annotated[list, add_messages]
    # Sub-orchestrator long-log message lane. Mirrors raw conversation turns.
    # On overflow, append path drops the oldest 3/4 of the lane and keeps appending.
    # Summarizer / memory compression for this lane is still pending.

    bypass_stage: bool
    # Set by orchestrator input_parser. True → graph skips stage agents, routes to compiler directly.
    # Normal non-stage input (greetings, process questions, acks). NOT an error state.

    # Per-agent message queues (tagged slices of global history)
    purpose_message: Annotated[list, add_messages]
    goals_message: Annotated[list, add_messages]
    job_message: Annotated[list, add_messages]
    major_message: Annotated[list, add_messages]
    uni_message: Annotated[list, add_messages]
    thinking_style_message: Annotated[list, add_messages]

    # ─── LAYER 2: EXTRACTED PROFILE ────────────────────────
    stage: StageCheck
    # Routing metadata. current_stage is funnel logic; anchor_stage owns the live turn.

    thinking: ThinkingProfile | None
    # Stage 0. How user learns + operates. Foundation all other agents build on

    purpose: PurposeProfile | None
    # Stage 1. WHY they want anything.

    goals: GoalsProfile | None
    # Stage 2. WHAT they want — both horizons wrapped in one atomic field.
    # goals.long  → 5–10 year horizon
    # goals.short → next 1–2 years

    job: JobProfile | None
    # Stage 3. WHERE they land post-study.

    job_research: JobResearch | None
    # Stage 3 retrieval packet. Written by planner / researcher nodes.
    # Read by the job synthesizer.

    major_research: MajorResearch | None
    # Stage 4 retrieval packet. Written by planner / researcher nodes.
    # Read by the major synthesizer.

    major: MajorProfile | None
    # Stage 4. HOW they get qualified.

    university: UniProfile | None
    # Stage 5. The Institution (Gatekeeping & ROI limits)

    uni_research: UniResearch | None
    # Stage 5 retrieval packet. Written by planner / researcher nodes.
    # Read by the university synthesizer.

    path_debate_ready: bool
    # Python-computed by stage_manager each turn.
    # True when all 6 profiles are done, no blocking user constraints gate B2,
    # and the orchestrator routed this turn to bypass/output instead of more drilling.
    # Output compiler reads this and switches to Case B2.
    # Never set by LLM. LLM CANNOT see this field.

    stage_transitioned: bool
    # True for exactly ONE turn after anchor_stage changes.
    # Written by stage_manager. Compiler injects STAGE_INTRO_BLOCK when True.
    # Never set by LLM.

    compiler_prompt: str
    # Assembled system prompt for output_compiler. Written by context_compiler each turn.
    # Pure Python decision tree output — no LLM involvement.

    # ─── LAYER 3: SYSTEM META ─────────────────────────────
    message_tag: MessageTag | None
    # Per-turn output modifier. Set by Orchestrator Tagger. Resets each turn.

    user_tag: UserTag | None
    # Persistent output modifier. Bool fields refresh in input_parser;
    # reasoning/text fields refresh in sub-orchestrator maintenance.
    
    troll_warnings: int
    # 0–3. Escalation path triggers at 3.
    # Managed by orchestrator each turn:
    #   troll flagged → count + 1 | NOT flagged → max(0, count - 1)  ← passive decay
    # Students are goofy. One troll msg shouldn't stick forever.


    escalation_pending: bool
    # True → output compiler writes the Case C close-out message.
    # Triggered by: harm signal | compliance_turns >= 9 | counter >= 3 | silent 10-turn window
    escalation_reason: str
    # Hardcoded string set by the node that triggers escalation.
    # Format: "{source}: {detail}" — output compiler reads this for the handoff message.
    # e.g. "contradict_count: 3 consecutive contradictions"
    #      "silent_window: troll 6/10, disengagement 5/10"
    #      "compliance: compliance_turns forced to 8 (chronic)"

    compliance_turns: int
    # Managed by counter_manager each turn:
    #   message_type == "compliance" → count + 1 | else → max(0, count - 1)
    # Prompt trigger: escalating technique by level (1-3 / 4-5 / 6-7 / 8-9)
    # Real escalation: 10-turn window >= 5/10 → force to 9; next trigger → 10 → escalate

    disengagement_turns: int
    # Managed by counter_manager each turn:
    #   message_type == "disengaged" → count + 1 | else → max(0, count - 1)
    # >= 3: DISENGAGEMENT_BLOCK (warning) | >= 4: escalation_pending = True

    avoidance_turns: int
    # Managed by counter_manager each turn:
    #   message_type == "avoidance" → count + 1 | else → max(0, count - 1)
    # >= 3: AVOIDANCE_BLOCK (warning) | >= 4: escalation_pending = True

    vague_turns: int
    # Managed by counter_manager each turn:
    #   message_type == "vague" → count + 1 | else → max(0, count - 1)
    # >= 3: VAGUE_BLOCK (pattern warning — not escalation)

    contradict_count: int
    # Managed by stage_manager each turn:
    #   contradict=True  → count + 1 | False → max(0, count - 1)
    # >= 3 → escalation_pending = True
    verdict: dict | None
    # Final cross-agent verdict. {"purpose": "APPROVE", "job": "REJECT: ...", ...}

    # ─── LAYER 4: SILENT MONITORING ─────────────────────────
    turn_count: int
    # Incremented each turn by orchestrator. Used for 10-turn window checks.
    trigger_window: dict
    # Tracks trigger count per counter in the current 10-turn window.
    # Shape: {"contradict": int, "compliance": int,
    #         "disengagement": int, "troll": int, "avoidance": int, "vague": int}
    # Every 10 turns (turn_count % 10 == 0 and turn_count > 0):
    #   if any counter >= 5 (50%):
    #     compliance → force compliance_turns = 9 (threshold = 10 → escalate)
    #     all others → escalation_pending = True
    #   then reset all values to 0

DEFAULT_STAGE = {
    "stage_related": [],
    "current_stage": "thinking",
    "anchor_stage": "thinking",
    "anchor_mode": "normal",
    "requested_anchor_stage": "",
    "contradict": False,
    "contradict_target": [],
}

DEFAULT_STATE: PathFinderState = {
    "messages": [],
    "stage_reasoning": StageReasoning(),
    "summary": "",
    "routing_memory": [],
    "bypass_stage": False,
    "purpose_message": [],
    "goals_message": [],
    "job_message": [],
    "major_message": [],
    "uni_message": [],
    "thinking_style_message": [],
    "stage": DEFAULT_STAGE,
    "thinking": None,
    "purpose": None,
    "goals": None,
    "job": None,
    "job_research": None,
    "major_research": None,
    "major": None,
    "university": None,
    "uni_research": None,
    "path_debate_ready": False,
    "stage_transitioned": False,
    "compiler_prompt": "",
    "message_tag": None,
    "user_tag": None,
    "troll_warnings": 0,
    "escalation_pending": False,
    "escalation_reason": "",
    "compliance_turns": 0,
    "disengagement_turns": 0,
    "avoidance_turns": 0,
    "vague_turns": 0,
    "contradict_count": 0,
    "verdict": None,
    "turn_count": 0,
    "trigger_window": {
        "contradict": 0, "compliance": 0,
        "disengagement": 0, "troll": 0, "avoidance": 0, "vague": 0,
    },
}
