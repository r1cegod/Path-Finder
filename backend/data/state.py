"""
PathFinder shared state — the single source of truth.

Every agent reads from and writes back to this state.
Orchestrator holds the full state. Agents get compressed handoffs.

─────────────────────────────────────────────────────────────
 MODEL HIERARCHY
─────────────────────────────────────────────────────────────
 FieldEntry
  └─► all profile fields              ← uniform {content, confidence} shape
 StageCheck                           ← routing + soft-rebound meta
 MessageTag                           ← per-message output modifier
 UserTag                              ← persistent user constraint modifier
 ProfileSummary                       ← per-stage running context summaries
 ThinkingProfile                      ← how user learns / operates
 PurposeProfile                       ← WHY they want anything
 GoalsLongProfile  ─┐
 GoalsShortProfile  ├─► GoalsProfile  ← WHAT they want (both horizons unified)
 JobProfile                           ← WHERE they land
 MajorProfile                         ← HOW they get qualified
 PathProfile                          ← terminal synthesis
─────────────────────────────────────────────────────────────
"""

from typing import TypedDict, Annotated
from langgraph.graph import add_messages
from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════
#  BASE WRAPPER
# ═══════════════════════════════════════════════════════════

class FieldEntry(BaseModel):
    content: str      # ← extracted text value from conversation
    confidence: float # ← 0.0–1.0; written ONLY by the Scoring Node
    # Rule: Scoring Node reads purpose_message → writes FieldEntry(s) back to state
    # ChatBot Node reads the FieldEntry → uses content to shape its next question
    # Never mutate confidence from the ChatBot Node.


# ═══════════════════════════════════════════════════════════
#  ROUTING + OUTPUT MODIFIERS
# ═══════════════════════════════════════════════════════════

class MessageTag(BaseModel):
    # ─ Per-message output modifier ─────────────────────────
    # Set by Orchestrator Tagger each turn. Does NOT persist across turns.
    message_type: str    # "true" | "vague" | "troll"
    drill_required: bool # True → active agent must probe this turn, not accept answer
    response_tone: str   # "socratic" | "firm" | "redirect"
    #                      socratic  → Socratic question drill
    #                      firm      → troll boundary enforcement
    #                      redirect  → pull user back to stage topic
    deflection_type: str | None = None
    # None           → no deflection
    # "avoidance"    → engages but consistently dodges a specific field (3+ turns)
    # "compliance"   → answers immediately but answer is surface/generic
    # "topic_jump"   → pivots to a different stage before current is resolved


class UserTag(BaseModel):
    # ─ Persistent user constraint modifier ─────────────────
    # Set once and updated as context reveals more. Survives across turns.
    parental_pressure: bool   # external authority forcing a path
    burnout_risk: str         # "low" | "moderate" | "high"
    urgency: str              # "low" | "high" — GAOKAO/deadline pressure
    autonomy_conflict: bool   # user wants freedom, constraints say otherwise

    # ─ Psychological architecture ───────────────────────────
    # Safe defaults: assume externally-defined until proven otherwise.
    self_authorship: str = "externally_defined"
    # "externally_defined" → choices driven by family/scores/society; face-value answers untrustworthy
    # "transitioning"      → developing own voice; handle with Socratic scaffolding
    # "self_authored"      → genuine internal compass; answers can be taken at face value

    compliance_signal: bool = False
    # True = student gives socially acceptable answers ("I want to help society")
    #      ≠ genuine ("I want money and don't want to work for anyone")
    # When True: ALL extracted FieldEntry confidence scores are suspect.
    # Counselor must probe the gap between stated answer and underlying reality.

    core_tension: str | None = None
    # The single unresolved conflict blocking real progress.
    # e.g. "high-achiever identity vs. desire for non-traditional path"
    # e.g. "parents want medicine → student profile points to design"
    # When set: all downstream agents orient toward surfacing this tension.


class ProfileSummary(BaseModel):
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
    path: str = ""


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


class PurposeProfile(BaseModel):
    # ─ Stage 1: WHY do they want anything at all? ──────────
    # Core motivation layer. Goal/Job/Major agents read this to calibrate fit.
    done: bool
    core_desire: FieldEntry       # wealth | impact | creative control | freedom from X
    work_relationship: FieldEntry # "calling" | "stepping stone" | "necessary evil"
    ai_stance: FieldEntry         # "fear" | "leverage" | "indifferent"
    location_vision: FieldEntry   # "remote" | "relocate to US" | "tied to hometown"
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


