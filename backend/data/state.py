"""
PathFinder shared state — the single source of truth.

Every agent reads from and writes back to this state.
Orchestrator holds the full state. Agents get compressed handoffs.
"""

from typing import TypedDict, Annotated
from langgraph.graph import add_messages


class PathFinderState(TypedDict):
    # ─── LAYER 1: CONVERSATION ─────────────────────────
    messages: Annotated[list, add_messages]
    # Auto-appends via LangGraph's add_messages reducer.
    # When you return {"messages": [new_msg]}, it APPENDS, not overwrites.

    profile_summary: str
    # Running text summary of what we know about the user.
    # Orchestrator updates this after each agent returns.
    # Agents receive THIS instead of full message history.

    purpose_message: Annotated[list, add_messages]
    goals_message: Annotated[list, add_messages]
    job_message: Annotated[list, add_messages]
    major_message: Annotated[list, add_messages]
    uni_message: Annotated[list, add_messages]
    purpose_content: str
    goals_content: str
    job__content: str
    major_content: str
    uni_content: str

    # ─── LAYER 2: EXTRACTED PROFILE ────────────────────
    track: str | None
    # "A" (uni required) | "B" (uni optional) | "C" (uni not required)

    purpose: dict | None
    # Extracted from Stage 1 drill. Keys: core_desire, work_relationship,
    # ai_stance, location_vision, risk_philosophy

    goals_long: dict | None
    # Stage 2. Keys: income_target, ownership_model, team_size, output_type

    goals_short: dict | None
    # Stage 3. Keys: skill_targets, portfolio_goal, credential_needed

    job: dict | None
    # Stage 4. Keys: role_category, company_stage, day_to_day, autonomy_level

    major: dict | None
    # Stage 5. Keys: field, curriculum_style, required_skills_coverage

    university: dict | None
    # Stage 6 output. Ranked list of universities with fit scores + reasoning.

    country_scope: str | None
    # "vietnam" | "abroad" | "both" — set by scope agent

    # ─── LAYER 3: SCORES ──────────────────────────────
    confidence_scores: dict
    # Per-stage confidence. {"purpose": 0.8, "goals_long": 0.6, ...}
    # Written ONLY by the Scoring Agent.

    fit_scores: dict
    # Per-university fit. {"fpt": {"purpose": 0.7, ...}, ...}
    # Written by Scoring Agent after Uni Agent provides candidates.

    # ─── LAYER 4: SYSTEM META ─────────────────────────
    current_agent: str
    # Which agent is currently active. Set by orchestrator.

    drill_depth: dict
    # How many drill rounds per stage. {"purpose": 3, "job": 1, ...}

    escalation_flags: list[str]
    # ["contradiction_purpose_job", "parent_pressure", ...]

    troll_warnings: int
    # 0-3. Terminate session at 3.

    uni_data: list[dict]
    # Loaded by Research Agent from JSON files.

    verdict: dict | None
    # Verdict check results. {"purpose": "APPROVE", "job": "REJECT: ...", ...}


# ─── DEFAULT STATE (used when creating a new session) ──────────────
DEFAULT_STATE: PathFinderState = {
    "messages": [],
    "profile_summary": "",
    "purpose_message": "",
    "goals_message": "",
    "job_message": "",
    "major_message": "",
    "uni_message": "",
    "purpose_content": "",
    "goals_content": "",
    "job_content": "",
    "major_content": "",
    "uni_content": "",
    "track": None,
    "purpose": None,
    "goals_long": None,
    "goals_short": None,
    "job": None,
    "major": None,
    "university": None,
    "country_scope": None,
    "confidence_scores": {},
    "fit_scores": {},
    "current_agent": "orchestrator",
    "drill_depth": {},
    "escalation_flags": [],
    "troll_warnings": 0,
    "uni_data": [],
    "verdict": None,
}
