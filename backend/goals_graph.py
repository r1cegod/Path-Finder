import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict

from backend.data.contracts.stages import (
    STAGE_TO_PROFILE_KEY,
    STAGE_TO_QUEUE_KEY,
    STAGE_TO_REASONING_KEY,
)
from backend.data.contracts.confidence import DONE_CONFIDENCE_THRESHOLD
from backend.data.prompts.goals import (
    CONFIDENT_PROMPT as GOALS_CONFIDENT_PROMPT,
    GOALS_DRILL_PROMPT,
)
from backend.data.state import GoalsProfile, PathFinderState, StageReasoning
from backend.stage_profile_utils import apply_reopen_invalidation, normalize_stage_profile

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# contract prep
STAGE = "goals"
PROFILE_KEY = STAGE_TO_PROFILE_KEY[STAGE]
QUEUE_KEY = STAGE_TO_QUEUE_KEY[STAGE]
REASONING_KEY = STAGE_TO_REASONING_KEY[STAGE]


def get_stage_reasoning(state: PathFinderState) -> StageReasoning:
    raw = state.get("stage_reasoning") or {}
    if isinstance(raw, dict):
        return StageReasoning(**raw)
    return raw


def get_current_stage(state: PathFinderState) -> str:
    stage_raw = state.get("stage") or {}
    if isinstance(stage_raw, dict):
        return stage_raw.get("anchor_stage") or stage_raw.get("current_stage", STAGE)
    return getattr(stage_raw, "anchor_stage", "") or getattr(stage_raw, "current_stage", STAGE)


def _extract_field_meta(field: object) -> tuple[str, float]:
    if field is None:
        return "", 0.0
    if isinstance(field, dict):
        return str(field.get("content", "") or ""), float(field.get("confidence", 0.0) or 0.0)
    return str(getattr(field, "content", "") or ""), float(getattr(field, "confidence", 0.0) or 0.0)


def _infer_probe_field(goals: object) -> str:
    if goals is None:
        return "income_target"

    if isinstance(goals, dict):
        long_profile = goals.get("long") or {}
        short_profile = goals.get("short") or {}
    else:
        long_profile = getattr(goals, "long", None) or {}
        short_profile = getattr(goals, "short", None) or {}

    ordered_fields = [
        ("income_target", long_profile),
        ("ownership_model", long_profile),
        ("portfolio_goal", short_profile),
        ("skill_targets", short_profile),
        ("credential_needed", short_profile),
        ("autonomy_level", long_profile),
        ("team_size", long_profile),
    ]

    for field_name, profile in ordered_fields:
        if isinstance(profile, dict):
            field = profile.get(field_name)
        else:
            field = getattr(profile, field_name, None)
        content, confidence = _extract_field_meta(field)
        if confidence <= DONE_CONFIDENCE_THRESHOLD or content in {"", "unclear", "not discussed", "none"}:
            return field_name

    return "income_target"


def _default_probe_instruction(field_name: str) -> str:
    defaults = {
        "income_target": "force a concrete number, timeframe, and the trade-off required to reach it.",
        "ownership_model": "force a choice between structural paths and the real cost each path demands.",
        "portfolio_goal": "force a concrete 1-year artifact or market proof instead of vague preparation.",
        "skill_targets": "force specific job-relevant skills rather than abstract or school-only preparation.",
        "credential_needed": "force justification for why a degree or credential is structurally necessary.",
        "autonomy_level": "force a trade-off between freedom, management, and income stability.",
        "team_size": "force a choice between solo control and the realities of larger-team ambition.",
    }
    return defaults.get(field_name, "force a concrete trade-off instead of a vague preference.")


def _strip_legacy_probe_suffix(text: str) -> str:
    # Defensive cleanup: the analyst now returns structured probe fields, but the model can
    # still leak an old-style trailing "PROBE:" line into goals_summary.
    lines = [line for line in (text or "").strip().splitlines() if line.strip()]
    while lines and lines[-1].strip().upper().startswith("PROBE:"):
        lines.pop()
    return "\n".join(lines).strip()


def _compose_probe_line(response: "GoalsAnalysis", is_current_stage: bool, goals: object) -> str:
    if not is_current_stage:
        return "PROBE: NONE (passive analysis only)"

    field_name = (response.probe_field or "").strip()
    if not field_name or field_name.upper() == "NONE":
        field_name = _infer_probe_field(goals)

    probe_instruction = (response.probe_instruction or "").strip()
    if probe_instruction.upper().startswith("PROBE:"):
        probe_instruction = probe_instruction.split(":", 1)[1].strip()
    if not probe_instruction or probe_instruction.upper().startswith("NONE"):
        probe_instruction = _default_probe_instruction(field_name)

    return f"PROBE: {field_name} - {probe_instruction}"


class GoalsAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals_summary: str
    probe_field: str
    probe_instruction: str


class ConfidentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals: GoalsProfile


llm = ChatOpenAI(model="gpt-5.4-mini", max_tokens=450)
analysis_llm = llm.with_structured_output(
    GoalsAnalysis,
    method="function_calling",
)
confident_llm = llm.with_structured_output(
    ConfidentOutput,
    method="function_calling",
)


def goals_agent(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    stage_reasoning = get_stage_reasoning(state)
    goals = state.get(PROFILE_KEY)
    purpose = state.get("purpose")
    message_tag = state.get("message_tag")

    is_current_stage_bool = get_current_stage(state) == STAGE

    response = analysis_llm.invoke(
        [
            SystemMessage(
                GOALS_DRILL_PROMPT.format(
                    is_current_stage=str(is_current_stage_bool),
                    stage_reasoning=getattr(stage_reasoning, REASONING_KEY),
                    goals=goals or "",
                    purpose=purpose or "",
                    message_tag=message_tag or "",
                )
            )
        ]
        + messages
    )

    summary_body = _strip_legacy_probe_suffix(response.goals_summary)
    probe_line = _compose_probe_line(response, is_current_stage_bool, goals)
    full_summary = f"{summary_body}\n{probe_line}" if summary_body else probe_line

    updated = stage_reasoning.model_copy(update={REASONING_KEY: full_summary})
    return {"stage_reasoning": updated.model_dump()}


def confident_node(state: PathFinderState) -> dict:
    messages = state[QUEUE_KEY]
    goals = state.get(PROFILE_KEY)

    response = confident_llm.invoke(
        [SystemMessage(GOALS_CONFIDENT_PROMPT.format(
            goals=goals or "",
        ))] + messages
    )
    return {PROFILE_KEY: response.goals.model_dump()}


def reopen_invalidator_node(state: PathFinderState) -> dict:
    raw = state.get(PROFILE_KEY)
    goals = GoalsProfile(**raw) if isinstance(raw, dict) else raw
    if goals is None:
        return {}
    reopened = apply_reopen_invalidation(state, STAGE, goals)
    normalized = normalize_stage_profile(STAGE, reopened)
    return {PROFILE_KEY: normalized.model_dump()}


builder = StateGraph(PathFinderState)
builder.add_node("goals_agent", goals_agent)
builder.add_node("confident", confident_node)
builder.add_node("reopen_invalidator", reopen_invalidator_node)
builder.add_edge(START, "confident")
builder.add_edge("confident", "reopen_invalidator")
builder.add_edge("reopen_invalidator", "goals_agent")
builder.add_edge("goals_agent", END)
goals_graph = builder.compile()