class MajorProfile(BaseModel):
    # ─ Stage 4: HOW do they get qualified? ─────────────────
    done: bool
    field: FieldEntry                    # "CS" | "Business" | "Design" | ...
    curriculum_style: FieldEntry         # "theory-heavy" | "project-based" | "mixed"
    required_skills_coverage: FieldEntry # does this major cover what JobProfile needs?


class PathProfile(BaseModel):
    # ─ Stage 6: Terminal synthesis (path_agent ONLY) ───────
    # path_agent reads ALL profiles and synthesizes the final recommendation.
    # This is NOT the Output Compiler. Compiler merges text. path_agent builds this object.
    done: bool
    track: str                    # "A" (uni required) | "B" (optional) | "C" (not needed)
    recommended_uni: str | None   # None if track == "C"
    recommended_major: str | None
    recommended_job: str
    timeline: str                 # "4-year plan" narrative
    confidence: float             # overall path confidence 0.0–1.0

class StageCheck(BaseModel):
    stage_related: list[str]
    rebound: bool
    current_stage: str
    contradict: bool
    contradict_target: list[str]
    forced_stage: str
    stage_skipped: list[str]

# ═══════════════════════════════════════════════════════════
#  LANGGRAPH STATE
# ═══════════════════════════════════════════════════════════

class PathFinderState(TypedDict):
    # ─── LAYER 1: CONVERSATION ─────────────────────────────
    messages: Annotated[list, add_messages]
    # Auto-appends via LangGraph's add_messages reducer.
    # Returning {"messages": [new_msg]} APPENDS — it does NOT overwrite.

    profile_summary: ProfileSummary
    # Per-stage running summaries. Each agent writes its own slot.
    # Agents read THEIR OWN slot here — not the raw global message history.
    # Orchestrator reads ALL slots for full context.

    summary: str
    deflection_reasoning: str
    tension_reasoning: str

    # Per-agent message queues (tagged slices of global history)
    purpose_message: Annotated[list, add_messages]
    goals_message: Annotated[list, add_messages]
    job_message: Annotated[list, add_messages]
    major_message: Annotated[list, add_messages]
    uni_message: Annotated[list, add_messages]
    thinking_style_message: Annotated[list, add_messages]

    # ─── LAYER 2: EXTRACTED PROFILE ────────────────────────
    stage: StageCheck
    # Routing + soft-rebound metadata. Set by Orchestrator Tagger each turn.

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

    major: MajorProfile | None
    # Stage 4. HOW they get qualified.

    university: dict | None
    # Stage 5. Placeholder — UniProfile scrapped for now.

    path: PathProfile | None
    # Stage 6. Terminal path synthesis by path_agent.

    # ─── LAYER 3: SYSTEM META ─────────────────────────────
    message_tag: MessageTag | None
    # Per-turn output modifier. Set by Orchestrator Tagger. Resets each turn.

    user_tag: UserTag | None
    # Persistent output modifier. Set once, updated as context grows.
    
    troll_warnings: int
    # 0–3. Terminate session at 3.

    verdict: dict | None
    # Final cross-agent verdict. {"purpose": "APPROVE", "job": "REJECT: ...", ...}

    limit_hit: bool
    thinking_limit: bool
    purpose_limit: bool
    goal_limit: bool
    job_limit: bool
    major_limit: bool
    uni_limit: bool
    path_limit: bool
    input_token: int

    active_tags: list[str]

# ─── DEFAULT STATE (used when creating a new session) ──────
DEFAULT_STATE: PathFinderState = {
    "messages": [],
    "profile_summary": ProfileSummary(),
    "summary": "",
    "deflection_reasoning": "",
    "tension_reasoning": "",
    "purpose_message": [],
    "goals_message": [],
    "job_message": [],
    "major_message": [],
    "uni_message": [],
    "thinking_style_message": [],
    "stage_related": [],
    "thinking": None,
    "purpose": None,
    "goals": None,
    "job": None,
    "major": None,
    "university": None,
    "path": None,
    "message_tag": None,
    "user_tag": None,
    "active_tags": [],
    "troll_warnings": 0,
    "verdict": None,
    "limit_hit": False,
    "thinking_limit": False,
    "purpose_limit": False,
    "goal_limit": False,
    "job_limit": False,
    "major_limit": False,
    "uni_limit": False,
    "path_limit": False,
    "input_token": 0
}
